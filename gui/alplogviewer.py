#!/usr/bin/env python
#
# Copyright (c) Patrick Hanckmann
# All rights reserved.
#
# License information is provided in LICENSE.md
#
# Author: Patrick Hanckmann <hanckmann@gmail.com>
# Project: Alpine System Info Log Viewer

import sys
import argparse
from typing import List
from datetime import datetime

from PyQt5 import QtCore, QtGui, QtWidgets

from alplogparser import AlpLogModule


__application__ = "Alpine System Info Log Viewer"
__author__ = "Patrick Hanckmann"
__email__ = "hanckmann@gmail.com"
__copyright__ = "Copyright 2020, Patrick Hanckmann"
__version__ = "0.0.1"
__status__ = "Testing"  # "Production"


class AlpLogModel(QtCore.QAbstractTableModel):

    def __init__(self, *args, **kwargs):
        QtCore.QAbstractTableModel.__init__(self, *args, **kwargs)
        self._data = [list()]
        self._header_vertical = []
        self._header_horizontal = []

    def set_model(self, models: List[AlpLogModule]):
        self.layoutAboutToBeChanged.emit()
        self._data = [model.to_table() for model in models]
        self._header_vertical = [model.to_table_header_vertical() for model in models]
        self._header_horizontal = [model.to_table_header_horizontal() for model in models]
        self.layoutChanged.emit()

    def rowCount(self, parent=None):
        return len(self._header_vertical)

    def columnCount(self, parent=None):
        return len(self._header_horizontal)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return QtCore.QVariant(str(self._data[index.row()][index.column()]))
            if role == QtCore.Qt.BackgroundRole:
                color = QtCore.Qt.white
                return QtGui.QBrush(color)
        return QtCore.QVariant()

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
        self.model = AlpLogModel()
        self.modules_model = QtCore.QStringListModel()
        self.setup_ui()

    def setup_ui(self):
        self.logo_icon = QtGui.QIcon('staal_logo.png')
        self.setWindowIcon(self.logo_icon)
        self.setWindowTitle("{} ({})".format(__application__, __version__))
        self.setMenu()
        self.setupStatusBar()

        # Header
        folderpath_label = QtWidgets.QLabel("Folder:")
        folderpath_lineeditlineedit = QtWidgets.QLineEdit()
        folderpath_lineeditlineedit.returnPressed.connect(lambda: self.send(self.folderpath_lineeditlineedit.text()))
        folderpath_lineeditlineedit.setMinimumWidth(400)
        self.folderpath_lineeditlineedit = folderpath_lineeditlineedit
        folderpath_select_button = QtWidgets.QPushButton(
            text="Select"
        )
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.addWidget(folderpath_label)
        header_layout.addWidget(folderpath_lineeditlineedit)
        header_layout.addWidget(folderpath_select_button)
        header_layout.addStretch(1)
        header_widget = QtWidgets.QWidget()
        header_widget.setLayout(header_layout)

        # Data
        self.modules_listview = QtWidgets.QListView()
        self.modules_listview.setMaximumWidth(200)
        self.modules_listview.setModel(self.modules_model)
        self.data_tableview = QtWidgets.QTableView()
        self.data_tableview.verticalHeader().setDefaultAlignment(QtCore.Qt.AlignRight)
        self.data_tableview.setModel(self.model)
        self.data_tableview.resizeColumnsToContents()
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

    def setupStatusBar(self, left=None, center=None, right=None):
        status_message_left = QtWidgets.QLabel("left")
        status_message_left.setAlignment(QtCore.Qt.AlignLeft)
        status_message_center = QtWidgets.QLabel("center")
        status_message_center.setAlignment(QtCore.Qt.AlignCenter)
        status_message_right = QtWidgets.QLabel("right")
        status_message_right.setAlignment(QtCore.Qt.AlignRight)
        statusbar = QtWidgets.QStatusBar()
        statusbar.addWidget(status_message_left, 1)
        statusbar.addWidget(status_message_center, 1)
        statusbar.addWidget(status_message_right, 1)
        if not left:
            left = "Newest: <datetime>"
        if not center:
            center = "Files: <count>"
        if not right:
            right = "Oldest: <datetime>"
        status_message_left.setText(left)
        status_message_center.setText(center)
        status_message_right.setText(right)
        self.status_message_center = status_message_center
        self.setStatusBar(statusbar)

    def show_error_message(self, message: str, title=None):
        print("ERROR: {}".format(message))
        if not title:
            title = "Error"
        QtWidgets.QMessageBox.critical(self, title, message)

    def show_about(self):
        QtWidgets.QMessageBox.about(self, "About", "\n".join((__application__,
                                                              " ",
                                                              "Version\t: {}".format(__version__),
                                                              "Author \t: {}".format(__author__),
                                                              "Email  \t: {}".format(__email__),
                                                              " ",
                                                              __copyright__.replace('Copyright', '©'))))


def get_options(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description="Parses command.")
    parser.add_argument("-f", "--folder", help="Folder containing the log files.")
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
