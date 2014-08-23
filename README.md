mkvstrip
========

Python script that acts as a front end for mkvtoolnix to remove excess audio and subtitle streams from mkv files as well as correct title information. The intent is to allow someone to setup a cronjob to run this script at regular intervals (for example, every night) and this script will keep your Movie collection from collecting excessive tracks.

This script was designed for running in a FreeNAS jail (FreeBSD) but should run in any OS that meets the requirements of this script.

Requirements:

1.  MKVToolNix 7.0.0 and 7.1.0 tested (should work on all recent and future versions though)
2.  Python 2.7.x

The ultimate goal is to make this script something that can be setup by variables in the script and then run nightly as a cronjob to keep your collection optimal.  See bugs as doing this would cause very undesirable behavior.

Known bugs:

1.  If multiple subtitle tracks exist and a bunch should be removed the subtitle tracks not desired will be removed but the log will show the extra tracks are retained.  This is strictly a cosmetic bug with the logging and the desired result (remove the unwanted subtitle tracks) still occurs.  Note that this does render "dry run" mode somewhat broken.
2.  If RENAME_TV or RENAME_MOVIE is set then every time the script is run every file is remuxed.  This can add considerable time to a directory being processed since every time the script is run every file *will* be remuxed.
3.  If the output of video, audio, and subtitle track titles have special characters they will be garbled in the screen and log output.  Note that the files do not end up with garbled entries.  Character sets probably need looked into.
4.  Using the variable os.path.dirname(os.path.realpath(__file__)) which should be for the current directory throws an error.
5.  Movies like Alien³, if titled properly, will silently fail with no error recorded in the log.  This likely has to do with the characterset used in the filename.

Future features to add:

1.  Have the script traverse the directories and subdirectories in alphabetical order.  The current order seems to be the order that the movie files were created, so there is no way for someone to casually look at the output and see that a particular file is remuxing and have a clue how far long it is.  (i.e. if you see that a movie with a 'z' starts you should be able to reason that you are nearly done with that directory)
2.  Consider adding a counter.  Adding code that has the script identify how many mkvs it needs to scan for the entire job and then adding a log entry at each file that says something like "(50/250) complete" when each video file completes would be useful for the user.
3.  Clean up the output of -h to be a bit more "user friendly".
4.  Allow for providing a single filename from the command line instead of a directory.


I am not an expert python coder so any help with bugs or features from the community is much appreciated!

Thanks to the following for their help with getting this working:

Terminus
