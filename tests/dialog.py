#!/usr/bin/python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from xapp.widgets import Dialog

LOREM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, "
    "quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo "
    "consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse "
    "cillum dolore eu fugiat nulla pariatur."
)


class DemoWindow(Gtk.Window):

    def __init__(self):
        super().__init__(title="XApp.widgets.Dialog() Demo")
        self.set_default_size(600, 500)
        self.set_border_width(12)

        outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        grid = Gtk.Grid(column_spacing=12, row_spacing=8)

        xapp_header = Gtk.Label()
        xapp_header.set_markup("<b>XApp</b>")
        grid.attach(xapp_header, 0, 0, 1, 1)

        gtk_header = Gtk.Label()
        gtk_header.set_markup("<b>Gtk</b>")
        grid.attach(gtk_header, 1, 0, 1, 1)

        rows = [
            ("Info",            self._xapp_info,            self._gtk_info),
            ("Warning",         self._xapp_warning,         self._gtk_warning),
            ("Error",           self._xapp_error,           self._gtk_error),
            ("Question",        self._xapp_question,        self._gtk_question),
            ("Custom",          self._xapp_custom,          self._gtk_custom),
            ("No title",        self._xapp_no_title,        self._gtk_no_title),
            ("Large text",      self._xapp_large_text,      self._gtk_large_text),
            ("Hint",            self._xapp_hint,            self._gtk_hint),
            ("Dialog no icon",  self._xapp_dialog_no_icon,  self._gtk_dialog_no_icon),
            ("Dialog icon",     self._xapp_dialog_icon,     self._gtk_dialog_icon),
            ("Widget",          self._xapp_widget,          self._gtk_widget),
        ]

        for row, (label, xapp_cb, gtk_cb) in enumerate(rows, start=1):
            xapp_btn = Gtk.Button(label=f"Show {label} dialog")
            xapp_btn.connect("clicked", xapp_cb)
            grid.attach(xapp_btn, 0, row, 1, 1)

            gtk_btn = Gtk.Button(label=f"Show {label} dialog")
            gtk_btn.connect("clicked", gtk_cb)
            grid.attach(gtk_btn, 1, row, 1, 1)

        outer_box.pack_start(grid, True, True, 0)

        self.result_label = Gtk.Label(label="Click a button to show a dialog.")
        outer_box.pack_start(self.result_label, False, False, 0)

        self.add(outer_box)
        self.connect("destroy", Gtk.main_quit)
        self.show_all()

    def _set_result(self, text):
        self.result_label.set_markup(f"<b>Result:</b> {text}")

    # XApp variants

    def _xapp_info(self, button):
        Dialog(self, "All done", "The operation completed successfully.").info()
        self._set_result("Info dialog closed")

    def _xapp_warning(self, button):
        Dialog(self, "Disk space low", "You have less than 500 MB remaining.").warning()
        self._set_result("Warning dialog closed")

    def _xapp_error(self, button):
        Dialog(self, "Could not save file", "Permission denied: /etc/hosts").error()
        self._set_result("Error dialog closed")

    def _xapp_question(self, button):
        confirmed = Dialog(self, "Delete item?", "This action cannot be undone.").question()
        self._set_result(f"Question answered: {'Yes' if confirmed else 'No'}")

    def _xapp_custom(self, button):
        dialog = Dialog(self, "Apply changes?", "Your settings will be saved and the service restarted.")
        dialog.add_button("Save", 1, "suggested-action")
        dialog.add_button("Discard", 2, "destructive-action")
        dialog.add_button("Cancel", 3)
        dialog.set_default_response(2)
        response = dialog.warning()
        self._set_result(f"Custom dialog response: {response}")

    def _xapp_no_title(self, button):
        Dialog(self, message="This dialog has no title.").info()
        self._set_result("No-title dialog closed")

    def _xapp_large_text(self, button):
        Dialog(self, "Lorem Ipsum", LOREM).info()
        self._set_result("Large text dialog closed")

    def _xapp_hint(self, button):
        Dialog(self, "Reset settings?",
            "All preferences will be restored to their defaults.",
            hint="This only affects the current user and can be undone by restoring a backup.").warning()
        self._set_result("Hint dialog closed")

    def _xapp_dialog_no_icon(self, button):
        Dialog(self, "Heads up", "This is a plain dialog with no icon.").dialog()
        self._set_result("Dialog (no icon) closed")

    def _xapp_dialog_icon(self, button):
        Dialog(self, "Bluetooth", "A new device has been paired.").dialog("bluetooth-symbolic")
        self._set_result("Dialog (icon) closed")

    def _xapp_widget(self, button):
        combo = Gtk.ComboBoxText()
        for opt in ("Option A", "Option B", "Option C"):
            combo.append_text(opt)
        combo.set_active(0)
        check = Gtk.CheckButton(label="Enable feature")
        dialog = Dialog(self, "Settings", "Configure the following options:")
        dialog.add_widget(combo)
        dialog.add_widget(check)
        response = dialog.info()
        if response == Gtk.ResponseType.OK:
            self._set_result(f"Widget dialog: {combo.get_active_text()!r}, enabled={check.get_active()}")
        else:
            self._set_result("Widget dialog cancelled")

    # Gtk variants

    def _gtk_info(self, button):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True,
            message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK,
            text="All done")
        dialog.format_secondary_text("The operation completed successfully.")
        dialog.run()
        dialog.destroy()
        self._set_result("Info dialog closed")

    def _gtk_warning(self, button):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True,
            message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.OK,
            text="Disk space low")
        dialog.format_secondary_text("You have less than 500 MB remaining.")
        dialog.run()
        dialog.destroy()
        self._set_result("Warning dialog closed")

    def _gtk_error(self, button):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True,
            message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK,
            text="Could not save file")
        dialog.format_secondary_text("Permission denied: /etc/hosts")
        dialog.run()
        dialog.destroy()
        self._set_result("Error dialog closed")

    def _gtk_question(self, button):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True,
            message_type=Gtk.MessageType.QUESTION, buttons=Gtk.ButtonsType.YES_NO,
            text="Delete item?")
        dialog.format_secondary_text("This action cannot be undone.")
        response = dialog.run()
        dialog.destroy()
        confirmed = response == Gtk.ResponseType.YES
        self._set_result(f"Question answered: {'Yes' if confirmed else 'No'}")

    def _gtk_custom(self, button):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True,
            message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.NONE,
            text="Apply changes?")
        dialog.format_secondary_text("Your settings will be saved and the service restarted.")
        dialog.add_button("Save", 1)
        dialog.add_button("Discard", 2)
        dialog.add_button("Cancel", 3)
        dialog.get_widget_for_response(1).get_style_context().add_class("suggested-action")
        dialog.get_widget_for_response(2).get_style_context().add_class("destructive-action")
        response = dialog.run()
        dialog.destroy()
        self._set_result(f"Custom dialog response: {response}")

    def _gtk_no_title(self, button):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True,
            message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK)
        dialog.format_secondary_text("This dialog has no title.")
        dialog.run()
        dialog.destroy()
        self._set_result("No-title dialog closed")

    def _gtk_large_text(self, button):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True,
            message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK,
            text="Lorem Ipsum")
        dialog.format_secondary_text(LOREM)
        dialog.run()
        dialog.destroy()
        self._set_result("Large text dialog closed")

    def _gtk_hint(self, button):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True,
            message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.OK,
            text="Reset settings?")
        dialog.format_secondary_text("All preferences will be restored to their defaults.")
        hint_label = Gtk.Label()
        hint_label.set_markup('<small><i>This only affects the current user and can be undone by restoring a backup.</i></small>')
        hint_label.set_xalign(0)
        hint_label.set_line_wrap(True)
        dialog.get_message_area().pack_start(hint_label, False, False, 0)
        hint_label.show()
        dialog.run()
        dialog.destroy()
        self._set_result("Hint dialog closed")

    def _gtk_dialog_no_icon(self, button):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True,
            message_type=Gtk.MessageType.OTHER, buttons=Gtk.ButtonsType.OK,
            text="Heads up")
        dialog.format_secondary_text("This is a plain dialog with no icon.")
        dialog.run()
        dialog.destroy()
        self._set_result("Dialog (no icon) closed")

    def _gtk_dialog_icon(self, button):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True,
            message_type=Gtk.MessageType.OTHER, buttons=Gtk.ButtonsType.OK,
            text="Bluetooth")
        dialog.format_secondary_text("A new device has been paired.")
        image = Gtk.Image.new_from_icon_name("bluetooth", Gtk.IconSize.DIALOG)
        dialog.set_image(image)
        image.show()
        dialog.run()
        dialog.destroy()
        self._set_result("Dialog (icon) closed")

    def _gtk_widget(self, button):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True,
            message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK,
            text="Settings")
        dialog.format_secondary_text("Configure the following options:")
        combo = Gtk.ComboBoxText()
        for opt in ("Option A", "Option B", "Option C"):
            combo.append_text(opt)
        combo.set_active(0)
        check = Gtk.CheckButton(label="Enable feature")
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.pack_start(combo, False, False, 0)
        vbox.pack_start(check, False, False, 0)
        dialog.get_message_area().pack_start(vbox, False, False, 0)
        vbox.show_all()
        dialog.run()
        self._set_result(f"Widget dialog: {combo.get_active_text()!r}, enabled={check.get_active()}")
        dialog.destroy()


if __name__ == "__main__":
    window = DemoWindow()
    Gtk.main()
