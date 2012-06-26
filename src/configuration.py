##
# Copyright (C) 2012 Beat Kueng <beat-kueng@gmx.net>
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


from gi.repository import Gtk, GObject, Peas, RB, Gdk
import os
import sys
import ConfigParser


SECTION_KEY = "JumpToWindow"
KEY_WINDOW_X = "window_x"
KEY_WINDOW_Y = "window_y"
KEY_WINDOW_W = "window_w"
KEY_WINDOW_H = "window_h"
CONFIG_FILE = "~/.config/JumpToWindow.conf"
 

class Configuration:

    def __init__(self):

        # init default values
        self.columns_visible = [ True ]*3
        self.columns_visible[1] = False

        self.window_x = 50
        self.window_y = 50


    def save_settings(self, main_window):
        config = ConfigParser.ConfigParser()

        config.add_section(SECTION_KEY)
        width,height=main_window.get_size()
        config.set(SECTION_KEY, KEY_WINDOW_X, self.window_x)
        config.set(SECTION_KEY, KEY_WINDOW_Y, self.window_y)
        config.set(SECTION_KEY, KEY_WINDOW_W, width)
        config.set(SECTION_KEY, KEY_WINDOW_H, height)

        config_file_name = os.path.expanduser(CONFIG_FILE)
        dir=os.path.dirname(config_file_name)
        if(not os.path.exists(dir)):
            os.mkdir(dir)
        with open(config_file_name, 'wb') as configfile:
            config.write(configfile)

    def load_settings(self, main_window):
        try:

            config = ConfigParser.ConfigParser()
            config.add_section(SECTION_KEY)
            config.set('DEFAULT', KEY_WINDOW_X, str(self.window_x))
            config.set('DEFAULT', KEY_WINDOW_Y, str(self.window_y))
            config.set('DEFAULT', KEY_WINDOW_W, '500')
            config.set('DEFAULT', KEY_WINDOW_H, '500')

            config.read(os.path.expanduser(CONFIG_FILE))

            self.window_x = config.getint(SECTION_KEY, KEY_WINDOW_X)
            self.window_y = config.getint(SECTION_KEY, KEY_WINDOW_Y)
            # moving the window here has no effect
            width = config.getint(SECTION_KEY, KEY_WINDOW_W)
            height = config.getint(SECTION_KEY, KEY_WINDOW_H)
            main_window.set_default_size(width,height)

        except Exception, e:
            print "Exception: "+str(e)

