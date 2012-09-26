#!/usr/bin/python2
from PyQt4 import QtGui
import pyexiv2
import re
import argparse
from tempfile import mkstemp
import os.path
import os
import stat


def get_umask():
    current_umask = os.umask(0)
    os.umask(current_umask)

    return current_umask

def set_perms(mask = (stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)):
    umask = get_umask()
    return ~umask & mask



class GenericTag(object):
    def __init__(self, imgMeta, tag, label=None):
        self.tag     = tag
        self.imgMeta = imgMeta
        self.set_label(label)


    def get(self):
        if self.has_key(self.tag):
            return self.imgMeta[self.tag].value
        else:
            return None

    def set_label(self, label):
        if label:
            self.label = label
        else:
            tag = re.split('\.', self.tag)[-1]
            self.label = tag.lower()

    def set(self, value):
        self.imgMeta[self.tag] = value

    def remove(self):
        try:
            del self.imgMeta[self.tag]
        except KeyError:
            pass

    def has_key(self, tag):
        if re.match('Exif.', tag):
            return tag in self.imgMeta.exif_keys
        elif re.match('Xmp.', tag):
            return tag in self.imgMeta.xmp_keys
        elif re.match('Iptc.', tag):
            return tag in self.imgMeta.iptc_keys

class ListTag(GenericTag):
    def set(self, value):
        if type(value) == str:
            value = re.split(",\s*", value)
        return GenericTag.set(self, ListTag.uniq(self.get(False) + value))


    def get(self, encode=True):
        value = GenericTag.get(self)
        if encode and value:
            return ", ".join(value)
        else:
            return value

    @staticmethod
    def uniq(seq, idfun=None):
        # order preserving
        if idfun is None:
            def idfun(x): return x
        seen = {}
        result = []
        for item in seq:
            marker = idfun(item)
            # in old Python versions:
            # if seen.has_key(marker)
            # but in new ones:
            if marker in seen: continue
            seen[marker] = 1
            result.append(item)
        return result


class DictTag(GenericTag):
    def set(self, text):
        GenericTag.set(self, {u'en-GB': text})

    def get(self, encode=True):
        value = GenericTag.get(self)
        if encode and value:
            if u'en-GB' in value:
                return value[u'en-GB']
            elif 'x-default' in value:
                return value['x-default']
            else:
                return ''
        else:
            return value

class MetaDataCollection(object):
    def __init__(self, imageData, outfile, read_only=False):
        self.infile    = imageData
        self.imageData = imageData.read()

        self.imageMeta = pyexiv2.ImageMetadata.from_buffer(self.imageData)

        self.imageMeta.read()

        self.tagList = list()
        self.tags    = dict()

        self.read_only = read_only
        self.outfile   = outfile


    def addTag(self, tag):
        self.tagList.append(tag.label)
        self.tags[tag.label] = tag
        return tag

    def tag(self, tagName, label=None, tagKlass=GenericTag):
        return self.addTag(tagKlass(self.imageMeta, tagName, label))

    def list_tag(self, tagName, label=None):
        return self.tag(tagName,label, ListTag)

    def dict_tag(self, tagName, label=None):
        return self.tag(tagName, label, DictTag)


    def each_tag(self):
        curr = 0
        length = len(self.tagList)
        while (curr < length):
            tag = self.tagList[curr]
            yield (tag, self.tags[tag])
            curr += 1

    @staticmethod
    def absolute_path(path):
        return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


    def save(self):
        if self.read_only:
            raise StandardError("Tried to save read only file!")
        else:
            # write back to the buffer
            self.imageMeta.write()
            if type(self.outfile) == file:
                self.outfile.write(self.imageMeta.buffer)
            else:
                path = MetaDataCollection.absolute_path(self.outfile)
                dirname = os.path.dirname(path)
                (outfd, tmpname) = mkstemp(dir=dirname, prefix='.tmp')
                try:
                    outfile = os.fdopen(outfd, "w")
                    outfile.write(self.imageMeta.buffer)

                    if self.infile != sys.stdin:
                        os.fchmod(outfd, set_perms(os.stat(self.infile.name).st_mode))
                    else:
                        os.fchmod(outfs, set_perms())

                    outfile.close()
                    os.rename(tmpname, path)
                except Exception, e:
                    os.remove(tmpname)
                    raise e




class SetImageMeta(QtGui.QWidget):
    def __init__(self, metadata, filename=None, parent=None, imgData=None, read_only=False):
        super(SetImageMeta, self).__init__(parent)

        self.setTags    = dict()
        self.metadata   = metadata

        # use a grid layout, for laziness
        self.mainLayout = QtGui.QGridLayout()
        self.setLayout(self.mainLayout)
        self.rowIdx = 0



        # add a thumbnail of the image
        if imgData:
            imgLabel = QtGui.QLabel(self)
            thumb = QtGui.QPixmap()
            thumb.loadFromData(imgData)
            thumb = thumb.scaledToWidth(100)
            imgLabel.setPixmap(thumb)
            self.mainLayout.addWidget(imgLabel, self.next_row(), 1)


        for label, tag in metadata.each_tag():
            self.addItemRow(label.capitalize(), tag)


        if not read_only:
            # and a save button
            self.btn = QtGui.QPushButton('Save', self)
            # when we save, save the image
            self.btn.clicked.connect(self.save)

            # add to the layout
            self.mainLayout.addWidget(self.btn, self.next_row(), 1);


        if filename:
            self.setWindowTitle(filename)
        else:
            self.setWindowTitle("No name");

    def addItemRow(self, label, tag):
        value = tag.get()

        lbl =  QtGui.QLabel(label)
        txt =  QtGui.QLineEdit(value)
        txt.setFixedWidth(400)
        row = self.next_row()
        self.mainLayout.addWidget(lbl, row, 0)
        self.mainLayout.addWidget(txt, row, 1)
        self.setTags[label] = [tag, txt]

    def next_row(self):
        self.rowIdx = self.rowIdx + 1
        return self.rowIdx



    def save(self):
        for key, value in self.setTags.iteritems():
            tag = value[0]
            txt = value[1]
            text = str(txt.text())
            if text == '':
                tag.remove()
            else:
                tag.set(text)
        self.metadata.save()
        self.close()


def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--title', type=str, help='The image title')
    parser.add_argument('-a', '--artist', type=str, help='The image artist')
    parser.add_argument('-d', '--description', '--desc', type=str, help='A description of the image')
    parser.add_argument('-s', '--source', type=str, help="Source of the image")
    parser.add_argument('-T', '--tags', type=str,action='append', help="Source of the image")
    parser.add_argument('-o', '--output', type=str, help='File to save the new image to')
    parser.add_argument('-n', '--no-gui',  action='store_true',  help='No GUI')
    parser.add_argument('-r', '--read-only',  action='store_true',  help="Don't edit the data in the file")
    parser.add_argument('-v', '--verbose', action='store_true', help='Print stuff about what is being done')
    parser.add_argument('infile',  nargs='?', default=sys.stdin)
    parser.add_argument('outfile',  nargs='?', default=sys.stdout)
    return parser


if __name__ == '__main__':
    import sys

    parser = create_arg_parser()
    args,xtra = parser.parse_known_args()
    from pprint import pprint as pp
    # pp(args)

    # set up files!
    if args.infile != sys.stdin:
        infile = open(args.infile, 'r')
        if not os.access(args.infile, os.W_OK):
            args.read_only = True
        if args.outfile == sys.stdout: # if we have no outfile, we probably actually want to save back to the image
            outfile = args.infile
        else:
            outfile = args.outfile
    else:
        infile = args.infile
        outfile = args.outfile





    meta = MetaDataCollection(infile, outfile, args.read_only)
    meta.dict_tag('Xmp.dc.title')
    meta.tag('Exif.Image.Artist')
    meta.dict_tag('Xmp.dc.description')
    meta.tag('Xmp.dc.source')
    meta.list_tag('Xmp.dc.subject', label='tags')


    valueSet = False
    if not args.read_only:
        argHash = vars(args)
        for label, tag in meta.each_tag():
            val = argHash[label]
            if val:
                if tag.get() != val:
                    valueSet = True
                tag.set(val)



    if args.no_gui:
        if args.verbose:
            for label, tag in meta.each_tag():
                tval = tag.get()
                if tval:
                    print ("{0}: {1}".format(label.capitalize(), tval))
        if not args.read_only and valueSet:
            meta.save()
    else:
        if type(args.infile) == file:
            filename = args.infile.name
        else:
            filename = args.infile
        app = QtGui.QApplication(sys.argv)
        widget = SetImageMeta(filename=filename, metadata=meta, imgData=meta.imageData, read_only=args.read_only)
        # add the various tag boxes
        widget.show()

        sys.exit(app.exec_())
