dev_config = False

class Config(object):
    DEBUG = True
    hostname = 'eegplatform2.c3ogcwmqzllz.us-east-1.rds.amazonaws.com'
    username = 'eeg2019'
    password = 'iO30IG1HbXcJ'
    dbname = 'eegplatform'
    #TODO: Fix the below by using the above.
    SQLALCHEMY_DATABASE_URI = "postgresql://eeg2019:iO30IG1HbXcJ@eegplatform2.c3ogcwmqzllz.us-east-1.rds.amazonaws.com/eegplatform"
    # SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POSTGRESCONNSTRING = "host='%s' dbname='%s' user='%s' password='%s'" % (hostname, dbname, username, password)
    ACCESS_KEY_ID = 'AKIAIPBTJEERNLJN2YPA'
    ACCESS_SECRET_KEY = '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'
    BUCKET_NAME = 'eegdata2'

class DevConfig(Config):
    SQLALCHEMY_DATABASE_URI = ''

    ACCESS_KEY_ID = ''
    ACCESS_SECRET_KEY = ''
    BUCKET_NAME = ''

def getConfig():
    return DevConfig() if dev_config else Config()
