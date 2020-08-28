from tempfile import NamedTemporaryFile
import psycopg2
import psycopg2.extras
from refactoredProcess import process_EZ
import arrow
import numpy as np
import time

import boto3
# To help import from different directories
from importlib import util
def moduleFromFile(module_name, file_path):
    spec = util.spec_from_file_location(module_name, file_path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
# print('Current dir: ' + os.getcwd())
configmod = moduleFromFile("configmodule", "../website/configmodule.py")
config = configmod.getConfig()
s3 = boto3.resource(
    's3',
    aws_access_key_id = config.ACCESS_KEY_ID,
    aws_secret_access_key = config.ACCESS_SECRET_KEY
)
bucket = s3.Bucket(config.BUCKET_NAME)

conn = psycopg2.connect(config.POSTGRESCONNSTRING)

### Notes
### Simple helper will never run on more than one thread b/c even if the process takes to long, we have flock in front of it
### flock prevents more than once instance of this running.
### status = 0 => not processed
### status = 1 => in process
### status = 2 => complete

def getNextFileId():
    '''Gets the next file id to process, returns None otherwise'''
    cur = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
    cur.execute("""
    SELECT id as file_id FROM public.file
    WHERE "procFlag" = 0 and "attempts" < 5
    ORDER BY "dateUpload" ASC LIMIT 1;
    """)
    r = cur.fetchone();

    if r is None:
        return None

    file_id = r['file_id']

    ## Update file flag and increment attempts
    cur.execute("""
        UPDATE public.file
        SET "procFlag" = 1, "attempts" = "attempts" + 1
        WHERE id = %s
    """, (file_id,))
    conn.commit()

    return file_id;

def getParams(file_id):
    '''Gathers the parameters needed for processing, returns None if not found'''

    cur = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
    cur.execute("""
    SELECT id as tp_id, file_id, study_id, channel, band, function, start_time, end_time
    FROM
        (SELECT DISTINCT ts_submit
        FROM public.to_process
        WHERE file_id = %s and pflag = 0 and attempts < 5
        LIMIT 1) as n_tp
    JOIN
        public.to_process as tp
    ON tp.ts_submit = n_tp.ts_submit
    WHERE tp.file_id = %s""", (file_id, file_id))

    params = cur.fetchall()
    if len(params) == 0:
        return None

    ## Update flag and increment attempts for each channel
    for param in params:
        tp_id = param['tp_id']
        cur.execute("""
            UPDATE public.to_process
            SET "pflag" = 1, "attempts" = "attempts" + 1
            WHERE id = %s;
        """, (tp_id,))
    conn.commit()

    return params

def extractParams(paramResults):
    '''Parse channel list and features for processing script'''
    chnls = []
    feats = []
    for param in paramResults:
        chnl = param['channel']
        if chnl not in chnls:
            chnls.append(chnl)

        feat = param['function']
        if feat not in feats:
            feats.append(feat)

    return chnls, feats

def getS3Key(file_id):
    cur = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
    cur.execute("""
    SELECT s3_key FROM public.file WHERE id = %s
    """, (file_id, ))

    r = cur.fetchone()
    return r['s3_key']

def downloadFile(s3_key):
    ftemp = NamedTemporaryFile(delete=True)
    bucket.download_file(s3_key, ftemp.name)
    ftemp.flush()
    return ftemp

def sendResults(file_id, study_id, start_time, end_time, r):
    print('Sending results ...')
    ts_completed = arrow.utcnow().to('US/Pacific').format('YYYY-MM-DD hh:mm:ss A')

    cur = conn.cursor()
    for chnl in r:
        for func in r[chnl]:
            for band in r[chnl][func]:
                #NOTE: np infinity values will be converted to Null in SQL
                val = r[chnl][func][band]

                ## This placeholder method takes care of any strings and converts python's None to SQL Null values
                cur.execute("""INSERT INTO public.result (file_id, study_id, channel, band, function, value, start_time, end_time, ts_completed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (file_id, study_id, chnl , band , func, val, start_time, end_time, ts_completed))

    conn.commit()
    print('Results ready to view')
    return None

def resetFileStatus(file_id):
    cur = conn.cursor()
    cur.execute("""
        UPDATE public.file
        SET "procFlag" = 0
        WHERE id = %s
    """, (file_id,))
    conn.commit()

def resetParamsStatus(params):
    cur = conn.cursor()

    for p in params:
        cur.execute("""
            UPDATE public.to_process
            SET "pflag" = 0
            WHERE id = %s
        """, (p['tp_id'],))
    conn.commit()

def setParamsStatusDone(params):
    cur = conn.cursor()
    for p in params:
        cur.execute("""
            UPDATE public.to_process
            SET "pflag" = 2
            WHERE id = %s
        """, (p['tp_id'],))
    conn.commit()

def setFileStatusDone(file_id):
    cur = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT COUNT(*) as count
        FROM public.to_process
        WHERE file_id = %s and pflag = 0 and attempts < 5
    """, (file_id,))

    tp = cur.fetchone()

    if int(tp['count']) > 0:
        ## This file has another set of params not processed yet, fully reset status
        cur.execute("""
            UPDATE public.file
            SET "procFlag" = 0, "attempts" = 0
            WHERE id = %s
        """, (file_id,))
    else:
        cur.execute("""
            UPDATE public.file
            SET "procFlag" = 2
            WHERE id = %s
        """, (file_id,))

    conn.commit()

def writeArtifacts(conn, file_id, study_id, res):
    cur = conn.cursor()
    artifact_algo = 'std'
    artifact_version = 'v0'
    ts_completed = arrow.utcnow().to('US/Pacific').format(
        'YYYY-MM-DD hh:mm:ss A')
    for channel in res:
        mask = res[channel]
        mask = str(mask).replace('[', '{').replace(']', '}')
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO public.artifact (file_id, study_id, channel, "artifactAlgo", "artifactVersion", "artifactCompDate", mask)
        VALUES (%s, %s, '%s', '%s','%s', '%s', '%s');"""
                    % (file_id, study_id, channel, artifact_algo, artifact_version, ts_completed, mask ))
    conn.commit()
    cur.close()

def wrapper_write_artifact(arti_dict, file_id, study_id):
    conn = psycopg2.connect(config.POSTGRESCONNSTRING)
    writeArtifacts(conn, file_id, study_id, arti_dict)
    conn.close()

def main():
    print('Checking database for any waiting files ...')
    start = time.time()

    file_id = getNextFileId()
    if file_id is None:
        print('No files to process.')
        return None #exit

    print('Processing file with id: ' + str(file_id))
    params = getParams(file_id)
    if params is None:
        print('ERROR: There are no parameters found')
        resetFileStatus(file_id)
        return None

    ### Only continue if there are files & there are parameters

    ## Can assume params min len is 1
    study_id = params[0]['study_id']
    start_time = int(params[0]['start_time'])
    end_time = int(params[0]['end_time'])

    chnls, feats = extractParams(params)
    print('channels: ' + str(chnls))
    print('feats: ' + str(feats))

    s3_key = getS3Key(file_id)

    try:
        ftemp = downloadFile(s3_key)
        results = process_EZ(ftemp.name, chnls, feats, start_time, end_time)
        # print(results)
        elapsed = (time.time() - start) % 60 #conver to seconds
        print('Elapsed time to process: ' + str(elapsed) + ' sec')
    except Exception as e:
        print("ERROR: {}".format(e))
        results = None # used to indicate an error

    if results is None:
        resetFileStatus(file_id)
        resetParamsStatus(params)
    else:
        setParamsStatusDone(params)
        setFileStatusDone(file_id)
        sendResults(file_id, study_id, start_time, end_time, results)


if __name__ == '__main__':
    main()
    conn.close()

## EOF ##
