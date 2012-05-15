"""
/***************************************************************************
 Grid Overlay
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
from qgis import core

from gridpropertiesdialog import GridPropertiesDialog
from gridpluginlayertype import GridPluginLayerType
from gridpluginlayer import GridPluginLayer
import resources

class GridOverlay:
    '''
    The main entry-point class.
    '''

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.action_newGrid = None

    def initGui(self):
        '''
        Sets this up as a Quantum GIS plug-in.
        '''
        # Create action_newGrid that will start plugin configuration
        self.action_newGrid = QtGui.QAction(
                        QtGui.QIcon(":/icons/icon.png"),
                        "Add Grid Overlay...", self.iface.mainWindow())
        
        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action_newGrid)
        self.iface.insertAddLayerAction(self.action_newGrid)

        self.action_newGrid.triggered.connect(self.run)
        
        core.QgsPluginLayerRegistry.instance().addPluginLayerType(GridPluginLayerType())
        
    def unload(self):
        '''
        Removes the plug-in menu item and icon.
        '''
        self.iface.removeAddLayerAction(self.action_newGrid)
        self.iface.removeToolBarIcon(self.action_newGrid)
        core.QgsPluginLayerRegistry.instance().removePluginLayerType(GridPluginLayer.LAYER_TYPE)

    def run(self):
        layer = GridPluginLayer()
        layer.showDialog()
        
        if layer.isValid():
            core.QgsMapLayerRegistry.instance().addMapLayer(layer)
