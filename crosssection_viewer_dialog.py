# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CrosssectionViewerDialog
                                 A QGIS plugin
 Leveelogic Crosssection Viewer
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2022-04-11
        git sha              : $Format:%H$
        copyright            : (C) 2022 by Breinbaas
        email                : breinbaasnl@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure, MouseButton

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

from leveelogic.objects.crosssection import (
    Crosssection,
    CharacteristicPointNames,
    CharacteristicPointType,
)

from .database import Database

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "crosssection_viewer_dialog_base.ui")
)


def get_key(dict, val):
    for key, value in dict.items():
        if val == value:
            return key
    raise ValueError(f"Unknown value '{val}' for the given dict.")


class CrosssectionViewerDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        """Constructor."""
        super(CrosssectionViewerDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self._iface = iface
        self._figure = None
        self._canvas = None
        self._crosssections = []
        self._crosssection_ids = []
        self._selected_index = -1
        self._database = Database()

        # fill the listbox with point types
        self.lwCharacteristicPoints.addItems(CharacteristicPointNames.values())
        self.lwCharacteristicPoints.setCurrentRow(2)

        self._initialize_figure_and_canvas()
        self._connect()

    def _connect(self):
        self.pbFirst.clicked.connect(self.onPbFirstClicked)
        self.pbPrev.clicked.connect(self.onPbPrevClicked)
        self.pbNext.clicked.connect(self.onPbNextClicked)
        self.pbLast.clicked.connect(self.onPbLastClicked)
        self.pbClear.clicked.connect(self.onPbClearClicked)
        self.pbRefresh.clicked.connect(self.onPbRefreshClicked)
        self.pbClipboard.clicked.connect(self.onPbClipboardClicked)
        self.pbUpdate.clicked.connect(self.onPbUpdateClicked)

    def onPbUpdateClicked(self):
        crosssection_id = self._crosssection_ids[self._selected_index]
        self._database.update_crosssection(
            crosssection_id, self._crosssections[self._selected_index]
        )

    def onPbClipboardClicked(self):
        crosssection = self._crosssections[self._selected_index]
        cb = QtWidgets.QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        text = ""
        for p in crosssection.points:
            text += f"{p.l},{p.z},"
        cb.setText(text[:-1], mode=cb.Clipboard)

    def onPbRefreshClicked(self):
        crosssection_id = self._crosssection_ids[self._selected_index]
        self._crosssections[
            self._selected_index
        ] = self._database.get_crosssection_by_id(crosssection_id)
        self._update_figure()

    def onPbClearClicked(self):
        self._crosssections[self._selected_index].characteristic_points = []
        self._update_figure()

    def onFigureMouseClicked(self, e):
        """Event that is called if the mouse is clicked within the figure"""
        crosssection = self._crosssections[self._selected_index]
        idx = self.lwCharacteristicPoints.currentRow()
        if idx < -1:
            return

        if e.button == MouseButton.LEFT:
            l = e.xdata
            cptype = get_key(
                CharacteristicPointNames,
                self.lwCharacteristicPoints.currentItem().text(),
            )
            if crosssection.start.l <= l and l <= crosssection.end.l:
                crosssection.add_characteristic_point(round(l, 2), cptype)
            self._update_figure()

        if idx < self.lwCharacteristicPoints.count() - 1:
            self.lwCharacteristicPoints.setCurrentRow(idx + 1)
        else:
            self.lwCharacteristicPoints.setCurrentRow(0)

    def onPbFirstClicked(self):
        self._selected_index = 0
        self._update_figure()

    def onPbPrevClicked(self):
        if self._selected_index > 0:
            self._selected_index -= 1
            self._update_figure()

    def onPbNextClicked(self):
        if self._selected_index < len(self._crosssections) - 1:
            self._selected_index += 1
            self._update_figure()

    def onPbLastClicked(self):
        self._selected_index = len(self._crosssections) - 1
        self._update_figure()

    def _initialize_figure_and_canvas(self):
        """Setup the figure and put it in the frame to display the chosen Cpt"""
        layout = QtWidgets.QVBoxLayout(self.frmCrosssection)
        self._figure = Figure()
        self._figure.set_tight_layout(True)
        self._canvas = FigureCanvas(self._figure)
        self._figure.canvas.mpl_connect("button_press_event", self.onFigureMouseClicked)
        layout.addWidget(self._canvas)

    def set_crosssections(self, crosssections):
        assert len(crosssections) > 0
        self._crosssections = crosssections
        self._selected_index = 0
        self._update_figure()

    def set_crosssection_ids(self, crosssection_ids):
        self._crosssection_ids = crosssection_ids

    def _update_figure(self):
        self._figure.clear()
        self._canvas.draw()

        # draw your own stuff because it gets annoying
        crosssection = self._crosssections[self._selected_index]

        ax = self._figure.add_subplot()
        ax.set_xlim(crosssection.start.l, crosssection.end.l)
        ax.set_ylim(crosssection.bottom - 0.5, crosssection.top + 0.5)
        ax.grid(which="both")
        ax.plot(
            [p.l for p in crosssection.points],
            [p.z for p in crosssection.points],
            "k",
        )

        for cp in crosssection.characteristic_points:
            ax.plot(
                [cp.l, cp.l],
                [crosssection.bottom - 0.5, crosssection.top + 0.5],
                "k--",
            )
            ax.text(
                cp.l,
                crosssection.bottom - 0.5,
                CharacteristicPointNames[cp.point_type],
                rotation=270,
            )

        self._figure.suptitle(
            f"dijkcode {crosssection.levee_code} metrering {crosssection.levee_chainage}"
        )
        self._canvas.draw()
