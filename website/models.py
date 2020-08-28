from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import INTEGER

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(80), nullable=False)
    study_id = db.Column(db.Integer, db.ForeignKey('study.id'), nullable=False)
    s3_key = db.Column(db.String(80), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    srate = db.Column(db.Integer, nullable=False)
    length = db.Column(db.Float, nullable=False) # in seconds
    channel_num = db.Column(db.Integer, nullable=False)
    procFlag = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, nullable=False)
    dateUpload = db.Column(db.String(30), nullable=False)
    study_id = db.Column(db.Integer, db.ForeignKey('study.id'))

    def __init__(self, filename, s3_key, user_id, username, srate,
                 length, channel_num, procFlag, attempts, dateUpload,
                 study_id):
        self.filename = filename
        self.s3_key = s3_key
        self.procFlag = procFlag
        self.user_id = user_id
        self.username = username
        self.srate = srate
        self.length = length
        self.channel_num = channel_num
        self.dateUpload = dateUpload
        self.attempts = attempts
        self.study_id = study_id

    def increment_attempt(self, attempts):
        self.attempts = attempts + 1

    def change_proc_flag(self, procFlag):
        self.procFlag = procFlag

    def get_proc_status(self, procFlag):
        if procFlag == 0:
            return "Pending"
        elif procFlag == 1:
            return "Processing"
        elif procFlag == 2:
            return "Done"
        else:
            return "Unknown"


class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'))
    study_id = db.Column(db.Integer, db.ForeignKey('study.id'))
    channel = db.Column(db.String(10), nullable=False)
    band = db.Column(db.String(10), nullable=False)
    function = db.Column(db.String(10), nullable=False)
    value = db.Column(db.Float)
    start_time = db.Column(db.Float)
    end_time = db.Column(db.Float)
    ts_completed = db.Column(db.String(30), nullable=True)

    def __init__(self, file_id, study_id, channel, band, function, value, start_time, end_time, ts_completed):
        self.file_id = file_id
        self.study_id = study_id
        self.channel = channel
        self.band = band
        self.function = function
        self.value = value
        self.start_time = start_time
        self.end_time = end_time
        self.ts_completed = ts_completed


class Channels(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'))
    channel = db.Column(db.String(3))
    ch_max = db.Column(db.Float)
    ch_median = db.Column(db.Float)
    ch_min = db.Column(db.Float)
    ch_98perc = db.Column(db.Float)
    ch_2perc = db.Column(db.Float)
    length = db.Column(db.Float)

    def __init__(self, file_id, channel, ch_max, ch_median, ch_min,
                 ch_98perc, ch_2perc, length):
        self.file_id = file_id
        self.channel = channel
        self.ch_max = ch_max
        self.ch_median = ch_median
        self.ch_min = ch_min
        self.ch_98perc = ch_98perc
        self.ch_2perc = ch_2perc
        self.length = length


class Study(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    study_name = db.Column(db.String(40), nullable=False)
    description = db.Column(db.String(500), nullable=True)

    def __init__(self, study_name, description):
        self.study_name = study_name
        self.description = description


class Collaborator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.Integer, db.ForeignKey('study.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, study_id, user_id):
        self.study_id = study_id
        self.user_id = user_id

class ToProcess(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'))
    study_id = db.Column(db.Integer, db.ForeignKey('study.id'))
    channel = db.Column(db.String(3), nullable=False)
    ### Long term band should NOT be nullable, but currently band chosen by process script.
    band = db.Column(db.String(10), nullable=True)
    function = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.Float)
    end_time = db.Column(db.Float)
    pflag = db.Column(db.Integer)
    attempts = db.Column(db.Integer)
    ### When it got submitted
    ts_submit = db.Column(db.String(30), nullable=False)


    def __init__(self, study_id, file_id, channel, band, function, start_time, end_time, pflag, attempts, ts_submit):
        self.file_id = file_id
        self.study_id = study_id
        self.channel = channel
        self.band = band
        self.function = function
        self.start_time = start_time
        self.end_time = end_time
        self.pflag = pflag
        self.attempts = attempts
        self.ts_submit =ts_submit

class Artifact(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), primary_key=True)
    study_id = db.Column(db.Integer, db.ForeignKey('study.id'))
    channel = db.Column(db.String(3), nullable=False)

    artifactAlgo = db.Column(db.String(40))
    artifactVersion = db.Column(db.String(40))
    artifactCompDate = db.Column(db.String(40))
    mask = db.Column(ARRAY(INTEGER, dimensions=2))

    def __init__(self, file_id, study_id, channel, artifactAlgo, artifactVersion, artifactCompDate, mask):
        self.file_id = file_id
        self.study_id = study_id
        self.channel = channel
        self.artifactAlgo = artifactAlgo
        self.artifactVersion = artifactVersion
        self.artifactCompDate = artifactCompDate
        self.mask = mask



## EOF ##
