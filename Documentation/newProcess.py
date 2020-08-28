
import pywt
import numpy as np
import pyedflib
import nolds
from tqdm import tqdm

max_nt = 30 # length of time segment in seconds
all_features = ["Power", "SampE"]

master_channel_list = ["Fp1","Fp2","F7","F3","Fz","F4","F8","T7","C3","Cz",
                       "C4","T8","P7","P3","Pz","P4","P8","O1","O2"]

def power(y): return np.sum(y**2)/y.size
def sampE(y): return nolds.sampen(y)

function_dict = {"Power": power,"SampE":sampE}

class Data:

    def __init__(self, filepath, max_nt):
        self.wavelet, self.mode = 'db4','cpd'
        self.D = {}
        self.data,self.channelNames,self.srate = self.extract_time_series(filepath,max_nt)
        self.levels = 2 
        ## Nick swapped this from self.levels = self._set_levels() to 2 for simplicity.
        #self._set_levels()
        self.nbands = self.levels+1

    def _set_levels(self):
        # Determine the number of levels required so that the lowest level approximation is roughly the
        # delta band (freq range 0-4 Hz)
        if   self.srate <= 128:  levels = 4
        elif self.srate <= 256:  levels = 5
        elif self.srate <= 512:  levels = 6
        elif self.srate <= 1024: levels = 7
        
        return levels

    def extract_time_series(self,filepath,max_nt=30):
        print(f'Processing {filepath}')
        f = pyedflib.EdfReader(filepath)         # read the edf file

        channelNames = f.getSignalLabels()       # channelnames (note that channels = Signals)
        srate = f.getSampleFrequency(3)          # sampling rate
        n = f.signals_in_file                    # number of signals
        data = np.zeros((n, f.getNSamples()[0]))
        for i in np.arange(n):
            data[i, :] = f.readSignal(i)         # shitty implementation of pyedflib
        nt = max_nt*srate                        # number of time periods
        m1 = 0                                   # start time
        m2 = m1 + nt                             # end time
        data = data[:,m1:m2]                     # truncating data to the max number of time periods (in s)
        return data,channelNames,srate

    def _features_settings(self,chnls,all_features):
        print('Setting features....')
        w = pywt.Wavelet(self.wavelet)
        for c, ch in enumerate(self.channelNames):

            if ch in chnls:
                self.D[ch] = {}
                m = np.mean(self.data[c])
                a_orig = self.data[c]-m           # the original signal, initially, de-meaned
                a = a_orig

                rec_a,rec_d = [] ,[]               # all the approximations and details

                for i in range(self.nbands):
                    (a, d) = pywt.dwt(a, w, self.mode)
                    f = pow(np.sqrt(2.0), i+1)
                    rec_a.append(a/f)
                    rec_d.append(d/f)

                # Use the details and last approximation to create all the power-of-2 freq bands
                self.f_labels,self.freqband = ['A0'],[a_orig] # A0 is the original signal
                fs = [self.srate]
                f = fs[0]
                N = len(a_orig)

                for j,r in enumerate(rec_d):
                    freq_name = 'D' + str(j+1)
                    self.f_labels.append(freq_name)
                    self.freqband.append(r[0:N])          # wavelet details for this band
                    fs.append(f)
                    f = f/2.0

                # We need one more
                f = f/2.0
                fs.append(f)

                # Keep only the last approximation
                j = len(rec_d)-1
                freq_name = 'A' + str(j+1)
                self.f_labels.append(freq_name)
                self.freqband.append(rec_a[j])       # wavelet approximation for this band

                for f in all_features:
                    self.D[ch][f] = {}

    def compute_features(self, all_features, chnls, function_dict):
        self._features_settings(chnls, all_features)
        print('Computing Non RQA features....')
        self._compute_nonrqa_features(all_features, chnls, function_dict)


    def _compute_nonrqa_features(self,all_features,chnls,function_dict):
        #--------------------------------------------------------------------
        # Compute features such as Power, Sample Entropy, Hurst parameter, DFA, Lyapunov exponents on each of the frequency bands
        #--------------------------------------------------------------------
        nonrqa_features = ['Power','SampE']
        for c, ch in enumerate(tqdm(self.channelNames)):
            if ch in chnls:
                for i, y in enumerate(self.freqband):
                    for feat in nonrqa_features:
                        if feat in all_features:
                            self.D[ch][feat][self.f_labels[i]] = function_dict[feat](y)

## EOF ##

t = Data('/Users/ncross/git/EEGPlatform/data/sample/20180422095733_B9-2-2 2yr.edf', 30)
t.compute_features(all_features,master_channel_list,function_dict)
print(t.D)

## EOF
