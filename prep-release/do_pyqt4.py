#! /usr/bin/env python
# -*- coding: utf-8 -*- 

import copy, os

thisDir = os.getcwd()
#read the current pyqt version
f = open('../pysoundanalyser/pyqtver.py', 'r')
pyqtverLines = f.readlines()
pyqtverLinesPyQt4 = copy.copy(pyqtverLines)
f.close()
for i in range(len(pyqtverLinesPyQt4)):
    if pyqtverLinesPyQt4[i].strip().split('=')[0].strip() == "pyqtversion":
           pyqtverLinesPyQt4[i] = "pyqtversion = 4\n"

#Change pyqtver to PyQt4
f = open('../pysoundanalyser/pyqtver.py', 'w')
f.writelines(pyqtverLinesPyQt4)
f.close()

os.system('pyrcc4 -py3 -o ../pysoundanalyser/qrc_resources.py ../resources.qrc')
os.system('pylupdate4 -verbose pysoundanalyser.pro')
os.system('lrelease -verbose pysoundanalyser.pro')
os.system('mv *.qm ../translations/')

os.chdir('../')
os.system('python3 setup-pyqt4.py sdist --formats=gztar,zip')
os.system('python3 setup-pyqt4.py bdist_wininst')

#revert to pyqt5
for i in range(len(pyqtverLines)):
    if pyqtverLines[i].strip().split('=')[0].strip() == "pyqtversion":
           pyqtverLines[i] = "pyqtversion = 5\n"
os.chdir('prep-release')
f = open('../pysoundanalyser/pyqtver.py', 'w')
f.writelines(pyqtverLines)
f.close()

os.system('pyrcc5 -py3 -o ../pysoundanalyser/qrc_resources.py ../resources.qrc')
os.system('pylupdate5 -verbose pysoundanalyser.pro')
os.system('lrelease -verbose pysoundanalyser.pro')
os.system('mv *.qm ../translations/')
