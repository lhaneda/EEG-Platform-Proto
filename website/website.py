#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import timedelta
from flask import Flask, session, redirect, render_template, url_for, request, flash, Response
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from flask_login import (current_user, LoginManager, login_required,
                         login_user, logout_user, UserMixin)
from wtforms import PasswordField, StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, Email
from wtforms.widgets import TextArea

import os
from werkzeug import secure_filename
import arrow
import re
from threading import Thread
import plot_generator
import copy

from tempfile import NamedTemporaryFile
import pyedflib
#from wtforms.validators import ValidationError
from wtforms.validators import StopValidation

import s3_resource
import numpy as np

# from models import db, User, File, Result, Channels, Study, Collaborator, ToProcess,
from models import *
import configmodule
#from configmodule import dev_config

import logging
from logging.handlers import TimedRotatingFileHandler

import get_artifacts

import make_csv

# Create and configure an app
app = Flask(__name__)

# logger setup
logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%d-%b-%y %H:%M:%S')
logger = logging.getLogger()
logger.setLevel(logging.ERROR)
log_filename = 'app_log.log'
handler = TimedRotatingFileHandler(log_filename, when='W0', backupCount=2)
handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
logger.addHandler(handler)

app.config.from_object(configmodule.getConfig())

with app.app_context():
    db.init_app(app)
    db.create_all()
    db.session.commit()

def EEGValid(form, field ):

    ### This validator is not working, but the basic idea is here
    file = field.data
    ### This helper loads a file and makes sure that it is readable and, if it is, returns
    ### basic statistics, note that it takes a file object and then creates a tempfile based on it.
    ftemp = NamedTemporaryFile(delete=False)
    file.save(ftemp)
    ftemp.flush()
    if os.path.getsize(ftemp.name) > 0:
        try:
            f = pyedflib.EdfReader(ftemp.name)

            rawdata = np.zeros((f.signals_in_file, f.getNSamples()[0]))
            for i in np.arange(f.signals_in_file):
                rawdata[i, :] = f.readSignal(i)  # shitty implementation of pyedflib

            # Can create and populate now to reference later
            form.eeg_data = {
                'channels' : f.getSignalLabels()
                , 'srate' : f.getSampleFrequency(3)
                , 'signal_num' : f.signals_in_file
                , 'length' : f.getNSamples()[0] / f.getSampleFrequency(3)
                , 'raw_data' : rawdata
            }

        except (FileNotFoundError, OSError) as e:
            logger.error('File with name %s cannot be processed', field.data.filename, exc_info=True)
            raise StopValidation("File Error, cannot be processed")
    else:
        logger.error('File with name %s is empty', field.data.filename)
        raise StopValidation("ERROR: File is Empty, NO FILE UPLOADED")

login_manager = LoginManager()
login_manager.login_view = 'login'
bootstrap = Bootstrap(app)

class RegistrationForm(FlaskForm):
    username = StringField('Username:', validators=[DataRequired()])
    email = StringField('Email:', validators=[DataRequired(), Email()])
    access_code = StringField('Access Code:', validators=[DataRequired()])
    password = PasswordField('Password:', validators = [DataRequired()])
    password_confirmation = PasswordField('Repeat Password:', validators=[DataRequired()]) #Need to be same as the other one.
    submit = SubmitField('Submit')



class ParametersForm(FlaskForm):
    #channel_num = StringField('Channel Num:',  validators=[DataRequired()])
    #band = StringField('Enter bands in Hz:',  validators=[DataRequired()])
    band = StringField('Enter bands in Hz:', validators=None, widget=TextArea())
    function = StringField('Function: ', validators=[DataRequired()])
    #features = SelectField('Feature: ', choices=[('SampE'), ('Power')])
    start_time = FloatField('Start Time(sec):', validators=[DataRequired()])
    segment_len = FloatField('Time Segment Length(sec):', validators=[DataRequired()])
    #file_to_exclude  = StringField('Files to exclude: ', validators=[DataRequired()])
    channels_to_exclude = StringField('Channls to exclude: ', validators=[DataRequired()])
    submit = SubmitField('Submit')

class LogInForm(FlaskForm):
    username = StringField('Username:', validators=[DataRequired()])
    password = PasswordField('Password:', validators=[DataRequired()])
    submit = SubmitField('Login')


class UploadFileForm(FlaskForm):
    file_selector = FileField('File', validators=[FileRequired(), EEGValid])
    submit = SubmitField('Submit')


class StudyForm(FlaskForm):
    study_name = StringField('Study Name:', validators=[DataRequired()])
    collab_name = StringField('Collaborator Names:', validators=None, widget=TextArea())
    description = StringField('Description:', validators=None, widget=TextArea())
    submit = SubmitField('Create')


class EditStudyForm(FlaskForm):
    collab_name = StringField('Collaborator Names:', validators=None, widget=TextArea())
    description = StringField('Description:', validators=None, widget=TextArea())
    file_selector = FileField('File', validators=[FileRequired(), EEGValid])
    submit = SubmitField('Submit')


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)


@app.route('/register', methods=('GET', 'POST'))
def register():
    registration_form = RegistrationForm()
    if registration_form.validate_on_submit():
        username = registration_form.username.data
        password = registration_form.password.data
        password_confirmation = registration_form.password_confirmation.data
        email = registration_form.email.data

        if(password != password_confirmation):
            flash('Error - Password Mismatch<br/>', 'error' )

        match = re.search("[^a-zA-Z0-9]+", username)
        user_count = User.query.filter_by(username=username).count()
        + User.query.filter_by(email=email).count()
        if(user_count > 0):
            flash('Error - Existing user : ' + username + ' OR ' + email + '<br/>', 'error')
        elif match:
            flash('Error - Username contains special charcters<br/>', 'error')
        else:
            user = User(username, email, password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html', form=registration_form)


@login_manager.user_loader
def load_user(id):  # id is the ID in User.
    return User.query.get(int(id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LogInForm()
    if login_form.validate_on_submit():
        username = login_form.username.data
        password = login_form.password.data
        # Look for it in the database.
        user = User.query.filter_by(username=username).first()

        # Login and validate the user.
        if user is not None and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username and password combination!', 'error')
    return render_template('login.html', form=login_form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/upload/<study_id>', methods=['GET', 'POST'])
@login_required
def upload(study_id):

    username = current_user.username
    user_id = User.query.filter_by(username=username).all()[0].id
    collabs = Collaborator.query.filter_by(user_id=user_id).all()
    if not int(study_id) in [x.study_id for x in collabs]:
        flash('You are not authorized to access this Study', 'error')
        return render_template('index.html')

    form = UploadFileForm()
    if form.validate_on_submit():

        file = form.file_selector.data

        s3_key = s3_resource.create_key(study_id, file)
        ### Note that create_key puts an 's' in front of this ###

        '''Checking if file is already in db'''
        # NOTE: If s3_key ever becomes non-unique, can use username and filename
        if File.query.filter_by(s3_key=s3_key).count() > 0:
            flash('File already exists', 'error')
            return render_template('index.html')

        '''Uploading file to bucket'''
        file.seek(0)
        try:
            s3_resource.upload_file(s3_key, file=file)

        except Exception as e:
            # print(e)
            logger.error('Error occured uploading file with name %s to s3.', file.filename, exc_info=True)
            flash('An error occured uploading file, please try again.', 'error')
            return render_template('index.html')

        '''Insert meta-data to db'''
        filename = secure_filename(file.filename)
        # Can user_id be saved in current_user upon login?
        user_id = User.query.filter_by(username=username).first().id

        filename = secure_filename(file.filename)
        # Getting timestamp
        utc = arrow.utcnow()
        local = utc.to('US/Pacific')
        timestamp = local.format('YYYY-MM-DD hh:mm:ss A')

        # Preprocessed data
        srate = form.eeg_data['srate']
        channels = form.eeg_data['channels']
        length = form.eeg_data['length']
        raw_data = form.eeg_data['raw_data']

        file = File(filename, s3_key, user_id, username, srate, length,
                    len(channels), 0, 0, timestamp, study_id)

        db.session.add(file)
        db.session.commit()
        db.session.refresh(file)

        # Get the artifacts for the channels in the edf file
        #Thread(target=get_artifacts.async_push_artifact, args=(app, raw_data, channels, file.id, file.study_id)).start()

        # Generate Plot
        # plot_generator.createAndSavePlot(form.eeg_data, file, username)

        filename = copy.copy( secure_filename(file.filename) )
        Thread(target=plot_generator.asyncCreateAndSavePlot, args=(app, form.eeg_data, filename, study_id)).start()

        '''Insert channel list to db'''
        # NOTE: Had to commit file to table first to get a file_id auto generated
        file = File.query.filter_by(s3_key=s3_key).first()
        for channel, chan_num in zip(channels, range(0, raw_data.shape[0])):
            ch_max = max(raw_data[chan_num, :])
            ch_median = np.median(raw_data[chan_num, :])
            ch_min = min(raw_data[chan_num, :])
            ch_98perc = np.percentile(raw_data[chan_num, :], 98)
            ch_2perc = np.percentile(raw_data[chan_num, :], 2)
            new_channel = Channels(file.id, channel, ch_max, ch_median, ch_min, ch_98perc, ch_2perc, length)
            db.session.add(new_channel)
            db.session.commit()

            ### Holdover to handle putting something in the toprocess table.
            tp = ToProcess(file.study_id, file.id, channel, None, 'Power', 0, 30, 0, 0, timestamp)
            #tp = ToProcess(file.study_id, file.id, channel, None, 'Power', start_time, segment_len, 0, 0, timestamp)
            db.session.add(tp)
            db.session.commit()

        flash('File uploaded successfully', 'success')


    return render_template('upload.html', form=form)


##for downloading files from website
@app.route('/download', methods=['POST'])
@login_required
def download():
    key = request.form['key']

    file_obj = s3_resource.download_file(key)

    return Response(
        file_obj['Body'].read(),
        mimetype='text/plain',
        headers={"Content-Disposition": "attachment;filename={}".format(key)}
    )


@app.route('/delete_file/<file_id>', methods=['POST'])
def delete_file(file_id):

    file = File.query.filter_by(id=file_id).first_or_404()
    study_id = file.study_id # to redirect later

    ## Check if user trying to delte the file is the uploader
    if file.username != current_user.username:
        return redirect(url_for('page_not_found'))

    ## Delete file from s3 bucket
    s3_resource.delete_file(file.s3_key)
    # TODO: Delete plot images in bucket

    ## Delete file from db
    Channels.query.filter_by(file_id=file_id).delete()
    Result.query.filter_by(file_id=file_id).delete()
    ToProcess.query.filter_by(file_id=file_id).delete()
    Artifact.query.filter_by(file_id=file_id).delete()

    db.session.delete(file)
    db.session.commit()

    flash('File deleted successfully')
    return redirect(url_for('list_files', study_id=study_id))

@app.route('/delete_study/<study_id>', methods=['POST'])
def delete_study(study_id):
    study = Study.query.filter_by(id=study_id).first_or_404()

    Result.query.filter_by(study_id=study_id).delete()
    ToProcess.query.filter_by(study_id=study_id).delete()
    Collaborator.query.filter_by(study_id=study_id).delete()
    Artifact.query.filter_by(study_id=study_id).delete()

    files = File.query.filter_by(study_id=study_id).all()
    for file in files:
        s3_resource.delete_file(file.s3_key)
        # TODO: Delete plot images in bucket
        Channels.query.filter_by(file_id=file.id).delete()

    File.query.filter_by(study_id=study_id).delete()
    db.session.delete(study)
    db.session.commit()

    flash('Study deleted successfully')
    return redirect(url_for('study_arch'))

@app.route('/list_files/<study_id>', methods=['GET', 'POST'])
@login_required
def list_files(study_id):

    ### should be a function
    username = current_user.username
    user_id = User.query.filter_by(username=username).all()[0].id
    collabs = Collaborator.query.filter_by(user_id=user_id).all()
    if not int(study_id) in [x.study_id for x in collabs]:
        flash('You are not authorized to access this Study', 'error')
        return render_template('index.html')
    ### or maybe a decorator

    studies = Study.query.filter_by(id=study_id).first_or_404()
    files = File.query.filter_by(study_id=study_id).all()

    return render_template('list_files.html', files=files, study_id=study_id)


@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/', methods=('GET', 'POST'))
def index():
    return render_template('index.html',
                           authenticated_user=current_user.is_authenticated)


@app.route('/list_channels/<study_id>/<filename>', methods=['GET', 'POST'])
@login_required
def list_channels(study_id, filename):

    ### should be a function
    username = current_user.username
    user_id = User.query.filter_by(username=username).all()[0].id
    collabs = Collaborator.query.filter_by(user_id=user_id).all()
    if not int(study_id) in [x.study_id for x in collabs]:
        flash('You are not authorized to access this Study', 'error')
        return render_template('index.html')
    ### or maybe a decorator

    file = File.query.filter_by(study_id = study_id, filename=filename).first_or_404()
    # channels = Result.query.join(Channels, Result.file_id == Channels.file_id).filter_by(file_id=file.id).all()
    channels = Channels.query.filter_by(file_id=file.id).all()

    try:
        image_data = s3_resource.get_imagedata(study_id, filename)
    except Exception as e:
        logger.error('Could not find plot image for file %s ', filename, exc_info=True)
        image_data = None

    return render_template('list_channels.html', channels=channels,
                           image_data=image_data)





@app.route('/parameters/<study_id>', methods=['GET', 'POST'])
@login_required
#def parameter_page(filename, study_name):
def parameters(study_id):
    username = current_user.username
    form = ParametersForm()
#def parameter_page(file_id, study_id):
    #user = User.query.filter_by(username=username).first()<-first
    #user_id = user.id <-first
    user_id = User.query.filter_by(username=username).all()[0].id
    collabs = Collaborator.query.filter_by(user_id=user_id).all()
    if not int(study_id) in [x.study_id for x in collabs]:
        flash('You are not authorized to access this Study', 'error')
        return render_template('index.html')

    studies = Study.query.filter_by(id=study_id).first_or_404()
    files = File.query.filter_by(study_id=study_id).all()

    #file = File.query.filter_by(study_id = study_id, filename=filename).first_or_404()
    # channels = Result.query.join(Channels, Result.file_id == Channels.file_id).filter_by(file_id=file.id).all()
    #\channels = Channels.query.filter_by(study_id=study_id).all()

    channel_names = []
    channel_set = set(channel_names)
    #collab_names = []
    #all_studies = Collaborator.query.filter_by(user_id=user_id).all()
    #for cur_study in all_studies:
    # for curr_file in files:
    #     #collab_user_id = collab.user_id
    #     curr_file_channels = Channels.query.filter_by(file_id=curr_file.id).all()
    #     for chan in  curr_file_channels:
    #         channel_names.append(chan.channel)
    #         #channel_names.add(chan.channel)
    #     #channel_names.append(curr_file_channels)
    #     #collab_username = User.query.filter_by(id=collab_user_id).first()
    #         channel_set.add(chan.channel)
        #collab_names.append(collab_username.username)

    channel_set = sorted(channel_set)
    start_times = []
    ##chan_ex = []
    # chan_to_exclude = form.channels_to_exclude.data
    # for chan in chan_to_exclude.split(','):
    #     chan_ex.append(chan)
    #     if chan in channel_set:
    #         channel_set.remove(chan)
    #





    chan_ex = []



    #study = Study.query.filter_by(study_name=study_name).first_or_404()
    #filename = File.query.filter_by(username=current_user.username, filename=filename)
    #return render_template('list_files.html', files=files, study_id=study_id, form=parameter_form)
    #######return render_template('parameters.html', files=files, study_id=study_id)
    if form.validate_on_submit():
    #if form.submit.data:
        chan_to_exclude = form.channels_to_exclude.data
        for chan in chan_to_exclude.split(','):
            chan_ex.append(chan)
            if chan in channel_set:
                channel_set.remove(chan)

        for proc_file in files:
            #proc_file = File.query.filter_by(study_id=study_id, filename=myfile.filename).all()
            #files = File.query.filter_by(study_id=study_id).all()


            function = form.function.data
            #channel_num = form.channel_num.data
            band = form.band.data
            start_time = form.start_time.data

            segment_len = form.segment_len.data


            # Getting timestamp
            utc = arrow.utcnow()
            local = utc.to('US/Pacific')
            timestamp = local.format('YYYY-MM-DD hh:mm:ss A')
            #form.feature.choices = [("")]

            #for chan in channel_set:
            #    tp = ToProcess(proc_file.study_id, proc_file.id, chan, band, function, start_time, segment_len, 0, 0, timestamp)


            tp = ToProcess(proc_file.study_id, proc_file.id, 'C3', band, function, start_time, segment_len, 0, 0, timestamp)

            #for chan in start_time.split(','):
            #    start_times.append(stime)

            db.session.add(tp)
            db.session.commit()

            flash('ToProcess added!')

            ### Holdover to handle putting something in the toprocess table.
        #    channels_add = Channels.query.filter_by(file_id=curr_file.id).all() <PART FO MAY3RD EDITS
            # for chan in channels_add:
            #     #channel_names.append(chan.channel)
            #     tp = ToProcess(proc_file.study_id, proc_file.id, chan, None, 'Power', 0, 30, 0, 0, timestamp)
            #
            #
            #     db.session.add(tp)
            #     db.session.commit()


        # if form.submit.data:
        #     function = form.function.data
        #     channel_num = form.channel_num.data
        #     band = form.band.data
        #     if form.start_time.data:
        #         start_time = form.start_time.data
        #     else:
        #         start_time = ''
        #     #start_time = form.start_time.data
        #     for stime in start_time.split(','):
        #         start_times.append(stime)
        #
        #     segment_len = form.segment_len.data
        return redirect(url_for('parameters', study_id=study_id))

            #return redirect(url_for('edit_study', study_id=study_id))
            #flash('time segments added!')
            #session['start_times'] = form.start_time.data
            #form.start_time.data = ''
            #return redirect(url_for('parameters', study_id=study_id, start_time=start_time))
            #return redirect(url_for('parameters', study_name=study_name))


    #return render_template('parameters.html', form=parameter_form)
    return render_template('parameters.html', files=files, study_id=study_id, form=form, channels=channel_set)



@app.route('/study', methods=['GET', 'POST'])
@login_required
def study():
    username = current_user.username
    user = User.query.filter_by(username=username).first()
    submit = SubmitField('Create')
    form = StudyForm()

    if form.submit.data:
        study_name = form.study_name.data

        # Add description if given
        if form.description.data:
            description = form.description.data
        else:
            description = ''
        stu = Study(study_name, description)
        db.session.add(stu)
        db.session.commit()
        db.session.refresh(stu)

        # Add the owner to the collaborator table
        user_id = user.id
        study_id = stu.id
        collab = Collaborator(study_id, user_id)
        db.session.add(collab)
        db.session.commit()

        # Add other collaborators if given
        if form.collab_name.data:
            collab_names = form.collab_name.data
            for collaborator in collab_names.split(','):
                collab_user = User.query.filter_by(username=collaborator).first()
                collab = Collaborator(study_id, collab_user.id)
                db.session.add(collab)
                db.session.commit()
        return render_template('index.html',
                               authenticated_user=current_user.is_authenticated)
    return render_template('study.html', form=form)

@app.route('/edit_study/<study_id>', methods=['GET', 'POST'])
@login_required
def edit_study(study_id):

    ### should be a function
    username = current_user.username
    user_id = User.query.filter_by(username=username).all()[0].id
    collabs = Collaborator.query.filter_by(user_id=user_id).all()
    if not int(study_id) in [x.study_id for x in collabs]:
        flash('You are not authorized to access this Study', 'error')
        return render_template('index.html')
    ### or maybe a decorator

    form = EditStudyForm()
    submit = SubmitField('Add')

    # show current data
    study = Study.query.filter_by(id=study_id).first()
    cur_description = study.description
    cur_study_id = study.id
    cur_collabs = db.session.query(User)\
                            .join(Collaborator, Study)\
                            .filter(Collaborator.study_id==cur_study_id,
                                    Collaborator.user_id==User.id).all()

    # Add collaborators
    if form.collab_name.data:
        collab_names = form.collab_name.data
        study = Study.query.filter_by(study_id=study_id).first()
        study_id = study.id
        for collaborator in collab_names.split(','):
            collab_user = User.query.filter_by(username=collaborator).first()
            collab = Collaborator(study_id, collab_user.id)
            db.session.add(collab)
            db.session.commit()
            db.session.refresh(collab)

    # Edit description
    if form.description.data:
        description = form.description.data
        study = Study.query.filter_by(study_id=study_id).first()
        study.description = description
        db.session.commit()
        db.session.refresh(study)

    # list current files?

    # upload more files?

    if form.submit.data:
        return redirect(url_for('edit_study', study_id=study_id))
    return render_template('edit_study.html', form=form, study_id=study_id, study_name=study.study_name,
                           description=cur_description, collaborators=cur_collabs)


@app.route('/study_status/<study_id>', methods=['GET'])
@login_required
def study_status(study_id):

    ### should be a function
    username = current_user.username
    user_id = User.query.filter_by(username=username).all()[0].id
    collabs = Collaborator.query.filter_by(user_id=user_id).all()
    if not int(study_id) in [x.study_id for x in collabs]:
        flash('You are not authorized to access this Study', 'error')
        return render_template('index.html')
    ### or maybe a decorator

    study = Study.query.filter_by(id=study_id).first_or_404()
    study_id = study.id
    study_name = study.study_name
    collab_names = []
    collaborators = Collaborator.query.filter_by(study_id=study_id).all()
    for collab in collaborators:
        collab_user_id = collab.user_id
        collab_username = User.query.filter_by(id=collab_user_id).first()
        collab_names.append(collab_username.username)
    description = study.description
    return render_template('study_status.html', study_name=study_name,
                           description=description, collaborators=collab_names)


@app.route('/study_arch', methods=['GET', 'POST'])
@login_required
def study_arch():
    studies = []
    username = current_user.username

    # get user id
    user = User.query.filter_by(username=username).first()
    user_id = user.id

    # get all the study id's for the user
    # each one points at a different study of the user
    all_studies = Collaborator.query.filter_by(user_id=user_id).all()

    for cur_study in all_studies:
        study_dict = dict()
        study_dict['collab_user_name'] = []
        study_id = cur_study.study_id

        # get the study name
        study = Study.query.filter_by(id=study_id).first()
        study_dict['study_name'] = study.study_name
        study_dict['study_id'] = study_id

        # get all collaborator names except myself
        all_collabs = Collaborator.query.filter_by(study_id=study_id).all()
        for u in all_collabs:
            u_name = User.query.filter_by(id=u.user_id).first()
            if u_name.username != username:
                study_dict['collab_user_name'].append(u_name.username)

        # count total EEG files uploaded
        files = File.query.filter_by(study_id=study_id).all()
        #files = File.query.filter_by(study_id=study_id).all()
        study_dict['file_count'] = len(files)
        study_dict['files'] = files


        studies.append(study_dict)
    return render_template('study_arch.html', studies=studies)

####Result Page####
@app.route('/result/<study_id>/<filename>', methods=['GET', 'POST'])
@login_required
def results(study_id, filename):
    file = File.query.filter_by(study_id=study_id, filename=filename).first_or_404()
    result_file = Result.query.filter_by(file_id=file.id).all()

    return render_template('result.html', result_file=result_file, filename=filename, study_id=study_id)

# Downloading Results as a csv file
@app.route('/return_csv', methods=['POST'])
@login_required
def return_csv():
    filename = request.form['filename']
    study_id = request.form['study_id']

    # get result file
    file = File.query.filter_by(study_id=study_id, filename=filename).first_or_404()
    result_file = Result.query.filter_by(file_id=file.id).all()

    csv = 'Channel, Band, Function, Value, Start Time, End Time, TS Completed \n'

    # iterate through the results table
    for file in result_file:
        channel = str(file.channel)
        band = str(file.band)
        function = str(file.function)
        value = str(file.value)
        start_time = str(file.start_time)
        end_time = str(file.end_time)
        ts_completed = str(file.ts_completed)
        row = channel + ", " + band + ", " + function + ", " + value + ", " + start_time + ", " + end_time + ", " + ts_completed
        csv += row + '\n'

    return Response(
        csv,
        mimetype='text/csv',
        headers={"Content-Disposition":
                "attachment;filename=output.csv"}
    )


def page_not_found(e):
  return render_template('404.html'), 404

if __name__ == '__main__':
    # login_manager needs to be initiated before running the app
    login_manager.init_app(app)
    app.register_error_handler(404, page_not_found)
    # flask-login uses sessions which require a secret Key
    app.secret_key = os.urandom(24)

app.run(host='0.0.0.0', port=8080, debug=True)
