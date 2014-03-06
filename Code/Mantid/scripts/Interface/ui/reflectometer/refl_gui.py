#This is an extension of refl_gui.py as that is a auto-generated script form pyqt and shouldn't be edited
#so this file provides any extra GUI tweaks not easily doable in the designer
#for the time being this also includes non-GUI behaviour
import refl_window
import refl_save
import refl_choose_col
import csv
from PyQt4 import QtCore, QtGui
from mantid.simpleapi import *
from isis_reflectometry.quick import *
from isis_reflectometry import load_live_runs
from isis_reflectometry.combineMulti import *
from latest_isis_runs import *
from mantid.api import Workspace, WorkspaceGroup

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

canMantidPlot = True

try:
    from mantidplot import *
except ImportError:
    canMantidPlot = False

class ReflGui(refl_window.Ui_windowRefl):
    __instrumentRuns = None

    def __del__(self):
        if self.windowRefl.modFlag:
            self.save(true)
    def on_buttonAuto_clicked(self):
        self.autoFill()
    def on_buttonTransfer_clicked(self):
        self.transfer()
    def on_checkTickAll_stateChanged(self,state):
        self.unTickAll(state)
    def on_textRB_editingFinished(self):
        self.populateList()
    def on_buttonClear_clicked(self):
        self.initTable()
    def on_buttonProcess_clicked(self):
        self.process()
    def on_comboInstrument_activated(self, instrument):
        config['default.instrument'] = self.instrument_list[instrument]
        print "Instrument is now: ", config['default.instrument']
        self.textRB.clear()
        self.populateList()
        self.current_instrument = self.instrument_list[instrument]
        self.comboPolarCorrect.setEnabled(self.current_instrument  in self.polarisation_instruments) # Enable as appropriate
        self.comboPolarCorrect.setCurrentIndex(self.comboPolarCorrect.findText('None')) # Reset to None
    def on_actionOpen_Table_triggered(self):
        self.loadTable()
    def on_actionReload_from_Disk_triggered(self):
        self.reloadTable()
    def on_actionSave_triggered(self):
        self.save()
    def on_actionSave_As_triggered(self):
        self.saveAs()
    def on_actionSave_Workspaces_triggered(self):
        self.saveWorkspaces()
    def actionClose_Refl_Gui_triggered(self):
        self.showHelp()
    def on_actionMantid_Help_triggered(self):
        self.showHelp()
    def on_tableMain_modified(self):
        if not self.loading:
            self.windowRefl.modFlag = True
    def actionCopy_triggered(self):
        self.copy_cells()
    def actionCut_triggered(self):
        self.copy_cells()
        self.clear_cells()
    def actionPaste_triggered(self):
        self.paste_cells()
    def actionClear_triggered(self):
        self.clear_cells()
    def actionChoose_Columns_triggered(self):
        self.chooseColumns()
    '''
    Event handler for polarisation correction selection.
    '''
    def on_comboPolarCorr_activated(self):
        if self.current_instrument in self.polarisation_instruments:
            chosen_method = self.comboPolarCorrect.currentText()
            self.current_polarisation_method = self.polarisation_options[chosen_method]
        else:
            logger.notice("Polarisation correction is not supported on " + self.current_instrument)
        
    #Further UI setup
    def setupUi(self, windowRefl):
        super(ReflGui,self).setupUi(windowRefl)
        self.shownCols = {}
        self.loading = False
        self.clip = QtGui.QApplication.clipboard()
        '''
        Setup instrument options with defaults assigned.
        '''
        self.instrument_list = ['INTER', 'SURF', 'CRISP', 'POLREF']
        self.polarisation_instruments = ['CRISP', 'POLREF'] 
        self.comboInstrument.addItems(self.instrument_list)
        current_instrument = config['default.instrument'].upper()
        if current_instrument in self.instrument_list:
            self.comboInstrument.setCurrentIndex(self.instrument_list.index(current_instrument))
        else:
            self.comboInstrument.setCurrentIndex(0)
            config['default.instrument'] = 'INTER'
        self.current_instrument = config['default.instrument']
        
        '''
        Setup polarisation options with default assigned
        '''
        self.polarisation_options = {'None' : PolarisationCorrection.NONE, '1-PNR' : PolarisationCorrection.PNR, '2-PA' : PolarisationCorrection.PA }
        self.comboPolarCorrect.clear()
        self.comboPolarCorrect.addItems(self.polarisation_options.keys())
        self.comboPolarCorrect.setCurrentIndex(self.comboPolarCorrect.findText('None'))
        self.current_polarisation_method = self.polarisation_options['None']
        self.comboPolarCorrect.setEnabled(self.current_instrument in self.polarisation_instruments)
        
        self.labelStatus = QtGui.QLabel("Ready")
        self.statusMain.addWidget(self.labelStatus)
        self.initTable()
        self.populateList()
        self.windowRefl = windowRefl
        self.connectSlots()
        
    def initTable(self):

        self.currentTable = None
        self.accMethod = None

        self.tableMain.resizeColumnsToContents()
        settings = QtCore.QSettings()
        settings.beginGroup("Mantid/ISISReflGui/Columns")
        for column in range(self.tableMain.columnCount()):
            for row in range(self.tableMain.rowCount()):
                if (column == 0) or (column == 5) or (column == 10):
                    item = QtGui.QTableWidgetItem()
                    item.setText('')
                    item.setToolTip('Runs can be colon delimited to coadd them')
                    self.tableMain.setItem(row, column, item)
                elif (column == 1) or (column == 6) or (column == 11):
                    item = QtGui.QTableWidgetItem()
                    item.setText('')
                    item.setToolTip('Angles are in degrees')
                    self.tableMain.setItem(row, column, item)
                elif (column == 17):
                    check = QtGui.QCheckBox()
                    check.setCheckState(False)
                    check.setToolTip('If checked, the runs in this row will be stitched together')
                    item = QtGui.QWidget()
                    layout = QtGui.QHBoxLayout(item)
                    layout.addWidget(check)
                    layout.setAlignment(QtCore.Qt.AlignCenter)
                    layout.setSpacing(0)
                    layout.setContentsMargins(0, 0, 0, 0)
                    item.setLayout(layout)
                    item.setContentsMargins(0, 0, 0, 0)
                    self.tableMain.setCellWidget(row, 17, item)
                else:
                    item = QtGui.QTableWidgetItem()
                    item.setText('')
                    self.tableMain.setItem(row, column, item)
            vis_state = settings.value(str(column), True, type=bool)
            self.shownCols[column] = vis_state
            if vis_state:
                self.tableMain.showColumn(column)
            else:
                self.tableMain.hideColumn(column)
        settings.endGroup()
        del settings
    def connectSlots(self):
        self.checkTickAll.stateChanged.connect(self.on_checkTickAll_stateChanged)
        self.comboInstrument.activated.connect(self.on_comboInstrument_activated)
        self.comboPolarCorrect.activated.connect(self.on_comboPolarCorr_activated)
        self.textRB.returnPressed.connect(self.on_textRB_editingFinished)
        self.buttonAuto.clicked.connect(self.on_buttonAuto_clicked)
        self.buttonSearch.clicked.connect(self.on_textRB_editingFinished)
        self.buttonClear.clicked.connect(self.on_buttonClear_clicked)
        self.buttonProcess.clicked.connect(self.on_buttonProcess_clicked)
        self.buttonTransfer.clicked.connect(self.on_buttonTransfer_clicked)
        self.actionOpen_Table.triggered.connect(self.on_actionOpen_Table_triggered)
        self.actionReload_from_Disk.triggered.connect(self.on_actionReload_from_Disk_triggered)
        self.actionSave.triggered.connect(self.on_actionSave_triggered)
        self.actionSave_As.triggered.connect(self.on_actionSave_As_triggered)
        self.actionSave_Workspaces.triggered.connect(self.on_actionSave_Workspaces_triggered)
        self.actionClose_Refl_Gui.triggered.connect(self.windowRefl.close)
        self.actionMantid_Help.triggered.connect(self.on_actionMantid_Help_triggered)
        self.actionAutofill.triggered.connect(self.on_buttonAuto_clicked)
        self.actionSearch_RB.triggered.connect(self.on_textRB_editingFinished)
        self.actionClear_Table.triggered.connect(self.on_buttonClear_clicked)
        self.actionProcess.triggered.connect(self.on_buttonProcess_clicked)
        self.actionTransfer.triggered.connect(self.on_buttonTransfer_clicked)
        self.actionClear.triggered.connect(self.actionClear_triggered)
        self.actionPaste.triggered.connect(self.actionPaste_triggered)
        self.actionCut.triggered.connect(self.actionCut_triggered)
        self.actionCopy.triggered.connect(self.actionCopy_triggered)
        self.actionChoose_Columns.triggered.connect(self.actionChoose_Columns_triggered)
        self.tableMain.cellChanged.connect(self.on_tableMain_modified)
        
    def populateList(self):
        # Clear existing
        self.listMain.clear()
        # Fill with ADS workspaces
        self.populateListADSWorkspaces()
        try:
            selectedInstrument = config['default.instrument'].strip().upper()
            if not self.__instrumentRuns:
                self.__instrumentRuns =  LatestISISRuns(instrument=selectedInstrument)
                self.spinDepth.setMaximum(self.__instrumentRuns.getNumCycles())
            elif not self.__instrumentRuns.getInstrument() == selectedInstrument:
                self.__instrumentRuns =  LatestISISRuns(selectedInstrument)
                self.spinDepth.setMaximum(self.__instrumentRuns.getNumCycles())
            if self.textRB.text():
                runs = []
                self.statusMain.showMessage("Searching Journals for RB number: " + self.textRB.text())
                try:
                    runs = self.__instrumentRuns.getJournalRuns(self.textRB.text(),self.spinDepth.value())
                except:
                    print "Problem encountered when listing archive runs. Please check your network connection and that you have access to the journal archives."
                    QtGui.QMessageBox.critical(self.tableMain, 'Error Retrieving Archive Runs',"Problem encountered when listing archive runs. Please check your network connection and that you have access to the journal archives.")
                    runs = []
                self.statusMain.clearMessage()
                for run in runs:
                    self.listMain.addItem(run)
        except Exception as ex:
            logger.notice("Could not list archive runs")
            logger.notice(str(ex))
    def populateListADSWorkspaces(self):
        names = mtd.getObjectNames()
        for ws in names:
            self.listMain.addItem(ws)
    def autoFill(self):
        col = 0
        # make sure all selected cells are in the same row
        sum = 0
        howMany = len(self.tableMain.selectedItems())
        for cell in self.tableMain.selectedItems():
            sum = sum + self.tableMain.row(cell)
        if (howMany):
            selectedrow = self.tableMain.row(self.tableMain.selectedItems()[0])
            if (sum / howMany == selectedrow):
                startrow = selectedrow + 1
                filled = 0
                for cell in self.tableMain.selectedItems():
                    row = startrow
                    txt = cell.text()
                    while (self.tableMain.item(row, 0).text() != ''):
                        item = QtGui.QTableWidgetItem()
                        item.setText(txt)
                        self.tableMain.setItem(row, self.tableMain.column(cell), item)
                        row = row + 1

                        filled = filled + 1
                if not filled:
                    QtGui.QMessageBox.critical(self.tableMain, 'Cannot perform Autofill',"No target cells to autofill. Rows to be filled should contain a run number in their first cell, and start from directly below the selected line.")
            else:
                QtGui.QMessageBox.critical(self.tableMain, 'Cannot perform Autofill',"Selected cells must all be in the same row.")
        else:
            QtGui.QMessageBox.critical(self.tableMain, 'Cannot perform Autofill',"There are no source cells selected.")

    '''
    Create a display name from a workspace.
    '''
    def create_workspace_display_name(self, candidate):
        if isinstance(mtd[candidate], WorkspaceGroup):
            todisplay = candidate # No single run number for a group of workspaces.
        else:
            todisplay = groupGet(mtd[candidate], "samp", "run_number")
        return todisplay
    def clear_cells(self):
        cells = self.tableMain.selectedItems()
        for cell in cells:
            column = cell.column()
            if not (column == 17 or column == 18):
                cell.setText('')
    def copy_cells(self):
        cells = self.tableMain.selectedItems()
        if not cells:
            print 'nothing to copy'
            return
        #first discover the size of the selection and initialise a list
        mincol = cells[0].column()
        if mincol == 17 or mincol == 18:
            return
            logger.error("Cannot copy, all cells out of range")
        maxrow = -1
        maxcol = -1
        minrow = cells[0].row()
        for cell in reversed(range(len(cells))):
            col = cells[cell].column()
            if col != 17 and col != 18:
                maxcol = col
                maxrow = cells[cell].row()
                break
        colsize = maxcol - mincol + 1
        rowsize = maxrow - minrow + 1
        selection = [['' for x in range(colsize)] for y in range(rowsize)]
        #now fill that list
        for cell in cells:
            row = cell.row()
            col = cell.column()
            if col != 17 and col != 18:
                selection[row - minrow][col - mincol] = str(cell.text())
        tocopy = ''
        for y in range(rowsize):
            for x in range(colsize):
                if x > 0:
                    tocopy += '\t'
                tocopy += selection[y][x]
            if y < (rowsize - 1):
                tocopy += '\n'
        self.copy_to_clipboard(tocopy)
    def paste_cells(self):
        pastedtext = self.clip.text()
        if not pastedtext:
            logger.warning("Nothing to Paste")
            return
        selected = self.tableMain.selectedItems()
        if not selected:
            logger.warning("Cannot paste, no editable cells selected")
            return
        '''
        quickly check if the last row is a single cell and blank
        MS excel adds a line break at the end of copied cells which can mess with this a bit
        I'd like this to be compatible both ways
        '''
        if pastedtext[-1] == '\n':
            pastedtext = pastedtext[:-1]
        #if the string is now empty the only thing on the clipboard as a line break
        if not pastedtext:
            logger.warning("Nothing to Paste")
            return
        pasted = pastedtext.split('\n')
        pastedcells = []
        for row in pasted:
            pastedcells.append(row.split('\t'))
        pastedcols = len(pastedcells[0])
        pastedrows = len(pastedcells)
        if len(selected) > 1:
            #discover the size of the selection
            mincol = selected[0].column()
            if mincol == 17 or mincol == 18:
                return
                logger.error("Cannot copy, all cells out of range")
            minrow = selected[0].row()
            #now fill that list
            for cell in selected:
                row = cell.row()
                col = cell.column()
                if col != 17 and col != 18 and (col - mincol) < pastedcols and (row - minrow) < pastedrows:
                    cell.setText(pastedcells[row - minrow][col - mincol])
        elif selected:
            #when only a single cell is selected, paste all the copied item up until the table limits
            cell = selected[0]
            currow = cell.row()
            homecol = cell.column()
            tablerows = self.tableMain.rowCount()
            for row in pastedcells:
                curcol = homecol
                if currow < tablerows:
                    for col in row:
                        if curcol != 17 and curcol != 18:
                            curcell = self.tableMain.item(currow, curcol)
                            curcell.setText(col)
                            curcol += 1
                        else:
                            #the row has hit the end of the editable cells
                            break
                    currow += 1
                else:
                    #it's dropped off the bottom of the table
                    break
        else:
            logger.warning("Cannot paste, no editable cells selected")
    def copy_to_clipboard(self,text):
        self.clip.setText(str(text))
    def transfer(self):
        col = 0
        row = 0
        while (self.tableMain.item(row, 0).text() != ''):
            row = row + 1
        for idx in self.listMain.selectedItems():
            contents = str(idx.text()).strip()
            first_contents = contents.split(':')[0]
            runnumber = None
            if mtd.doesExist(first_contents):
                runnumber = self.create_workspace_display_name(first_contents)
            else:
                try:
                    temp = Load(Filename=first_contents, OutputWorkspace="_tempforrunnumber")
                    runnumber = groupGet("_tempforrunnumber", "samp", "run_number")
                    DeleteWorkspace(temp)
                except:
                    print "Unable to load file. Please check your managed user directories."
                    QtGui.QMessageBox.critical(self.tableMain, 'Error Loading File',"Unable to load file. Please check your managed user directories.")
            item = QtGui.QTableWidgetItem()
            item.setText(runnumber)
            self.tableMain.setItem(row, col, item)
            item = QtGui.QTableWidgetItem()
            item.setText(self.textRuns.text())
            self.tableMain.setItem(row, col + 2, item)
            col = col + 5
            if col >= 11:
                col = 0
                row = row + 1
    def unTickAll(self,state):
        for row in range(self.tableMain.rowCount()):
            self.tableMain.cellWidget(row, 17).children()[1].setCheckState(state)
    def getAccMethod(self):
        msgBox = QtGui.QMessageBox()
        msgBox.setText("The Data to be processed required that a Live Data service be started. What accumulation method would you like it to use?")
        msgBox.setIcon(QtGui.QMessageBox.Question)
        AddButton = msgBox.addButton("Add", QtGui.QMessageBox.ActionRole | QtGui.QMessageBox.AcceptRole)
        ReplaceButton = msgBox.addButton("Replace", QtGui.QMessageBox.ActionRole | QtGui.QMessageBox.AcceptRole)
        AppendButton = msgBox.addButton("Append", QtGui.QMessageBox.ActionRole | QtGui.QMessageBox.AcceptRole)
        msgBox.setDefaultButton(AddButton)
        msgBox.setEscapeButton(AddButton)
        reply = msgBox.exec_()
        if msgBox.clickedButton() == AppendButton:
            return "Append"
        elif msgBox.clickedButton() == ReplaceButton:
            return "Replace"
        else:
            return "Add"
    def process(self):
#--------- If "Process" button pressed, convert raw files to IvsLam and IvsQ and combine if checkbox ticked -------------
        willProcess = True
        rows = self.tableMain.selectionModel().selectedRows()
        rowIndexes=[]
        for idx in rows:
            rowIndexes.append(idx.row())
        if not len(rowIndexes):
            reply = QtGui.QMessageBox.question(self.tableMain, 'Process all rows?',"This will process all rows in the table. Continue?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.No:
                print "Cancelled!"
                willProcess = False
            else:
                rowIndexes = range(self.tableMain.rowCount())
        if willProcess:
            for row in rowIndexes:  # range(self.tableMain.rowCount()):
                runno = []
                loadedRuns = []
                wksp = []
                wkspBinned = []
                overlapLow = []
                overlapHigh = []
                g = ['g1', 'g2', 'g3']
                theta = [0, 0, 0]
                if (self.tableMain.item(row, 0).text() != ''):
                    for i in range(3):
                        r = str(self.tableMain.item(row, i * 5).text())
                        if (r != ''):
                            runno.append(r)
                        ovLow = str(self.tableMain.item(row, i * 5 + 3).text())
                        if (ovLow != ''):
                            overlapLow.append(float(ovLow))
                        ovHigh = str(self.tableMain.item(row, i * 5 + 4).text())
                        if (ovHigh != ''):
                            overlapHigh.append(float(ovHigh))
                    print len(runno), "runs: ", runno
                    # Determine resolution
                    if (self.tableMain.item(row, 15).text() == ''):

                        loadedRun = None
                        if load_live_runs.is_live_run(runno[0]):
                            if not self.accMethod:
                            #reply = QtGui.QMessageBox.question(self.tableMain, 'Accumulation Method?',"The Data to be processed required that a Live Data service be started. What accumulation method would you like it to use?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                                self.accMethod = self.getAccMethod()
                            loadedRun = load_live_runs.get_live_data(config['default.instrument'], Accumulation = self.accMethod)
                        else:
                            Load(Filename=runno[0], OutputWorkspace="run")
                            loadedRun = mtd["run"]
                        try:
                            dqq = calcRes(loadedRun)
                            item = QtGui.QTableWidgetItem()
                            item.setText(str(dqq))
                            self.tableMain.setItem(row, 15, item)
                            print "Calculated resolution: ", dqq
                        except IndexError:
                            logger.error("Cannot calculate resolution owing to unknown log properties. dq/q will need to be manually entered.")
                            return
                    else:
                        dqq = float(self.tableMain.item(row, 15).text())
                    # Populate runlist
                    first_wq = None
                    for i in range(len(runno)):
                        theta, qmin, qmax, wlam, wq = self.dorun(runno[i], row, i)
                        if not first_wq:
                            first_wq = wq # Cache the first Q workspace
                        theta = round(theta, 3)
                        qmin = round(qmin, 3)
                        qmax = round(qmax, 3)
                        wksp.append(wq.name())
                        if (self.tableMain.item(row, i * 5 + 1).text() == ''):
                            item = QtGui.QTableWidgetItem()
                            item.setText(str(theta))
                            self.tableMain.setItem(row, i * 5 + 1, item)
                        if (self.tableMain.item(row, i * 5 + 3).text() == ''):
                            item = QtGui.QTableWidgetItem()
                            item.setText(str(qmin))
                            self.tableMain.setItem(row, i * 5 + 3, item)
                            overlapLow.append(qmin)
                        if (self.tableMain.item(row, i * 5 + 4).text() == ''):
                            item = QtGui.QTableWidgetItem()
                            if i == len(runno) - 1:
                            # allow full high q-range for last angle
                                qmax = 4 * math.pi / ((4 * math.pi / qmax * math.sin(theta * math.pi / 180)) - 0.5) * math.sin(theta * math.pi / 180)
                            item.setText(str(qmax))
                            self.tableMain.setItem(row, i * 5 + 4, item)
                            overlapHigh.append(qmax)
                        if wksp[i].find(',') > 0 or wksp[i].find(':') > 0:
                            runlist = []
                            l1 = wksp[i].split(',')
                            for subs in l1:
                                l2 = subs.split(':')
                                for l3 in l2:
                                    runlist.append(l3)
                            wksp[i] = first_wq.name()
                                
                        ws_name_binned = wksp[i] + '_binned'
                        ws = getWorkspace(wksp[i])
                        w1 = getWorkspace(wksp[0])
                        w2 = getWorkspace(wksp[len(wksp) - 1])
                        if len(overlapLow):
                            Qmin = overlapLow[0]
                        else:
                            Qmin = w1.readX(0)[0]
                        if len(overlapHigh):
                            Qmax = overlapHigh[len(overlapHigh) - 1]
                        else:
                            Qmax = max(w2.readX(0))
                        Rebin(InputWorkspace=wksp[i], Params=str(overlapLow[i]) + ',' + str(-dqq) + ',' + str(overlapHigh[i]), OutputWorkspace=ws_name_binned)
                        wkspBinned.append(ws_name_binned)
                        wsb = getWorkspace(ws_name_binned)
                        Imin = min(wsb.readY(0))
                        Imax = max(wsb.readY(0))
                        if canMantidPlot:
                            g[i] = plotSpectrum(ws_name_binned, 0, True)
                            titl = groupGet(ws_name_binned, 'samp', 'run_title')
                            if (i > 0):
                                mergePlots(g[0], g[i])
                            if (type(titl) == str):
                                g[0].activeLayer().setTitle(titl)
                            g[0].activeLayer().setAxisScale(Layer.Left, Imin * 0.1, Imax * 10, Layer.Log10)
                            g[0].activeLayer().setAxisScale(Layer.Bottom, Qmin * 0.9, Qmax * 1.1, Layer.Log10)
                            g[0].activeLayer().setAutoScale()
                    if (self.tableMain.cellWidget(row, 17).children()[1].checkState() > 0):
                        if (len(runno) == 1):
                            print "Nothing to combine!"
                        elif (len(runno) == 2):
                            outputwksp = runno[0] + '_' + runno[1][3:5]
                        else:
                            outputwksp = runno[0] + '_' + runno[2][3:5]
                        print runno
                        w1 = getWorkspace(wksp[0])
                        w2 = getWorkspace(wksp[len(wksp) - 1])
                        begoverlap = w2.readX(0)[0]
                        # get Qmax
                        if (self.tableMain.item(row, i * 5 + 4).text() == ''):
                            overlapHigh = 0.3 * max(w1.readX(0))
                        print overlapLow, overlapHigh
                        wcomb = combineDataMulti(wkspBinned, outputwksp, overlapLow, overlapHigh, Qmin, Qmax, -dqq, 1)
                        if (self.tableMain.item(row, 16).text() != ''):
                            Scale(InputWorkspace=outputwksp, OutputWorkspace=outputwksp, Factor=1 / float(self.tableMain.item(row, 16).text()))
                        Qmin = getWorkspace(outputwksp).readX(0)[0]
                        Qmax = max(getWorkspace(outputwksp).readX(0))
                        if canMantidPlot:
                            gcomb = plotSpectrum(outputwksp, 0, True)
                            titl = groupGet(outputwksp, 'samp', 'run_title')
                            gcomb.activeLayer().setTitle(titl)
                            gcomb.activeLayer().setAxisScale(Layer.Left, 1e-8, 100.0, Layer.Log10)
                            gcomb.activeLayer().setAxisScale(Layer.Bottom, Qmin * 0.9, Qmax * 1.1, Layer.Log10)
        self.accMethod = None
    def dorun(self, runno, row, which):
        g = ['g1', 'g2', 'g3']
        transrun = str(self.tableMain.item(row, which * 5 + 2).text())
        angle = str(self.tableMain.item(row, which * 5 + 1).text())
        loadedRun = runno
        if load_live_runs.is_live_run(runno):
            if not self.accMethod:
                self.accMethod = self.getAccMethod()
            loadedRun = load_live_runs.get_live_data(InstrumentName = config['default.instrument'], Accumulation = self.accMethod)
        wlam, wq, th = quick(loadedRun, trans=transrun, theta=angle)

        if ':' in runno:
            runno = runno.split(':')[0]
        if ',' in runno:
            runno = runno.split(',')[0]
      
        inst = groupGet(wq, 'inst')
        lmin = inst.getNumberParameter('LambdaMin')[0] + 1
        lmax = inst.getNumberParameter('LambdaMax')[0] - 2
        qmin = 4 * math.pi / lmax * math.sin(th * math.pi / 180)
        qmax = 4 * math.pi / lmin * math.sin(th * math.pi / 180)
        return th, qmin, qmax, wlam, wq
    
    def saveTable(self, filename):
        try:
            writer = csv.writer(open(filename, "wb"))
            for row in range(self.tableMain.rowCount()):
                rowtext = []
                for column in range(self.tableMain.columnCount() - 1):
                    rowtext.append(self.tableMain.item(row, column).text())
                if (len(rowtext) > 0):
                    writer.writerow(rowtext)
            self.current_table = filename
            print "Saved file to " + filename
            self.windowRefl.modFlag = False
        except:
            return False
        self.windowRefl.modFlag = False
        return True
    def save(self, failsave = False):
        filename = ''
        if failsave:
            #this is an emergency autosave as the program is failing
            print "The ISIS Reflectonomy GUI has encountered an error, it will now attempt to save a copy of your work."
            msgBox = QtGui.QMessageBox()
            msgBox.setText("The ISIS Reflectonomy GUI has encountered an error, it will now attempt to save a copy of your work.\nPlease check the log for details.")
            msgBox.setStandardButtons(QtGui.QMessageBox.Ok)
            msgBox.setIcon(QtGui.QMessageBox.Critical)
            msgBox.setDefaultButton(QtGui.QMessageBox.Ok)
            msgBox.setEscapeButton(QtGui.QMessageBox.Ok)
            msgBox.exec_()
            import datetime
            failtime = datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
            if self.current_table:
                filename = self.current_table.rsplit('.',1)[0] + "_recovered_" + failtime + ".tbl"
            else:
                mantidDefault = config['defaultsave.directory']
                if os.path.exists(mantidDefault):
                    filename = os.path.join(mantidDefault,"mantid_reflectometry_recovered_" + failtime + ".tbl")
                else:
                    import tempfile
                    tempDir = tempfile.gettempdir()
                    filename = os.path.join(tempDir,"mantid_reflectometry_recovered_" + failtime + ".tbl")
        else:
            #this is a save-on-quit or file->save
            if self.current_table:
                filename = self.current_table
            else:
                saveDialog = QtGui.QFileDialog(self.widgetMainRow.parent(), "Save Table")
                saveDialog.setFileMode(QtGui.QFileDialog.AnyFile)
                saveDialog.setNameFilter("Table Files (*.tbl);;All files (*.*)")
                saveDialog.setDefaultSuffix("tbl")
                saveDialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
                if saveDialog.exec_():
                    filename = saveDialog.selectedFiles()[0]
                else:
                    return False
        return self.saveTable(filename)
    def saveAs(self):
        saveDialog = QtGui.QFileDialog(self.widgetMainRow.parent(), "Save Table")
        saveDialog.setFileMode(QtGui.QFileDialog.AnyFile)
        saveDialog.setNameFilter("Table Files (*.tbl);;All files (*.*)")
        saveDialog.setDefaultSuffix("tbl")
        saveDialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
        if saveDialog.exec_():
            filename = saveDialog.selectedFiles()[0]
            self.saveTable(filename)
    def loadTable(self):
        self.loading = True
        loadDialog = QtGui.QFileDialog(self.widgetMainRow.parent(), "Open Table")
        loadDialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        loadDialog.setNameFilter("Table Files (*.tbl);;All files (*.*)")
        if loadDialog.exec_():
            try:
                filename = loadDialog.selectedFiles()[0]
                self.current_table = filename
                reader = csv.reader(open(filename, "rb"))
                row = 0
                for line in reader:
                    if (row < 100):
                        for column in range(self.tableMain.columnCount() - 1):
                            item = QtGui.QTableWidgetItem()
                            item.setText(line[column])
                            self.tableMain.setItem(row, column, item)
                        row = row + 1
            except:
                print 'Could not load file: ' + filename + '. File not found or unable to read from file.'
        self.loading = False
        self.windowRefl.modFlag = False
    def reloadTable(self):
        self.loading = True
        filename = self.current_table
        if filename:
            try:
                reader = csv.reader(open(filename, "rb"))
                row = 0
                for line in reader:
                    if (row < 100):
                        for column in range(self.tableMain.columnCount() - 1):
                            item = QtGui.QTableWidgetItem()
                            item.setText(line[column])
                            self.tableMain.setItem(row, column, item)
                        row = row + 1
            except:
                print 'Could not load file: ' + filename + '. File not found or unable to read from file.'
        else:
            print 'No file in table to reload.'
        self.loading = False
        self.windowRefl.modFlag = False
    def saveWorkspaces(self):
        try:
            Dialog = QtGui.QDialog()
            u = refl_save.Ui_SaveWindow()
            u.setupUi(Dialog)
            Dialog.exec_()
        except Exception as ex:
            logger.notice("Could not open save workspace dialog")
            logger.notice(str(ex))
    def chooseColumns(self):
        try:
            Dialog = QtGui.QDialog()
            u = refl_choose_col.ReflChoose()
            u.setupUi(Dialog, self.shownCols, self.tableMain)
            if Dialog.exec_():
                settings = QtCore.QSettings()
                settings.beginGroup("Mantid/ISISReflGui/Columns")
                for key, value in u.visiblestates.iteritems():
                    self.shownCols[key] = value
                    settings.setValue(str(key), value)
                    if value:
                        self.tableMain.showColumn(key)
                    else:
                        self.tableMain.hideColumn(key)
                settings.endGroup()
                del settings
        except Exception as ex:
            logger.notice("Could not open choose columns dialog")
            logger.notice(str(ex))
    def showHelp(self):
        import webbrowser
        webbrowser.open('http://www.mantidproject.org/ISIS_Reflectometry_GUI')

        
'''
Get a representative workspace from the input workspace.
'''        
def get_representative_workspace(run):
    if isinstance(run, WorkspaceGroup):
        run_number = groupGet(run[0], "samp", "run_number")
        _runno = Load(Filename=str(run_number))
    elif isinstance(run, Workspace):
        _runno = run
    elif isinstance(run, int):
        _runno = Load(Filename=run, OutputWorkspace=runno)
    elif isinstance(run, str) and mtd.doesExist(run): 
        ws = mtd[run]
        if isinstance(ws, WorkspaceGroup):
            run_number = groupGet(ws[0], "samp", "run_number")
            _runno = Load(Filename=str(run_number))
    elif isinstance(run, str):
        _runno = Load(Filename=run.replace("raw", "nxs", 1), OutputWorkspace=runno)
    else:
        raise TypeError("Must be a workspace, int or str")
    return _runno

'''
Calculate the resolution from the slits.
'''
def calcRes(run):
    
    runno = get_representative_workspace(run)
    # Get slits and detector angle theta from NeXuS
    th = groupGet(runno, 'samp', 'THETA')
    inst = groupGet(runno, 'inst')
    s1z = inst.getComponentByName('slit1').getPos().getZ() * 1000.0  # distance in mm
    s2z = inst.getComponentByName('slit2').getPos().getZ() * 1000.0  # distance in mm
    s1vg = inst.getComponentByName('slit1')
    s1vg = s1vg.getNumberParameter('vertical gap')[0]
    s2vg = inst.getComponentByName('slit2')
    s2vg = s2vg.getNumberParameter('vertical gap')[0]
    print "s1vg=", s1vg, "s2vg=", s2vg, "theta=", th
    #1500.0 is the S1-S2 distance in mm for SURF!!!
    resolution = math.atan((s1vg + s2vg) / (2 * (s2z - s1z))) * 180 / math.pi / th
    print "dq/q=", resolution
    if not type(run) == type(Workspace):
        DeleteWorkspace(runno)
    return resolution

def groupGet(wksp, whattoget, field=''):
    '''
    returns information about instrument or sample details for a given workspace wksp,
    also if the workspace is a group (info from first group element)
    '''
    if (whattoget == 'inst'):
        if isinstance(wksp, str):
            at = getattr(mtd[wksp],'size',None)
            if callable(at):
                return mtd[wksp][0].getInstrument()
            else:
                return mtd[wksp].getInstrument()
        elif isinstance(wksp, Workspace):
            at = getattr(wksp,'size',None)
            if callable(at):
                return wksp[0].getInstrument()
            else:
                return wksp.getInstrument()
        else:
            return 0
    elif (whattoget == 'samp' and field != ''):
        if isinstance(wksp, str):
            at = getattr(mtd[wksp],'size',None)
            if callable(at):
                try:
                    log = mtd[wksp][0].getRun().getLogData(field).value
                    if (type(log) is int or type(log) is str):
                        res = log
                    else:
                        res = log[-1]
                except RuntimeError:
                    res = 0
                    print "Block " + field + " not found."
            else:
                try:
                    log = mtd[wksp].getRun().getLogData(field).value
                    if (type(log) is int or type(log) is str):
                        res = log
                    else:
                        res = log[-1]
                except RuntimeError:
                    res = 0
                    print "Block " + field + " not found."
        elif isinstance(wksp, Workspace):
            at = getattr(wksp,'size',None)
            if callable(at):
                try:
                    log = wksp[0].getRun().getLogData(field).value
                    if (type(log) is int or type(log) is str):
                        res = log
                    else:
                        res = log[-1]
                except RuntimeError:
                    res = 0
                    print "Block " + field + " not found."
            else:
                try:
                    log = wksp.getRun().getLogData(field).value
                    if (type(log) is int or type(log) is str):
                        res = log
                    else:
                        res = log[-1]
                except RuntimeError:
                    res = 0
                    print "Block " + field + " not found."
        else:
            res = 0
        return res
    elif (whattoget == 'wksp'):
        if isinstance(wksp, str):
            at = getattr(mtd[wksp],'size',None)
            if callable(at):
                return mtd[wksp][0].getNumberHistograms()
            else:
                return mtd[wksp].getNumberHistograms()
        elif isinstance(wksp, Workspace):
            at = getattr(wksp,'size',None)
            if callable(at):
                return mtd[wksp][0].getNumberHistograms()
            else:
                return wksp.getNumberHistograms()
        else:
            return 0
def getWorkspace(wksp):
    if isinstance(wksp, Workspace):
        return wksp
    elif isinstance(wksp, str):
        if isinstance(mtd[wksp], WorkspaceGroup):
            wout = mtd[wksp][0]
        else:
            wout = mtd[wksp]
        return wout
    else:
        print "Unable to get workspace: " + wksp
        return 0
