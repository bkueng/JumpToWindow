#! /usr/bin/env python

import dbus
 
bus = dbus.SessionBus()
service = bus.get_object('org.rhythmbox.JumpToWindow', '/org/rhythmbox/JumpToWindow')
service_func = service.get_dbus_method('dbus_activate', 'org.rhythmbox.JumpToWindow')
print service_func("")

