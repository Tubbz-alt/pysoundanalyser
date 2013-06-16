#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   Copyright (C) 2010-2013 Samuele Carcagno <sam.carcagno@gmail.com>
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
import sip
sip.setapi("QString", 2)
import sys, platform, os, copy, pickle, traceback
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QApplication
import logging, signal
from pysoundanalyser_pack import qrc_resources

from numpy import sin, cos, pi, sqrt, abs, arange, zeros, mean, concatenate, convolve, angle, real, log2, log10, int_, linspace, repeat, ceil, unique, hamming, hanning, blackman, bartlett, round, transpose
from numpy.fft import rfft, irfft, fft, ifft
import scipy
from tempfile import mkstemp
from pysoundanalyser_pack.global_parameters import*
from pysoundanalyser_pack._version_info import*
from pysoundanalyser_pack.utilities_open_manual import*
__version__ = pysnd_version
signal.signal(signal.SIGINT, signal.SIG_DFL)



local_dir = os.path.expanduser("~") +'/.local/share/data/pysoundanalyser/'
if os.path.exists(local_dir) == False:
    os.makedirs(local_dir)
stderrFile = os.path.expanduser("~") +'/.local/share/data/pysoundanalyser/pysoundanalyser_stderr_log.txt'

logging.basicConfig(filename=stderrFile,level=logging.DEBUG,)



def excepthook(except_type, except_val, tbck):
    """ Show errors in message box"""
    # recover traceback
    tb = traceback.format_exception(except_type, except_val, tbck)
    ret = QtGui.QMessageBox.critical(None, "Critical Error! Something went wrong, the following info may help you troubleshooting",
                                    ''.join(tb),
                                    QtGui.QMessageBox.Ok)
    timeStamp = ''+ time.strftime("%d/%m/%y %H:%M:%S", time.localtime()) + ' ' + '\n'
    logMsg = timeStamp + ''.join(tb)
    logging.debug(logMsg)



#__version__ = "2012.10.02"

if platform.system() == 'Windows':
    import winsound

import pysndlib as sndlib
from pysoundanalyser_pack.utility_functions import*
#from pysoundanalyser_pack.utility_generate_stimuli import*
import pysoundanalyser_pack.random_id as random_id
from pysoundanalyser_pack.win_waveform_plot import*
from pysoundanalyser_pack.win_spectrum_plot import*
from pysoundanalyser_pack.win_spectrogram_plot import*
from pysoundanalyser_pack.win_acf_plot import*
from pysoundanalyser_pack.win_autocorrelogram_plot import*
from pysoundanalyser_pack.dialog_edit_preferences import*
from pysoundanalyser_pack.dialog_resample import*
from pysoundanalyser_pack.dialog_save_sound import*
from pysoundanalyser_pack.dialog_change_channel import*
from pysoundanalyser_pack.dialog_concatenate import*
from pysoundanalyser_pack.dialog_cut import*
from pysoundanalyser_pack.dialog_apply_filter import*
from pysoundanalyser_pack.dialog_generate_sound import*
from pysoundanalyser_pack.dialog_generate_noise import*
from pysoundanalyser_pack.dialog_generate_sinusoid import*
#from pysoundanalyser_pack.dialog_get_font import*
tmpprm = {}; tmpprm['data'] = {}
tmpprm = global_parameters(tmpprm)
tmpprm = get_prefs(tmpprm)
if tmpprm['pref']['wavmanager'] == 'scipy':
    from pysoundanalyser_pack.scipy_wav import scipy_wavwrite, scipy_wavread
elif tmpprm['pref']['wavmanager'] == 'audiolab':
    import scikits.audiolab as audiolab
    from scikits.audiolab import Sndfile

class applicationWindow(QtGui.QMainWindow):
    """main window"""
    def __init__(self, prm):
        QtGui.QMainWindow.__init__(self)
        self.prm = prm
        self.prm['version'] = __version__
        self.prm['revno'] = pysnd_revno
        self.prm['builddate'] = pysnd_builddate
        self.currLocale = prm['data']['currentLocale']
        self.currLocale.setNumberOptions(self.currLocale.OmitGroupSeparator | self.currLocale.RejectGroupSeparator)
        self.setWindowTitle(self.tr("Python Sound Analyser"))
        # main widget
        self.main_widget = QtGui.QWidget(self)
        #MENU-----------------------------------

        self.menubar = self.menuBar()
        #FILE MENU
        self.fileMenu = self.menubar.addMenu(self.tr('&File'))

        exitButton = QtGui.QAction(QtGui.QIcon(':/exit.svg'), self.tr('Exit'), self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.setStatusTip(self.tr('Exit application'))
        self.connect(exitButton, QtCore.SIGNAL('triggered()'), QtCore.SLOT('close()'))
        self.statusBar()
        self.fileMenu.addAction(exitButton)


        #EDIT MENU
        self.editMenu = self.menubar.addMenu(self.tr('&Edit'))
        self.editPrefAction = QtGui.QAction(self.tr('Preferences'), self)
        self.editMenu.addAction(self.editPrefAction)
        self.connect(self.editPrefAction, QtCore.SIGNAL('triggered()'), self.onEditPref)

        self.selectAllAction = QtGui.QAction(self.tr('Select All'), self)
        self.editMenu.addAction(self.selectAllAction)
        self.connect(self.selectAllAction, QtCore.SIGNAL('triggered()'), self.onSelectAll)

        #GET MENU
        self.getMenu = self.menubar.addMenu(self.tr('&Get'))
        self.getRMSAction = QtGui.QAction(self.tr('Root Mean Square'), self)
        self.getMenu.addAction(self.getRMSAction)
        self.connect(self.getRMSAction, QtCore.SIGNAL('triggered()'), self.onClickGetRMSButton)

        #GET MENU
        self.processMenu = self.menubar.addMenu(self.tr('&Process'))
        self.applyFilterMenu = self.processMenu.addMenu(self.tr('&Apply Filter'))
        self.fir2PresetsAction = QtGui.QAction(self.tr('FIR2 Presets'), self)
        self.applyFilterMenu.addAction(self.fir2PresetsAction)
        self.connect(self.fir2PresetsAction, QtCore.SIGNAL('triggered()'), self.onClickApplyFIR2PresetsButton)
        

        #GENERATE MENU
        self.generateMenu = self.menubar.addMenu(self.tr('&Generate'))
        self.generateNoiseAction = QtGui.QAction(self.tr('Noise'), self)
        self.generateMenu.addAction(self.generateNoiseAction)
        self.connect(self.generateNoiseAction, QtCore.SIGNAL('triggered()'), self.onClickGenerateNoise)
        self.generateSinusoidAction = QtGui.QAction(self.tr('Sinusoid'), self)
        self.generateMenu.addAction(self.generateSinusoidAction)
        self.connect(self.generateSinusoidAction, QtCore.SIGNAL('triggered()'), self.onClickGenerateSinusoid)
        self.generateHarmComplAction = QtGui.QAction(self.tr('Harmonic Complex'), self)
        self.generateMenu.addAction(self.generateHarmComplAction)
        self.connect(self.generateHarmComplAction, QtCore.SIGNAL('triggered()'), self.onClickGenerateHarmCompl)
        #PLOT MENU
        self.plotMenu = self.menubar.addMenu(self.tr('&Plot'))
        self.plotWaveformAction = QtGui.QAction(self.tr('Waveform'), self)
        self.plotMenu.addAction(self.plotWaveformAction)
        self.connect(self.plotWaveformAction, QtCore.SIGNAL('triggered()'), self.onClickPlotButton)
        #
        self.plotSpectrumAction = QtGui.QAction(self.tr('Spectrum'), self)
        self.plotMenu.addAction(self.plotSpectrumAction)
        self.connect(self.plotSpectrumAction, QtCore.SIGNAL('triggered()'), self.onClickSpectrumButton)
        #
        self.plotSpectrogramAction = QtGui.QAction(self.tr('Spectrogram'), self)
        self.plotMenu.addAction(self.plotSpectrogramAction)
        self.connect(self.plotSpectrogramAction, QtCore.SIGNAL('triggered()'), self.onClickSpectrogramButton)
        #
        self.plotAutocorrelationAction = QtGui.QAction(self.tr('Autocorrelation'), self)
        self.plotMenu.addAction(self.plotAutocorrelationAction)
        self.connect(self.plotAutocorrelationAction, QtCore.SIGNAL('triggered()'), self.onClickAutocorrelationButton)
        #
        self.plotAutocorrelogramAction = QtGui.QAction(self.tr('Autocorrelogram'), self)
        self.plotMenu.addAction(self.plotAutocorrelogramAction)
        self.connect(self.plotAutocorrelogramAction, QtCore.SIGNAL('triggered()'), self.onClickAutocorrelogramButton)

        #HELP MENU
        self.helpMenu = self.menubar.addMenu(self.tr('&Help'))

        self.onShowManualPdfAction = QtGui.QAction(self.tr('Manual'), self)
        self.helpMenu.addAction(self.onShowManualPdfAction)
        self.connect(self.onShowManualPdfAction, QtCore.SIGNAL('triggered()'), onShowManualPdf)

        
        self.onAboutAction = QtGui.QAction(self.tr('About pysoundanalyser'), self)
        self.helpMenu.addAction(self.onAboutAction)
        self.connect(self.onAboutAction, QtCore.SIGNAL('triggered()'), self.onAbout)

        # create a vertical box layout widget
        vbl = QtGui.QVBoxLayout()
        self.sndList = {}
     
        #LOAD BUTTON
        loadButton = QtGui.QPushButton(self.tr("Load Sound"), self)
        QtCore.QObject.connect(loadButton,
                               QtCore.SIGNAL('clicked()'), self.onClickLoadButton)
        #SAVE BUTTON
        saveButton = QtGui.QPushButton(self.tr("Save As"), self)
        QtCore.QObject.connect(saveButton,
                               QtCore.SIGNAL('clicked()'), self.onClickSaveButton)

        #CLONE BUTTON
        cloneButton = QtGui.QPushButton(self.tr("Clone Sound"), self)
        QtCore.QObject.connect(cloneButton,
                               QtCore.SIGNAL('clicked()'), self.onClickCloneButton)
        
        #RENAME BUTTON
        renameButton = QtGui.QPushButton(self.tr("Rename"), self)
        QtCore.QObject.connect(renameButton,
                               QtCore.SIGNAL('clicked()'), self.onClickRenameButton)
        #REMOVE BUTTON
        removeButton = QtGui.QPushButton(self.tr("Remove"), self)
        QtCore.QObject.connect(removeButton,
                               QtCore.SIGNAL('clicked()'), self.onClickRemoveButton)
        #REMOVE ALL
        removeAllButton = QtGui.QPushButton(self.tr("Remove All"), self)
        QtCore.QObject.connect(removeAllButton,
                               QtCore.SIGNAL('clicked()'), self.onClickRemoveAllButton)
        #PLAY BUTTON
        playButton = QtGui.QPushButton(self.tr("Play"), self)
        QtCore.QObject.connect(playButton,
                               QtCore.SIGNAL('clicked()'), self.onClickPlayButton)
        #SPECTRUM BUTTON
        spectrumButton = QtGui.QPushButton(self.tr("Spectrum"), self)
        QtCore.QObject.connect(spectrumButton,
                               QtCore.SIGNAL('clicked()'), self.onClickSpectrumButton)
        #SPECTROGRAM BUTTON
        spectrogramButton = QtGui.QPushButton(self.tr("Spectrogram"), self)
        QtCore.QObject.connect(spectrogramButton,
                               QtCore.SIGNAL('clicked()'), self.onClickSpectrogramButton)

        #AUTOCORRELATION BUTTON
        autocorrelationButton = QtGui.QPushButton(self.tr("Autocorrelation"), self)
        QtCore.QObject.connect(autocorrelationButton,
                               QtCore.SIGNAL('clicked()'), self.onClickAutocorrelationButton)
        #AUTOCORRELOGRAM BUTTON
        autocorrelogramButton = QtGui.QPushButton(self.tr("Autocorrelogram"), self)
        QtCore.QObject.connect(autocorrelogramButton,
                               QtCore.SIGNAL('clicked()'), self.onClickAutocorrelogramButton)
        
        #PLOT BUTTON
        plotButton = QtGui.QPushButton(self.tr("Plot Waveform"), self)
        QtCore.QObject.connect(plotButton,
                               QtCore.SIGNAL('clicked()'), self.onClickPlotButton)
        #RESAMPLE BUTTON
        resampleButton = QtGui.QPushButton(self.tr("Resample"), self)
        QtCore.QObject.connect(resampleButton,
                               QtCore.SIGNAL('clicked()'), self.onClickResampleButton)

        #SCALE BUTTON
        scaleButton = QtGui.QPushButton(self.tr("Scale"), self)
        QtCore.QObject.connect(scaleButton,
                               QtCore.SIGNAL('clicked()'), self.onClickScaleButton)

        #LEVEL DIFF BUTTON
        levelDiffButton = QtGui.QPushButton(self.tr("Level Difference"), self)
        QtCore.QObject.connect(levelDiffButton,
                               QtCore.SIGNAL('clicked()'), self.onClickLevelDiffButton)

        #CONCATENATE BUTTON
        concatenateButton = QtGui.QPushButton(self.tr("Concatenate"), self)
        QtCore.QObject.connect(concatenateButton,
                               QtCore.SIGNAL('clicked()'), self.onClickConcatenateButton)
        #CUT BUTTON
        cutButton = QtGui.QPushButton(self.tr("Cut"), self)
        QtCore.QObject.connect(cutButton,
                               QtCore.SIGNAL('clicked()'), self.onClickCutButton)
        
        #MOVE DOWN BUTTON
        moveDownButton = QtGui.QPushButton(self.tr("Move Down"), self)
        QtCore.QObject.connect(moveDownButton,
                               QtCore.SIGNAL('clicked()'), self.onClickMoveDownButton)
        #MOVE UP BUTTON
        moveUpButton = QtGui.QPushButton(self.tr("Move Up"), self)
        QtCore.QObject.connect(moveUpButton,
                               QtCore.SIGNAL('clicked()'), self.onClickMoveUpButton)



        self.sndTableWidget = QtGui.QTableWidget()
        #self.sndTableWidget.setSortingEnabled(True)
        self.sndTableWidget.setColumnCount(3)
        self.sndTableWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.sndTableWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        
        self.sndTableWidget.setHorizontalHeaderLabels([self.tr('Label'), self.tr('Channel'), 'id'])
        self.sndTableWidget.hideColumn(2)
        self.connect(self.sndTableWidget, QtCore.SIGNAL("itemChanged(QTableWidgetItem*)"), self.tableItemChanged)
        self.connect(self.sndTableWidget, QtCore.SIGNAL("cellDoubleClicked(int,int)"), self.onCellDoubleClicked)
        vbl.addWidget(loadButton)
        vbl.addWidget(saveButton)
        vbl.addWidget(cloneButton)
        vbl.addWidget(concatenateButton)
        vbl.addWidget(cutButton)
        vbl.addWidget(playButton)
        vbl.addWidget(plotButton)
        vbl.addWidget(spectrumButton)
        vbl.addWidget(spectrogramButton)
        vbl.addWidget(autocorrelationButton)
        vbl.addWidget(autocorrelogramButton)
        vbl.addWidget(levelDiffButton)
        vbl.addWidget(scaleButton)
        vbl.addWidget(resampleButton)
        vbl.addWidget(renameButton)
        vbl.addWidget(removeButton)
        vbl.addWidget(removeAllButton)
        
        
        vbl.addStretch(1)

        vbl3 = QtGui.QVBoxLayout()
        vbl3.addWidget(moveUpButton)
        vbl3.addWidget(moveDownButton)
        self.infoPane = QtGui.QLabel(self.tr('No Selection                                           '))
        vbl3.addWidget(self.infoPane)
        vbl3.addStretch(1)
        grid = QtGui.QGridLayout(self.main_widget)
        #grid.addLayout(vbl1, 1, 1)
        grid.addLayout(vbl, 1, 1)
        grid.addWidget(self.sndTableWidget,1,2)
        grid.addLayout(vbl3,1,3)
        QtCore.QObject.connect(self.sndTableWidget, QtCore.SIGNAL('itemSelectionChanged()'), self.onSelectionChanged)
        # set the focus on the main widget
        self.main_widget.setFocus()
        # set the central widget of MainWindow to main_widget
        self.setCentralWidget(self.main_widget)
    def tableItemChanged(self, item):
        pass
        
    def onEditPref(self):
        dialog = preferencesDialog(self)
        if dialog.exec_():
            dialog.permanentApply()
    def onSelectAll(self):
        for i in range(self.sndTableWidget.rowCount()):
            for j in range(self.sndTableWidget.columnCount()):
                self.sndTableWidget.item(i,j).setSelected(True)
    def swapRow(self, row1, row2):

        lab1 = self.sndTableWidget.takeItem(row1,0)
        lab2 = self.sndTableWidget.takeItem(row2,0)
        chan1 = self.sndTableWidget.takeItem(row1,1)
        chan2 = self.sndTableWidget.takeItem(row2,1)
        id1 = self.sndTableWidget.takeItem(row1,2)
        id2 = self.sndTableWidget.takeItem(row2,2)

        self.sndTableWidget.setItem(row1, 0, lab2)
        self.sndTableWidget.setItem(row2, 0, lab1)
        self.sndTableWidget.setItem(row1, 1, chan2)
        self.sndTableWidget.setItem(row2, 1, chan1)
        self.sndTableWidget.setItem(row1, 2, id2)
        self.sndTableWidget.setItem(row2, 2, id1)

        for j in range(self.sndTableWidget.columnCount()):
            self.sndTableWidget.item(row1, j).setSelected(False)
            self.sndTableWidget.item(row2, j).setSelected(True)

    def onClickMoveDownButton(self):
        lastRow = self.sndTableWidget.rowCount() - 1
        rows = self.findSelectedItemRows()
        if len(rows) > 1:
            QtGui.QMessageBox.warning(self, self.tr('Warning'), self.tr('Only one sound can be moved at a time'))
        elif len(rows) < 1:
            pass
        else:
            row = rows[0]
            if row == lastRow:
                pass
            else:
                self.swapRow(row, row+1)
    def onClickMoveUpButton(self):
        rows = self.findSelectedItemRows()
        if len(rows) > 1:
            QtGui.QMessageBox.warning(self, self.tr('Warning'), self.tr('Only one sound can be moved at a time'))
        elif len(rows) < 1:
            pass
        else:
            row = rows[0]
            if row == 0:
                pass
            else:
                self.swapRow(row, row-1)
        
        
    def onClickLoadButton(self):
        #self.sndTableWidget.setSortingEnabled(False)
        files = QtGui.QFileDialog.getOpenFileNames(self, self.tr("pysoundanalyser - Choose file to load"), '',self.tr("Supported Sound Files (*.wav);;All Files (*)"))
        
        for f in range(len(files)):
            sndFile = files[f]
            #xxxxxxxxxxxxxxx
            #Should check here if it is a valid wav file
            foo = True 
            if foo == True:
                
                x,fs,nb = self.loadWav(sndFile)
                thisSnd = {}
                if len(x.shape) == 2:
                    thisSnd['wave'] = x[:,0]
                else:
                    thisSnd['wave'] = x
                thisSnd['fs'] = int(fs)
                thisSnd['nBits'] = nb
                thisSnd['chan'] = self.tr('Right')
                thisSnd['nSamples'] = len(thisSnd['wave'])
                thisSnd['duration'] = thisSnd['nSamples'] / thisSnd['fs']
                tmpName = sndFile
                tmpName = sndFile.split('/')[len(sndFile.split('/'))-1]
                tmpName = tmpName.split('.')[0]
                tmpNameR =  tmpName #+ '-R'#'snd-0-R'
                tmpNameL =  tmpName #+ '-L'#'snd-0-L'
        
                thisSnd['label'] = tmpNameR
                condSat = 0
                while condSat == 0:
                    tmp_id = random_id.random_id(5, 'alphanumeric')
                    if tmp_id in self.sndList:
                        condSat = 0
                    else:
                        condSat = 1
                self.sndList[tmp_id] = copy.copy(thisSnd)
                currCount = len(self.sndList)
                self.sndTableWidget.setRowCount(currCount)
                newItem = QtGui.QTableWidgetItem(thisSnd['label'])
                newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.sndTableWidget.setItem(currCount-1, 0, newItem)
                newItem = QtGui.QTableWidgetItem(thisSnd['chan'])
                newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.sndTableWidget.setItem(currCount-1, 1, newItem)
                self.sndList[tmp_id]['qid'] = QtGui.QTableWidgetItem(tmp_id)
                self.sndTableWidget.setItem(currCount-1, 2, self.sndList[tmp_id]['qid'])
                
        
                if len(x.shape) == 2:
                    thisSnd = {}
                    thisSnd['wave'] = x[:,1]
                    thisSnd['fs'] = int(fs)
                    thisSnd['nBits'] = nb
                    thisSnd['chan'] = self.tr('Left')
                    thisSnd['nSamples'] = len(thisSnd['wave'])
                    thisSnd['duration'] = thisSnd['nSamples'] / thisSnd['fs']
                    thisSnd['label'] = tmpNameL
                    condSat = 0
                    while condSat == 0:
                        tmp_id = random_id.random_id(5, 'alphanumeric')
                        if tmp_id in self.sndList:
                            condSat = 0
                        else:
                            condSat = 1
                    self.sndList[tmp_id] = copy.copy(thisSnd)
                    currCount = len(self.sndList)
                    self.sndTableWidget.setRowCount(currCount)
                    newItem = QtGui.QTableWidgetItem(thisSnd['label'])
                    newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                    self.sndTableWidget.setItem(currCount-1, 0, newItem)
                    newItem = QtGui.QTableWidgetItem(thisSnd['chan'])
                    newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                    self.sndTableWidget.setItem(currCount-1, 1, newItem)
                    self.sndList[tmp_id]['qid'] = QtGui.QTableWidgetItem(tmp_id)
                    self.sndTableWidget.setItem(currCount-1, 2, self.sndList[tmp_id]['qid'])

       
                
            else:
                pass
        selItems = self.sndTableWidget.selectedItems()
        #self.sndTableWidget.setSortingEnabled(True)
    def loadFileValid(self, sndFile):
        #xxxxxxxxxxxxxxx
        # need to update this function
        if len(sndFile) == 0:
            fileValid = False
            msg = None
        else:
            try:
                fileToRead = Sndfile(str(sndFile), 'r')
                fileValid = True
                fileToRead.close()
            except IOError:
                msg = self.tr("Cannot open %1 IOError").arg(sndFile) #'Cannot open' + sndFile + '\n IOError'
                fileValid = False
        #else:
        #    fileValid = False
        #    msg = 'cannot open' + sndFile + ' only wav supported at the moment'
        if fileValid == False and msg != None:
            QtGui.QMessageBox.warning(self, self.tr('Warning'), msg)

        return fileValid
    def loadWav(self,fName):
        if self.prm['pref']['wavmanager'] == 'scipy':
            fs, snd, nbits = scipy_wavread(fName)
       
        return snd, fs, nbits
    def onSelectionChanged(self):
        ids = self.findSelectedItemIds()
        if len(ids) == 0:
            self.infoPane.setText(self.tr('No Selection'))
        elif len(ids) == 2:
            snd1 = self.sndList[ids[0]]
            snd2 = self.sndList[ids[1]]
            rms1 = sndlib.getRms(snd1['wave'])
            rms2 = sndlib.getRms(snd2['wave'])
            dbDiff = 20*log10(rms1/rms2)
            if dbDiff >= 0:
                w = '+'
            elif dbDiff < 0:
                w = ''
            self.infoPane.setText(self.tr("{0} is \n {1} {2} dB than \n {3}").format(snd1['label'], w, self.currLocale.toString(dbDiff), snd2['label']))
        elif len(ids) > 2:
            self.infoPane.setText(self.tr('Multiple Selection'))
        else:
            selectedSound = ids[0]
            dur = round(self.sndList[selectedSound]['duration'], 3)
            chan = self.sndList[selectedSound]['chan']
            fs = int(self.sndList[selectedSound]['fs'])
            if 'nBits' in self.sndList[selectedSound]:
                nb = self.currLocale.toString(int(self.sndList[selectedSound]['nBits']))
            else:
                nb = 'Undefined'
            nSamp = self.sndList[selectedSound]['nSamples']

            allInfo = self.tr("Duration: {0} sec.\n\nChannel: {1} \n\nSamp. Freq.: {2} \n\nBits: {3}" ).format(dur, chan, self.currLocale.toString(fs), nb) 
            self.infoPane.setText(allInfo)
            
    def findSelectedItemIds(self):
        selItems = self.sndTableWidget.selectedItems()
        selItemsRows = []
        for i in range(len(selItems)):
            selItemsRows.append(selItems[i].row())
        selItemsRows = unique(selItemsRows)
        selItemsIds = []
        for i in range(len(selItemsRows)):
            selItemsIds.append(str(self.sndTableWidget.item(selItemsRows[i], 2).text()))
        return selItemsIds
    def findSelectedItemRows(self):
        selItems = self.sndTableWidget.selectedItems()
        selItemsRows = []
        for i in range(len(selItems)):
            selItemsRows.append(selItems[i].row())
        selItemsRows = unique(selItemsRows)
        return selItemsRows
    def onCellDoubleClicked(self, row, col):
        if col == 0:
            self.onClickRenameButton()
        elif col == 1:
            self.onDoubleClickChannelCell()

    def onClickSaveButton(self):
        ids = self.findSelectedItemIds()
        sampRate = self.sndList[ids[0]]['fs']
        condition = True
        nSampList = []
        for i in range(len(ids)):
            selectedSound = ids[i]
            if self.sndList[selectedSound]['fs'] != sampRate:
                QtGui.QMessageBox.warning(self, self.tr('Warning'), self.tr('Cannot write sounds with different sample rates'))
                condition = False
                break
         
            nSampList.append(self.sndList[selectedSound]['nSamples'])
        if condition == True:
            snd = zeros((max(nSampList), 2))
            for i in range(len(ids)):
                selectedSound = ids[i]
                nSampDiff = max(nSampList) - len(self.sndList[selectedSound]['wave'])
                if self.sndList[selectedSound]['chan'] == self.tr('Right'):
                    snd[:,1] =  snd[:,1] + concatenate((self.sndList[selectedSound]['wave'], zeros(nSampDiff)), axis=0)
                elif self.sndList[selectedSound]['chan'] == self.tr('Left'):
                    snd[:,0] =  snd[:,0] + concatenate((self.sndList[selectedSound]['wave'], zeros(nSampDiff)), axis=0)

        #Apparently there's an inversion to do
        thisSnd = copy.copy(snd)
        snd[:,1] = thisSnd[:,0]
        snd[:,0] = thisSnd[:,1]
        #if 
       
        dialog = saveSoundDialog(self)
        if dialog.exec_():
            fs = sampRate
            if dialog.channelChooser.currentText() == self.tr('Mono'):
                wave = snd[:,0] + snd[:,1]
                nChannels = 1
            else:
                wave = snd
                nChannels = 2
            ftow = QtGui.QFileDialog.getSaveFileName(self, self.tr('Choose file to write'), self.tr('.{0}').format(dialog.suggestedExtension), self.tr('All Files (*)'))
            if len(ftow) > 0:
                if self.prm['pref']['wavmanager'] == 'scipy':
                    scipy_wavwrite(ftow, fs, int(dialog.encodingChooser.currentText()), wave)
                elif self.prm['pref']['wavmanager'] == 'audiolab':
                    ftow = str(ftow)
                    fAll = audiolab.Format("wav", pcm + str(dialog.encodingChooser.currentText()))
                    f = Sndfile(ftow, 'w', fAll, nChannels, fs)
                    f.write_frames(wave)
                    f.close()


    
    def onClickCloneButton(self):
        #self.sndTableWidget.setSortingEnabled(False)
        ids = self.findSelectedItemIds()
        for i in range(len(ids)):
            selectedSound = ids[i]
            thisSnd = copy.copy(self.sndList[selectedSound])
            thisSnd['label'] = self.sndList[selectedSound]['label'] + ' (copy)'
            condSat = 0
            while condSat == 0:
                tmp_id = random_id.random_id(5, 'alphanumeric')
                if tmp_id in self.sndList:
                    condSat = 0
                else:
                    condSat = 1
            self.sndList[tmp_id] = thisSnd
            currCount = len(self.sndList)
            self.sndTableWidget.setRowCount(currCount)
            newItem = QtGui.QTableWidgetItem(thisSnd['label'])
            #newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.sndTableWidget.setItem(currCount-1, 0, newItem)
            newItem = QtGui.QTableWidgetItem(thisSnd['chan'])
            #newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.sndTableWidget.setItem(currCount-1, 1, newItem)
            self.sndList[tmp_id]['qid'] = QtGui.QTableWidgetItem(tmp_id)
            self.sndTableWidget.setItem(currCount-1, 2, self.sndList[tmp_id]['qid'])
            #self.sndTableWidget.setSortingEnabled(True)
    def onClickPlotButton(self):
        ids = self.findSelectedItemIds()
        for i in range(len(ids)):
           selectedSound = ids[i]
           waveformPlot(self, self.sndList[selectedSound], self.prm)
    def onClickSpectrumButton(self):
       ids = self.findSelectedItemIds()
       for i in range(len(ids)):
           selectedSound = ids[i]
           spectrumPlot(self, self.sndList[selectedSound], self.prm)
    def onClickAutocorrelationButton(self):
       ids = self.findSelectedItemIds()
       for i in range(len(ids)):
           selectedSound = ids[i]
           acfPlot(self, self.sndList[selectedSound], self.prm)
    def onClickAutocorrelogramButton(self):
       ids = self.findSelectedItemIds()
       for i in range(len(ids)):
           selectedSound = ids[i]
           autocorrelogramPlot(self, self.sndList[selectedSound], self.prm)
    def onClickSpectrogramButton(self):
       ids = self.findSelectedItemIds()
       for i in range(len(ids)):
           selectedSound = ids[i]
           spectrogramPlot(self, self.sndList[selectedSound], self.prm)
    def onClickRenameButton(self):
        ids = self.findSelectedItemIds()
        if len(ids) > 1:
            QtGui.QMessageBox.warning(self, self.tr('Warning'), self.tr('Only one sound can be renamed at a time'))
        elif len(ids) < 1:
            pass
        else:
            selectedSound = ids[0]
            msg = self.tr('New name:')
            text, ok = QtGui.QInputDialog.getText(self, self.tr('Input Dialog'), msg)
            if ok:
                    self.sndTableWidget.item(self.sndList[selectedSound]['qid'].row(), 0).setText(text)
                    self.sndList[selectedSound]['label'] = text

    def onDoubleClickChannelCell(self):
        ids = self.findSelectedItemIds()
        if len(ids) > 1:
            QtGui.QMessageBox.warning(self, self.tr('Warning'), self.tr('Only sound can be changed at a time'))
        else:
            selectedSound = ids[0]
            multipleSelection = False
            currChan = self.sndList[selectedSound]['chan']
            dialog = changeChannelDialog(self, multipleSelection, currChan)
            if dialog.exec_():
                newChan = dialog.chooser.currentText()
                self.sndTableWidget.item(self.sndList[selectedSound]['qid'].row(), 1).setText(newChan)
                self.sndList[selectedSound]['chan'] = newChan

          
    def onClickLevelDiffButton(self):
        ids = self.findSelectedItemIds()
        if len(ids) == 1:
            pass
        elif len(ids) > 2:
            QtGui.QMessageBox.warning(self, self.tr('Level Difference'), self.tr('Only two sounds can be compared at a time'))
        else:
            snd1 = self.sndList[ids[0]]
            snd2 = self.sndList[ids[1]]
            rms1 = sndlib.getRms(snd1['wave'])
            rms2 = sndlib.getRms(snd2['wave'])
            dbDiff = 20*log10(rms1/rms2)
            if dbDiff >= 0:
                w = '+'
            elif dbDiff < 0:
                w = ''

            QtGui.QMessageBox.information(self, self.tr('Level Difference'), self.tr('{0} is {1} {2} dB than {3}').format(snd1['label'], w, self.currLocale.toString(dbDiff), snd2['label']))


    def onClickScaleButton(self):
        ids = self.findSelectedItemIds()
        val, ok = QtGui.QInputDialog.getDouble(self, self.tr('Scale Level'), self.tr('Add or subtract decibels'))
        if ok:
            for i in range(len(ids)):
                selectedSound = ids[i]
                self.sndList[selectedSound]['wave'] = sndlib.scale(val, self.sndList[selectedSound]['wave'])
       


    def onClickRemoveButton(self):
        ids = self.findSelectedItemIds()
        for i in range(len(ids)):
            selectedSound = ids[i]
            self.sndTableWidget.removeRow(self.sndList[selectedSound]['qid'].row())
            del self.sndList[selectedSound]

    def onClickRemoveAllButton(self):
        ks = list(self.sndList.keys())
        for i in range(len(ks)):
            self.sndTableWidget.removeRow(self.sndList[ks[i]]['qid'].row())
            del self.sndList[ks[i]]
 

    def onClickGetRMSButton(self):
        ids = self.findSelectedItemIds()
        rmsVals = []
        msg = self.tr('')
        for i in range(len(ids)):
            selectedSound = ids[i]
            rmsVals.append(sndlib.getRms(self.sndList[selectedSound]['wave']))
            msg = self.tr('{0} {1} : {2} \n').format(msg, self.sndList[selectedSound]['label'], self.currLocale.toString(rmsVals[i])) 
        QtGui.QMessageBox.information(self, self.tr('Root Mean Square'), msg)
      
        
       
    def onClickPlayButton(self):
        ids = self.findSelectedItemIds()
        sampRate = self.sndList[ids[0]]['fs']
        condition = True
        nSampList = []
        for i in range(len(ids)):
            selectedSound = ids[i]
            if self.sndList[selectedSound]['fs'] != sampRate:
                QtGui.QMessageBox.warning(self, self.tr('Warning'), self.tr('Cannot play sounds with different sample rates'))
                condition = False
                break
            nSampList.append(self.sndList[selectedSound]['nSamples'])
        if condition == True:
            snd = zeros((max(nSampList), 2))
            for i in range(len(ids)):
                selectedSound = ids[i]
                nSampDiff = max(nSampList) - len(self.sndList[selectedSound]['wave'])
                if self.sndList[selectedSound]['chan'] == self.tr('Right'):
                    snd[:,1] =  snd[:,1] + concatenate((self.sndList[selectedSound]['wave'], zeros(nSampDiff)), axis=0)
                elif self.sndList[selectedSound]['chan'] == self.tr('Left'):
                    snd[:,0] =  snd[:,0] + concatenate((self.sndList[selectedSound]['wave'], zeros(nSampDiff)), axis=0)

        
        wave = snd
        fs = sampRate
        nbits = self.prm['pref']['nBits']
        playCmd = str(self.prm['pref']['playCommand'])
        self.playSound(wave, fs, nbits, playCmd, False, 'temp')

    def playSound(self, snd, fs, nbits, playCmd, writewav, fname):
        playCmd = str(playCmd)
        enc = 'pcm'+ str(nbits)
        if writewav == True:
            fname = fname
        else:
            if platform.system() == 'Windows':
                fname = 'tmp_snd.wav'
            else:
                (hnl, fname) = mkstemp('tmp_snd.wav')
        if playCmd == 'audiolab':
            snd = transpose(snd)
            audiolab.play(snd, fs)
            if writewav == True:
                snd = transpose(snd)
                if self.prm["pref"]["wavmanager"] == "audiolab":
                    audiolab.wavwrite(snd, fname, fs = fs, enc = enc)
                elif self.prm["pref"]["wavmanager"] == "scipy":
                    scipy_wavwrite(fname, fs, nbits, snd)
        else:
            if self.prm["pref"]["wavmanager"] == "audiolab":
                audiolab.wavwrite(snd, fname, fs = fs, enc = enc)
            elif self.prm["pref"]["wavmanager"] == "scipy":
                scipy_wavwrite(fname, fs, nbits, snd)
            if playCmd == 'winsound':
                winsound.PlaySound(fname, winsound.SND_FILENAME)
            else:
                cmd = playCmd + ' ' + fname
                os.system(cmd)
            if writewav == False:
                os.remove(fname)
    
        return
            
    def onClickResampleButton(self):
        ids = self.findSelectedItemIds()
        if len(ids) < 1:
            pass
        else:
            if len(ids) == 1:
                multipleSelection = False
                currSampRate = self.sndList[ids[0]]['fs']
            elif len(ids) > 1:
                multipleSelection = True
                currSampRate = None

            dialog = resampleDialog(self, multipleSelection, currSampRate)
            if dialog.exec_():
                newSampRate = dialog.newSampRate
                resampMethod = str(dialog.convertorChooser.currentText())
                smoothWindow = str(dialog.winChooser.currentText())
                if smoothWindow == self.tr('none'):
                    smoothWindow = None
                for i in range(len(ids)):
                    selectedSound = ids[i]
                    self.sndList[selectedSound]['wave'] = scipy.signal.resample(self.sndList[selectedSound]['wave'], round(len(self.sndList[selectedSound]['wave'])*newSampRate/self.sndList[selectedSound]['fs']), window=smoothWindow) 
                    self.sndList[selectedSound]['fs'] = newSampRate
                    self.sndList[selectedSound]['nSamples'] = len(self.sndList[selectedSound]['wave'])
                    self.onSelectionChanged()

    def onClickConcatenateButton(self):
        ids = self.findSelectedItemIds()
        if len(ids) == 1:
            pass
        elif len(ids) > 2:
            QtGui.QMessageBox.warning(self, self.tr('Concatenate Sounds'), self.tr('Only two sounds can be concatenated at a time'))
        else:
            snd1 = self.sndList[ids[0]]
            snd2 = self.sndList[ids[1]]

            if snd1['fs'] != snd2['fs']:
                QtGui.QMessageBox.warning(self, self.tr('Concatenate Sounds'), self.tr('Cannot concatenate sounds with different sampling rates'))
            else:
                sampRate = snd1['fs']
                dialog = concatenateDialog(self, snd1, snd2)
                if dialog.exec_():
                     delay = self.currLocale.toDouble(dialog.delayWidget.text())[0]
                     delayType = str(dialog.delayTypeChooser.currentText())
                     thisSnd = {}
                     if dialog.order == 'given':
                         thisSnd['wave'] = concatenateSounds(snd1['wave'], snd2['wave'], delay, delayType, sampRate)
                     else:
                         thisSnd['wave'] = concatenateSounds(snd2['wave'], snd1['wave'], delay, delayType, sampRate)

                     thisSnd['label'] = str(dialog.outNameWidget.text())#snd1['label'] + '-' + snd2['label']
                     thisSnd['chan'] = str(dialog.outChanChooser.currentText())
                     thisSnd['nSamples'] = len(thisSnd['wave'])
                     thisSnd['fs'] = sampRate
                     thisSnd['duration'] = thisSnd['nSamples'] / thisSnd['fs']
                     thisSnd['nBits'] = 0
                     thisSnd['format'] = ''
                     condSat = 0
                     while condSat == 0:
                         tmp_id = random_id.random_id(5, 'alphanumeric')
                         if tmp_id in self.sndList:
                             condSat = 0
                         else:
                             condSat = 1
                     self.sndList[tmp_id] = thisSnd
                     currCount = len(self.sndList)
                     self.sndTableWidget.setRowCount(currCount)
                     newItem = QtGui.QTableWidgetItem(thisSnd['label'])
                     
                     self.sndTableWidget.setItem(currCount-1, 0, newItem)
                     newItem = QtGui.QTableWidgetItem(thisSnd['chan'])
                     
                     self.sndTableWidget.setItem(currCount-1, 1, newItem)
                     self.sndList[tmp_id]['qid'] = QtGui.QTableWidgetItem(tmp_id)
                     self.sndTableWidget.setItem(currCount-1, 2, self.sndList[tmp_id]['qid'])
                     

    def onClickCutButton(self):
        ids = self.findSelectedItemIds()

        for i in range(len(ids)):
            snd = self.sndList[ids[i]]
            fs = snd["fs"]
            nSamples = snd["wave"].shape[0]
            dialog = cutDialog(self, snd)
            if dialog.exec_():
                startCut = self.currLocale.toDouble(dialog.fromWidget.text())[0]
                endCut = self.currLocale.toDouble(dialog.toWidget.text())[0]
                cutUnit = str(dialog.unitChooser.currentText())
                if cutUnit == "Seconds":
                    startCut = int(round(startCut*fs))
                    endCut = int(round(endCut*fs))
                elif cutUnit == "Milliseconds":
                    startCut = int(round(startCut/1000*fs))
                    endCut = int(round(endCut/1000*fs))

                if startCut < 0 or endCut > nSamples:
                    QtGui.QMessageBox.warning(self, self.tr('Cut Sound'), self.tr('Values out of range'))
                elif startCut == 0 and endCut == nSamples:
                    QtGui.QMessageBox.warning(self, self.tr('Cut Sound'), self.tr('Cannot cut entire sound, please use remove button'))
                else:
                    snd["wave"] = cutSampleRegion(snd["wave"], startCut, endCut)
                    snd['nSamples'] = len(snd['wave'])
                    snd['duration'] = snd['nSamples'] / snd['fs']
                    self.onSelectionChanged()

    def onClickApplyFIR2PresetsButton(self):
        ids = self.findSelectedItemIds()
        if len(ids) < 1:
            pass
        else:
            dialog = applyFIR2PresetsDialog(self)
            if dialog.exec_():
                if dialog.currFilterType == self.tr('lowpass'):
                    cutoff = self.currLocale.toDouble(dialog.cutoffWidget.text())[0]
                    highStop = self.currLocale.toDouble(dialog.endCutoffWidget.text())[0]
                    for i in range(len(ids)):
                        selectedSound = ids[i]
                        filterOrder = self.currLocale.toInt(dialog.filterOrderWidget.text())[0]
                        self.sndList[selectedSound]['wave'] = fir2FiltAlt(0, 0, cutoff, cutoff*highStop, 'lowpass', self.sndList[selectedSound]['wave'], self.sndList[selectedSound]['fs'], filterOrder)
                elif dialog.currFilterType == self.tr('highpass'):
                    cutoff = self.currLocale.toDouble(dialog.cutoffWidget.text())[0]
                    lowStop = self.currLocale.toDouble(dialog.startCutoffWidget.text())[0]
                    for i in range(len(ids)):
                        selectedSound = ids[i]
                        filterOrder = self.currLocale.toInt(dialog.filterOrderWidget.text())[0]
                        self.sndList[selectedSound]['wave'] = fir2FiltAlt(cutoff*lowStop, cutoff, 0, 0, 'highpass', self.sndList[selectedSound]['wave'], self.sndList[selectedSound]['fs'], filterOrder)
                elif dialog.currFilterType == self.tr('bandpass'):
                    lowerCutoff = self.currLocale.toDouble(dialog.lowerCutoffWidget.text())[0]
                    lowStop = self.currLocale.toDouble(dialog.startCutoffWidget.text())[0]
                    higherCutoff = self.currLocale.toDouble(dialog.higherCutoffWidget.text())[0]
                    highStop = self.currLocale.toDouble(dialog.endCutoffWidget.text())[0]
                    for i in range(len(ids)):
                        selectedSound = ids[i]
                        filterOrder = self.currLocale.toInt(dialog.filterOrderWidget.text())[0]
                        self.sndList[selectedSound]['wave'] = fir2FiltAlt(lowerCutoff*lowStop, lowerCutoff, higherCutoff, higherCutoff*highStop, 'bandpass', self.sndList[selectedSound]['wave'], self.sndList[selectedSound]['fs'], filterOrder)
                elif dialog.currFilterType == self.tr('bandstop'):
                    lowerCutoff = self.currLocale.toDouble(dialog.lowerCutoffWidget.text())[0]
                    highStop = self.currLocale.toDouble(dialog.endCutoffWidget.text())[0]
                    higherCutoff = self.currLocale.toDouble(dialog.higherCutoffWidget.text())[0]
                    lowStop = self.currLocale.toDouble(dialog.startCutoffWidget.text())[0]
                    for i in range(len(ids)):
                        selectedSound = ids[i]
                        filterOrder = self.currLocale.toInt(dialog.filterOrderWidget.text())[0]
                        self.sndList[selectedSound]['wave'] = fir2FiltAlt(lowerCutoff, lowerCutoff*highStop, higherCutoff*lowStop, higherCutoff, 'bandstop', self.sndList[selectedSound]['wave'], self.sndList[selectedSound]['fs'], filterOrder)

    def onClickGenerateNoise(self):
        dialog = generateNoiseDialog(self)
        if dialog.exec_():
            label = dialog.noiseLabelWidget.text()
            duration = self.currLocale.toDouble(dialog.noiseDurationWidget.text())[0]
            ramps = self.currLocale.toDouble(dialog.noiseRampsWidget.text())[0]
            spectrumLevel = self.currLocale.toDouble(dialog.noiseLevelWidget.text())[0]
            fs = self.currLocale.toInt(dialog.sampRateWidget.text())[0]
            ear = dialog.noiseEarChooser.currentText()
            if ear == self.tr('Right'):
                ear = 'Right'
            elif ear == self.tr('Left'):
                ear = 'Left'
            elif ear == self.tr('Both'):
                ear = 'Both'
            if dialog.currNoiseType == self.tr('white'):
                thisNoise = sndlib.broadbandNoise(spectrumLevel, duration, ramps, ear, fs, self.prm['pref']['maxLevel'])
            elif dialog.currNoiseType == self.tr('pink'):
                refHz = self.currLocale.toDouble(dialog.reWidget.text())[0]
                thisNoise = sndlib.broadbandNoise(spectrumLevel, duration, ramps, ear, fs, self.prm['pref']['maxLevel'])
                thisNoise = sndlib.makePinkRef(thisNoise, fs, refHz)

            if ear == 'Right' or ear == 'Left':
                thisSnd = {}
                if ear == 'Right':
                    thisSnd['wave'] = thisNoise[:,1]
                elif ear == 'Left':
                    thisSnd['wave'] = thisNoise[:,0]
                thisSnd['fs'] = fs
                thisSnd['nBits'] = 0
                thisSnd['chan'] = dialog.noiseEarChooser.currentText()
                thisSnd['nSamples'] = len(thisSnd['wave'])
                thisSnd['duration'] = thisSnd['nSamples'] / float(thisSnd['fs'])
                thisSnd['label'] = label
                condSat = 0
                while condSat == 0:
                    tmp_id = random_id.random_id(5, 'alphanumeric')
                    if tmp_id in self.sndList:
                        condSat = 0
                    else:
                        condSat = 1
                self.sndList[tmp_id] = copy.copy(thisSnd)
                currCount = len(self.sndList)
                self.sndTableWidget.setRowCount(currCount)
                newItem = QtGui.QTableWidgetItem(thisSnd['label'])
                newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.sndTableWidget.setItem(currCount-1, 0, newItem)
                newItem = QtGui.QTableWidgetItem(thisSnd['chan'])
                newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.sndTableWidget.setItem(currCount-1, 1, newItem)
                self.sndList[tmp_id]['qid'] = QtGui.QTableWidgetItem(tmp_id)
                self.sndTableWidget.setItem(currCount-1, 2, self.sndList[tmp_id]['qid'])

            if ear == 'Both':
                for i in range(2):
                    thisSnd = {}
                    if i == 1:
                        thisSnd['wave'] = thisNoise[:,1]
                        thisSnd['chan'] = self.tr('Right')
                    else:
                        thisSnd['wave'] = thisNoise[:,0]
                        thisSnd['chan'] = self.tr('Left')
                    thisSnd['fs'] = fs
                    thisSnd['nBits'] = 0
                    thisSnd['nSamples'] = len(thisSnd['wave'])
                    thisSnd['duration'] = thisSnd['nSamples'] / float(thisSnd['fs'])
                    thisSnd['label'] = label
                    condSat = 0
                    while condSat == 0:
                        tmp_id = random_id.random_id(5, 'alphanumeric')
                        if tmp_id in self.sndList:
                            condSat = 0
                        else:
                            condSat = 1
                    self.sndList[tmp_id] = copy.copy(thisSnd)
                    currCount = len(self.sndList)
                    self.sndTableWidget.setRowCount(currCount)
                    newItem = QtGui.QTableWidgetItem(thisSnd['label'])
                    newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                    self.sndTableWidget.setItem(currCount-1, 0, newItem)
                    newItem = QtGui.QTableWidgetItem(thisSnd['chan'])
                    newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                    self.sndTableWidget.setItem(currCount-1, 1, newItem)
                    self.sndList[tmp_id]['qid'] = QtGui.QTableWidgetItem(tmp_id)
                    self.sndTableWidget.setItem(currCount-1, 2, self.sndList[tmp_id]['qid'])
           
    def onClickGenerateSinusoid(self):
        dialog = generateSinusoidDialog(self)
        if dialog.exec_():
            label = dialog.soundLabelWidget.text()
            freq = self.currLocale.toDouble(dialog.soundFrequencyWidget.text())[0]
            phase = self.currLocale.toDouble(dialog.soundPhaseWidget.text())[0]
            duration = self.currLocale.toDouble(dialog.soundDurationWidget.text())[0]
            ramps = self.currLocale.toDouble(dialog.soundRampsWidget.text())[0]
            level = self.currLocale.toDouble(dialog.soundLevelWidget.text())[0]
            fs = self.currLocale.toInt(dialog.sampRateWidget.text())[0]
            ear = dialog.soundEarChooser.currentText()
            if ear == self.tr('Right'):
                ear = 'Right'
            elif ear == self.tr('Left'):
                ear = 'Left'
            elif ear == self.tr('Both'):
                ear = 'Both'

            if ear == 'Both':
                itd = self.currLocale.toDouble(dialog.itdWidget.text())[0]
                itdRef = dialog.itdRefChooser.currentText()
                ild = self.currLocale.toDouble(dialog.ildWidget.text())[0]
                ildRef = dialog.ildRefChooser.currentText()
            else:
                itd = 0
                itdRef = None
                ild = 0
                ildRef = None
          
            thisSound = sndlib.binauralPureTone(freq, phase, level, duration, ramps, ear, itd, itdRef, ild, ildRef, fs, self.prm['pref']['maxLevel'])
          

            if ear == 'Right' or ear == 'Left':
                thisSnd = {}
                if ear == 'Right':
                    thisSnd['wave'] = thisSound[:,1]
                elif ear == 'Left':
                    thisSnd['wave'] = thisSound[:,0]
                thisSnd['fs'] = fs
                #thisSnd['nBits'] = 0
                thisSnd['chan'] = dialog.soundEarChooser.currentText()
                thisSnd['nSamples'] = len(thisSnd['wave'])
                thisSnd['duration'] = thisSnd['nSamples'] / thisSnd['fs']
                thisSnd['label'] = label
                condSat = 0
                while condSat == 0:
                    tmp_id = random_id.random_id(5, 'alphanumeric')
                    if tmp_id in self.sndList:
                        condSat = 0
                    else:
                        condSat = 1
                self.sndList[tmp_id] = copy.copy(thisSnd)
                currCount = len(self.sndList)
                self.sndTableWidget.setRowCount(currCount)
                newItem = QtGui.QTableWidgetItem(thisSnd['label'])
                newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.sndTableWidget.setItem(currCount-1, 0, newItem)
                newItem = QtGui.QTableWidgetItem(thisSnd['chan'])
                newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.sndTableWidget.setItem(currCount-1, 1, newItem)
                self.sndList[tmp_id]['qid'] = QtGui.QTableWidgetItem(tmp_id)
                self.sndTableWidget.setItem(currCount-1, 2, self.sndList[tmp_id]['qid'])

            if ear == 'Both':
                for i in range(2):
                    thisSnd = {}
                    if i == 0:
                        thisSnd['wave'] = thisSound[:,1]
                        thisSnd['chan'] = self.tr('Right')
                    else:
                        thisSnd['wave'] = thisSound[:,0]
                        thisSnd['chan'] = self.tr('Left')
                    thisSnd['fs'] = fs
                    thisSnd['nSamples'] = len(thisSnd['wave'])
                    thisSnd['duration'] = thisSnd['nSamples'] / thisSnd['fs']
                    thisSnd['label'] = label
                    condSat = 0
                    while condSat == 0:
                        tmp_id = random_id.random_id(5, 'alphanumeric')
                        if tmp_id in self.sndList:
                            condSat = 0
                        else:
                            condSat = 1
                    self.sndList[tmp_id] = copy.copy(thisSnd)
                    currCount = len(self.sndList)
                    self.sndTableWidget.setRowCount(currCount)
                    newItem = QtGui.QTableWidgetItem(thisSnd['label'])
                    newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                    self.sndTableWidget.setItem(currCount-1, 0, newItem)
                    newItem = QtGui.QTableWidgetItem(thisSnd['chan'])
                    newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                    self.sndTableWidget.setItem(currCount-1, 1, newItem)
                    self.sndList[tmp_id]['qid'] = QtGui.QTableWidgetItem(tmp_id)
                    self.sndTableWidget.setItem(currCount-1, 2, self.sndList[tmp_id]['qid'])

    def onClickGenerateHarmCompl(self):
        dialog = generateSoundDialog(self, "Harmonic Complex")
        if dialog.exec_():

            for i in range(dialog.sndPrm['nFields']):
                dialog.sndPrm['field'][i] = self.currLocale.toDouble(dialog.field[i].text())[0]
            for i in range(dialog.sndPrm['nChoosers']):
                dialog.sndPrm['chooser'][i] = dialog.chooser[i].currentText()
            
            label = dialog.soundLabelWidget.text()
            fs = self.currLocale.toInt(dialog.sampRateWidget.text())[0]
            F0                  = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("F0 (Hz)"))]
            bandwidth           = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("Bandwidth (Hz)"))]
            bandwidthCents      = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("Bandwidth (Cents)"))]
            spacingCents        = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("Spacing (Cents)"))]
            itd                 = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("ITD (micro s)"))]
            ipd                 = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("IPD (radians)"))]
            narrowbandCmpLevel  = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("Narrow Band Component Level (dB SPL)"))]
            iterations          = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("Iterations"))]
            gain                = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("Gain"))]
            lowHarm             = int(dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("Low Harmonic"))])
            highHarm            = int(dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("High Harmonic"))])
            lowFreq             = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("Low Freq. (Hz)"))]
            highFreq            = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("High Freq. (Hz)"))]
            lowStopComplex      = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("Low Stop"))]
            highStopComplex     = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("High Stop"))]
            harmonicLevel       = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("Harmonic Level (dB SPL)"))]
            spectrumLevel       = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("Spectrum Level (dB SPL)"))]
            componentLevel      = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("Component Level (dB SPL)"))]
            duration            = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("Duration (ms)"))]
            ramp                = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("Ramp (ms)"))]
            noise1LowFreq       = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("No. 1 Low Freq. (Hz)"))]
            noise1HighFreq      = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("No. 1 High Freq. (Hz)"))]
            noise1SpectrumLevel = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("No. 1 S. Level (dB SPL)"))]
            noise2LowFreq       = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("No. 2 Low Freq. (Hz)"))]
            noise2HighFreq      = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("No. 2 High Freq. (Hz)"))]
            noise2SpectrumLevel = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("No. 2 S. Level (dB SPL)"))]
            stretch             = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("Stretch (%)"))]
            harmSpacing         = dialog.sndPrm['field'][dialog.sndPrm['fieldLabel'].index(dialog.tr("Harmonic Spacing (Cents)"))]
            
            channel           = dialog.sndPrm['chooser'][dialog.sndPrm['chooserLabel'].index(dialog.tr("Ear:"))]
            harmType          = dialog.sndPrm['chooser'][dialog.sndPrm['chooserLabel'].index(dialog.tr("Type:"))]
            harmPhase         = dialog.sndPrm['chooser'][dialog.sndPrm['chooserLabel'].index(dialog.tr("Phase:"))]
            noiseType         = dialog.sndPrm['chooser'][dialog.sndPrm['chooserLabel'].index(dialog.tr("Noise Type:"))]
            irnConfiguration  = dialog.sndPrm['chooser'][dialog.sndPrm['chooserLabel'].index(dialog.tr("IRN Type:"))]
            hugginsPhaseRel   = dialog.sndPrm['chooser'][dialog.sndPrm['chooserLabel'].index(dialog.tr("Phase relationship:"))]
            dichoticDifference= dialog.sndPrm['chooser'][dialog.sndPrm['chooserLabel'].index(dialog.tr("Dichotic Difference:"))]
            harmonicity       = dialog.sndPrm['chooser'][dialog.sndPrm['chooserLabel'].index(dialog.tr("Harmonicity:"))]

            lowStop = 0.8
            highStop = 1.2

            if harmType == self.tr("Sinusoid"):
                self.stimulusCorrect = sndlib.complexTone(F0, harmPhase, lowHarm, highHarm, stretch, harmonicLevel, duration, ramp, channel, fs, self.prm['pref']['maxLevel'])
            elif harmType == self.tr("Narrowband Noise"):
                self.stimulusCorrect = sndlib.harmComplFromNarrowbandNoise(F0, lowHarm, highHarm, spectrumLevel, bandwidth, duration, ramp, channel, fs, self.prm['pref']['maxLevel'])
            elif harmType == self.tr("IRN"):
                delay = 1/float(F0)
                self.stimulusCorrect = sndlib.makeIRN(delay, gain, iterations, irnConfiguration, spectrumLevel, duration, ramp, channel, fs, self.prm['pref']['maxLevel'])
            elif harmType == self.tr("Huggins Pitch"):
                self.stimulusCorrect = sndlib.makeHuggins(F0, lowHarm, highHarm, spectrumLevel, bandwidth, hugginsPhaseRel, "White", duration, ramp, fs, self.prm['pref']['maxLevel'])
                channel = self.tr("Both")
            elif harmType == self.tr("Simple Dichotic"):
                self.stimulusCorrect = sndlib.makeSimpleDichotic(F0, lowHarm, highHarm, componentLevel, lowFreq, highFreq,
                                                            spacingCents, bandwidthCents, hugginsPhaseRel, dichoticDifference,
                                                            itd, ipd, 0, duration, ramp, fs, self.prm['pref']['maxLevel'])
                channel = self.tr("Both")
            elif harmType == self.tr("Narrowband Noise 2"):
                self.stimulusCorrect = sndlib.makeSimpleDichotic(F0, lowHarm, highHarm, componentLevel, lowFreq, highFreq,
                                                            spacingCents, bandwidthCents, hugginsPhaseRel, "Level",
                                                            0, 0, narrowbandCmpLevel, duration, ramp, fs, self.prm['pref']['maxLevel'])
                channel = self.tr("Both")
        
            if harmType != self.tr("Simple Dichotic") and harmType != self.tr("Narrowband Noise 2"):
                self.stimulusCorrect = sndlib.fir2Filt(lowFreq*lowStopComplex, lowFreq, highFreq, highFreq*highStopComplex, self.stimulusCorrect, fs)
        
            if noiseType != self.tr("None"):
                if channel == self.tr("Odd Left") or channel == self.tr("Odd Right"): #alternating harmonics, different noise to the two ears
                    noiseR = sndlib.broadbandNoise(noise1SpectrumLevel, duration + ramp*6, 0, self.tr("Right"), fs, self.prm['pref']['maxLevel'])
                    noiseL = sndlib.broadbandNoise(noise1SpectrumLevel, duration + ramp*6, 0, self.tr("Left"), fs, self.prm['pref']['maxLevel'])
                    noise = noiseR + noiseL
                else:
                    noise = sndlib.broadbandNoise(noise1SpectrumLevel, duration + ramp*6, 0, channel, fs, self.prm['pref']['maxLevel'])
                if noiseType == self.tr("Pink"):
                    noise = sndlib.makePink(noise, self.prm)
                noise1 = sndlib.fir2Filt(noise1LowFreq*lowStop, noise1LowFreq, noise1HighFreq, noise1HighFreq*highStop, noise, fs)
                noise2 = sndlib.scale(noise2SpectrumLevel - noise1SpectrumLevel, noise)
                noise2 = sndlib.fir2Filt(noise2LowFreq*lowStop, noise2LowFreq, noise2HighFreq, noise2HighFreq*highStop, noise2, fs)
                noise = noise1 + noise2
                noise = noise[0:self.stimulusCorrect.shape[0],]
                noise = sndlib.gate(ramp, noise, fs)
                self.stimulusCorrect = self.stimulusCorrect + noise 
          
            thisSound = self.stimulusCorrect

            if channel in ['Right', 'Left']:
                thisSnd = {}
                if channel == 'Right':
                    thisSnd['wave'] = thisSound[:,1]
                elif channel == 'Left':
                    thisSnd['wave'] = thisSound[:,0]
                thisSnd['fs'] = fs
                #thisSnd['nBits'] = 0
                thisSnd['chan'] = channel
                thisSnd['nSamples'] = len(thisSnd['wave'])
                thisSnd['duration'] = thisSnd['nSamples'] / thisSnd['fs']
                thisSnd['label'] = label
                condSat = 0
                while condSat == 0:
                    tmp_id = random_id.random_id(5, 'alphanumeric')
                    if tmp_id in self.sndList:
                        condSat = 0
                    else:
                        condSat = 1
                self.sndList[tmp_id] = copy.copy(thisSnd)
                currCount = len(self.sndList)
                self.sndTableWidget.setRowCount(currCount)
                newItem = QtGui.QTableWidgetItem(thisSnd['label'])
                newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.sndTableWidget.setItem(currCount-1, 0, newItem)
                newItem = QtGui.QTableWidgetItem(thisSnd['chan'])
                newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.sndTableWidget.setItem(currCount-1, 1, newItem)
                self.sndList[tmp_id]['qid'] = QtGui.QTableWidgetItem(tmp_id)
                self.sndTableWidget.setItem(currCount-1, 2, self.sndList[tmp_id]['qid'])

            if channel in ['Both', 'Odd Right', 'Odd Left']:
                for i in range(2):
                    thisSnd = {}
                    if i == 0:
                        thisSnd['wave'] = thisSound[:,1]
                        thisSnd['chan'] = self.tr('Right')
                    else:
                        thisSnd['wave'] = thisSound[:,0]
                        thisSnd['chan'] = self.tr('Left')
                    thisSnd['fs'] = fs
                    thisSnd['nSamples'] = len(thisSnd['wave'])
                    thisSnd['duration'] = thisSnd['nSamples'] / thisSnd['fs']
                    thisSnd['label'] = label
                    condSat = 0
                    while condSat == 0:
                        tmp_id = random_id.random_id(5, 'alphanumeric')
                        if tmp_id in self.sndList:
                            condSat = 0
                        else:
                            condSat = 1
                    self.sndList[tmp_id] = copy.copy(thisSnd)
                    currCount = len(self.sndList)
                    self.sndTableWidget.setRowCount(currCount)
                    newItem = QtGui.QTableWidgetItem(thisSnd['label'])
                    newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                    self.sndTableWidget.setItem(currCount-1, 0, newItem)
                    newItem = QtGui.QTableWidgetItem(thisSnd['chan'])
                    newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                    self.sndTableWidget.setItem(currCount-1, 1, newItem)
                    self.sndList[tmp_id]['qid'] = QtGui.QTableWidgetItem(tmp_id)
                    self.sndTableWidget.setItem(currCount-1, 2, self.sndList[tmp_id]['qid'])
           
 
    def onAbout(self):
        QtGui.QMessageBox.about(self, self.tr("About pysoundanalyser"),
                                self.tr("""<b>Python Sound Analyser</b> <br>
                                - version: {0}; <br>
                                - revno: {1}; <br>
                                - build date: {2} <br>
                                <p> Copyright &copy; 2010-2012 Samuele Carcagno. <a href="mailto:sam.carcagno@gmail.com">sam.carcagno@gmail.com</a> 
                                All rights reserved. <p>
                This program is free software: you can redistribute it and/or modify
                it under the terms of the GNU General Public License as published by
                the Free Software Foundation, either version 3 of the License, or
                (at your option) any later version.
                <p>
                This program is distributed in the hope that it will be useful,
                but WITHOUT ANY WARRANTY; without even the implied warranty of
                MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
                GNU General Public License for more details.
                <p>
                You should have received a copy of the GNU General Public License
                along with this program.  If not, see <a href="http://www.gnu.org/licenses/">http://www.gnu.org/licenses/</a>
                <p>Python {3} - Qt {4} - PyQt {5} on {6}""").format(__version__, self.prm['revno'], self.prm['builddate'], platform.python_version(), QtCore.QT_VERSION_STR, QtCore.PYQT_VERSION_STR, platform.system()))
    



def main(argv):
    prm = {}
    prm['data'] = {}
    #prm['data'] = {}; prm['prefs'] = {}
    # create the GUI application
    qApp = QtGui.QApplication(sys.argv)
    sys.excepthook = excepthook
    #first read the locale settings
    locale = QtCore.QLocale().system().name() #returns a string such as en_US
    qtTranslator = QtCore.QTranslator()
    if qtTranslator.load("qt_" + locale, ":/translations/"):
        qApp.installTranslator(qtTranslator)
    appTranslator = QtCore.QTranslator()
    if appTranslator.load("pysoundanalyser_" + locale, ":/translations/"):
        qApp.installTranslator(appTranslator)
    prm['data']['currentLocale'] = QtCore.QLocale(locale)
    QtCore.QLocale.setDefault(prm['data']['currentLocale'])
    
    rootDirectory = os.path.abspath(os.path.dirname(sys.argv[0]))
    prm['rootDirectory'] = rootDirectory
    
    prm = get_prefs(prm)
    prm = global_parameters(prm)
    
    #then load the preferred language
    if prm['pref']['country'] != "System Settings":
        locale =  prm['pref']['language']  + '_' + prm['pref']['country']#returns a string such as en_US
        qtTranslator = QtCore.QTranslator()
        if qtTranslator.load("qt_" + locale, ":/translations/"):
            qApp.installTranslator(qtTranslator)
        appTranslator = QtCore.QTranslator()
        if appTranslator.load("pysoundanalyser_" + locale, ":/translations/") or locale == "en_US":
            qApp.installTranslator(appTranslator)
            prm['data']['currentLocale'] = QtCore.QLocale(locale)
            QtCore.QLocale.setDefault(prm['data']['currentLocale'])
            prm['data']['currentLocale'].setNumberOptions(prm['data']['currentLocale'].OmitGroupSeparator | prm['data']['currentLocale'].RejectGroupSeparator)

    
    qApp.setWindowIcon(QtGui.QIcon(":/johnny_automatic_crashing_wave.svg"))
    ## Look and feel changed to CleanLooks
    #QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("QtCurve"))
    QtGui.QApplication.setPalette(QtGui.QApplication.style().standardPalette())
    #qApp.currentLocale = locale
    # instantiate the ApplicationWindow widget
    qApp.setApplicationName('pysoundanalyser')
    aw = applicationWindow(prm)


    # show the widget
    aw.show()
    # start the Qt main loop execution, exiting from this script
    # with the same return code of Qt application
    sys.exit(qApp.exec_())
if __name__ == "__main__":
    main(sys.argv[1:])
   
