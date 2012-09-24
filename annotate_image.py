#!/usr/bin/python2
from PyQt4 import QtGui
import pyexiv2
import re
import argparse

class GenericTag(object):
    def __init__(self, imgMeta, tag):
        self.tag     = tag
        self.imgMeta = imgMeta


    def get(self):
        if self.has_key(self.tag):
            return self.imgMeta[self.tag].value
        else:
            return None

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
        return GenericTag.set(self,  re.split(",\s*", value))

    def get(self, encode=True):
        value = GenericTag.get(self)
        if encode and value:
            return ", ".join(value)
        else:
            return value


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
    def __init__(self, imageData):
        self.imageData = imageData
        self.imageMeta = pyexiv2.ImageMetadata.from_buffer(imageData)
        self.imageMeta.read()
        self.tagList = dict()

    @staticmethod
    def from_file(f):
        data = f.read()
        return MetaDataCollection(data)

    def tag(self, tagName, tagKlass=GenericTag):
        self.tagList[tagName] = tagKlass(self.imageMeta, tagName)
        return self.tagList[tagName]

    def list_tag(self, tagName):
        return self.tag(tagName, ListTag)

    def dict_tag(self, tagName):
        return self.tag(tagName, DictTag)









class SetImageMeta(QtGui.QWidget):
    def __init__(self, filename=None, parent=None, imgData=None):
        super(SetImageMeta, self).__init__(parent)

        self.setTags    = dict()

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


        # and a save button
        self.btn = QtGui.QPushButton('Save', self)
        self.mainLayout.addWidget(self.btn, self.next_row(), 1);

        # when we save, save the image
        self.btn.clicked.connect(self.save)

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
        self.imgMeta.write(True)
        exit()


def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--title', type=str, help='The image title')
    parser.add_argument('-a', '--artist', type=str, help='The image artist')
    parser.add_argument('-d', '--description', '--desc', type=str, help='A description of the image')
    parser.add_argument('-s', '--source', type=str, help="Source of the image")
    parser.add_argument('-T', '--tags', type=str,action='append', help="Source of the image")
    parser.add_argument('-o', '--output', type=str, help='File to save the new image to')
    parser.add_argument('-n', '--no-gui',  action='store_false',  help='No GUI')
    parser.add_argument('-r', '--read-only',  action='store_true',  help="Just read the data, don't display it")
    parser.add_argument('infile',  nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    return parser


if __name__ == '__main__':
    import sys

    parser = create_arg_parser()
    args,xtra = parser.parse_known_args()
    from pprint import pprint as pp
    meta = MetaDataCollection(args.infile.read())


    app = QtGui.QApplication(sys.argv)


    widget = SetImageMeta(filename=args.infile.name, imgData=meta.imageData, read_only=args.read_only)
    # add the various tag boxes
    widget.addItemRow('Title'       , meta.dict_tag('Xmp.dc.title'))
    widget.addItemRow('Artist'      , meta.tag('Exif.Image.Artist'))
    widget.addItemRow('Description' , meta.dict_tag('Xmp.dc.description'))
    widget.addItemRow('Source'      , meta.tag('Xmp.dc.source'))
    widget.addItemRow('Tags'        , meta.list_tag('Xmp.dc.subject'))
    widget.show()

    sys.exit(app.exec_())
