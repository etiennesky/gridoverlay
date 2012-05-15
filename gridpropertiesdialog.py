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
from ui_grid_properties import Ui_GridProperties

class GridPropertiesDialog(QtGui.QDialog):

    def __init__(self, symbol):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_GridProperties()
        self.ui.setupUi(self)
        validator = QtGui.QDoubleValidator(-10000000.0, 10000000.0, 6, None)
        self.ui.editOriginX.setValidator(validator)
        self.ui.editOriginY.setValidator(validator)
        self.symbol = symbol
        self.ui.btnStyle.clicked.connect(self.chooseStyle)
    
    def chooseStyle(self):
        dlg = gui.QgsSymbolV2SelectorDialog(self.symbol,
                                            core.QgsStyleV2.defaultStyle(),
                                            None, False)
        dlg.show()
        dlg.exec_()
