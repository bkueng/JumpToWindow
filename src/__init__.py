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

import gconf

from gi.repository import Gtk, GObject, Peas, RB, Gdk
import os
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import sys
import ConfigParser


SECTION_KEY = "JumpToWindow"
KEY_WINDOW_X = "window_x"
KEY_WINDOW_Y = "window_y"
KEY_WINDOW_W = "window_w"
KEY_WINDOW_H = "window_h"
CONFIG_FILE = "~/.config/JumpToWindow.conf"
 

class MyDBUSService(dbus.service.Object):
    def __init__(self, jump_to_window):
        bus_name = dbus.service.BusName('org.rhythmbox.JumpToWindow', bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, '/org/rhythmbox/JumpToWindow')
        self.jump_to_window = jump_to_window
 
    @dbus.service.method('org.rhythmbox.JumpToWindow')
    def dbus_activate(self, str_arg):
        return self.jump_to_window.dbus_activate(str_arg)
 



class JumpToPlaying(GObject.GObject, Peas.Activatable):
    __gtype_name = 'JumpToPlaying'
    object = GObject.property(type=GObject.GObject)

    def __init__(self):
        GObject.GObject.__init__(self)

        DBusGMainLoop(set_as_default=True)
        self.dbus_service = MyDBUSService(self)

        self.columns_visible = [ True ]*3
        self.columns_visible[1] = False

        self.source=None
        self.source_view=None


    def save_settings(self):
        config = ConfigParser.ConfigParser()

        config.add_section(SECTION_KEY)
        width,height=self.window.get_size()
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

    def load_settings(self):
        try:

            config = ConfigParser.ConfigParser()
            config.add_section(SECTION_KEY)
            self.window_x = 50
            self.window_y = 50
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
            self.window.set_default_size(width,height)

        except Exception, e:
            print "Exception: "+str(e)

        
    def dbus_activate(self, str_arg):
        self.window.show()
#        self.window.present() #helps grabbing the focus ?
        self.show_entries()
        self.txt_search.grab_focus()
        self.txt_search.select_region(0,-1)
        return "success"


    def btn_play_clicked(self, widget, data=None):
        if(self.play_selected_item()):
            self.window.hide()

    def btn_clear_clicked(self, widget, data=None):
        self.txt_search.set_text("")
        self.txt_search.grab_focus()

    def visible_func(self, model, iter, user_data):
        text_list = self.txt_search.get_text().lower().split(' ')
        for text in text_list:
            visible=False
            for i in range(len(self.columns_visible)):
                if(self.columns_visible[i] and 
                        text in model.get_value(iter, i).lower()):
                    visible=True
            if(not visible): return(False)
        return visible


    def source_entries_replaced(self, view, user_data=None):
        if(view==self.source_view):
            GObject.idle_add(self.refresh_entries)

    def source_entry_added(self, view, entry, user_data=None):
        if(view==self.source_view):
            GObject.idle_add(self.refresh_entries)

    def source_entry_deleted(self, view, entry, user_data=None):
        if(view==self.source_view):
            GObject.idle_add(self.refresh_entries)

    # connect to a source and listen for changes
    def track_source(self, new_source):
        if(new_source==self.source): return
        # disconnect old source...
        try:
            if(self.source_view!=None):
                self.source_view.disconnect(self.source_view_id_replace)
                self.source_view.disconnect(self.source_view_id_add)
                self.source_view.disconnect(self.source_view_id_del)
        except:
            pass
        self.source_view = new_source.get_entry_view()
        if(self.source_view!=None):
            self.source_view_id_replace= \
                    self.source_view.connect("entries-replaced",
                    self.source_entries_replaced)
            self.source_view_id_add= \
                    self.source_view.connect("entry-added",
                    self.source_entry_added)
            self.source_view_id_del= \
                    self.source_view.connect("entry-deleted",
                    self.source_entry_deleted)

        self.source=new_source

    def refresh_entries(self):
        self.show_entries(True)

    # updates the currently playing source if necessary
    def show_entries(self, need_refresh=False):
        try:
            # current playing entry:
#            entry = self.shell_player.get_playing_entry()
#            if(entry != None):
#                print dir(entry)
## uri:
#                self.location = entry.get_string(RB.RhythmDBPropType.LOCATION)
#                print self.location

#print source items:
#            print source
#            for row in source.props.query_model:
#                entry = row[0]
#                print entry.get_string(RB.RhythmDBPropType.TITLE)

# the playlists:
#        for x in list(self.shell.props.sourcelist.props.model):
##           if list(x)[2] == "Playlists"
#            print list(x)


            new_source = self.shell_player.get_active_source()
            if(not need_refresh and new_source==self.source): return

            self.track_source(new_source)

            model = Gtk.ListStore(str, str, str, int)

            i=0
            for row in self.source.props.query_model: #or: base_query_model ?
                entry = row[0]
                artist = entry.get_string(RB.RhythmDBPropType.ARTIST)
                album = entry.get_string(RB.RhythmDBPropType.ALBUM)
                title = entry.get_string(RB.RhythmDBPropType.TITLE)
                model.append([artist, album, title, i])
                i+=1

            self.modelfilter = model.filter_new()
            self.modelfilter.set_visible_func(self.visible_func, None)
            self.playlist_tree.set_model(self.modelfilter)

            self.select_first_item()

        except Exception, e:
            print "Exception: "+str(e)


    def play_selected_item(self):
        model, treeiter=self.tree_selection.get_selected()
        if(treeiter!=None):
            item_idx=self.modelfilter.get_value(treeiter, self.column_item_idx)
            i=0
            # we assume the source did not change since model creation
            for row in self.source.props.query_model:
                if(i==item_idx):
                    entry=row[0]
                    self.shell_player.play_entry(entry, self.source)
                    return True
                i+=1
        return False

    def keypress(self, widget, event):
        key = Gdk.keyval_name (event.keyval).lower()
        if(key == "return"):
            if(self.play_selected_item()):
                self.window.hide()
        elif(key == "up"):
            self.select_previous_item()
            return True
        elif(key == "down"):
            self.select_next_item()
            return True

        #print "key pressed "+key
        return False

    def select_next_item(self):
        model, treeiter=self.tree_selection.get_selected()
        if(treeiter!=None):
            nextiter=model.iter_next(treeiter)
            if(nextiter!=None):
                self.select_item(nextiter)
            else:
                self.select_first_item() #wrap around

    def select_previous_item(self):
        model, seliter=self.tree_selection.get_selected()
        iter=self.modelfilter.get_iter_first()
        if(iter!=None and seliter!=None):
            nextiter=model.iter_next(iter)
            while(nextiter!=None):
                if(model.get_path(nextiter)==model.get_path(seliter)):
                    self.select_item(iter)
                    return
                iter=nextiter
                nextiter=model.iter_next(iter)
            self.select_item(iter) #wrap around

    def select_item(self, treeiter):
        self.tree_selection.select_iter(treeiter)
        path=self.modelfilter.get_path(treeiter)
        self.playlist_tree.scroll_to_cell(path)

    def select_first_item(self):
        iter=self.modelfilter.get_iter_first()
        if(iter): self.select_item(iter)

    def txt_search_changed(self, widget, string, *args):
        self.modelfilter.refilter()
        self.select_first_item()

    def create_columns(self, treeView):
    
        rendererText = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Artist", rendererText, text=0)
        column.set_sort_column_id(0)    
        column.set_property("expand", True)
        column.set_visible(self.columns_visible[0])
        treeView.append_column(column)
        
        rendererText = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Album", rendererText, text=1)
        column.set_sort_column_id(1)
        column.set_property("expand", True)
        column.set_visible(self.columns_visible[1])
        treeView.append_column(column)

        rendererText = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Title", rendererText, text=2)
        column.set_sort_column_id(2)
        column.set_property("expand", True)
        column.set_visible(self.columns_visible[2])
        treeView.append_column(column)

        column = Gtk.TreeViewColumn()
        column.set_visible(False)
        treeView.append_column(column)
        self.column_item_idx=3

    def delete_event(self,window,event):
        #don't delete; hide instead
        window.hide_on_delete()
        return True
    
    def window_show(self, widget):
        self.window.move(self.window_x, self.window_y)

    def window_hide(self, widget):
        self.save_settings()

    def window_configure(self, widget, event):
        self.window_x,self.window_y=self.window.get_position()
        return False

    def do_activate (self):

        self.shell = self.object
        self.library = self.shell.props.library_source
        self.shell_player = self.shell.props.shell_player
        self.playlist_manager = self.shell.props.playlist_manager
        self.db = self.shell.props.db
        self.backend_player = self.shell_player.props.player


        # load the window
        source_dir=os.path.dirname(os.path.abspath(__file__))

        builder = Gtk.Builder()
        builder.add_from_file(source_dir+"/window.glade")
        self.window=builder.get_object("window1")
        self.window.connect("key-press-event", self.keypress)
        self.window.connect("delete-event", self.delete_event)
        self.window.connect("hide", self.window_hide)
        self.window.connect("show", self.window_show)
        self.window.set_title("Rhythmbox - JumpToWindow")
        self.window.add_events(Gdk.EventType.CONFIGURE)
        self.window.connect("configure-event", self.window_configure)
        
        self.playlist_tree=builder.get_object("tree_playlist")
        self.create_columns(self.playlist_tree)
        self.tree_selection = builder.get_object("tree_playlist_selection")

        self.txt_search=builder.get_object("txt_search")
        self.txt_search.connect("changed", self.txt_search_changed, None)

        btn_play=builder.get_object("btn_play")
        btn_play.connect("clicked", self.btn_play_clicked, None)

        btn_clear=builder.get_object("btn_clear")
        btn_clear.connect("clicked", self.btn_clear_clicked, None)


        self.load_settings()

    
    def do_deactivate (self):
        
        self.window.hide()

