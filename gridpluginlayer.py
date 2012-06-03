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

from PyQt4 import QtCore, QtGui, QtXml
from qgis import core
from qgis.core import QGis
from util import *

from gridpropertiesdialog import GridPropertiesDialog


class GridPluginLayer(core.QgsPluginLayer):
    LAYER_TYPE = 'grid'

    _featuremap = {
        0: core.QgsField('cell_num', QtCore.QVariant.Int, 'integer', 8),
        1: core.QgsField('angle', QtCore.QVariant.Double, 'double', 8, 4),
        2: core.QgsField('ordinate', QtCore.QVariant.String, 'string', 32),
        3: core.QgsField('alignment', QtCore.QVariant.String, 'string', 8),
        4: core.QgsField('offset_x', QtCore.QVariant.Double, 'double', 8, 4),
        5: core.QgsField('offset_y', QtCore.QVariant.Double, 'double', 8, 4)
       }

    def __init__(self):
        core.QgsPluginLayer.__init__(self, GridPluginLayer.LAYER_TYPE,
                                     'Grid overlay')
        self.setValid(True)

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
        self.label = core.QgsLabel(GridPluginLayer._featuremap)
        self.label_features = []
        self.draw_labels = False
        self.label_type = 0
        self.label_precision = 0
        self.label_orientation = 0
        self.label_format = 0
        self.label_hemisphere = True
        self.label_leading_zeros = True
        self.label_degrees_diff = False
        self.label_xoff_horizontal = 0.0
        self.label_xoff_vertical = 0.0
        self.label_yoff_horizontal = 0.0
        self.label_yoff_vertical = 0.0

        proj = core.QgsProject.instance()
        # Default CRS: 3452 == EPSG:4326
        srid = proj.readNumEntry('SpatialRefSys', '/ProjectCRSID', 3452)[0]
        # It's OK to use the internal ID because it's a one-time
        # initialisation straight from the current project.
        crs = core.QgsCoordinateReferenceSystem(srid, core.QgsCoordinateReferenceSystem.InternalCrsId)
        self.setCrs(crs)

    def draw(self, renderContext):
        mapToPixel = renderContext.mapToPixel()

        proj = core.QgsProject.instance()
        # Default CRS: 3452 == EPSG:4326
        srid = proj.readNumEntry('SpatialRefSys', '/ProjectCRSID', 3452)[0]
        crs = core.QgsCoordinateReferenceSystem(srid, core.QgsCoordinateReferenceSystem.InternalCrsId)

        xform = core.QgsCoordinateTransform(self.crs(), crs)

        self.symbol.startRender(renderContext)

        for line in self.grid:
            polyline = QtGui.QPolygonF()

            for vertex in line:
                end = mapToPixel.transform(xform.transform(vertex))
                polyline.append(QtCore.QPointF(end.x(), end.y()))

                if QGis.QGIS_VERSION_INT < 10800:
                    self.symbol.renderPolyline(polyline, renderContext)
                else:
                    self.symbol.renderPolyline(polyline, None, renderContext)

        self.symbol.stopRender(renderContext)
        return True

    def drawLabels(self, renderContext):
        if self.draw_labels:
            for feat in self.label_features:
                self.label.renderLabel(renderContext, feat, False)

    def generateGrid(self):
        self.grid = []

        baseVec = QgsVector(1.0, 0.0).rotateBy(math.radians(360.0 - self.baselineAngle)) * self.cellSizeX
        perpVec = baseVec.perpVector().normal() * self.cellSizeY

        # Generate horizontal lines as a piecewise curve.
        for h in xrange(self.gridOffsetY, self.numCellsY + self.gridOffsetY + 1):
            line = []

            for l in xrange(self.gridOffsetX, self.numCellsX + self.gridOffsetX + 1):
                bar = (perpVec * h) + (baseVec * l)
                line.append(core.QgsPoint(self.origin.x() + bar.x, self.origin.y() + bar.y))

            self.grid.append(line)

        # Generate vertical lines as a piecewise curve.
        for v in xrange(self.gridOffsetX, self.numCellsX + self.gridOffsetX + 1):
            line = []

            for l in xrange(self.gridOffsetY, self.numCellsY + self.gridOffsetY + 1):
                bar = (baseVec * v) + (perpVec * l)
                line.append(core.QgsPoint(self.origin.x() + bar.x, self.origin.y() + bar.y))

            self.grid.append(line)

        self.generateLabels()
        
        lower_left = (baseVec * self.gridOffsetX) + (perpVec * self.gridOffsetY)
        lower_right = lower_left + (baseVec * self.numCellsX)
        upper_left = lower_left + (perpVec * self.numCellsY)
        upper_right = lower_right + (perpVec * self.numCellsY)

        minx = min(lower_left.x, min(lower_right.x, min(upper_left.x, upper_right.x)))
        miny = min(lower_left.y, min(lower_right.y, min(upper_left.y, upper_right.y)))
        maxx = max(lower_left.x, max(lower_right.x, max(upper_left.x, upper_right.x)))
        maxy = max(lower_left.y, max(lower_right.y, max(upper_left.y, upper_right.y)))

        self.setExtent(core.QgsRectangle(minx + self.origin.x(), miny + self.origin.y(), maxx + self.origin.x(), maxy + self.origin.y()))
        
    def generateLabels(self):
        self.label_features = []
        baseVec = QgsVector(1.0, 0.0).rotateBy(math.radians(360.0 - self.baselineAngle)) * self.cellSizeX
        halfBaseVec = baseVec / 2.0
        perpVec = baseVec.perpVector().normal() * self.cellSizeY
        halfPerpVec = perpVec / 2.0

        # CRS coordinates.
        if self.label_type == 0:
            for cell in xrange(0, len(self.grid[0])):
                feat = core.QgsFeature()
                feat.addAttribute(0, cell)
                self._setHorizontalLabelAttributes(feat, math.degrees(baseVec.angle()))

                labelvalue = self.grid[0][cell].x()
                if self.crs().geographicFlag():
                    showDegrees = True
                    
                    if self.label_degrees_diff and cell > 0 and cell < len(self.grid[0]) - 1:
                        if labelvalue < 0.0:
                            lastLabelValue = self.grid[0][cell + 1].x()
                        else:
                            lastLabelValue = self.grid[0][cell - 1].x()
                        
                        if (abs(lastLabelValue) // 1 == abs(labelvalue) // 1) and ((lastLabelValue < 0.0) == (labelvalue < 0.0)):
                            showDegrees = False
                    
                    labeltext = self.formatLabel(labelvalue, '%e', showDegrees)
                else:
                    labeltext = '{0:0.{precision}f}'.format(labelvalue, precision=self.label_precision)
                    
                feat.addAttribute(2, labeltext)
                feat.setGeometry(core.QgsGeometry().fromPoint(self.grid[0][cell]))
                self.label_features.append(feat)
            
            for cell in xrange(0, len(self.grid[self.numCellsY + 1])):
                feat = core.QgsFeature()
                feat.addAttribute(0, cell)
                self._setVerticalLabelAttributes(feat, math.degrees(baseVec.angle()))

                labelvalue = self.grid[self.numCellsY + 1][cell].y()
                if self.crs().geographicFlag():
                    showDegrees = True
                    
                    if self.label_degrees_diff and cell > 0 and cell < len(self.grid[self.numCellsY + 1]) - 1:
                        if labelvalue < 0.0:
                            lastLabelValue = self.grid[self.numCellsY + 1][cell + 1].y()
                        else:
                            lastLabelValue = self.grid[self.numCellsY + 1][cell - 1].y()
                        
                        if (abs(lastLabelValue) // 1 == abs(labelvalue) // 1) and ((lastLabelValue < 0.0) == (labelvalue < 0.0)):
                            showDegrees = False
                    
                    labeltext = self.formatLabel(labelvalue, '%n', showDegrees)
                else:
                    labeltext = '{0:0.{precision}f}'.format(labelvalue, precision=self.label_precision)

                feat.addAttribute(2, labeltext)
                feat.setGeometry(core.QgsGeometry().fromPoint(self.grid[self.numCellsY + 1][cell]))
                self.label_features.append(feat)

        elif self.label_type == 1:
            # Cell coordinates.
            for cell in xrange(0, len(self.grid[0]) - 1):
                feat = core.QgsFeature()
                feat.addAttribute(0, cell)
                self._setHorizontalLabelAttributes(feat, math.degrees(baseVec.angle()))
                
                # Labels representing CRS coordinates are placed in the centre of the cell.
                p = core.QgsPoint(self.grid[0][cell].x() + halfBaseVec.x, self.grid[0][cell].y() + halfBaseVec.y)
                feat.setGeometry(core.QgsGeometry().fromPoint(p))
            
                self.label_features.append(feat)
            
            for cell in xrange(0, len(self.grid[self.numCellsY + 1]) - 1):
                feat = core.QgsFeature()
                feat.addAttribute(0, cell)
                self._setVerticalLabelAttributes(feat, math.degrees(baseVec.angle()))
                
                p = core.QgsPoint(self.grid[self.numCellsY + 1][cell].x() + halfPerpVec.x, self.grid[self.numCellsY + 1][cell].y() + halfPerpVec.y)
                feat.setGeometry(core.QgsGeometry().fromPoint(p))
                
                self.label_features.append(feat)

        elif self.label_type == 2:
            # Grid reference - cell.
            for celly in xrange(0, len(self.grid[self.numCellsY + 1]) - 1):
                for cellx in xrange(0, len(self.grid[0]) - 1):
                    feat = core.QgsFeature()
                    feat.addAttribute(0, (celly * len(self.grid[0])) + cellx)
                    self._setHorizontalLabelAttributes(feat, math.degrees(baseVec.angle()))

                    labeltext = u'{0} {1}'.format(cellx, celly)
                    feat.addAttribute(2, labeltext)
                    
                    # Labels representing CRS coordinates are placed in the centre of the cell.
                    px = core.QgsPoint(self.grid[0][cellx].x() + halfBaseVec.x, self.grid[0][cellx].y() + halfBaseVec.y)
                    py = core.QgsPoint(self.grid[self.numCellsY + 1][celly].x() + halfPerpVec.x, self.grid[self.numCellsY + 1][celly].y() + halfPerpVec.y)
                    pp = core.QgsPoint(px.x() + py.x(), px.y() + py.y())
                    feat.setGeometry(core.QgsGeometry().fromPoint(pp))
                
                    self.label_features.append(feat)

    def _setHorizontalLabelAttributes(self, feature, angle):
        if self.label_orientation == 0 or self.label_orientation == 3:
            feature.addAttribute(1, angle)
            feature.addAttribute(3, 'top')
            feature.addAttribute(4, self.label_xoff_horizontal)
            feature.addAttribute(5, self.label_xoff_vertical)
        else:
            feature.addAttribute(1, angle + 90.0)
            feature.addAttribute(3, 'right')
            feature.addAttribute(4, self.label_xoff_vertical)
            feature.addAttribute(5, self.label_xoff_horizontal)

    def _setVerticalLabelAttributes(self, feature, angle):
        if self.label_orientation == 0 or self.label_orientation == 2:
            feature.addAttribute(1, angle)
            feature.addAttribute(3, 'right')
            feature.addAttribute(4, self.label_yoff_horizontal)
            feature.addAttribute(5, self.label_yoff_vertical)
        else:
            feature.addAttribute(1, angle + 90.0)
            feature.addAttribute(3, 'bottom')
            feature.addAttribute(4, self.label_yoff_vertical)
            feature.addAttribute(5, self.label_yoff_horizontal)

    def formatLabel(self, angleValue, hemisphere, showDegrees):
        angle = Angle(angleValue)
        labeltext = ''
        
        if showDegrees:
            sign, hemisphere = ('', hemisphere) if self.label_hemisphere else ('%g', '')
        else:
            sign = ''
            hemisphere = ''
            
        pad = '0' if self.label_leading_zeros else ''

        if self.label_format == 0:
            # Decimal degrees.
            decimal = '.%{0}d'.format(self.label_precision) if self.label_precision > 0 else ''
            if showDegrees:
                labeltext = u'{0:{sign}%{pad}D\u00b0{decimal} {hemisphere}}'.format(angle, decimal=decimal, sign=sign, hemisphere=hemisphere, pad=pad)
            else:
                labeltext = u'{0:{sign}{decimal} {hemisphere}}'.format(angle, decimal=decimal, sign=sign, hemisphere=hemisphere)
            
        elif self.label_format == 1:
            # Degrees, decimal minutes.
            decimal = '.%{0}m'.format(self.label_precision) if self.label_precision > 0 else ''
            if showDegrees:
                labeltext = u'{0:{sign}%{pad}D\u00b0 %{pad}M\'{decimal} {hemisphere}}'.format(angle, decimal=decimal, sign=sign, hemisphere=hemisphere, pad=pad)
            else:
                labeltext = u'{0:{sign}%{pad}M\'{decimal} {hemisphere}}'.format(angle, decimal=decimal, sign=sign, hemisphere=hemisphere, pad=pad)
            
        elif self.label_format == 2:
            # Degrees, minutes, decimal seconds.
            decimal = '.%{0}s'.format(self.label_precision) if self.label_precision > 0 else ''
            if showDegrees:
                labeltext = u'{0:{sign}%{pad}D\u00b0 %{pad}M\' %{pad}S"{decimal} {hemisphere}}'.format(angle, decimal=decimal, sign=sign, hemisphere=hemisphere, pad=pad)
            else:
                labeltext = u'{0:{sign}%{pad}M\' %{pad}S"{decimal} {hemisphere}}'.format(angle, decimal=decimal, sign=sign, hemisphere=hemisphere, pad=pad)
        
        return labeltext

    def setCrs(self, crs):
        core.QgsPluginLayer.setCrs(self, crs)
        self.generateGrid()
        self.setCacheImage(None)
        self.emit(QtCore.SIGNAL('repaintRequested()'))

    def readXml(self, node):
        element = node.toElement()
        
        org_x = float(element.attribute('origin_x', '0.0'))
        org_y = float(element.attribute('origin_y', '0.0'))
        self.origin = core.QgsPoint(org_x, org_y)
        self.numCellsX = int(element.attribute('num_cells_x', '1'))
        self.numCellsY = int(element.attribute('num_cells_y', '1'))
        self.gridOffsetX = int(element.attribute('grid_offset_x', '0'))
        self.gridOffsetY = int(element.attribute('grid_offset_y', '0'))
        self.cellSizeX = float(element.attribute('cell_size_x', '10.0'))
        self.cellSizeY = float(element.attribute('cell_size_y', '10.0'))
        self.baselineAngle = float(element.attribute('baseline_angle', '0.0'))
        
        labelElement = node.firstChildElement('label')
        if labelElement is not None:
            self.draw_labels = bool(labelElement.attribute('draw_labels', '0'))
            self.label_type = int(labelElement.attribute('type', '0'))
            self.label_precision = int(labelElement.attribute('precision', '0'))
            self.label_orientation = int(labelElement.attribute('orientation', '0'))
            self.label_format = int(labelElement.attribute('format', '0'))
            self.label_hemisphere = bool(labelElement.attribute('hemisphere', 'true'))
            self.label_xoff_horizontal = float(labelElement.attribute('xoff_horizontal', '0.0'))
            self.label_xoff_vertical = float(labelElement.attribute('xoff_vertical', '0.0'))
            self.label_yoff_horizontal = float(labelElement.attribute('yoff_horizontal', '0.0'))
            self.label_yoff_vertical = float(labelElement.attribute('yoff_vertical', '0.0'))
            self.label_leading_zeros = bool(labelElement.attribute('leading_zeros', 'true'))
            self.label_degrees_diff = bool(labelElement.attribute('degrees_diff', 'false'))
            attributesElement = labelElement.firstChildElement('labelattributes')
            if attributesElement is not None:
                self.label.readXML(attributesElement)
        
        self.generateGrid()
        self.readSymbology(node, None)

        return True

    def writeXml(self, node, doc):
        element = node.toElement()
        element.setAttribute('type', 'plugin')
        element.setAttribute('name', GridPluginLayer.LAYER_TYPE);
        # Custom properties.
        element.setAttribute('origin_x', str(self.origin.x()))
        element.setAttribute('origin_y', str(self.origin.y()))
        element.setAttribute('num_cells_x', str(self.numCellsX))
        element.setAttribute('num_cells_y', str(self.numCellsY))
        element.setAttribute('grid_offset_x', str(self.gridOffsetX))
        element.setAttribute('grid_offset_y', str(self.gridOffsetY))
        element.setAttribute('cell_size_x', str(self.cellSizeX))
        element.setAttribute('cell_size_y', str(self.cellSizeY))
        element.setAttribute('baseline_angle', str(self.baselineAngle))

        labelElement = doc.createElement('label')
        labelElement.setAttribute('draw_labels', str(self.draw_labels))
        labelElement.setAttribute('type', str(self.label_type))
        labelElement.setAttribute('precision', str(self.label_precision))
        labelElement.setAttribute('orientation', str(self.label_orientation))
        labelElement.setAttribute('format', str(self.label_format))
        labelElement.setAttribute('hemisphere', str(self.label_hemisphere))
        labelElement.setAttribute('xoff_horizontal', str(self.label_xoff_horizontal))
        labelElement.setAttribute('xoff_vertical', str(self.label_xoff_vertical))
        labelElement.setAttribute('yoff_horizontal', str(self.label_yoff_horizontal))
        labelElement.setAttribute('yoff_vertical', str(self.label_yoff_vertical))
        labelElement.setAttribute('leading_zeros', str(self.label_leading_zeros))
        labelElement.setAttribute('degrees_diff', str(self.label_degrees_diff))
        self.label.writeXML(labelElement, doc)
        
        node.appendChild(labelElement)
        
        self.writeSymbology(node, doc, None)

        return True

    def readSymbology(self, node, errorMessage):
        symbolElement = node.firstChildElement('symbol')

        if symbolElement is not None and symbolElement.attribute('name') == 'grid_lines':
            self.symbol = core.QgsSymbolLayerV2Utils.loadSymbol(symbolElement)
            self.setCacheImage(None)
            self.emit(QtCore.SIGNAL('repaintRequested()'))
            return True
        else:
            return False

    def writeSymbology(self, node, doc, errorMessage):
        symbolElement = core.QgsSymbolLayerV2Utils.saveSymbol('grid_lines', self.symbol, doc, None)
        node.appendChild(symbolElement)
        return True

    def showDialog(self):
        dlg = GridPropertiesDialog(self)

        dlg.show()
        result = dlg.exec_()

        if result == 1:
            self.generateGrid()
            self.setValid(True)
            self.setCacheImage(None)
            self.emit(QtCore.SIGNAL('repaintRequested()'))
        else:
            self.setValid(False)
