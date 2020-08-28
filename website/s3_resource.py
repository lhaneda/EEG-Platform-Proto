import boto3
from werkzeug import secure_filename
from configmodule import getConfig
import io
import base64
import tempfile

config = getConfig()

s3_resource = boto3.resource(
    's3',
    aws_access_key_id = config.ACCESS_KEY_ID,
    aws_secret_access_key = config.ACCESS_SECRET_KEY
)

s3_bucket = s3_resource.Bucket(config.BUCKET_NAME)

def saveimg(plt, filename, study_id):
    with tempfile.NamedTemporaryFile() as f:
        plt.savefig(f.name, format='png')
        img_data = open(f.name, "rb")
        s3_bucket.put_object(Key='s' + study_id + '/image/' + filename +  '.png', Body=img_data,
                                 ContentType="image/png")

def create_key(study_id, file):
    return "s" + study_id + "/" + secure_filename(file.filename)

def upload_file(key, file):
    """Uploads file to the user's folder in S3 bucket"""
    # create unique key/path for bucket
    try:
        s3_bucket.put_object(Key=key, Body=file)
    except Exception as e:
        print(e)

def delete_file(key):
    """Deletes file from bucket given the key"""
    try:
        s3_bucket.Object(key).delete()
    except Exception as e:
        print(e)

def download_file(key):
    """Gets file from bucket with given key"""
    return s3_bucket.Object(key).get()

def get_imagedata(study_id, filename):

    tdta = download_file( 's' + study_id + '/image/' + filename + '.png' )['Body'].read()
    img64 = base64.b64encode(tdta).decode('utf8')

    return img64


def get_files(username):
    """Returns a list of files in the user's folder"""

    # prefix with folder name
    dir = username + "/"

    unsorted_keys = []
    # Use prefix filter to only get user's files
    for object_summary in s3_bucket.objects.filter(Prefix=dir):
        unsorted_keys.append([object_summary.key, object_summary.last_modified.strftime("%Y-%m-%d %H:%M:%S")])

    return unsorted_keys
