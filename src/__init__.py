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
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

import configuration
from configuration_widget import ConfigurationWidget

UI_STRING = '''
<ui>
<menubar name="MenuBar">
<menu name="ViewMenu" action="View">
<menuitem name="JumpToWindow" action="JumpToWindow"/>
</menu>
</menubar>
</ui>
'''

global_dbus_obj=None

# IPC class: for hotkey activation
class MyDBUSService(dbus.service.Object):
    def __init__(self, main_window):
        bus_name = dbus.service.BusName('org.rhythmbox.JumpToWindow'
                , bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name
                , '/org/rhythmbox/JumpToWindow')
        self.main_window = main_window

    def set_main_window(self, main_window):
        self.main_window=main_window

    @dbus.service.method('org.rhythmbox.JumpToWindow')
    def dbus_activate(self, str_arg):
        if(self.main_window==None): return "error: not initialized"
        return self.main_window.dbus_activate(str_arg)
 


class JumpToWindow(GObject.GObject, Peas.Activatable):
    __gtype_name = 'JumpToWindow'
    object = GObject.property(type=GObject.GObject)

    def __init__(self):
        GObject.GObject.__init__(self)

        self.source=None
        self.source_view=None
        self.modelfilter=None

        self.is_updating=False
        self.need_refresh_source=False
        self.last_search_text=""

        self.was_last_space=False
        self.last_cursor_pos = 0

    def dbus_activate_from_menu(self, str_arg, shell):
	self.dbus_activate(str_arg)


    def dbus_activate(self, str_arg):
        self.window.show()
#        self.window.present() #helps grabbing the focus ?

        self.is_updating=True #avoid updating the filter multiple times
        search_changed=False
        try:
            self.txt_search.grab_focus()
            if(self.config.keep_search_text):
                self.txt_search.select_region(0,-1)
            else:
                search_changed=(self.txt_search.get_text()!="")
                self.txt_search.set_text("")
            self.show_entries()
            if(self.is_updating and search_changed):
                self.modelfilter.refilter()
        except Exception, e:
            print "Exception: "+str(e)
        self.is_updating=False
        self.make_default_entry_selection()
        return "success"

    def playlist_row_activated(self, treeview, path, view_column,
            user_param1=None):
        self.play_selected_item()

    def btn_play_hide_clicked(self, widget, data=None):
        if(self.play_selected_item()):
            self.window.hide()
    
    def btn_hide_clicked(self, widget, data=None):
        self.window.hide()

    def btn_enqueue_clicked(self, widget, data=None):
        self.enqueue_selected_item()

    def btn_clear_clicked(self, widget, data=None):
        self.txt_search.set_text("")
        self.txt_search.grab_focus()

    def get_queue_source(self):
        return self.shell.get_property("queue-source")

    # model filter: use search text to filter items
    def visible_func(self, model, iter, user_data):
        text_list = self.txt_search.get_text().lower().split(' ')
        for text in text_list:
            visible=False
            for i in range(len(self.config.columns_search)):
                if(self.config.columns_search[i] and 
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
        if(new_source==self.source): return True
        # disconnect old source...
        try:
            if(self.source_view!=None):
                self.source_view.disconnect(self.source_view_id_replace)
                self.source_view.disconnect(self.source_view_id_add)
                self.source_view.disconnect(self.source_view_id_del)
        except:
            pass
        self.source=new_source
        if(new_source==None):
            self.source_view=None
            return False
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
        return True

    def refresh_entries(self):
        self.need_refresh_source=True
        if(self.window.get_visible()):
            self.show_entries()

    # updates the currently playing source if necessary
    def show_entries(self):
        try:

# code snipplet for the playlists:
#        for x in list(self.shell.props.sourcelist.props.model):
##           if list(x)[2] == "Playlists"
#            print list(x)


            new_source = self.shell_player.get_active_source()
            if(not self.need_refresh_source and new_source==self.source): return
            self.need_refresh_source=False


            if(not self.track_source(new_source)):
                self.modelfilter=None
                return

            model = Gtk.ListStore(str, str, str, int, str)

            for row in self.source.props.query_model: #or: base_query_model ?
                entry = row[0]
                artist = entry.get_string(RB.RhythmDBPropType.ARTIST)
                album = entry.get_string(RB.RhythmDBPropType.ALBUM)
                title = entry.get_string(RB.RhythmDBPropType.TITLE)
                play_count = int(entry.get_ulong(
                    RB.RhythmDBPropType.PLAY_COUNT))
                location = entry.get_string(RB.RhythmDBPropType.LOCATION)
                model.append([artist, album, title, play_count, location])

            self.modelfilter = model.filter_new()
            self.modelfilter.set_visible_func(self.visible_func, None)
            self.playlist_tree.set_model(self.modelfilter)
            self.is_updating=False

        except Exception, e:
            print "Exception: "+str(e)

    def get_selected_entry(self):
        model, treeiter=self.tree_selection.get_selected()
        if(treeiter!=None):
            sel_loc=self.modelfilter.get_value(treeiter, self.column_item_loc)
            for row in self.source.props.query_model:
                entry=row[0]
                loc = entry.get_string(RB.RhythmDBPropType.LOCATION)
                if(loc==sel_loc):
                    return entry
        return None

    def play_selected_item(self):
        sel_entry=self.get_selected_entry()
        if(sel_entry!=None):
            self.shell_player.play_entry(sel_entry, self.source)
            return True
        return False

    def enqueue_selected_item(self):
        sel_entry=self.get_selected_entry()
        queue_source=self.get_queue_source()
        if(sel_entry!=None and queue_source!=None):
            queue_query_model = queue_source.get_property("query-model")
            if(queue_query_model!=None):
                queue_query_model.add_entry(sel_entry,-1)
                return True
        return False

    def keypress(self, widget, event):
        key = Gdk.keyval_name (event.keyval).lower()
        handled=True
        cursor_pos = self.txt_search.get_property("cursor-position")
        text_has_focus=self.txt_search.has_focus()
        shift_down=event.state & Gdk.ModifierType.SHIFT_MASK

        if(key == "return" or key == "kp_enter"):
            if(event.state & Gdk.ModifierType.MOD1_MASK):
                self.enqueue_selected_item()
            else:
                if(self.play_selected_item()):
                    self.window.hide()
        elif(key == "escape"):
            self.window.hide()
        elif(key == "up"):
            self.select_previous_item(False)
        elif(key == "down"):
            self.select_next_item(False)
        elif(key == "f" and shift_down and text_has_focus):
            self.scroll_page_down()
        elif(key == "b" and shift_down and text_has_focus):
            self.scroll_page_up()
        elif(key == "space"):
            handled=False
            if(text_has_focus):
                if(self.was_last_space and cursor_pos == self.last_cursor_pos+1
                    or self.txt_search.get_text()==""):
                    handled=True
                if(shift_down):
                    self.select_previous_item(False)
                else:
                    self.select_next_item(False)
        else:
            handled=False

        self.was_last_space=(key=="space")
        self.last_cursor_pos = cursor_pos
        if(handled): self.last_cursor_pos-=1

        #print "key pressed "+key
        #print " state "+str(event.state)
        return handled

    def select_next_item(self, use_align=True):
        model, treeiter=self.tree_selection.get_selected()
        if(treeiter!=None):
            nextiter=model.iter_next(treeiter)
            if(nextiter!=None):
                self.select_item(nextiter, use_align)
            else:
                self.select_first_item(use_align) #wrap around

    def select_previous_item(self, use_align=True):
        model, seliter=self.tree_selection.get_selected()
        if(self.modelfilter==None or seliter==None): return
        sel_path=model.get_path(seliter)
        # this is really slow. why the heck is there no iter_previous?
        iter=self.modelfilter.get_iter_first()
        if(iter!=None and seliter!=None):
            nextiter=model.iter_next(iter)
            while(nextiter!=None):
                if(model.get_path(nextiter)==sel_path):
                    self.select_item(iter, use_align)
                    return
                iter=nextiter
                nextiter=model.iter_next(iter)
            self.select_item(iter, use_align) #wrap around

    def scroll_page_down(self):
        paths=self.playlist_tree.get_visible_range()
        if(paths!=None):
            self.select_item_path(paths[len(paths)-1], True)

    def scroll_page_up(self):
        paths=self.playlist_tree.get_visible_range()
        if(paths!=None):
            self.select_item_path(paths[len(paths)-2], True, 1.0)
            paths=self.playlist_tree.get_visible_range()
            if(paths!=None):
                self.select_item_path(paths[len(paths)-2], True)

    def select_item(self, treeiter, use_align=True):
        if(self.modelfilter==None): return
        path=self.modelfilter.get_path(treeiter)
        self.select_item_path(path, use_align)

    def select_item_path(self, tree_path, use_align, align=0.0):
        if(tree_path!=None):
            self.tree_selection.select_path(tree_path)
            self.playlist_tree.scroll_to_cell(tree_path, None, use_align, align)

    def select_first_item(self, use_align=True):
        if(self.modelfilter==None): return
        iter=self.modelfilter.get_iter_first()
        if(iter): self.select_item(iter, use_align)

    def make_default_entry_selection(self):
        # by default, select currently playing song
        playing_entry = self.shell_player.get_playing_entry()
        if(playing_entry != None):
            playing_loc = playing_entry.get_string(RB.RhythmDBPropType.LOCATION)
            iter=self.modelfilter.get_iter_first()
            while(iter!=None):
                entry_loc=self.modelfilter.get_value(iter, self.column_item_loc)
                if(entry_loc == playing_loc):
                    self.select_item(iter)
                    return
                iter=self.modelfilter.iter_next(iter)
        model, seliter=self.tree_selection.get_selected()
        if(seliter==None):
            self.select_first_item() # fallback if current playing not found


    def txt_search_changed(self, widget, string, *args):
        text=self.txt_search.get_text().strip()
        if(not self.is_updating and text!=self.last_search_text):
            self.modelfilter.refilter()
            self.select_first_item()
        self.last_search_text=text

    def create_columns(self, treeView):
    
        # clear the columns first
        column=treeView.get_column(0)
        while(column!=None):
            treeView.remove_column(column)
            column=treeView.get_column(0)

        font_size=int(self.config.font_size)
        column_headers = [ "Artist", "Album", "Title", "Play count" ]
        for i in range(len(column_headers)):
            rendererText = Gtk.CellRendererText()
            if(font_size>0): rendererText.set_property("size-points", font_size)
            column = Gtk.TreeViewColumn(column_headers[i], rendererText, text=i)
            column.set_resizable(True)
            column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            if(self.config.columns_size[i] <= 0):
                self.config.columns_size[i]=100
            column.set_fixed_width(self.config.columns_size[i])
            column.set_visible(self.config.columns_visible[i])
            treeView.append_column(column)
        
        column = Gtk.TreeViewColumn()
        column.set_visible(False)
        treeView.append_column(column)
        self.column_item_loc=len(column_headers)

    def delete_event(self,window,event):
        #don't delete the window; hide instead
        window.hide_on_delete()
        return True
    
    def window_show(self, widget):
        self.window.move(self.config.window_x, self.config.window_y)

    def window_hide(self, widget):
        width,height=self.window.get_size()
        if(width!=self.config.window_w or height!=self.config.window_h):
            self.config.need_save_config=True
            self.config.window_w = width
            self.config.window_h = height
        columns=self.playlist_tree.get_columns()
        for i in range(len(columns)):
            if(columns[i].get_visible() and 
                    self.config.columns_size[i] != columns[i].get_width()):
                self.config.need_save_config=True
        self.config.save_settings(self.window, self.playlist_tree)

    def window_configure(self, widget, event):
        window_x,window_y=self.window.get_position()
        if(window_x!=self.config.window_x or window_y!=self.config.window_y):
            self.config.need_save_config=True
            self.config.window_x = window_x
            self.config.window_y = window_y
        return False

    def config_changed(self, config):
        self.create_columns(self.playlist_tree)
        self.refresh_entries()
        GObject.idle_add(lambda : self.config.save_settings(
            self.window, self.playlist_tree))

    def do_activate (self):

        global global_dbus_obj

        if(global_dbus_obj==None):
            DBusGMainLoop(set_as_default=True)
            self.dbus_service = MyDBUSService(self)
            global_dbus_obj = self.dbus_service
        else:
            global_dbus_obj.set_main_window(self)
            self.dbus_service = global_dbus_obj

        if(configuration.global_config_obj==None):
            configuration.global_config_obj=configuration.Configuration()
        self.config=configuration.global_config_obj
        self.config.connect("config-changed", self.config_changed)


        self.shell = self.object
        self.library = self.shell.props.library_source
        self.shell_player = self.shell.props.shell_player
        self.playlist_manager = self.shell.props.playlist_manager
        self.db = self.shell.props.db
        self.backend_player = self.shell_player.props.player


        # load the window
        source_dir=os.path.dirname(os.path.abspath(__file__))

        builder = Gtk.Builder()
        builder.add_from_file(source_dir+"/../ui/window.glade")
        self.window=builder.get_object("window1")
        self.window.connect("key-press-event", self.keypress)
        self.window.connect("delete-event", self.delete_event)
        self.window.connect("hide", self.window_hide)
        self.window.connect("show", self.window_show)
        self.window.set_title("Rhythmbox - JumpToWindow")
        self.window.add_events(Gdk.EventType.CONFIGURE)
        self.window.connect("configure-event", self.window_configure)
        
        self.playlist_tree=builder.get_object("tree_playlist")
        self.tree_selection = builder.get_object("tree_playlist_selection")
        self.playlist_tree.connect("row-activated", self.playlist_row_activated)

        self.txt_search=builder.get_object("txt_search")
        self.txt_search.connect("changed", self.txt_search_changed, None)

        btn_play_hide=builder.get_object("btn_play_hide")
        btn_play_hide.connect("clicked", self.btn_play_hide_clicked, None)

        btn_hide=builder.get_object("btn_hide")
        btn_hide.connect("clicked", self.btn_hide_clicked, None)

        btn_enqueue=builder.get_object("btn_enqueue")
        btn_enqueue.connect("clicked", self.btn_enqueue_clicked, None)

        btn_clear=builder.get_object("btn_clear")
        btn_clear.connect("clicked", self.btn_clear_clicked, None)


        self.config.load_settings(self.window)
        self.create_columns(self.playlist_tree)

	shell = self.object
        self.action = Gtk.Action (name='JumpToWindow', label=_('Show JumpToWindow'),
                      tooltip=_(''),
                      stock_id='')
        self.action_id = self.action.connect ('activate', self.dbus_activate_from_menu, 'org.rhythmbox.JumpToWindow')
        self.action_group = Gtk.ActionGroup (name='JumpToWindowPluginActions')
        self.action_group.add_action_with_accel (self.action, "<control><shift>J")

        uim = shell.props.ui_manager
        uim.insert_action_group (self.action_group, 0)
        self.ui_id = uim.add_ui_from_string (UI_STRING)
        uim.ensure_update ()

    
    def do_deactivate (self):

        self.dbus_service.set_main_window(None)
        self.dbus_service = None
        self.config=None

        self.window.destroy()
        self.window=None

