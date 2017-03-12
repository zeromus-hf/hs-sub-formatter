## sub_format.py

A little script to format subtitle files for HoneySelect's UITranslation plugin.

### Requirements
Just needs python 2.7

### Usage

Typically when you format subtitle files from someone else, things may not be in the correct place so it's a good idea to do a dry-run and address any *unknown line* errors like so:

	$ tools/sub_format.py HoneySelect/Audio/c00.txt c00.txt --dry-run
	Dry-run specified.
	Unknown line #sub ''hs_01_160'' [] at line 1206
	Unknown line  at line 1602
	Unknown line  at line 1607
	Unknown line  at line 1612
	warning: sub ha_01_206 (line 2551) with comment "" on line 2550 has duplicate comment at line 2553
	Unknown line sub "hh_01_227" Nuugu...hahaha oh, so much came out. Right? at line 4119
	Unknown line sub "hso_01_025" I'm getting so excited...it's amazing. at line 4294
	error: Please resolve the unknown lines

Then when they've been addressed, re-run without the `--dry-run` switch and checkout your newly formatted subtitle file.

Ocassionally subtitle files will have duplicate comments for the same ID, which are usually ignored but displayed as the script is running. Sometimes subtitle lines will have comments that have different text, or actual subtitles will have different translations for the same ID. In this case, you'll be prompted at the end to decide which comment and/or translation to use. Normally I prefer to resolving the offending lines than decide using the script as it can provide a bit more context as to what the duplicate came from. In most cases, for me, it's because the same ID is used more than once with the simple solution of incrementing the last digits of the ID.

### Unicode issues on Windows

Since this deals with utf8 subtitles, errors and the like will need to be outputted to the console. Windows needs to have a few prerequisites in order for python to display unicode characters properly. I recommend using an alternative windows terminal emulator if using Windows so that you can run commands before the shell starts. If using a git's MSYS shell, you can easily set this up by editing your `.bashrc` file.

You'll need to do the following:
- The console code page to unicode with `chcp 65001`. I'm using [ConEMU](https://conemu.github.io/) so I can run this command in `Environment -> Startup` settings.
- Force python to treat the stdout as utf8 by setting the environment variable `PYTHONIOENCODING` to `utf8`


