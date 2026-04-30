#!/usr/bin/python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class Dialog:
    """
    A builder for message dialogs. Instantiate with content, optionally add
    custom buttons, then call info(), warning(), error(), question() or dialog()
    to show it.

    If no buttons are added, sensible defaults are used based on the call type.
    """

    def __init__(self, parent, title=None, message=None, hint=None):
        self._parent = parent
        self._title = title
        self._message = message
        self._hint = hint
        self._buttons = []  # list of (label, response_id, style_class)
        self._widgets = [] # list of extra widgets to add below the message
        self._default_response_id = None

    def add_button(self, label, response_id, style=None):
        self._buttons.append((label, response_id, style))

    def add_widget(self, widget):
        self._widgets.append(widget)

    def set_default_response(self, response_id):
        self._default_response_id = response_id

    def _run(self, icon_name, default_buttons):
        dlg = Gtk.Dialog(
            title="",
            transient_for=self._parent,
            modal=True,
            destroy_with_parent=True,
        )
        dlg.set_default_size(360, -1)
        dlg.set_resizable(False)

        headerbar = Gtk.HeaderBar()
        headerbar.set_show_close_button(False)
        dlg.set_titlebar(headerbar)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            headerbar {
                background: @theme_bg_color;
                background-image: none;
                border: none;
                box-shadow: none;
                min-height: 0;
                padding: 0;
            }
        """)
        headerbar.get_style_context().add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Content grid: icon in col 0, labels in col 1
        grid = Gtk.Grid()
        grid.set_border_width(12)
        grid.set_column_spacing(12)
        grid.set_row_spacing(6)
        grid.set_halign(Gtk.Align.CENTER)

        row = 0

        if self._title:
            title_label = Gtk.Label()
            title_label.set_markup(f"<b><big>{self._title}</big></b>")
            title_label.set_xalign(0)
            title_label.set_line_wrap(True)
            title_label.set_max_width_chars(60)
            grid.attach(title_label, 1, row, 1, 1)
            row += 1

        if self._message is not None:
            message_label = Gtk.Label(label=self._message)
            message_label.set_xalign(0)
            message_label.set_line_wrap(True)
            message_label.set_max_width_chars(60)
            grid.attach(message_label, 1, row, 1, 1)
            row += 1

        if self._hint is not None:
            hint_label = Gtk.Label()
            hint_label.set_markup(f'<small><i>{self._hint}</i></small>')
            hint_label.set_xalign(0)
            hint_label.set_line_wrap(True)
            hint_label.set_max_width_chars(60)
            grid.attach(hint_label, 1, row, 1, 1)
            row += 1

        if icon_name is not None:
            image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
            image.set_valign(Gtk.Align.START)
            grid.attach(image, 0, 0, 1, row)

        dlg.get_content_area().add(grid)

        for widget in self._widgets:
            grid.attach(widget, 1, row, 1, 1)
            row += 1

        # Buttons
        button_box = dlg.get_action_area()
        button_box.get_style_context().remove_class("linked")
        button_box.set_margin_top(6)
        button_box.set_margin_bottom(6)
        button_box.set_margin_start(6)
        button_box.set_margin_end(6)
        button_box.set_spacing(6)

        buttons = self._buttons if self._buttons else default_buttons
        for label, response_id, style in buttons:
            btn = dlg.add_button(label, response_id)
            if style:
                btn.get_style_context().add_class(style)

        if self._default_response_id:
            dlg.set_default_response(self._default_response_id)

        dlg.show_all()
        response = dlg.run()
        for widget in self._widgets:
            grid.remove(widget)
        dlg.destroy()
        return response

    def info(self):
        return self._run("dialog-information", [(Gtk.STOCK_OK, Gtk.ResponseType.OK, None)])

    def warning(self):
        return self._run("dialog-warning", [(Gtk.STOCK_OK, Gtk.ResponseType.OK, None)])

    def error(self):
        return self._run("dialog-error", [(Gtk.STOCK_OK, Gtk.ResponseType.OK, None)])

    def question(self):
        """Returns True if the user clicked Yes, False otherwise."""
        response = self._run("dialog-question", [
            (Gtk.STOCK_NO,  Gtk.ResponseType.NO,  None),
            (Gtk.STOCK_YES, Gtk.ResponseType.YES, None),
        ])
        return response == Gtk.ResponseType.YES

    def dialog(self, icon_name=None):
        """Show a plain dialog with no message type icon, or a custom icon by name."""
        return self._run(icon_name, [(Gtk.STOCK_OK, Gtk.ResponseType.OK, None)])
