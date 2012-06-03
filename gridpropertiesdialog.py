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
        self.ui.comboLabelType.currentIndexChanged.connect(self.disableDegreeFields)

        self.symbol = gridlayer.symbol.clone()
        self.label_attributes = core.QgsLabelAttributes()
        
        # Store attributes in case the user changes font attributes but cancels the dialog box.
        self.label_attributes.setFamily(gridlayer.label.labelAttributes().family())
        self.label_attributes.setBold(gridlayer.label.labelAttributes().bold())
        self.label_attributes.setItalic(gridlayer.label.labelAttributes().italic())
        self.label_attributes.setUnderline(gridlayer.label.labelAttributes().underline())
        self.label_attributes.setStrikeOut(gridlayer.label.labelAttributes().strikeOut())
        self.label_attributes.setSize(gridlayer.label.labelAttributes().size(), core.QgsLabelAttributes.PointUnits)
        self.label_attributes.setColor(gridlayer.label.labelAttributes().color())

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
        self.ui.comboLabelType.setCurrentIndex(gridlayer.label_type)
        self.ui.spinPrecision.setValue(gridlayer.label_precision)
        self.ui.comboOrientation.setCurrentIndex(gridlayer.label_orientation)
        
        self.ui.comboLabelFormat.setCurrentIndex(gridlayer.label_format)
        self.ui.checkHemisphere.setChecked(gridlayer.label_hemisphere)
        self.ui.checkLeadingZeros.setChecked(gridlayer.label_leading_zeros)
        self.ui.checkDegreesDiff.setChecked(gridlayer.label_degrees_diff)
        self.ui.spinXOffsetHorizontal.setValue(gridlayer.label_xoff_horizontal)
        self.ui.spinXOffsetVertical.setValue(gridlayer.label_xoff_vertical)
        self.ui.spinYOffsetHorizontal.setValue(gridlayer.label_yoff_horizontal)
        self.ui.spinYOffsetVertical.setValue(gridlayer.label_yoff_vertical)
        
        self.disableDegreeFields(0)
        
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
        self.gridlayer.label_type = self.ui.comboLabelType.currentIndex()
        self.gridlayer.label_precision = self.ui.spinPrecision.value()
        self.gridlayer.label_orientation = self.ui.comboOrientation.currentIndex()
        self.gridlayer.symbol = self.symbol.clone()

        self.gridlayer.label.labelAttributes().setFamily(self.label_attributes.family())
        self.gridlayer.label.labelAttributes().setBold(self.label_attributes.bold())
        self.gridlayer.label.labelAttributes().setItalic(self.label_attributes.italic())
        self.gridlayer.label.labelAttributes().setUnderline(self.label_attributes.underline())
        self.gridlayer.label.labelAttributes().setStrikeOut(self.label_attributes.strikeOut())
        self.gridlayer.label.labelAttributes().setSize(self.label_attributes.size(), core.QgsLabelAttributes.PointUnits)
        self.gridlayer.label.labelAttributes().setColor(self.label_attributes.color())

        if self.gridlayer.label_type == 0 or self.gridlayer.label_type == 2:
            self.gridlayer.label.setLabelField(core.QgsLabel.Text, 2)
        elif self.gridlayer.label_type == 1:
            self.gridlayer.label.setLabelField(core.QgsLabel.Text, 0)
        
        self.gridlayer.label.setLabelField(core.QgsLabel.Angle, 1)
        self.gridlayer.label.setLabelField(core.QgsLabel.Alignment, 3)
        self.gridlayer.label.setLabelField(core.QgsLabel.XOffset, 4)
        self.gridlayer.label.setLabelField(core.QgsLabel.YOffset, 5)

        self.gridlayer.label_format = self.ui.comboLabelFormat.currentIndex()
        self.gridlayer.label_hemisphere = self.ui.checkHemisphere.isChecked()
        self.gridlayer.label_leading_zeros = self.ui.checkLeadingZeros.isChecked()
        self.gridlayer.label_degrees_diff = self.ui.checkDegreesDiff.isChecked()
        self.gridlayer.label_xoff_horizontal = self.ui.spinXOffsetHorizontal.value()
        self.gridlayer.label_xoff_vertical = self.ui.spinXOffsetVertical.value()
        self.gridlayer.label_yoff_horizontal = self.ui.spinYOffsetHorizontal.value()
        self.gridlayer.label_yoff_vertical = self.ui.spinYOffsetVertical.value()
        
        QtGui.QDialog.accept(self)
        
    def reject(self):
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

    def disableDegreeFields(self, index):
        if index == 1 or index == 2:
            self.ui.checkDegreesDiff.setEnabled(False)
            self.ui.comboLabelFormat.setEnabled(False)
            self.ui.spinPrecision.setEnabled(False)
            self.ui.checkHemisphere.setEnabled(False)
            self.ui.checkLeadingZeros.setEnabled(False)
        elif not self.gridlayer.crs().geographicFlag():
            self.ui.checkDegreesDiff.setEnabled(False)
            self.ui.comboLabelFormat.setEnabled(False)
            self.ui.spinPrecision.setEnabled(True)
            self.ui.checkHemisphere.setEnabled(False)
            self.ui.checkLeadingZeros.setEnabled(False)
        else:
            self.ui.checkDegreesDiff.setEnabled(True)
            self.ui.comboLabelFormat.setEnabled(True)
            self.ui.spinPrecision.setEnabled(True)
            self.ui.checkHemisphere.setEnabled(True)
            self.ui.checkLeadingZeros.setEnabled(True)
