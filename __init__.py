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

# This script initializes the plugin, making it known to QGIS.

version_major = 0
version_minor = 1
version_revision = 1

def name():
    return "Grid Overlay"
def description():
    return "Overlays a user-definable grid on the map."
def version():
    return "Version %d.%d.%d" % (version_major, version_minor, version_revision)
def icon():
    return "icon.png"
def qgisMinimumVersion():
    return "1.7"
def category():
    return "Layers"
def classFactory(iface):
    from gridoverlay import GridOverlay
    return GridOverlay(iface)
