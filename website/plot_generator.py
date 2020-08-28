import matplotlib
matplotlib.use('Agg') #If threading issues with matplotlib try Agg as opposed to TkAgg
import matplotlib.pyplot as plt
import s3_resource

def createPlot(rawdata, srate, chnls):
    fig, ax = plt.subplots(len(rawdata), sharex=True, figsize=(20, 20))

    for chn in range(len(rawdata)):
        ax[chn].plot([x / srate for x in range(len(rawdata[chn]))], rawdata[chn])
        ax[chn].yaxis.label.set_size(24)
        ax[chn].set(ylabel=chnls[chn])

    ax[len(rawdata) - 1].set(xlabel='Time in Seconds')
    ax[len(rawdata) - 1].xaxis.label.set_size(24)

    plt.xticks(fontsize=18)
    return plt

def createAndSavePlot(eeg_data, filename, study_id):
    plt = createPlot(eeg_data['raw_data'], eeg_data['srate'], eeg_data['channels'])
    s3_resource.saveimg(plt, filename, study_id)

def asyncCreatePlot(app, rawdata, srate, chnl):
    with app.app_context():
        createPlot(rawdata, srate, chnl)

def asyncCreateAndSavePlot(app, eeg_data, filename, study_id):
    with app.app_context():
        createAndSavePlot(eeg_data, filename, study_id)

## EOF ##