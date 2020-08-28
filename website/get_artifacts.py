import sys
import os
sys.path.insert(0, os.path.abspath('../code/spark/'))
sys.path.insert(0, os.path.abspath('../code/'))
from artifact_detect import *
from SimpleHelper import wrapper_write_artifact


def extract_edf(file_path):
    """
    Extract time series data from an edf file.
    :param file_path: local file path for a single edf file
    :return: time series data, channel names, info of each signal, 
    headers, and signal metadata
    """
    f = pyedflib.EdfReader(file_path)

    # metadata
    meta = print_object_attrs(f)

    # time series data
    channelNames = f.getSignalLabels()
    signal_info = f.getSignalHeaders()
    headers = f.getHeader()
    headers = {key: str(value) for key, value in headers.items()}
    n = f.signals_in_file
    ts_data = np.zeros((n, f.getNSamples()[0]))
    for i in np.arange(n):
        ts_data[i, :] = f.readSignal(i)

    return ts_data, channelNames, signal_info, headers, meta


def get_artifacts(raw_data, channels):
    artifact_idx = {}
    for ch, data in zip(channels, raw_data):
        artifact_idx[ch] = get_bad_intervals(data).tolist()
    return artifact_idx


def insert_artifact(raw_data, channels, file_id, study_id):
    artifact_idx = get_artifacts(raw_data, channels)
    wrapper_write_artifact(artifact_idx, file_id, study_id)


def async_push_artifact(app, raw_data, channels, file_id, study_id):
    with app.app_context():
        insert_artifact(raw_data, channels, file_id, study_id)
