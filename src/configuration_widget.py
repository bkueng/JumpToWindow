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


from gi.repository import Gtk, GObject, RB, Gdk, PeasGtk
import configuration
import os


class ConfigurationWidget(GObject.GObject, PeasGtk.Configurable):
    __gtype_name__ = 'ConfigurationWidget' 
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        GObject.GObject.__init__(self)

        if(configuration.global_config_obj==None):
            configuration.global_config_obj=configuration.Configuration()
        self.config=configuration.global_config_obj

        self.is_loading=False


    def txt_font_size_changed(self, widget, string, *args):
        if(self.is_loading): return
        try:
            self.config.font_size = int(self.txt_font_size.get_text())
        except:
            self.config.font_size = 0
        self.config.config_changed()

    def chk_toggled(self, widget):
        if(self.is_loading): return
        self.config.keep_search_text = self.chk_keep_search.get_active()

        self.config.columns_visible[0] = self.chk_artist.get_active()
        self.config.columns_visible[1] = self.chk_album.get_active()
        self.config.columns_visible[2] = self.chk_title.get_active()
        #self.config.columns_visible[3] = self.chk_play_count.get_active()

        self.config.columns_search[0] = self.chk_search_artist.get_active()
        self.config.columns_search[1] = self.chk_search_album.get_active()
        self.config.columns_search[2] = self.chk_search_title.get_active()

        self.config.config_changed()


    def do_create_configure_widget(self):

        self.is_loading=True
        source_dir=os.path.dirname(os.path.abspath(__file__))

        builder = Gtk.Builder()
        builder.add_from_file(source_dir+"/../ui/configuration.glade")

        self.chk_keep_search=builder.get_object("chk_keep_search")
        self.chk_keep_search.connect("toggled", self.chk_toggled)
        self.chk_keep_search.set_active(self.config.keep_search_text)

        self.chk_artist=builder.get_object("chk_artist")
        self.chk_artist.connect("toggled", self.chk_toggled)
        self.chk_artist.set_active(self.config.columns_visible[0])
        self.chk_album=builder.get_object("chk_album")
        self.chk_album.connect("toggled", self.chk_toggled)
        self.chk_album.set_active(self.config.columns_visible[1])
        self.chk_title=builder.get_object("chk_title")
        self.chk_title.connect("toggled", self.chk_toggled)
        self.chk_title.set_active(self.config.columns_visible[2])
        #self.chk_play_count=builder.get_object("chk_play_count")
        #self.chk_play_count.connect("toggled", self.chk_toggled)
        #self.chk_play_count.set_active(self.config.columns_visible[3])

        self.chk_search_artist=builder.get_object("chk_search_artist")
        self.chk_search_artist.connect("toggled", self.chk_toggled)
        self.chk_search_artist.set_active(self.config.columns_search[0])
        self.chk_search_album=builder.get_object("chk_search_album")
        self.chk_search_album.connect("toggled", self.chk_toggled)
        self.chk_search_album.set_active(self.config.columns_search[1])
        self.chk_search_title=builder.get_object("chk_search_title")
        self.chk_search_title.connect("toggled", self.chk_toggled)
        self.chk_search_title.set_active(self.config.columns_search[2])

        self.txt_font_size=builder.get_object("txt_font_size")
        self.txt_font_size.connect("changed", self.txt_font_size_changed
                , None)
        self.txt_font_size.set_value(self.config.font_size)

        box_config_widget=builder.get_object("box_config")

        self.is_loading=False

        return box_config_widget
