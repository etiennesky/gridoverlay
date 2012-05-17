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
from qgis.core import QGis

from gridpropertiesdialog import GridPropertiesDialog

class QgsVector(object):
  """2D vector class with (almost) the same signature as the QGIS one."""
  def __init__(self, x=0.0, y=0.0):
    self.x = x
    self.y = y

  def __neg__(self):
    return QgsVector(-self.x, -self.y)

  def __mul__(self, scalar):
    return QgsVector(self.x * scalar, self.y * scalar)

  def __div__(self, scalar):
    return QgsVector(self.x, self.y) * (1.0 / scalar)

  def __add__(self, v):
    return QgsVector(self.x + v.x, self.y + v.y)

  # Vector dot product.
  def __and__(self, v):
    return self.x * v.x + self.y * v.y

  def length(self):
    return math.sqrt(self.x * self.x + self.y * self.y)

  def perpVector(self):
    return QgsVector(-self.y, self.x)

  def angle(self, v=None):
    if v is None:
      ang = math.atan2(self.y, self.x)
      return ang + 2.0 * math.pi if ang < 0.0 else ang
    else:
      return v.angle() - self.angle()

  def rotateBy(self, rot):
    ang = math.atan2(self.y, self.x) + rot
    length = self.length()
    return QgsVector(length * math.cos(ang), length * math.sin(ang))

  def normal(self):
    if self.length() == 0.0:
      raise

    return QgsVector(self.x, self.y) / self.length()

class GridPluginLayer(core.QgsPluginLayer):
    LAYER_TYPE = 'grid'

    _fmap = {0: core.QgsField('cell_num', QtCore.QVariant.Int, 'integer', 8),
            1: core.QgsField('angle', QtCore.QVariant.Double, 'double', 8, 4),
            2: core.QgsField('ordinate', QtCore.QVariant.Double, 'double', 8, 4)
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
        self.label_features = []
        self.label_attributes = core.QgsLabelAttributes()
        self.draw_labels = False
        self.label_type = 0
        self.label_precision = 0
        self.label_orientation = 0

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
              label = core.QgsLabel(GridPluginLayer._fmap)
              label.labelAttributes().setFamily(self.label_attributes.family())
              label.labelAttributes().setBold(self.label_attributes.bold())
              label.labelAttributes().setItalic(self.label_attributes.italic())
              label.labelAttributes().setUnderline(self.label_attributes.underline())
              label.labelAttributes().setStrikeOut(self.label_attributes.strikeOut())
              label.labelAttributes().setSize(self.label_attributes.size(), core.QgsLabelAttributes.PointUnits)
              label.labelAttributes().setColor(self.label_attributes.color())
              label.setLabelField(core.QgsLabel.Text, 2)
              label.setLabelField(core.QgsLabel.Angle, 1)
              label.renderLabel(renderContext, feat, False)

    def generateGrid(self):
        self.grid = []
        self.label_features = []

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

        for cell in xrange(0, len(self.grid[0])):
          feat = core.QgsFeature()
          feat.addAttribute(0, cell)
          feat.addAttribute(1, math.degrees(baseVec.angle()))
          feat.addAttribute(2, self.grid[0][cell].x())
          feat.setGeometry(core.QgsGeometry().fromPoint(self.grid[0][cell]))
          self.label_features.append(feat)

        for cell in xrange(0, len(self.grid[self.numCellsY + 1])):
          feat = core.QgsFeature()
          feat.addAttribute(0, cell)
          feat.addAttribute(1, math.degrees(baseVec.angle()))
          feat.addAttribute(2, self.grid[self.numCellsY + 1][cell].y())
          feat.setGeometry(core.QgsGeometry().fromPoint(self.grid[self.numCellsY + 1][cell]))
          self.label_features.append(feat)

        lower_left = baseVec * self.gridOffsetX
        lower_right = baseVec * (self.numCellsX + self.gridOffsetX)
        upper_left = perpVec * (self.numCellsY + self.gridOffsetY)
        upper_right = lower_right + upper_left

        minx = min(lower_left.x, min(lower_right.x, min(upper_left.x, upper_right.x)))
        miny = min(lower_left.y, min(lower_right.y, min(upper_left.y, upper_right.y)))
        maxx = max(lower_left.x, max(lower_right.x, max(upper_left.x, upper_right.x)))
        maxy = max(lower_left.y, max(lower_right.y, max(upper_left.y, upper_right.y)))

        self.setExtent(core.QgsRectangle(minx + self.origin.x(), miny + self.origin.y(), maxx + self.origin.x(), maxy + self.origin.y()))

    def setCrs(self, crs):
        core.QgsPluginLayer.setCrs(self, crs)
        self.generateGrid()
        self.setCacheImage(None)
        self.emit(QtCore.SIGNAL('repaintRequested()'))

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
        self.generateGrid()
        self.readSymbology(node, None)

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
