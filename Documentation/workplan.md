# Work plan: 

### 4/24

1. LH -> Merge in Results Page, verify that it works. Do it at study level and put all results for all files on that study.
2. GC -> Finish up rest of the formatting annonyances on the crontab. 
2. GC -> dictionary results rather than lists for psycopg2 / fix all the bad defaults. file = 1
3. Ginny -> Parameters page? 



### For the week ending 4/10


Tasks 

    1. Script which will take in the the following input and generate an output. Importantly, this will NOT be part of the website.py or associated with the website right away. 
        a. input: EEG file, channel (list of them), band [list], functions to run (list), time start, time end
        b. output: the values generated for power and sampE for each band (not choosen).
        d. Note: the file "newProcess.py" does a bunch of this work, but is very simplified and should be the starting point
	At the end there should be a single function that is called process_EZ( ... )
	e. Try to make it its own function that we can call with a process off the main thread.

    2. Do not allow special characters in the user name [LH]
    3. Image front-end work: make the channel list table less wide and put the image to the right of the channel table list (Feel free to fix any thing about the ugliness of the images)
    4. Make the figure drawing a subprocess not tied to the main completion.

Old tasks which are complete


    0. Fix time on file loading (figure out what it is doing -- convert to PST & then add PST to column heading) [GV -- DONE]
        a. Modify the "file list" page to include (srate, num channels, length in seconds) information about each file in a table (e.g. one row per file) [DONE] 
    
    1. Verify why files are not working with the four lines of code. Run all code on samples files see which ones work and document why they don't work. 
    	a. Goal of this: make sure that there is a one-to-one match between files that don't upload and files that don't work in an interactive terminal. [DONE -- ONLY FILES LEFT WORK]
    
    2. Make sure that when duplicate file names are uploaded that you don't get an error. [DONE -- WORKS GREAT]
    

    4. [Something to keep in mind] Another project. 
    	a. On the channels page, add a pre-rendered plot of the time series of the channels. Key thing: do the rendering on upload. [DONE]
	


### For the week ending 4/3 

Tasks 

    0. Fix time on file loading (figure out what it is doing -- convert to PST & then add PST to column heading) [GV]
        a. Modify the "file list" page to include (srate, num channels, length in seconds) information about each file in a table (e.g. one row per file) [Continuing] 
    
    1. Verify why files are not working with the four lines of code. Run all code on samples files see which ones work and document why they don't work. 
    	a. Goal of this: make sure that there is a one-to-one match between files that don't upload and files that don't work in an interactive terminal. 
    
    2. Make sure that when duplicate file names are uploaded that you don't get an error.
    
    3. [Stretch] Script which will take in the the following input and generate an output. Importantly, this will NOT be part of the website.py or associated with the website right away. 
        a. input: EEG file, channel (list of them), band [list], functions to run (list), time start, time end
        b. output: the values generated for power and sampE for each band (not choosen).
        c. focus on using power and sampE from the old_process.py script.
        d. Note: the file "newProcess.py" does a bunch of this work, but is very simplified and should be the starting point
	At the end there should be a single function that is called process_EZ( ... )

    4. [Something to keep in mind] Another project. 
    	a. On the channels page, add a pre-rendered plot of the time series of the channels. Key thing: do the rendering on upload. 

### For the week ending 3/27
Tasks 

    0. Fix time on file loading (figure out what it is doing -- convert to PST & then add PST to column heading) [Continuing]
    
    1. Verify why files are not working with the four lines of code. Run all code on samples files see which ones work and document why they don't work. [Continuing]
    
    2. EEGValid -- verify that it works on those files that pass #1.
        a. Put srate & length & number of channels into the files table( length should be in time-> num of elements / srate) [done]
        b. Put all channels into the channel info table. [done]
        c. Modify the "file list" page to include (srate, num channels, length in seconds) information about each file in a table (e.g. one row per file) [continue]
        d. Put all channels into the channel info table. [done]
	e. click on filename in "list file" tab -> a page showing the channel list for that file. [done]
	
    3. Verify foreign keys.[Done]

    4. [Easier Stretch] Make sure that when bad files are uploaded, graceful failing / logging. [done]
    
    5. [Stretch] Script which will take in the the following input and generate an output:
        a. input: EEG file, channel (list of them), functions to run (list), time start, time end
        b. output: the values generated for power and sampE for each band (not choosen).
        c. focus on using power and sampE from the old_process.py script.
        d. Note: the file "newProcess.py" does a bunch of this work, but is very simplified and should be the starting point

### For the week after spring break,CS students

Tasks: (3/6/2019 -- I think that 0,1,2 are doable by after spring break) If you have extra time, then start looking at 3/4)

    0. Fix time on file loading (figure out what it is doing -- convert to PST & then add PST to column heading)
    
    1. Modify the upload to script to do the following upon upload (validator isn't working fully right now)
        a. Verify that the file is "good" <- has an srate & channels & time (length)
        b. Put srate & length into the files table( length should be in time-> num of elements / srate)
        c. Put all channels into the channel info table.
        d. Modify the "file list" page to include all (non-channel) of this information about each file in a table (e.g. one row per file)
    2. In the table definitions we can add foreign key definitions <- do this.

	3. Script which will take in the the following input and generate an output:
	    a. input: EEG file, channel (list of them), functions to run (list), time start, time end
	    b. output: the values generated for power and sampE for each band (not choosen).
	    c. focus on using power and sampE from the old_process.py script.
        d. Note: the file "newProcess.py" does a bunch of this work, but is very simplified and should be the starting point

    4. On the list files pages, add the ability to delete files [FINISHED] 
    5. Added download feature


### Longer term 
1. Create a true local environment (one that points to a local postgres/directory rather than s3)
1. Set up a python environment
1. Add the ability to import file formats outside of EDF (which would require converting to using the MNE library, which can be found here: https://martinos.org/mne/stable/manual/io.html). The MNE library may not be compatible with spark, which would mean using the library to convert signals to a different type and then using spark to process the resulting changed files.
1. Add a real web address
1. Buttons on download page are probably copy protected. 
1. When converting to MNE, add the cool head chart
1. Add bulk uploading, filerename and move image data (compressed) into the database
1. Channels Names: Lower Case & Add the "Kids" channel
1. How do we store the mask for the artifact? 
1. Need to fix location of all modules. Right now deploy doens't work b/c you need to be in the website directory to run.
1. Multiple File uploads at a time
1. Delete study confirmation (delete button does nothing).
1. Create a script which deletes everything (all database tables, all s3 files, etc.).
1. We put all the routing and function defs are in website.py (and now its very large). _Usually_, website.py is a list of imports & routes. 
1. Dealing with the pathing and being able to call website from *not* the current directory (e.g. python "EEGPlatform/website/website.py")
1. Security Flask. Add this.
