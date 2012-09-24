#!/usr/bin/python2
from PyQt4 import QtGui
import pyexiv2
import re

class SetImageMeta(QtGui.QWidget):
    def __init__(self, parent=None, filename=None):
        super(SetImageMeta, self).__init__(parent)

        self.setTags    = dict()

        # use a grid layout, for laziness
        self.mainLayout = QtGui.QGridLayout()
        self.setLayout(self.mainLayout)

        # load up the metadata
        self.imgMeta = pyexiv2.ImageMetadata(filename)
        self.imgMeta.read()


        # add a thumbnail of the image
        imgLabel = QtGui.QLabel(self)
        imgLabel.setPixmap(QtGui.QPixmap(filename).scaledToWidth(100))
        self.mainLayout.addWidget(imgLabel, 0, 1)

        # add the various tag boxes
        self.addItemRow(TagEntry('Title', 'Xmp.dc.title', self.dictArg, self.toDict), 1)
        self.addItemRow(TagEntry('Artist', 'Exif.Image.Artist'), 2)
        self.addItemRow(TagEntry('Description', 'Xmp.dc.description', self.dictArg, self.toDict), 3)
        self.addItemRow(TagEntry('Source', 'Xmp.dc.source'), 4)
        self.addItemRow(TagEntry('Tags', 'Xmp.dc.subject', self.listArg, self.toList), 5)

        # and a save button
        self.btn = QtGui.QPushButton('Save', self)
        self.mainLayout.addWidget(self.btn, 6, 1);

        # when we save, save the image
        self.btn.clicked.connect(self.save)

        if filename:
            self.setWindowTitle(filename)
        else:
            self.setWindowTitle("No name");

    def addItemRow(self, tag, row):
        if self.has_key(tag.tag):
            value = tag.decode(self.imgMeta)
        else:
            value = ''
        lbl =  QtGui.QLabel(tag.label)
        txt =  QtGui.QLineEdit(value)
        txt.setFixedWidth(400)
        self.mainLayout.addWidget(lbl, row, 0)
        self.mainLayout.addWidget(txt, row, 1)
        self.setTags[tag.tag] = [tag, txt]

    @staticmethod
    def dictArg(metaData, tag):
        value = metaData[tag].value
        if u'en-GB' in value:
            return value[u'en-GB']
        elif 'x-default' in value:
            return value['x-default']
        else:
            return ''

    @staticmethod
    def toDict(text):
        return {u'en-GB': text}

    @staticmethod
    def listArg(metaData, tag):
        value = metaData[tag].value
        return ", ".join(value)

    @staticmethod
    def toList(text):
        return re.split(",\s*", text)

    def has_key(self, tag):
        if re.match('Exif.', tag):
            return tag in self.imgMeta.exif_keys
        elif re.match('Xmp.', tag):
            return tag in self.imgMeta.xmp_keys
        elif re.match('Iptc.', tag):
            return tag in self.imgMeta.iptc_keys

    def save(self):
        for key, value in self.setTags.iteritems():
            tag = value[0]
            txt = value[1]
            text = str(txt.text())
            if text == '':
                try:
                    del self.imgMeta[key]
                except KeyError:
                    pass
            else:
                self.imgMeta[key] = tag.encode(text)
        self.imgMeta.write(True)
        exit()



class TagEntry:
    def __init__(self, label, tag, decodeFunc=None, encodeFunc=None):
        self.label = label
        self.tag   = tag
        self.decodeFunc =  decodeFunc
        self.encodeFunc = encodeFunc

    def encode(self, text):
        if self.encodeFunc:
            return self.encodeFunc(text)
        else:
            return text

    def decode(self, imgMeta):
        if self.decodeFunc:
            return self.decodeFunc(imgMeta, self.tag)
        else:
            return imgMeta[self.tag].value


if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)

    widget = SetImageMeta(filename=sys.argv[1])
    widget.show()

    sys.exit(app.exec_())
