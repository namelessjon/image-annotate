# Image Annotate

Simple python script for adding some annotations to images

## What?

This script uses pyexiv to let you set some tags on images -- title, artist, description of the work, a source url, and tags/keywords.

It can be used from the commandline, but can also present a very simple gui app.

It was written partly to learn about GUI, and partly to scratch an itch for annotating artwork I find online.


## How does it work?

  You'll need python2 (bite me!), pyexiv, and pyqt4.  Then you just run it with the image as an argument.


``` shell
usage: image_annotate.py [-h] [-t TITLE] [-a ARTIST] [-d DESCRIPTION]
                         [-s SOURCE] [-T TAGS] [-o OUTPUT] [-n] [-r] [-v]
                         [infile] [outfile]

positional arguments:
  infile
  outfile

optional arguments:
  -h, --help            show this help message and exit
  -t TITLE, --title TITLE
                        The image title
  -a ARTIST, --artist ARTIST
                        The image artist
  -d DESCRIPTION, --description DESCRIPTION, --desc DESCRIPTION
                        A description of the image
  -s SOURCE, --source SOURCE
                        Source of the image
  -T TAGS, --tags TAGS  Source of the image
  -o OUTPUT, --output OUTPUT
                        File to save the new image to
  -n, --no-gui          No GUI
  -r, --read-only       Don't edit the data in the file
  -v, --verbose         Print stuff about what is being done
```

The infile can be piped in `STDIN`, in this case you might want to use `-o` to specify the filename.
