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
2.  If the output of video, audio, and subtitle track titles have special characters they will be garbled in the screen and log output.  Note that the files do not end up with garbled entries.  Character sets probably need looked into.
3.  Some videos will have the correct audio language but for some reason will still report that the language doesn't exist.  The script will skip the file (as it is supposed to) because you don't want to end up with an audio-free file.  I have plenty of examples, I just have to figure out why this behavior exists.
4.  Movies like Alien³, if titled properly, will silently fail with no error recorded in the log.  This likely has to do with the character-set used in the filename.  This obviously needs to be fixed because quite a few movies, if titled properly, have odd symbols.

Future features to add:

1.  Clean up the output of -h to be a bit more "user friendly".
2.  Add a -f parameter to allow for providing a single filename from the command line instead of a directory.  Currently -d works for single file names.
3.  It would be nice if the script would actually distinguish between when you are in dry run mode and it would have done something and when you wouldn't have made any changes and would at least provide a 1 or 2 line message appropriate.  For example, if a change would have been made say something like "changes are not being applied because you are in dry run mode" or "no changes made because no changes are necessary".  It is somewhat unintuitive to have it say " Nothing to do for /mnt/Entertainment/Movies/Whatever.mkv" just because it is in dry run mode.
4.  If a file rename would have happened without dry run mode being enabled there is no log output.  But if you disable dry run mode then it renames it properly.  This should be logged if a change should have been made but wasn't.

I am not an expert python coder so any help with bugs or features from the community is much appreciated!

Thanks to the following for their help with getting this working:

Terminus, willforde
