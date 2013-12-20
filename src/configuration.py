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


from gi.repository import Gtk, GObject, RB, Gdk
import os
import configparser


SECTION_KEY = "JumpToWindow"
CONFIG_FILE = "~/.config/JumpToWindow.conf"
 
global_config_obj=None


class Configuration(GObject.GObject):
    __gtype_name__ = 'Configuration'
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        GObject.GObject.__init__(self)

        # init default values
        self.columns_visible = [ True ]*4
        self.columns_visible[1] = False
        self.columns_visible[3] = False

        self.columns_size = [ 150 ]*5

        self.columns_search = [ True ]*3
        self.columns_search[1] = False

        self.window_x = 50
        self.window_y = 50
        self.window_w = 500
        self.window_h = 500

        self.keep_search_text = True
        self.font_size = 0


        self.need_save_config=False


    def save_settings(self, main_window, tree_view):
        if(not self.need_save_config): return
        self.need_save_config=False
        config = configparser.ConfigParser()

        config.add_section(SECTION_KEY)
        width,height=main_window.get_size()
        config.set(SECTION_KEY, 'window_x', str(self.window_x))
        config.set(SECTION_KEY, 'window_y', str(self.window_y))
        config.set(SECTION_KEY, 'window_w', str(width))
        config.set(SECTION_KEY, 'window_h', str(height))

        config.set(SECTION_KEY, 'keep_search', str(self.keep_search_text))
        config.set(SECTION_KEY, 'font_size', str(self.font_size))

        for i in range(len(self.columns_visible)):
            config.set(SECTION_KEY, 'columns_visible'+str(i),
                    str(self.columns_visible[i]))
        for i in range(len(self.columns_search)):
            config.set(SECTION_KEY, 'columns_search'+str(i),
                    str(self.columns_search[i]))

        columns=tree_view.get_columns()
        for i in range(len(columns)):
            if(columns[i].get_visible()):
                self.columns_size[i] = columns[i].get_width()
                config.set(SECTION_KEY, 'columns_size'+str(i),
                        str(columns[i].get_width()))

        config_file_name = os.path.expanduser(CONFIG_FILE)
        dir=os.path.dirname(config_file_name)
        if(not os.path.exists(dir)):
            os.mkdir(dir)
        with open(config_file_name, 'w') as configfile:
            config.write(configfile)

    def load_settings(self, main_window):
        try:

            config = configparser.ConfigParser()
            config.add_section(SECTION_KEY)
            config.set('DEFAULT', 'window_x', str(self.window_x))
            config.set('DEFAULT', 'window_y', str(self.window_y))
            config.set('DEFAULT', 'window_w', str(self.window_w))
            config.set('DEFAULT', 'window_h', str(self.window_h))

            config.set('DEFAULT', 'keep_search', str(self.keep_search_text))
            config.set('DEFAULT', 'font_size', str(self.font_size))

            for i in range(len(self.columns_visible)):
                config.set('DEFAULT', 'columns_visible'+str(i),
                        str(self.columns_visible[i]))
            for i in range(len(self.columns_search)):
                config.set('DEFAULT', 'columns_search'+str(i),
                        str(self.columns_search[i]))

            for i in range(len(self.columns_size)):
                config.set('DEFAULT', 'columns_size'+str(i),
                        str(self.columns_size[i]))

            config.read(os.path.expanduser(CONFIG_FILE))

            self.window_x = config.getint(SECTION_KEY, 'window_x')
            self.window_y = config.getint(SECTION_KEY, 'window_y')
            # we move the window on every show to keep a fixed position
            width = config.getint(SECTION_KEY, 'window_w')
            height = config.getint(SECTION_KEY, 'window_h')
            main_window.set_default_size(width,height)

            self.keep_search_text=config.getboolean(SECTION_KEY, 'keep_search')
            self.font_size=config.getint(SECTION_KEY, 'font_size')

            for i in range(len(self.columns_visible)):
                self.columns_visible[i]=config.getboolean(SECTION_KEY
                        , 'columns_visible'+str(i))
            for i in range(len(self.columns_search)):
                self.columns_search[i]=config.getboolean(SECTION_KEY
                        , 'columns_search'+str(i))

            for i in range(len(self.columns_size)):
                self.columns_size[i]=config.getint(SECTION_KEY
                        , 'columns_size'+str(i))

        except Exception as e:
            print("Exception: "+str(e))
    
    def config_changed(self):
        self.need_save_config=True
        self.emit("config-changed")


GObject.type_register(Configuration)
GObject.signal_new("config-changed", Configuration, GObject.SIGNAL_RUN_FIRST,
                   GObject.TYPE_NONE, ())
