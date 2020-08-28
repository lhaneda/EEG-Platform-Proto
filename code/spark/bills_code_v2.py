#! python
#
#  ml_multiscale_signal_analysis.py
#
#
#  Created by Bill Bosl on 06/12/2016.
#  Copyright (c) 2016 MindLight Medical. All rights reserved.
#
import sys, os
import pywt
import glob
import numpy as np
import pandas as pd
import math
#from pyrqa.time_series import SingleTimeSeries
from pyrqa.settings import Settings
from pyrqa.neighbourhood import FixedRadius
from pyrqa.metric import EuclideanMetric
#from pyrqa.computation import RecurrencePlotComputation
from pyrqa.computation import RQAComputation
#from pyrqa.image_generator import ImageGenerator
import mse
import eegtools
import pyedflib
import nolds
import scipy

# A few global variables
all_features = ["Power", "SampE", "hurst_rs", "dfa", "cd", "lyap0", "RR", "DET", "LAM", "L_entr", "L_max", "L_mean", "TT"]
#all_features = ["Power", "SampE", "hurst_rs", "dfa", "cd", "lyap0"]
f_labels = []
DEVICE = "unk"
AGE = 0
FORMAT = "long"
SEGMENT = "beg"  # "beg" = beginning, "mid" = middle, "end" = end. Position from which to extract the segment
SUBSAMPLE = True

# Use these for conversion to standard 10-20 location terminology
hydroCell128_channelList = [22,9,33,24,11,124,122,45,36,129,104,108,58,52,62,92,108,70,83]
EGI_64v2 = [12,2,19,13,4,62,60,24,17,65,54,52,27,28,34,46,49,36,44]
egi_channel_names = ["C3","C4","O1","O2","Cz","F3","F4","F7","F8","Fz","Fp1","Fp2","P3","P4","Pz","T7","T8","P7","P8"]
master_channel_list = ["EEG Cross", "Fp1","Fp2","FP1","FP2","T3","T5","T4","T6","F7","F3","Fz","F4","F8","T7","C3","Cz","C4","T8","P7","P3","Pz","P4","P8","O1","O2"]
#master_channel_list = ["C3"] for testing
processed_channel_names = []


#----------------------------------------------------------------------
# Total power
#----------------------------------------------------------------------
def bandpower(x):
    p = scipy.sum(x * x) / x.size
    return p


#----------------------------------------------------------------------
# Read in the list of file names, then process each file, writing
# the computed features to the appropriate output file.
#----------------------------------------------------------------------
def read_fileList(argv):
    global DEVICE, AGE, FORMAT, SEGMENT, SUBSAMPLE

    #---------------------------------
    # Default values
    outfilename = "outfile.csv"
    max_nt = 30 # length of time segment in seconds
    dataset = "unknown"

    # Let's get command line arguments
    argc = len(argv)
    arg_check = 0
    for i in range(argc):
        if argv[i] == '-i':
            globList = argv[i+1]
            arg_check += 1
        if argv[i] == '-o':
            outfilename = argv[i+1]
            overwritefileFlag = True
            arg_check += 1
        if argv[i] == '-d':
            dataset = argv[i+1]
            overwritefileFlag = True
            arg_check += 1
        if argv[i] == '-a':
            AGE = int(argv[i+1])
            overwritefileFlag = True
            arg_check += 1
        if argv[i] == '-nt':
            max_nt = int(argv[i + 1])  # length of time series in seconds
            overwritefileFlag = True
            arg_check += 1
        if argv[i] == '-format':
            FORMAT = argv[i+1]
            arg_check += 1
        if argv[i] == '-seg':
            SEGMENT = argv[i+1]
            arg_check += 1
        if argv[i] == '-sub':
            SUBSAMPLE = bool(argv[i+1])
            arg_check += 1

    if arg_check < 2:
        print ("Usage: python ml_multiscale_signal_analysis -i \"*.*\" -o outfile.csv -nt 20 -format <long, wide> -seg <beg, mid, end> -sub <True, False>")
        sys.exit()

    #---------------------------------
    # Get the list of filenames
    return glob.glob(globList), outfilename, max_nt, dataset


#----------------------------------------------------------------------
# Extract the time series and sensor names from the file. We will
# process only .edf and .csv files at this time.
#----------------------------------------------------------------------
def extract_time_series(filename, max_nt):
    global DEVICE
    
    file = open(filename,'r')
    last = len(filename)

    if filename[last-4] == '.':
        tag = filename[last-3:last]
    elif filename[last-5] == '.':
        tag = filename[last-4:last]
    else:
        print ("Cannot read tag. Exiting.")
        exit()


    PROCESS_FILE = False
    if tag == "edf":
#        try:
        if 1==1:
            print ("filename = ", filename)
            edfData = eegtools.io.load_edf(filename)
            #f = pyedflib.EdfReader(filename)
            PROCESS_FILE = True
#        except:
#            print ("Can't open file ", filename)
#            return [[0.0]], [], 0.0

        if 1==0:
            f = pyedflib.EdfReader(filename)
            nch = f.signals_in_file
            channelNames = f.getSignalLabels()
            data = np.zeros((nch, f.getNSamples()[0]))
            for i in np.arange(nch):
                data[i, :] = f.readSignal(i)
            print ("shape of edfData: ", data.shape)
            #data = data / 1000.0  # convert microvolts --> millivolts
            nch, nt = data.shape
            srate = f.getSampleFrequency(0)

            #print ("data shape = ", data.shape)
            print ("srate = ", srate)
            #print ("channels: ", channelNames)
            #print ("n seconds = ", len(data[0])/srate)
        else:
            edfData = eegtools.io.load_edf(filename)
            data = edfData[0] / 1000.0
            srate = edfData[1]
            channelNames = edfData[2]



        # Remove the "-Ref1:8" part of the filename for some sensors
        tag = "-Ref1:8"
        for c, ch in enumerate(channelNames):
            if tag in ch:
                n = len(ch)
                channelNames[c] = ch[0:n-7]

    elif tag == "easy":
        # The following information can be read directly from the corresponding .info file.
        # We hardcode it here for testing purposes.
        srate = 500.0
        channelNames = ["Fp1","Fp2","C3","C4","T7","T8","O1","O2"]
        headers = channelNames + ['flag','time']

        # We need to swap axes to be consistent with the EDF format above
        pd_data = pd.read_csv(filename, delimiter = "\t", names=headers).T
        data = pd_data.as_matrix()[0:len(channelNames)] / 1000.0
        data_channels, nt = data.shape
        PROCESS_FILE = True

    elif tag == "csv":
        print ("Can't process .csv files yet: ", filename)
        return [[0.0]], [], 0.0
        #
        # fill in code to read from csv file
        #

    if PROCESS_FILE:
        # This is for the WearableSensing DS-7
        if 'Trigger' in channelNames:
            channelNames.remove('Trigger')
            data = data[0:7]

        data_channels, nt = data.shape

        # We generally want only the standard 10-20 channels (19 max)
        # The high density EGI nets have numbered channel names. We'll need to convert.
        new_data = []
        new_channel_list = []

        if len(data) == 129:  # EGI hydrocell 128
            for c, ch in enumerate(egi_channel_names):
                new_channel_list.append(ch)
                i = hydroCell128_channelList[c] - 1
                new_data.append(data[i])
            DEVICE = "EGI hydrocell 128"
            channelNames = new_channel_list

        elif len(data) == 65:  # EGI 64 v2
            for c, ch in enumerate(egi_channel_names):
                new_channel_list.append(ch)
                i = EGI_64v2[c] - 1
                i = EGI_64v2[c] - 1
                new_data.append(data[i])
            DEVICE = "EGI 64 v2"
            channelNames = new_channel_list


        # Let's trim the data array so that time series are not more than max_nt seconds
        max_nt_points = max_nt * srate
        nt = int(min(max_nt_points, nt))

        m = len(data)
        n = len(data[0])
        if "beg" in SEGMENT:
            m1 = 0
        if "end" in SEGMENT:
            m1 = n-nt
        elif "mid" in SEGMENT:
            m1 = (n-nt)/2
        else:
            m1 = 0
        m2 = m1 + nt

        new_data = []
        if SUBSAMPLE:
            for i in range(m):
                # Here we subsample to force all sampling rates to be
                # approximately in the 200 to 250 Hz range
                if srate > 999.0:
                    segment  = np.array(data[i][m1:m2:4])
                    srate = srate/4.0
                elif srate > 499.0:
                    segment  = np.array(data[i][m1:m2:2])
                    srate = srate/2.0
                else:
                    segment = np.array(data[i][m1:m2])

                new_data.append( segment )
        else:
            for i in range(m):
                segment = np.array(data[i][m1:m2])
                new_data.append(segment)

        new_data = np.array(new_data)

    return new_data, channelNames, srate

#----------------------------------------------------------------------
# Features to be computed for each scale:
#   RQA: RR, DET, LAM, L_max, L_entr, L_mean, TT
#   Sample entropy: SampE
#   Power
#
#   Scales are relative to the sampling rate of the digital time
#   series.
#----------------------------------------------------------------------
def process_data(data, channelNames, srate):
    global f_labels, processed_channel_names

    # Default RQA parameters
    embedding = 10				# Embedding dimension
    tdelay = 2					# Time delay
    tau = 30					# threshold

    # Multiscaling is accomplished with a wavelet transform
    # Options for basis functions: ['haar', 'db', 'sym', 'coif', 'bior', 'rbio', 'dmey']
    #wavelet = 'haar'
    wavelet = 'db4'
    mode = 'cpd'
    #mode = pywt.Modes.smooth

    # Simple array for entropy value
    ent = np.zeros(1)

    # Determine the number of levels required so that
    # the lowest level approximation is roughly the
    # delta band (freq range 0-4 Hz)

    if   srate <= 128:  levels = 4
    elif srate <= 256:  levels = 5
    elif srate <= 512:  # subsample
        srate = srate / 2.0
        n = len(data[0])
        data = data[0:, 0:n:2]
        levels = 5
    elif srate <= 1024:
        srate = srate / 4.0
        n = len(data[0])
        data = data[0:, 0:n:4]
        levels = 5
    nbands = levels

    wavelet_scale = {}
    f_limit = {}

    # The following function returns the highest level (ns) approximation
    # in dec[0], then details for level ns in dec[1]. Each successive
    # level of detail coefficients is in dec[2] through dec[ns].
    #
    #   level       approximation       details
    #   0           original signal     --
    #   1                -              dec[ns]
    #   2                -              dec[ns-1]
    #   3                -              dec[ns-2]
    #   i              -                dec[ns-i+1]
    #   ns          dec[0]              dec[1]

    WRITE_RP_IMAGE_FILE = False

    # Print screen headers
    sys.stdout.write("%10s %6s " % ("Sensor", "Freq"))
    for f in all_features:
        sys.stdout.write(" %8s " % (f))
    sys.stdout.write("\n")

    D = {}

    for c, ch in enumerate(channelNames):
        if ch in master_channel_list:
            processed_channel_names.append(ch)

            # Create a raw recurrence plot image for the original signal from this channel
            if WRITE_RP_IMAGE_FILE:
                rp_plot_name = filename + "_" + ch + "_" + "rp" + ".png"
                print ("            write rp image file ", rp_plot_name)
                settings = Settings(data[c],
                                    embedding_dimension=embedding, time_delay=tdelay, neighbourhood=FixedRadius(0) )
                #computation = RQAComputation.create(settings, verbose=False)
                rp_computation = RecurrencePlotComputation.create(settings, verbose=False)
                result = rp_computation.run()
                ImageGenerator.save_recurrence_plot(result.recurrence_matrix_reverse, rp_plot_name)

            D[ch] = {}

            #--------------------------------------------------------------------
            # Get the wavelet decomposition. See pywavelet (or pywt) documents.
            # Deconstruct the waveforms
            # S = An + Dn + Dn-1 + ... + D1
            #--------------------------------------------------------------------
            w = pywt.Wavelet(wavelet)
            m = np.mean(data[c])
            a_orig = data[c]-m # the original signal, initially
            a = a_orig

            ca = []     # all the approximations
            cd = []     # all the details
            sqrt2 = np.sqrt(2.0)
            for i in range(nbands):
                (a, d) = pywt.dwt(a, w, mode)
                f = pow(sqrt2, i+1)
                ca.append(a/f)
                cd.append(d/f)


            if 1==0: # this will build full reconstructed signals at every level
                rec_a = []  # reconstructed approximations
                rec_d = []  # reconstructed details
                for i, coeff in enumerate(ca):
                    coeff_list = [coeff, None] + [None] * i
                    rec_a.append(pywt.waverec(coeff_list, w))
                for i, coeff in enumerate(cd):
                    coeff_list = [None, coeff] + [None] * i
                    rec_d.append(pywt.waverec(coeff_list, w))
            else:
                rec_a = ca
                rec_d = cd

            # Use the details and last approximation to create all the power-of-2 freq bands
            f_labels = ['A0']
            wavelet_scale = {}
            wavelet_scale['A0'] = 0
            f_limit = {}
            f_limit['A0'] = srate/2.0
            fs = [srate]
            freqband = [a_orig]    # A0 is the original signal
            N = len(a_orig)
            f = srate/4.0
            for j,r in enumerate(rec_a):
                freq_name = 'A' + str(j+1)
                wavelet_scale[freq_name] = j+1
                f_limit[freq_name] = f
                f = f/2.0
                f_labels.append(freq_name)
                freqband.append(r[0:N])          # wavelet approximation for this band

            f = srate/2.0
            for j,r in enumerate(rec_d):
                freq_name = 'D' + str(j+1)
                wavelet_scale[freq_name] = j+1
                f_limit[freq_name] = f
                f = f / 2.0
                f_labels.append(freq_name)
                freqband.append(r[0:N])          # wavelet details for this band

            #--------------------------------------------------------------------
            # Compute features on each of the frequency bands
            #--------------------------------------------------------------------
            for f in all_features:
                D[ch][f] = {}

            #----------------------
            # Feature set 1: Power
            for i, y in enumerate(freqband):
                v = bandpower(y)
                D[ch]["Power"][f_labels[i]] = v

                #----------------------
                # Feature set 2: Sample Entropy, Hurst parameter, DFA, Lyapunov exponents
                D[ch]["SampE"][f_labels[i]] = nolds.sampen(y)

                try:
                    D[ch]["hurst_rs"][f_labels[i]] = nolds.hurst_rs(y)
                except:
                    D[ch]["hurst_rs"][f_labels[i]] = 0.0

                try:
                    D[ch]["dfa"][f_labels[i]] = nolds.dfa(y)
                except:
                    D[ch]["dfa"][f_labels[i]] = 0.0

                try:
                    D[ch]["cd"][f_labels[i]] = nolds.corr_dim(y, embedding)
                except:
                    D[ch]["cd"][f_labels[i]] = 0.0

                try:
                    #lyap = nolds.lyap_e(y, emb_dim= embedding)
                    lyap0 = nolds.lyap_r(y, emb_dim=embedding)
                except:
                    #lyap = [0.0, 0.0, 0.0]
                    lyap0 = 0.0
                D[ch]["lyap0"][f_labels[i]] = lyap0

                #----------------------
                # Feature set 3: Recurrence Quantitative Analysis (RQA)
                # This routine seems to be incredibly slow and may need improvement
                rqa_features = ["RR", "DET", "LAM", "L_entr", "L_max", "L_mean", "TT"]
                pyRQA_names = ['recurrence_rate', 'determinism', 'laminarity', 'entropy_diagonal_lines', \
                               'longest_diagonal_line','average_diagonal_line', 'trapping_time'   ]

                # First check to see if RQA values are needed at all
                compute_RQA = False
                for r in rqa_features:
                    if r in all_features:
                        compute_RQA = True
                        break

                if compute_RQA:
                #for i, y in enumerate(freqband):
                    settings = Settings(y,
                                embedding_dimension=embedding,
                                time_delay=tdelay,
                                neighbourhood=FixedRadius(tau)
                                #similarity_measure=EuclideanMetric,
                                #theiler_corrector=1,
                                #min_diagonal_line_length=2,
                                #min_vertical_line_length=2,
                                #min_white_vertical_line_length=2)
                    )
                    computation = RQAComputation.create(settings, verbose=False)
                    result = computation.run()

                    # We have to pull out each value
                    w = f_labels[i]
                    D[ch]["RR"][w] = result.recurrence_rate
                    D[ch]["DET"][w] = result.determinism
                    D[ch]["LAM"][w] = result.laminarity
                    D[ch]["L_entr"][w] = result.entropy_diagonal_lines
                    D[ch]["L_max"][w] = result.longest_diagonal_line
                    D[ch]["L_mean"][w] = result.average_diagonal_line
                    D[ch]["TT"][w] = result.trapping_time

                    # Write results from first channel to the screen, to give
                    # visual feedback that the code is running

                w = f_labels[i]
                sys.stdout.write( "%10s %6s " %(ch, w ) )
                for dyn_inv in all_features: # D[ch].keys():
                    v = D[ch][dyn_inv][w]
                    sys.stdout.write( " %8.3f " %( v ) )
                sys.stdout.write("\n")

    return D, srate, wavelet_scale, f_limit


# ----------------------------------------------------------------------
# Write features using long or wide format
# ----------------------------------------------------------------------
def write_features(fout, D, id, age, srate, wavelet_scale, f_limit):

    if FORMAT == 'long':
        for ch in D.keys(): # processed_channel_names: # D.keys():
            for f in all_features: # D[ch].keys():
                for lab in f_labels: #D[ch][f].keys():
                    fout.write("%s, %d, %5.1f, %s, %s, %s, %d, %f, %7.3e " \
                               % (id, age, srate, f, ch, lab, wavelet_scale[lab], f_limit[lab], D[ch][f][lab]))
                    fout.write("\n")

    elif FORMAT == 'wide':
        fout.write("%s, %d, %5.1f" % (id, age, srate) )
        for ch in processed_channel_names: # D.keys():
            for f in all_features: # D[ch].keys():
                for lab in f_labels: # D[ch][f].keys():
                    fout.write(", %7.3e " % (D[ch][f][lab]))
        fout.write("\n")


#----------------------------------------------------------------------
# Main
#----------------------------------------------------------------------
if __name__ == "__main__":
    fileList, outfilename, max_nt, dataset = read_fileList(sys.argv)

    overwritefileFlag = True
    fileExists = os.path.isfile(outfilename)
    try:
        if overwritefileFlag:
            fout = open(outfilename, 'w')
        else:
            fout = open(outfilename, 'a')
    except:
        print ("Cannot open ", outfilename, ". Exiting ...")
        exit()

    # Each file contains data from one subject, at one time or clinical encounter.
    # Process one at a time and write the computed features.
    count = 0
    total_count = len(fileList)
    for filename in fileList:

        # Extract age from input list
        age = AGE

        # Extract an ID from the file or filename
        n = len(filename)
        ID = filename[0:n-4]

        # This is for ISP files, which have the form ISPxxxxEEGaam.
        # where xxxx is the ID and aa is the age
        if 'ISP' in filename :
            ID = filename[3:7]
            age = int(filename[10:12])

        # for testing, we'll send messages about progress ...
        sys.stdout.write("Processing data file %s \n" %(ID) )
        data, channelNames, srate = extract_time_series(filename, max_nt)
        if len(data[0]) < max_nt*srate:
            print ("File ", filename, " does not have the required length and will not be processed.")
        else:
            count += 1
            D, srate, wavelet_scale, f_limit = process_data(data, channelNames, srate)

            if count == 1: # Write headers
                #sys.stdout.write("%s" % ("ID, Age, Rate, Channel, Feature, Wavelet, Scale, Freq, Value\n"))
                if FORMAT == 'long':
                    fout.write("%s" % ("ID, Age, Rate, Channel, Feature, Wavelet, Scale, Freq, Value\n"))

                elif FORMAT == 'wide':
                    fout.write("%s" % ("ID, Age, Rate"))
                    for ch in D.keys():
                        for f in D[ch].keys():
                            for lab in D[ch][f].keys():
                                h = ch + ':' + f + ':' + lab
                                fout.write(", %s" % (h))
                    fout.write("\n")

            write_features(fout, D, ID, age, srate, wavelet_scale, f_limit)
            print ("File %d of %d finished. Results written to %s." % (count,total_count,fout.name))

    sys.stdout.write("Processed %d files.\n" %(count) )
