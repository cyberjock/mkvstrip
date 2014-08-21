mkvstrip
========

Python script that acts like a front end for mkvtoolnix to remove excess audio and subtitle streams from mkv files as well as correct title information. The intent is to allow someone to setup a cronjob to run this script at regular intervals (for example, every night) and this script will keep your Movie collection from collecting excessive tracks.

This script was designed for running in a FreeNAS jail (FreeBSD) but should run in any OS that meets the requirements of this script (mkvtoolnix 7.0.0 and 7.1.0 and python 2.7.x).

The ultimate goal is to make this script something that can be setup by variables in the script and then run nightly as a cronjob to keep your collection optimal.  See bugs as doing this would cause very undesirable behavior for your server.

Known bugs:

1.  If multiple subtitle tracks exist and a bunch should be removed the subtitle tracks not desired will be removed but the log will show the extra tracks are retained.  This is strictly a cosmetic bug with the logging and the desired result (remove the unwanted subtitle tracks) still occurs.  Note that this does render "dry run" mode somewhat broken.
2.  If RENAME_TV or RENAME_MOVIE is set then every time the script is run every file is remuxed.  This can add considerable time to a directory being processed since every time the script is run every file *will* be remuxed.
3.  If the output of video, audio, and subtitle track titles include garbled characters.  Character sets probably need looked into.
4.  Using the variable os.path.dirname(os.path.realpath(__file__)) which should be for the current directory throws an error.

Future features to add:

1.  Have the script traverse the directories and subdirectories in alphabetical order.  The current order seems to be the order that the movie files were created, so there is no way for someone to casually look at the output and see that a particular file is remuxing and have a clue how far long it is.
2.  Consider adding a counter.  Adding code that has the script identify how many mkvs it needs to scan for the entire job and then adding a log entry at each file that says something like "(50/250) complete" when each video file completes would be useful for the user.
3.  Clean up the output of -h to be a bit more "user friendly".


I am not an expert python coder so any help with bugs or features from the community is much appreciated!

Thanks to the following for their help with getting this working:

Cyberjock and Terminus
