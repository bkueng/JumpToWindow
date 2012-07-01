##
# Copyright (C) 2012 Beat Küng <beat-kueng@gmx.net>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#

INSTALL_DIR = $(HOME)/.local/share/rhythmbox/plugins/JumpToWindow
# global: /usr/lib/rhythmbox/plugins

all:

install:
	mkdir -p $(INSTALL_DIR)
	cp -r src ui JumpToWindow.plugin $(INSTALL_DIR)
	@echo 
	@echo "==================================================================="
	@echo "Now create a global hotkey that executes the script"
	@echo "$(INSTALL_DIR)/src/activate.py"
	@echo "==================================================================="
	@echo

uninstall:
	rm -r $(INSTALL_DIR)

