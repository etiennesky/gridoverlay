"""
/***************************************************************************
 GridPluginLayer - manages and draws an overlay grid.
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

import math

from PyQt4 import QtCore, QtGui
from qgis import core

from gridpropertiesdialog import GridPropertiesDialog

class GridPluginLayer(core.QgsPluginLayer):
    LAYER_TYPE = 'grid'

    def __init__(self):
        core.QgsPluginLayer.__init__(self, GridPluginLayer.LAYER_TYPE,
                                     'Grid overlay')
        self.setValid(False)

        proj = core.QgsProject.instance()
        # Default CRS: 3452 == EPSG:4326
        srid = proj.readNumEntry('SpatialRefSys', '/ProjectCRSID', 3452)[0]
        # It's OK to use the internal ID because it's a one-time
        # initialisation straight from the current project.
        crs = core.QgsCoordinateReferenceSystem(srid, core.QgsCoordinateReferenceSystem.InternalCrsId)
        self.setCrs(crs)
        
        props = {'width':'0', 'color':'0,255,0'}
        self.symbol = core.QgsLineSymbolV2.createSimple(props)

        self.origin = core.QgsPoint(0.0, 0.0)
        self.numCellsX = 1
        self.numCellsY = 1
        self.gridOffsetX = 0
        self.gridOffsetY = 0
        self.cellSizeX = 10.0
        self.cellSizeY = 10.0
        self.baselineAngle = 0.0
        self.grid = []
        self.generateGrid()

    def draw(self, renderContext):
        mapToPixel = renderContext.mapToPixel()

        proj = core.QgsProject.instance()
        # Default CRS: 3452 == EPSG:4326
        srid = proj.readNumEntry('SpatialRefSys', '/ProjectCRSID', 3452)[0]
        # It's OK to use the internal ID because it's a one-time
        # initialisation straight from the current project.
        crs = core.QgsCoordinateReferenceSystem(srid, core.QgsCoordinateReferenceSystem.InternalCrsId)
        
        xform = core.QgsCoordinateTransform(self.crs(), crs)

        self.symbol.startRender(renderContext)

        for line in self.grid:
            polyline = QtGui.QPolygonF()

            for vertex in line:
                end = mapToPixel.transform(xform.transform(vertex))
                polyline.append(QtCore.QPointF(end.x(), end.y()))

            self.symbol.renderPolyline(polyline, renderContext)

        self.symbol.stopRender(renderContext)

        return True

    def generateGrid(self):
        self.grid = []

        # Angle of the baseline, clockwise.
        angleSin = math.sin(math.radians(360.0 - self.baselineAngle))
        angleCos = math.cos(math.radians(360.0 - self.baselineAngle))

        # Generate horizontal lines as a piecewise curve.
        for h in xrange(self.gridOffsetY, self.numCellsY + self.gridOffsetY + 1):
            line = []
            veca = core.QgsPoint(self.cellSizeY * -angleSin * h, self.cellSizeY * angleCos * h)

            for l in xrange(self.gridOffsetX, self.numCellsX + self.gridOffsetX + 1):
                vecb = core.QgsPoint(self.cellSizeX * angleCos * l, self.cellSizeX * angleSin * l)
                line.append(core.QgsPoint(self.origin.x() + veca.x() + vecb.x(), self.origin.y() + veca.y() + vecb.y()))

            self.grid.append(line)

        # Generate vertical lines as a piecewise curve.
        for v in xrange(self.gridOffsetX, self.numCellsX + self.gridOffsetX + 1):
            line = []
            veca = core.QgsPoint(self.cellSizeX * angleCos * v, self.cellSizeX * angleSin * v)

            for l in xrange(self.gridOffsetY, self.numCellsY + self.gridOffsetY + 1):
                vecb = core.QgsPoint(self.cellSizeY * -angleSin * l, self.cellSizeY * angleCos * l)
                line.append(core.QgsPoint(self.origin.x() + veca.x() + vecb.x(), self.origin.y() + veca.y() + vecb.y()))

            self.grid.append(line)
        
        x = []
        y = []
        x.append((self.gridOffsetX * self.cellSizeX * angleCos) +
                 (self.gridOffsetY * self.cellSizeY * -angleSin))
        x.append(((self.numCellsX + self.gridOffsetX) * self.cellSizeX * angleCos) +
                 (self.gridOffsetY * self.cellSizeY * -angleSin))
        x.append((self.gridOffsetX * self.cellSizeX * angleCos) +
                 (self.gridOffsetY * self.cellSizeY * -angleSin))
        x.append(((self.numCellsX + self.gridOffsetX) * self.cellSizeX * angleCos) +
                 ((self.numCellsY + self.gridOffsetY) * self.cellSizeY * -angleSin))

        y.append((self.gridOffsetX * self.cellSizeX * angleSin) +
                 (self.gridOffsetY * self.cellSizeY * angleCos))
        y.append((self.gridOffsetX * self.cellSizeX * angleSin) +
                 ((self.numCellsY + self.gridOffsetY) * self.cellSizeY * angleCos))
        y.append(((self.numCellsX + self.gridOffsetX) * self.cellSizeX * angleSin) +
                 (self.gridOffsetY * self.cellSizeY * angleCos))
        y.append(((self.numCellsX + self.gridOffsetX) * self.cellSizeX * angleSin) +
                 ((self.numCellsY + self.gridOffsetY) * self.cellSizeY * angleCos))
                 
        self.setExtent(core.QgsRectangle(min(x) + self.origin.x(), min(y) + self.origin.y(), max(x) + self.origin.x(), max(y) + self.origin.y()))
        

    def readXml(self, node):
        org_x = float(node.toElement().attribute('origin_x', '0.0'))
        org_y = float(node.toElement().attribute('origin_y', '0.0'))
        self.origin = core.QgsPoint(org_x, org_y)
        self.numCellsX = int(node.toElement().attribute('num_cells_x', '1'))
        self.numCellsY = int(node.toElement().attribute('num_cells_y', '1'))
        self.gridOffsetX = int(node.toElement().attribute('grid_offset_x', '0'))
        self.gridOffsetY = int(node.toElement().attribute('grid_offset_y', '0'))
        self.cellSizeX = float(node.toElement().attribute('cell_size_x', '10.0'))
        self.cellSizeY = float(node.toElement().attribute('cell_size_y', '10.0'))
        self.baselineAngle = float(node.toElement().attribute('baseline_angle', '0.0'))

        symbolElement = node.firstChildElement('symbol')
        if symbolElement is not None and symbolElement.attribute('name') == 'grid_lines':
          self.symbol = core.QgsSymbolLayerV2Utils.loadSymbol(symbolElement)

        self.generateGrid()
        return True

    def writeXml(self, node, doc):
        element = node.toElement()
        element.setAttribute("type", "plugin")
        element.setAttribute("name", GridPluginLayer.LAYER_TYPE);
        # Custom properties.
        element.setAttribute("origin_x", str(self.origin.x()))
        element.setAttribute("origin_y", str(self.origin.y()))
        element.setAttribute("num_cells_x", str(self.numCellsX))
        element.setAttribute("num_cells_y", str(self.numCellsY))
        element.setAttribute("grid_offset_x", str(self.gridOffsetX))
        element.setAttribute("grid_offset_y", str(self.gridOffsetY))
        element.setAttribute("cell_size_x", str(self.cellSizeX))
        element.setAttribute("cell_size_y", str(self.cellSizeY))
        element.setAttribute("baseline_angle", str(self.baselineAngle))
        symbolElement = core.QgsSymbolLayerV2Utils.saveSymbol('grid_lines', self.symbol, doc, None)
        node.appendChild(symbolElement)

        return True

    def showDialog(self):
        dlg = GridPropertiesDialog(self.symbol)
        dlg.ui.editOriginX.setText(str(self.origin.x()))
        dlg.ui.editOriginY.setText(str(self.origin.y()))
        dlg.ui.spinCountX.setValue(self.numCellsX)
        dlg.ui.spinCountY.setValue(self.numCellsY)
        dlg.ui.spinOffsetX.setValue(self.gridOffsetX)
        dlg.ui.spinOffsetY.setValue(self.gridOffsetY)
        dlg.ui.spinCellSizeX.setValue(self.cellSizeX)
        dlg.ui.spinCellSizeY.setValue(self.cellSizeY)
        dlg.ui.spinAngle.setValue(self.baselineAngle)
        dlg.show()
        result = dlg.exec_()
        
        if result == 1:
            self.setValid(True)
            self.origin = core.QgsPoint(float(dlg.ui.editOriginX.text()), float(dlg.ui.editOriginY.text()))
            self.numCellsX = dlg.ui.spinCountX.value()
            self.numCellsY = dlg.ui.spinCountY.value()
            self.gridOffsetX = dlg.ui.spinOffsetX.value()
            self.gridOffsetY = dlg.ui.spinOffsetY.value()
            self.cellSizeX = dlg.ui.spinCellSizeX.value()
            self.cellSizeY = dlg.ui.spinCellSizeY.value()
            self.baselineAngle = dlg.ui.spinAngle.value()

            self.generateGrid()
            self.setCacheImage(None)
            self.emit(QtCore.SIGNAL('repaintRequested()'))
