"""
/***************************************************************************
 GridProperties - GUI for setting grid overlay properties.
                                 A QGIS plugin
 Overlays a user-definable grid on the map.
                             -------------------
        begin                : 2012-05-11
        copyright            : (C) 2012 by John Donovan
        email                : mersey.viking@gmail.com
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

from PyQt4 import QtGui
from qgis import core, gui
from qgis.core import QGis

from ui_grid_properties import Ui_GridProperties

class GridPropertiesDialog(QtGui.QDialog):

    def __init__(self, gridlayer):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_GridProperties()
        self.ui.setupUi(self)

        self.gridlayer = gridlayer
        
        validator = QtGui.QDoubleValidator(-10000000.0, 10000000.0, 6, None)
        self.ui.editOriginX.setValidator(validator)
        self.ui.editOriginY.setValidator(validator)
        self.ui.btnStyle.clicked.connect(self.chooseStyle)
        self.ui.btnFont.clicked.connect(self.chooseFont)
        self.ui.btnColour.clicked.connect(self.chooseColour)

        self.symbol = gridlayer.symbol.clone()
        self.label_attributes = gridlayer.label_attributes
        
        # Store attributes in case the user changes font attributes but cancels the dialog box.
        self.family = gridlayer.label_attributes.family()
        self.bold = gridlayer.label_attributes.bold()
        self.italic = gridlayer.label_attributes.italic()
        self.underline = gridlayer.label_attributes.underline()
        self.strikeOut = gridlayer.label_attributes.strikeOut()
        self.size = gridlayer.label_attributes.size()
        self.color = gridlayer.label_attributes.color()

        self.ui.boxLabels.setChecked(gridlayer.draw_labels)
        self.ui.editOriginX.setText(str(gridlayer.origin.x()))
        self.ui.editOriginY.setText(str(gridlayer.origin.y()))
        self.ui.spinCountX.setValue(gridlayer.numCellsX)
        self.ui.spinCountY.setValue(gridlayer.numCellsY)
        self.ui.spinOffsetX.setValue(gridlayer.gridOffsetX)
        self.ui.spinOffsetY.setValue(gridlayer.gridOffsetY)
        self.ui.spinCellSizeX.setValue(gridlayer.cellSizeX)
        self.ui.spinCellSizeY.setValue(gridlayer.cellSizeY)
        self.ui.spinAngle.setValue(gridlayer.baselineAngle)
        
    def accept(self):
        self.gridlayer.origin = core.QgsPoint(float(self.ui.editOriginX.text()), float(self.ui.editOriginY.text()))
        self.gridlayer.numCellsX = self.ui.spinCountX.value()
        self.gridlayer.numCellsY = self.ui.spinCountY.value()
        self.gridlayer.gridOffsetX = self.ui.spinOffsetX.value()
        self.gridlayer.gridOffsetY = self.ui.spinOffsetY.value()
        self.gridlayer.cellSizeX = self.ui.spinCellSizeX.value()
        self.gridlayer.cellSizeY = self.ui.spinCellSizeY.value()
        self.gridlayer.baselineAngle = self.ui.spinAngle.value()
        self.gridlayer.draw_labels = self.ui.boxLabels.isChecked()
        self.gridlayer.symbol = self.symbol.clone()
        QtGui.QDialog.accept(self)

    def reject(self):
        # Restore original label attributes.
        self.gridlayer.label_attributes.setFamily(self.family)
        self.gridlayer.label_attributes.setBold(self.bold)
        self.gridlayer.label_attributes.setItalic(self.italic)
        self.gridlayer.label_attributes.setUnderline(self.underline)
        self.gridlayer.label_attributes.setStrikeOut(self.strikeOut)
        self.gridlayer.label_attributes.setSize(self.size, core.QgsLabelAttributes.PointUnits)
        self.gridlayer.label_attributes.setColor(self.color)
        QtGui.QDialog.reject(self)

    def chooseStyle(self):
        if QGis.QGIS_VERSION_INT < 10800:
            dlg = gui.QgsSymbolV2SelectorDialog(self.symbol,
                                                core.QgsStyleV2.defaultStyle())
        else:
            dlg = gui.QgsSymbolV2SelectorDialog(self.symbol,
                                                core.QgsStyleV2.defaultStyle(),
                                                None)
        dlg.show()
        dlg.exec_()

    def chooseFont(self):
        dlg = QtGui.QFontDialog()
        dlg.show()
        result = dlg.exec_()
        
        if result == 1:
            font = dlg.selectedFont()
            self.label_attributes.setFamily(font.family())
            self.label_attributes.setBold(font.bold())
            self.label_attributes.setItalic(font.italic())
            self.label_attributes.setUnderline(font.underline())
            self.label_attributes.setStrikeOut(font.strikeOut())
            self.label_attributes.setSize(font.pointSizeF(), core.QgsLabelAttributes.PointUnits)

    def chooseColour(self):
        dlg = QtGui.QColorDialog(self.label_attributes.color())
        dlg.setOptions(QtGui.QColorDialog.ShowAlphaChannel)
        dlg.show()
        result = dlg.exec_()
        
        if result == 1:
            self.label_attributes.setColor(dlg.selectedColor())