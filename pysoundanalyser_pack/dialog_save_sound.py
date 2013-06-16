# -*- coding: utf-8 -*-
#   Copyright (C) 2010-2011 Samuele Carcagno <sam.carcagno@gmail.com>
#   This file is part of pysoundanalyser

#    pysoundanalyser is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    pysoundanalyser is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with pysoundanalyser.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals
from PyQt4 import QtGui, QtCore

class saveSoundDialog(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        grid = QtGui.QGridLayout()
        n = 0
        
        #self.fileToWrite = None
        self.guessFileExtension = True
        formatLabel = QtGui.QLabel(self.tr('File Format: '))
        grid.addWidget(formatLabel, n, 0)
        self.formatChooser = QtGui.QComboBox()
        self.formatChooser.addItems(["wav"])#available_file_formats())
        self.formatChooser.setCurrentIndex(0)
        grid.addWidget(self.formatChooser, n, 1)
        self.connect(self.formatChooser,  QtCore.SIGNAL("currentIndexChanged(int)"), self.onFileFormatChange)
        self.suggestedExtension = str(self.formatChooser.currentText())

        encodingLabel = QtGui.QLabel(self.tr('Bits: '))
        grid.addWidget(encodingLabel, n, 2)
        self.encodingChooser = QtGui.QComboBox()
        self.encodingChooser.addItems(["16", "24", "32"])#available_encodings(str(self.formatChooser.currentText())))
        self.encodingChooser.setCurrentIndex(0)
        grid.addWidget(self.encodingChooser, n, 3)

        n = n+1
        channelLabel = QtGui.QLabel(self.tr('Channel: '))
        grid.addWidget(channelLabel, n, 0)
        self.channelChooser = QtGui.QComboBox()
        self.channelChooser.addItems([self.tr('Stereo'), self.tr('Mono')])
        self.channelChooser.setCurrentIndex(0)
        grid.addWidget(self.channelChooser, n, 1)
        
        n = n+1
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok|
                                     QtGui.QDialogButtonBox.Cancel)
        
        self.connect(buttonBox, QtCore.SIGNAL("accepted()"),
                     self, QtCore.SLOT("accept()"))
        self.connect(buttonBox, QtCore.SIGNAL("rejected()"),
                     self, QtCore.SLOT("reject()"))
        grid.addWidget(buttonBox, n, 2)
        self.setLayout(grid)
        self.setWindowTitle(self.tr("Save Sound Options"))

    def onFileFormatChange(self):
        pass
        ## for i in range(self.encodingChooser.count()):
        ##     self.encodingChooser.removeItem(0)
        ## self.encodingChooser.addItems(available_encodings(str(self.formatChooser.currentText())))
        ## self.suggestedExtension = str(self.formatChooser.currentText())
    
       
