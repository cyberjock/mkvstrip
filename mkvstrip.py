#!/usr/bin/env python

# Welcome to mkvstrip.py.  This script can go through a folder looking for extraneous audio and subtitle tracks and removes them.  Additionally you can choose to overwrite the title field of the mkv.

# Version = 0.9 (8/21/2014)
# The latest version can always be found at https://github.com/cyberjock/mkvstrip

# This python script has the following requirements:
# 1.  Mkvtoolnix installed: 7.0.0 and 7.1.0 were tested (should work with recent prior versions like 6.x and 5.x though)
# 2.  Python installed: 2.7.8_2 in FreeBSD/FreeNAS jail and 2.7.8 in Windows (should work with the entire 2.7.x series though)

# Note that this script will remux the entire directory provided from the command line or the below variable.  If you point this to a large amount of files this could potentially keep the storage location near saturation speed until it completes.  In tests this could render the storage media for your movies or tv shows so busy that it becomes nearly unresponsive until completion of this script (I was able to remux at over 1GB/sec in tests).  As this process is not CPU intensive your limiting factor is likely to be the throughput speed of the storage location of the video files being checked/remuxed.  For example, remuxing a 15GB movie file I had took 9 minutes over 1Gb LAN but just 32 seconds locally from a FreeNAS jail.

# Keep in mind that because of how remuxing works this won't affect the quality of the included video/audio streams.

# Using this over a file share is ***STRONGLY*** discouraged as this could take considerable time (days/weeks?) to complete due to the throughput bottleneck of network speeds.  

# Use this script at your own risk (or reward).  Unknown bugs could result in this script eating your files.  There are a few "seatbelts" to ensure that nothing too undesirable happens.  For example, if only one audio track exists and it doesn't match your provided languages an ERROR is logged and the video file is skipped.  I tested this extensively and I've used this for my collection, but there is no guarantee that bugs don't exist for you.  ALWAYS TEST A SMALL SAMPLE OF COPIES OF YOUR FILES TO ENSURE THE EXPECTED RESULT IS OBTAINED BEFORE UNLEASHING THIS SCRIPT ON YOUR MOVIES OR TV SHOWS BLINDLY.

# Some default variables are provided below but all can be overwritten by command line parameters.  If the default variables are commented out then you MUST pass the appropriate info from the command line.

# A remux should only occur if a change needs to be made to the file.  If no change is required then the file isn't remuxed.

# For help with the command line parameters use the -h parameter.

# Location for mkvmerge executable binary.
# Note that the location always uses the / versus the \ as appropriate for some OSes.
# Windows is usually set to something like C:/Program Files (x86)/MkvToolNix/mkvmerge.exe
# For a FreeNAS jail (and FreeBSD) this usually something like /usr/local/bin/mkvmerge
MKVMERGE_BIN = '/usr/local/bin/mkvmerge'

# Log errors to file.  Log file will be in the same directory as mkvstrip.py and will include the year, month, day and time that mkvstrip is invoked.
LOG = True

# Directory to process.
# Note that the location always uses the / versus the \ for location despite what the OS uses (*cough* Windows).
# Windows is usually something like C:/Movies
# FreeNAS jails (and FreeBSD) should be something like /mnt/tank/Movies or similar.
# DIR = os.path.dirname(os.path.realpath(__file__))
# DIR = '/mnt/tank/Entertainment/Movies'

# The below parameter lets mkvstrip go through the motions of what it would do but won't actually change any files.  This allows you to review the logs and ensure that everything in the log is what you'd actually like to do before actually doing it. (see bug list)
DRY_RUN = False

# PRESERVE_TIMESTAMP keeps the timestamps of the old file if set.  This prevents you from having an entire library that has a date/time stamp of today.  Recommended to be enabled.
# Note that if Plex has already inventoried your files it may or may not like this setting and may or may not like you remuxing your entire library suddenly. I recommend you stop Plex and then do an analysis of your library afterwards. 
PRESERVE_TIMESTAMP = True

# List of audio languages to retain.  Default is English (eng) and undetermined (und).  'und' (undetermined) is always recommended in case audio tracks aren't identified.
AUDIO_LANG = [ 'eng', 'und' ]

# List of subtitle languages to retain. Default is English (eng) and undetermined (und).  'und' (undetermined) is always recommended in case subtitle tracks aren't identified.
SUBTITLE_LANG = [ 'eng', 'und' ]

# Log files that have no subtitles in the languages chosen.  This is to allow you to be informed of videos that are missing subtitles so you can take action as necessary.  A WARNING message is logged if at least one subtitle language track isn't found.
LOG_MISSING_SUBTITLE = True

# Rewrite the title field of mkv files to include the immediate parent directory.  If set to true it will rename the title field of the MKV to be the in the format of "(parent directory) - (name of video file without .mkv extension)" as this is the most common organization of TV shows for Plex.  This setting is mutually exclusive of RENAME_MOVIE.
# Note: If RENAME_TV is set and your files *only* need a title change that a remux will still be triggered.  So use with caution.  (See bug list)
RENAME_TV = True

# Rewrite the title field of mkv files to include the video file name without the .mkv extension.  This setting is mutually exclusive of RENAME_TV.
# Note: If RENAME_MOVIE is set and your files *only* need a title change that a remux will still be triggered.  So use with caution. (see bug list)
RENAME_MOVIE = False

# Known bugs and limitations with this version:
# 1. 

for i in [
        'MKVMERGE_BIN',
        'LOG',
        'DIR',
        'DRY_RUN',
        'PRESERVE_TIMESTAMP',
        'AUDIO_LANG',
        'SUBTITLE_LANG',
        'LOG_MISSING_SUBTITLE',
        'RENAME_TV',
        'RENAME_MOVIE' ]:
    if i not in globals():
        raise RuntimeError('%s configuration variable is required.' % (i))

import os, re, sys, atexit, subprocess
from datetime import datetime
from StringIO import StringIO
from argparse import ArgumentParser

class Logger(object):
    _files = dict()

    @staticmethod
    def init(*args):
        for path in args:
            if path not in Logger._files:
                Logger._files[path] = open(path, 'w')
                Logger.write('Log file opened at', path)
                Logger.write('--')

    @staticmethod
    def write(*args, **kwargs):
        for k in kwargs:
            if k not in [ 'stderr', 'indent' ]:
                raise TypeError('write() got an unexpected keyword argument \'%s\'' % (k))

        ts = datetime.now().strftime('[ %Y-%m-%d %I:%M:%S %p ] ')
        msg = ' '.join(str(i) for i in args)

        # Build list of files to log to
        files = list()
        if 'stderr' in kwargs:
            files.append(sys.stderr)
        else:
            files.append(sys.stdout)
        files += Logger._files.values()

        for f in files:
            print >> f, ts,
            if 'indent' in kwargs:
                Logger._indent(kwargs['indent'], f)
            print >> f, msg

    @staticmethod
    def destroy():
        Logger.write('--')
        Logger.write('Finished processing.')
        for f in Logger._files.values():
            f.close()

    @staticmethod
    def _indent(x, file):
        for i in range(x):
            print >> file, ' ',

class Track(object):
    def __init__(self, id, name, language, default=None):
        super(Track, self).__init__()
        self.id = int(id)
        self.name = name
        self.language = language
        self.default = default

    def __str__(self):
        return 'Track #%i (%s): %s' % (self.id, self.language, self.name)

class VideoTrack(Track):
    pass

class AudioTrack(Track):
    pass

class SubtitleTrack(Track):
    pass

def stringifyLanguages(tracks, filtered_tracks=None):
    if filtered_tracks is None:
        t = set([ i.language for i in tracks ])
    else:
        t = set([ i.language for i in tracks if i not in filtered_tracks ])

    if t:
        return sorted(t)
    return str(None)

atexit.register(Logger.destroy)

parser = ArgumentParser(description='Strips unnecessary tracks from MKV files.')
group = parser.add_mutually_exclusive_group()
group.add_argument('-l', '--log', default=None, action='store_true', help='Log to file in addition to STDOUT and STDERR.')
group.add_argument('--no-log', default=None, action='store_false', dest='log')
parser.add_argument('-d', '--dir', default=DIR)
group = parser.add_mutually_exclusive_group()
group.add_argument('-y', '--dry-run', default=None, action='store_true')
group.add_argument('--no-dry-run', default=None, action='store_false', dest='dry_run')
group = parser.add_mutually_exclusive_group()
group.add_argument('-p', '--preserve-timestamp', default=None, action='store_true')
group.add_argument('--no-preserve-timestamp', default=None, action='store_false', dest='preserve_timestamp')
parser.add_argument('-a', '--audio-language', action='append', help='Audio languages to retain. May be specified multiple times.')
parser.add_argument('-s', '--subtitle-language', action='append', help='Subtitle languages to retain. May be specified multiple times.')
group = parser.add_mutually_exclusive_group()
group.add_argument('-m', '--log-subtitle', default=None, action='store_true', help='Log if stripped file doesn\'t have a subtitle track.')
group.add_argument('--no-log-subtitle', default=None, action='store_false', dest='log_subtitle')
rename = parser.add_mutually_exclusive_group()
rename.add_argument('-r', '--rename-tv', default=None, action='store_true', help='Rename video track names to include immediate parent directory.')
rename.add_argument('-e', '--rename-movie', default=None, action='store_true', help='Use the filename to rename the video track names.')
parser.add_argument('--no-rename-tv', default=None, action='store_false', dest='rename_tv')
parser.add_argument('--no-rename-movie', default=None, action='store_false', dest='rename_movie')
parser.add_argument('-b', '--mkvmerge-bin', default=MKVMERGE_BIN, help='Path to mkvmerge binary.')
args = parser.parse_args()

LOG = LOG if args.log is None else args.log
if LOG:
    LOG_DIR = os.path.dirname(os.path.realpath(__file__))
    LOG_FILE = datetime.now().strftime('log_%Y%m%d-%H%M%S.log')
    LOG_PATH = os.path.abspath(os.path.join(LOG_DIR, LOG_FILE))
    Logger.init(LOG_PATH)

Logger.write('Running', os.path.basename(__file__), 'with configuration:')

MKVMERGE_BIN = os.path.abspath(args.mkvmerge_bin)
Logger.write('MKVMERGE_BIN =', MKVMERGE_BIN)

DIR = os.path.abspath(args.dir)
Logger.write('DIR =', DIR)

DRY_RUN = DRY_RUN if args.dry_run is None else args.dry_run
Logger.write('DRY_RUN =', DRY_RUN)

PRESERVE_TIMESTAMP = PRESERVE_TIMESTAMP if args.preserve_timestamp is None else args.preserve_timestamp
Logger.write('PRESERVE_TIMESTAMP =', PRESERVE_TIMESTAMP)

AUDIO_LANG = AUDIO_LANG if args.audio_language is None else args.audio_language
Logger.write('AUDIO_LANG =', AUDIO_LANG)
if len(AUDIO_LANG) == 0:
    raise RuntimeError('At least one audio language to retain must be specified.')

# We don't need to check for subtitles to retain since some people might choose to retain nothing at all.
SUBTITLE_LANG = SUBTITLE_LANG if args.subtitle_language is None else args.subtitle_language
Logger.write('SUBTITLE_LANG =', SUBTITLE_LANG)

LOG_MISSING_SUBTITLE = LOG_MISSING_SUBTITLE if args.log_subtitle is None else args.log_subtitle
Logger.write('LOG_MISSING_SUBTITLE =', LOG_MISSING_SUBTITLE)

RENAME_TV = RENAME_TV if args.rename_tv is None else args.rename_tv
Logger.write('RENAME_TV =', RENAME_TV)

RENAME_MOVIE = RENAME_MOVIE if args.rename_movie is None else args.rename_movie
Logger.write('RENAME_MOVIE =', RENAME_MOVIE)

if RENAME_TV is True and RENAME_MOVIE is True:
    raise RuntimeError('Setting RENAME_TV = True and RENAME_MOVIE = True at the same time is not allowed.')

NAME_RE = re.compile(r'^(.+)\.mkv$', flags=re.IGNORECASE)
VIDEO_RE = re.compile(r'^Track ID (?P<id>\d+): video \([\w/\.-]+\) [number:\d+ uid:\d+ codec_id:[\w/]+ codec_private_length:\d+ codec_private_data:[a-f\d]+ language:(?P<language>[a-z]{3})(?: track_name:(?P<name>.+))? pixel_dimensions')
AUDIO_RE = re.compile(r'^Track ID (?P<id>\d+): audio \([\w/]+\) [number:\d+ uid:\d+ codec_id:[\w/]+ codec_private_length:\d+ language:(?P<language>[a-z]{3})(?: track_name:(?P<name>.+))? default_track:(?P<default>[01]{1})')
SUBTITLE_RE = re.compile(r'^Track ID (?P<id>\d+): subtitles \([\w/]+\) [number:\d+ uid:\d+ codec_id:[\w/]+ codec_private_length:\d+ language:(?P<language>[a-z]{3})(?: track_name:(?P<name>.+))? default_track:(?P<default>[01]{1}) forced_track:([01]{1})')

for dirpath, dirnames, filenames in os.walk(DIR):
    for filename in filenames:

        # Process MKV files only
        if not filename.lower().endswith('.mkv'):
            continue

        Logger.write('============')

        # Path to file
        path = os.path.join(dirpath, filename)

        # Attempt to identify file
        Logger.write('Identifying', path)
        cmd = [ MKVMERGE_BIN, '--identify-verbose', path ]
        try:
            result = subprocess.check_output(cmd)
        except subprocess.CalledProcessError:
            Logger.write('Failed to identify', path, stderr=True)
            continue

        # Find video, audio, and subtitle tracks
        video = list()
        audio = list()
        subtitles = list()
        Logger.write('Searching for video, audio, and subtitle tracks...')
        for line in StringIO(result):
            matches = AUDIO_RE.match(line)
            if matches is not None:
                audio.append(AudioTrack(**matches.groupdict()))
            else:
                matches = SUBTITLE_RE.match(line)
                if matches is not None:
                    subtitles.append(SubtitleTrack(**matches.groupdict()))
                else:
                    matches = VIDEO_RE.match(line)
                    if matches is not None:
                        video.append(VideoTrack(**matches.groupdict()))
        Logger.write('Found video track(s):')
        for i in video:
            Logger.write(i, indent=4)
        Logger.write('Found audio track(s):')
        for i in audio:
            Logger.write(i, indent=4)
        Logger.write('Found subtitle track(s):')
        for i in subtitles:
            Logger.write(i, indent=4)

        # Filter out tracks that don't match languages specified.
        Logger.write('Filtering audio track(s)...')
        audio_lang = filter(lambda x: x.language in AUDIO_LANG, audio)
        Logger.write('Removing audio languages(s):', stringifyLanguages(audio, audio_lang))
        Logger.write('Retaining audio language(s):', stringifyLanguages(audio_lang))

        # Skip files that don't have the specified language audio tracks
        if len(audio_lang) == 0:
            Logger.write('ERROR: No audio tracks matching specified language(s) for', path, '... Skipping.', stderr=True)
            continue

        Logger.write('Filtering subtitle track(s)...')
        subtitles_lang = filter(lambda x: x.language in SUBTITLE_LANG, subtitles)
        Logger.write('Removing subtitle languages(s):', stringifyLanguages(subtitles, subtitles_lang))
        Logger.write('Retaining subtitle language(s):', stringifyLanguages(subtitles))

        # Log that the file doesn't have the specified language subtitle tracks
        if len(subtitles_lang) == 0 and LOG_MISSING_SUBTITLE is True:
            Logger.write('WARNING: No subtitle tracks matching specified language(s) for', path, stderr=True)

        # Print tracks to retain
        Logger.write('Number of audio tracks retained:', len(audio_lang))
        Logger.write('Remuxing with the following audio track(s):')
        for i in audio_lang:
            Logger.write(i, indent=4)
        Logger.write('Number of subtitle tracks retained:', len(subtitles_lang))
        Logger.write('Remuxing with the following subtitle track(s):')
        for i in subtitles_lang:
            Logger.write(i, indent=4)

        # Skip files that don't need processing
        if len(audio) == len(audio_lang) and len(subtitles) == len(subtitles_lang) \
                and RENAME_TV is False and RENAME_MOVIE is False:
            Logger.write('Nothing to do for', path)
            continue

        # Build command
        cmd = [ MKVMERGE_BIN, '--output' ]

        target = path + '.tmp'
        cmd.append(target)

        if RENAME_TV is True:
            drive, tail = os.path.splitdrive(path)
            parent = os.path.split(os.path.dirname(tail))[-1]
            name = NAME_RE.match(os.path.basename(tail)).group(1)
	    cmd += [ '--title', parent + ': ' + name ]
        elif RENAME_MOVIE is True:
            name = NAME_RE.match(os.path.basename(path)).group(1)
	    cmd += [ '--title', name ]

        if len(audio_lang) > 0:
            cmd += [ '--audio-tracks', ','.join([ str(i.id) for i in audio_lang ]) ]
            for i in range(len(audio_lang)):
                cmd += [ '--default-track', ':'.join([ str(audio_lang[i].id), '0' if i else '1' ]) ]

        if len(subtitles_lang) > 0:
            cmd+= [ '--subtitle-tracks', ','.join([ str(i.id) for i in subtitles_lang ]) ]
            for i in range(len(subtitles_lang)):
                cmd += [ '--default-track', ':'.join([ str(subtitles_lang[i].id), '0']) ]

        cmd.append(path)

        # Attempt to process file
        Logger.write('Processing %s...' % (path))
        if DRY_RUN is False:
            try:
                result = subprocess.check_output(cmd)
            except subprocess.CalledProcessError as e:
                Logger.write('Remux of', path, 'failed!', stderr=True)
                Logger.write(e.cmd, stderr=True)
                Logger.write(e.output, stderr=True)
                continue
            else:
                Logger.write('Remux of', path, 'successful.')

        # Preserve timestamp
        if PRESERVE_TIMESTAMP is True:
            Logger.write('Preserving timestamp of', path)
            if DRY_RUN is False:
                stat = os.stat(path)
                os.utime(target, (stat.st_atime, stat.st_mtime))

        # Overwrite original file
        if DRY_RUN is False:
            try:
                os.unlink(path)
            except:
                os.unlink(target)
                Logger.write('Renaming of', target, 'to', path, 'failed!', stderr=True)
            else:
                os.rename(target, path)
