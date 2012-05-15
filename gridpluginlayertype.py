"""
/***************************************************************************
 GridPluginLayerType - registers itself to Quantum as a Plugin Layer
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

from qgis import core

from gridpluginlayer import GridPluginLayer

class GridPluginLayerType(core.QgsPluginLayerType):
    def __init__(self):
        core.QgsPluginLayerType.__init__(self, GridPluginLayer.LAYER_TYPE)
    
    def createLayer(self):
        return GridPluginLayer()

    def showLayerProperties(self, layer):
        layer.showDialog()
        return True
