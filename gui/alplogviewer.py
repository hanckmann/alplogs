#!/usr/bin/env python
#
# Copyright (c) Patrick Hanckmann
# All rights reserved.
#
# License information is provided in LICENSE.md
#
# Author: Patrick Hanckmann <hanckmann@gmail.com>
# Project: Alpine System Info Log Viewer

import os
import sys
import argparse
from typing import List
from pathlib import Path

from PyQt5 import QtCore, QtGui, QtWidgets

from alplogparser import AlpLogParser, AlpLogModule


__application__ = 'Alpine System Info Log Viewer'
__author__ = 'Patrick Hanckmann'
__email__ = 'hanckmann@gmail.com'
__copyright__ = 'Copyright 2020, Patrick Hanckmann'
__version__ = '0.0.1'
__status__ = 'Testing'  # 'Production'


class AlpLogModel(QtCore.QAbstractTableModel):

    def __init__(self, *args, **kwargs):
        QtCore.QAbstractTableModel.__init__(self, *args, **kwargs)
        self.set_items(items=None)

    def set_items(self, items: List[AlpLogModule]):
        self.layoutAboutToBeChanged.emit()
        if items:
            self._data = [model.to_dict() for model in items]
            self._header_vertical = [str(model.timestamp.isoformat()).replace('T', ' ') for model in items]
            self._header_horizontal = items[0].to_table_header()
        else:
            self._data = [list()]
            self._header_vertical = []
            self._header_horizontal = []
        self.layoutChanged.emit()

    def rowCount(self, parent=None):
        return len(self._header_vertical)

    def columnCount(self, parent=None):
        return len(self._header_horizontal)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return QtCore.QVariant(self.cell_data(row=index.row(), column=index.column()))
            if role == QtCore.Qt.BackgroundRole:
                color = QtCore.Qt.white
                item = self.cell_data(row=index.row(), column=index.column())
                if not item:
                    color = QtGui.QColor(255, 255, 222)
                if index.row() < self.rowCount() - 1:
                    item_below = self.cell_data(row=index.row() + 1, column=index.column())
                    if not item == item_below:
                        color = QtGui.QColor(255, 200, 200)
                return QtGui.QBrush(color)
        return QtCore.QVariant()

    def cell_data(self, row, column):
        key = self._header_horizontal[column]
        if key in self._data[row]:
            return str(self._data[row][key])
        else:
            return ''

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Vertical:
                return self._header_vertical[section]
            if orientation == QtCore.Qt.Horizontal:
                return self._header_horizontal[section]


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self,
                 parent=None,
                 *args,
                 **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        # Build UI
        self.data = list()
        self.model = AlpLogModel()
        self.modules_model = QtCore.QStringListModel()
        self.setup_ui()

    def show_folder_input_dialog(self):
        location = os.getcwd()
        folder = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                            'Open Log Folder',
                                                            location,
                                                            QtWidgets.QFileDialog.ShowDirsOnly)
        self.folderpath_lineeditlineedit.setText(folder)

    def analyse_logs(self):
        folder = self.folderpath_lineeditlineedit.text()
        if not folder:
            self.show_error_message(message='You have not set the log files folder!', title='No folder set')
        self.data = list()
        self.model.set_items([])
        self.modules_model.removeRows(0, self.modules_model.rowCount())
        # Iterate through all logs
        paths = Path(folder).glob('**/system_status.*')
        log = None
        for path in paths:
            del log
            log = AlpLogParser(filepath=path)
            self.data.append(log)
        self.data = sorted(self.data, key=lambda k: k.modules[0].timestamp, reverse=True)
        if self.data:
            self.modules_model.setStringList(self.data[-1].names())
            self.setupStatusBar(items=len(self.data),
                                first=self.data[0].modules[0].timestamp,
                                last=self.data[-1].modules[0].timestamp)
        else:
            self.modules_model.setStringList([])
            self.setupStatusBar(items=0)

    def on_listview_clicked(self, selected, deselected):
        if self.data:
            module_models = tuple([item.modules[selected.indexes()[0].row()] for item in self.data])
            self.model.set_items(module_models)
            self.data_tableview.resizeColumnsToContents()

    def setup_ui(self):
        self.logo_icon = QtGui.QIcon('staal_logo.png')
        self.setWindowIcon(self.logo_icon)
        self.setWindowTitle('{} ({})'.format(__application__, __version__))
        self.setMenu()
        self.setupStatusBar(items=0)

        # Header
        folderpath_label = QtWidgets.QLabel('Folder:')
        folderpath_lineeditlineedit = QtWidgets.QLineEdit()
        folderpath_lineeditlineedit.setText('/home/patrick/Projects/alplogs/logs')
        folderpath_lineeditlineedit.returnPressed.connect(lambda: self.send(self.folderpath_lineeditlineedit.text()))
        folderpath_lineeditlineedit.setMinimumWidth(400)
        self.folderpath_lineeditlineedit = folderpath_lineeditlineedit
        folderpath_select_button = QtWidgets.QPushButton(
            text='Select',
            clicked=lambda: self.show_folder_input_dialog()
        )
        analyse_button = QtWidgets.QPushButton(
            text='Analyse',
            clicked=lambda: self.analyse_logs()
        )
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.addWidget(folderpath_label)
        header_layout.addWidget(folderpath_lineeditlineedit)
        header_layout.addWidget(folderpath_select_button)
        header_layout.addWidget(analyse_button)
        header_layout.addStretch(1)
        header_widget = QtWidgets.QWidget()
        header_widget.setLayout(header_layout)

        # Data
        self.modules_listview = QtWidgets.QListView()
        self.modules_listview.setMaximumWidth(200)
        self.modules_listview.setModel(self.modules_model)
        self.modules_listview.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.modules_listview.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        # self.modules_listview.selectionChanged.connect(self.on_listview_clicked)
        self.modules_listview_selection_model = self.modules_listview.selectionModel()
        self.modules_listview_selection_model.selectionChanged.connect(self.on_listview_clicked)
        self.data_tableview = QtWidgets.QTableView()
        self.data_tableview.verticalHeader().setDefaultAlignment(QtCore.Qt.AlignRight)
        self.data_tableview.setModel(self.model)
        data_layout = QtWidgets.QHBoxLayout()
        data_layout.addWidget(self.modules_listview)
        data_layout.addWidget(self.data_tableview)
        data_widget = QtWidgets.QWidget()
        data_widget.setLayout(data_layout)

        # Central
        central_layout = QtWidgets.QVBoxLayout()
        central_layout.addWidget(header_widget)
        central_layout.addWidget(data_widget)
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

    def setMenu(self):
        main_menu = self.menuBar()

        about_button = QtWidgets.QAction('About', self)
        about_button.setStatusTip('About')
        about_button.triggered.connect(self.show_about)
        exit_button = QtWidgets.QAction('Exit', self)
        exit_button.setShortcut('Ctrl+Q')
        exit_button.setStatusTip('Exit application')
        exit_button.triggered.connect(self.close)
        file_menu = main_menu.addMenu('File')
        file_menu.addAction(about_button)
        file_menu.addSeparator()
        file_menu.addAction(exit_button)

    def setupStatusBar(self, items=None, first=None, last=None, right=None):
        status_message_left = QtWidgets.QLabel('left')
        status_message_left.setAlignment(QtCore.Qt.AlignLeft)
        status_message_right = QtWidgets.QLabel('right')
        status_message_right.setAlignment(QtCore.Qt.AlignRight)
        statusbar = QtWidgets.QStatusBar()
        statusbar.addWidget(status_message_left, 1)
        statusbar.addWidget(status_message_right, 1)
        left = ''
        if items is not None:
            left = 'Logs: {}'.format(items)
        if first is not None:
            left = '   From: {}'.format(first.isoformat().replace('T', ' '))
        if last is not None:
            left = '   Until: {}'.format(last.isoformat().replace('T', ' '))
        if not right:
            right = 'ScoobyDoobyDoo!!!'
        status_message_left.setText(left)
        status_message_right.setText(right)
        self.setStatusBar(statusbar)

    def show_error_message(self, message: str, title=None):
        print('ERROR: {}'.format(message))
        if not title:
            title = 'Error'
        QtWidgets.QMessageBox.critical(self, title, message)

    def show_about(self):
        QtWidgets.QMessageBox.about(self, 'About', '\n'.join((__application__,
                                                              ' ',
                                                              'Version\t: {}'.format(__version__),
                                                              'Author \t: {}'.format(__author__),
                                                              'Email  \t: {}'.format(__email__),
                                                              ' ',
                                                              __copyright__.replace('Copyright', '©'))))


def get_options(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='Parses command.')
    parser.add_argument('-f', '--folder', help='Folder containing the log files.')
    options = parser.parse_args(args)
    return options


if __name__ == '__main__':
    # Options
    options = get_options(sys.argv[1:])

    # Start UI
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
