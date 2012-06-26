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
import gobject


SECTION_KEY = "JumpToWindow"
CONFIG_FILE = "~/.config/JumpToWindow.conf"
 

class Configuration(gobject.GObject):

    def __init__(self):
        self.__gobject_init__()

        # init default values
        self.columns_visible = [ True ]*4
        self.columns_visible[1] = False

        self.columns_search = [ True ]*3
        self.columns_search[1] = False

        self.window_x = 50
        self.window_y = 50

        self.keep_search_text = True

        self.config_window=None
        self.is_loading=False


    def save_settings(self, main_window):
        config = ConfigParser.ConfigParser()

        config.add_section(SECTION_KEY)
        width,height=main_window.get_size()
        config.set(SECTION_KEY, 'window_x', self.window_x)
        config.set(SECTION_KEY, 'window_y', self.window_y)
        config.set(SECTION_KEY, 'window_w', width)
        config.set(SECTION_KEY, 'window_h', height)

        config.set(SECTION_KEY, 'keep_search', str(self.keep_search_text))

        for i in range(len(self.columns_visible)):
            config.set(SECTION_KEY, 'columns_visible'+str(i),
                    str(self.columns_visible[i]))
        for i in range(len(self.columns_search)):
            config.set(SECTION_KEY, 'columns_search'+str(i),
                    str(self.columns_search[i]))

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
            config.set('DEFAULT', 'window_x', str(self.window_x))
            config.set('DEFAULT', 'window_y', str(self.window_y))
            config.set('DEFAULT', 'window_w', '500')
            config.set('DEFAULT', 'window_h', '500')

            config.set('DEFAULT', 'keep_search', str(self.keep_search_text))

            for i in range(len(self.columns_visible)):
                config.set('DEFAULT', 'columns_visible'+str(i),
                        str(self.columns_visible[i]))
            for i in range(len(self.columns_search)):
                config.set('DEFAULT', 'columns_search'+str(i),
                        str(self.columns_search[i]))

            config.read(os.path.expanduser(CONFIG_FILE))

            self.window_x = config.getint(SECTION_KEY, 'window_x')
            self.window_y = config.getint(SECTION_KEY, 'window_y')
            # moving the window here has no effect
            width = config.getint(SECTION_KEY, 'window_w')
            height = config.getint(SECTION_KEY, 'window_h')
            main_window.set_default_size(width,height)

            self.keep_search_text=config.getboolean(SECTION_KEY, 'keep_search')

            for i in range(len(self.columns_visible)):
                self.columns_visible[i]=config.getboolean(SECTION_KEY
                        , 'columns_visible'+str(i))
            for i in range(len(self.columns_search)):
                self.columns_search[i]=config.getboolean(SECTION_KEY
                        , 'columns_search'+str(i))

        except Exception, e:
            print "Exception: "+str(e)
    
    def delete_event(self,window,event):
        self.config_window=None
        return False

    def btn_ok_clicked(self, widget, data=None):
        self.config_window.destroy()
        self.config_window=None

    def chk_toggled(self, widget):
        if(self.is_loading): return
        self.keep_search_text = self.chk_keep_search.get_active()

        self.columns_visible[0] = self.chk_artist.get_active()
        self.columns_visible[1] = self.chk_album.get_active()
        self.columns_visible[2] = self.chk_title.get_active()
        self.columns_visible[3] = self.chk_play_count.get_active()

        self.columns_search[0] = self.chk_search_artist.get_active()
        self.columns_search[1] = self.chk_search_album.get_active()
        self.columns_search[2] = self.chk_search_title.get_active()

        self.emit("config-changed")

    def show_config_dialog(self, *var_args):

        self.is_loading=True
        if(self.config_window==None):
            source_dir=os.path.dirname(os.path.abspath(__file__))

            builder = Gtk.Builder()
            builder.add_from_file(source_dir+"/configuration.glade")
            self.config_window=builder.get_object("window1")
            self.config_window.connect("delete-event", self.delete_event)
            self.config_window.set_title(
                    "Rhythmbox - JumpToWindow Configuration")

            self.chk_keep_search=builder.get_object("chk_keep_search")
            self.chk_keep_search.connect("toggled", self.chk_toggled)
            self.chk_keep_search.set_active(self.keep_search_text)

            self.chk_artist=builder.get_object("chk_artist")
            self.chk_artist.connect("toggled", self.chk_toggled)
            self.chk_artist.set_active(self.columns_visible[0])
            self.chk_album=builder.get_object("chk_album")
            self.chk_album.connect("toggled", self.chk_toggled)
            self.chk_album.set_active(self.columns_visible[1])
            self.chk_title=builder.get_object("chk_title")
            self.chk_title.connect("toggled", self.chk_toggled)
            self.chk_title.set_active(self.columns_visible[2])
            self.chk_play_count=builder.get_object("chk_play_count")
            self.chk_play_count.connect("toggled", self.chk_toggled)
            self.chk_play_count.set_active(self.columns_visible[3])

            self.chk_search_artist=builder.get_object("chk_search_artist")
            self.chk_search_artist.connect("toggled", self.chk_toggled)
            self.chk_search_artist.set_active(self.columns_search[0])
            self.chk_search_album=builder.get_object("chk_search_album")
            self.chk_search_album.connect("toggled", self.chk_toggled)
            self.chk_search_album.set_active(self.columns_search[1])
            self.chk_search_title=builder.get_object("chk_search_title")
            self.chk_search_title.connect("toggled", self.chk_toggled)
            self.chk_search_title.set_active(self.columns_search[2])

            btn_ok=builder.get_object("btn_ok")
            btn_ok.connect("clicked", self.btn_ok_clicked)

        self.is_loading=False

        self.config_window.show()

gobject.type_register(Configuration)
gobject.signal_new("config-changed", Configuration, gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE, ())
