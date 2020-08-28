import pywt
import numpy as np
import pyedflib
import nolds
from tqdm import tqdm

default_channel_list = ["Fp1","Fp2","F7","F3","Fz","F4","F8","T7","C3","Cz",
                       "C4","T8","P7","P3","Pz","P4","P8","O1","O2"]

all_features = ["Power", "SampE"]

def power(y): return np.sum(y**2)/y.size
def sampE(y): return nolds.sampen(y)

function_dict = {"Power":power, "SampE":sampE}

def extract_time_series(filepath, time_start, time_end):
    file = pyedflib.EdfReader(filepath)             # read the edf file

    chnls = file.getSignalLabels()                  # channelnames (note that channels = Signals)
    srate = file.getSampleFrequency(3)              # sampling rate
    sigNum = file.signals_in_file                   # number of signals
    data = np.zeros((sigNum, file.getNSamples()[0]))
    for i in np.arange(sigNum):
        data[i, :] = file.readSignal(i)             # shitty implementation of pyedflib

    start = time_start*srate                        # start time
    end = time_end*srate                            # end time
    data = data[:,start:end]                        # truncating data to the max number of time periods (in s)

    return data, chnls, srate


def get_levels(srate):
    # Determine the number of levels required so that the lowest level approximation is roughly the
    # delta band (freq range 0-4 Hz)
    if   srate <= 128:  return 4
    elif srate <= 256:  return 5
    elif srate <= 512:  return 6
    elif srate <= 1024: return 7


def features_settings(features, wavelet, channelNames, data, nbands, mode, srate):
    print('Setting features ...')
    w = pywt.Wavelet(wavelet)
    for c, ch in enumerate(channelNames):

        m = np.mean(data[c])
        a_orig = data[c]-m                 # the original signal, initially, de-meaned
        a = a_orig

        rec_a,rec_d = [] ,[]               # all the approximations and details

        for i in range(nbands):
            (a, d) = pywt.dwt(a, w, mode)
            f = pow(np.sqrt(2.0), i+1)
            rec_a.append(a/f)
            rec_d.append(d/f)

        # Use the details and last approximation to create all the power-of-2 freq bands
        f_labels,freqband = ['A0'],[a_orig] # A0 is the original signal
        fs = [srate]
        f = fs[0]
        N = len(a_orig)

        for j,r in enumerate(rec_d):
            freq_name = 'D' + str(j+1)
            f_labels.append(freq_name)
            freqband.append(r[0:N])          # wavelet details for this band
            fs.append(f)
            f = f/2.0

        # We need one more
        f = f/2.0
        fs.append(f)

        # Keep only the last approximation
        j = len(rec_d)-1
        freq_name = 'A' + str(j+1)
        f_labels.append(freq_name)
        freqband.append(rec_a[j])       # wavelet approximation for this band

    print("Done setting features")
    return f_labels, freqband


def compute_nonrqa_features(features, channelNames, freqbands, f_labels, results):
    #--------------------------------------------------------------------
    # Compute features such as Power, Sample Entropy, Hurst parameter, DFA, Lyapunov exponents on each of the frequency bands
    #--------------------------------------------------------------------

    for c, ch in enumerate(tqdm(channelNames)):
        for i, y in enumerate(freqbands):
            for feat in features:
                results[ch][feat][f_labels[i]] = function_dict[feat](y)


def prep_results(features, t_chnls):
    results = {}

    for feat in features:
        if feat not in all_features:
            print("WARNING: Feature {} is not supported, no calculations will be made".format(feat))
            del features[feat]

    for chnl in t_chnls:
        if chnl not in default_channel_list:
            print("WARNING: Channel {} is not supported, no calculations will be made".format(chnl))
            del channelist[chnl]
        else:
            results[chnl] = {}
            for feat in features:
                results[chnl][feat] = {}
    return results

# Data pulled in EEGValid: channels, srate, rawdata, signal_num, length, raw_data
'''
Input:
    - channelist: channels to be analyzed
    - features: features to compute
'''
def process_EZ(filepath, channelist=default_channel_list, features=all_features, time_start=0, time_end=30):
    print('Processing ' + filepath)

    if time_start < 0 or time_end < time_start:
        print("ERROR: Unacceptable time start and/or time end")
        return None

    wavelet, mode = 'db4','cpd' #if constants, can move out of func

    results = prep_results(features, channelist)
    # TODO: check channelist against actual channels in file?

    data, temp_chnls, srate = extract_time_series(filepath, time_start, time_end)
    levels = 2 ## swapped this from levels = get_levels(srate) for simplicity
    nbands = levels+1

    chnls = []
    for chnl in channelist:
        if chnl in temp_chnls and chnl in default_channel_list:
            chnls.append(chnl)

    ## computing features
    f_labels, freqbands = features_settings(features, wavelet, chnls, data, nbands, mode, srate)
    compute_nonrqa_features(features, chnls, freqbands, f_labels, results)

    return results

# testFile = './data/sample/20180422091207_B9-1-2 2yr.edf'
# r = process_EZ(testFile)
# print(r)

## EOF ##
