# Makefile for Grid Overlay plugin 
PLUGINNAME = gridoverlay

PY_FILES = gridoverlay.py gridpluginlayer.py gridpluginlayertype.py gridpropertiesdialog.py __init__.py

EXTRAS = CHANGELOG Makefile metadata.txt icon.png LICENSE TODO

UI_FILES = ui_grid_properties.py

RESOURCE_FILES = resources_rc.py

#get plugin version for use in 'make package'
ifeq ($(strip $(GIT_VERSION)),)
	GIT_VERSION=HEAD
endif
PLUGINVER1=$(shell grep version= metadata.txt)
PLUGINVER=$(shell expr substr $(PLUGINVER1) 9 20)

default: compile

clean:
	rm -f *.pyc
	rm -f ui_*.py*
	rm -f resources_rc.py

compile:  $(UI_FILES) $(RESOURCE_FILES)

resources_rc.py : resources.qrc
	pyrcc4 -o resources_rc.py resources.qrc

%.py : %.ui
	pyuic4 -o $@ $<

# The deploy  target only works on unix like operating system where
# the Python plugin directory is located at:
# $HOME/.qgis/python/plugins
deploy: compile
	mkdir -p $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vf $(UI_FILES) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vf $(RESOURCE_FILES) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vf $(EXTRAS) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)

# Create a zip package of the plugin named $(PLUGINNAME).zip. 
# This requires use of git (your plugin development directory must be a 
# git repository).
package: compile
		rm -f $(PLUGINNAME)-$(PLUGINVER).zip
		git archive --prefix=$(PLUGINNAME)/ -o $(PLUGINNAME)-$(PLUGINVER).zip $(GIT_VERSION)
		echo "Created package: $(PLUGINNAME)-$(PLUGINVER).zip"
