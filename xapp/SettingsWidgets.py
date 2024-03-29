#!/usr/bin/python3

import math
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('XApp', '1.0')
from gi.repository import Gio, Gtk, GObject, Gdk, GLib, XApp

settings_objects = {}

class EditableEntry (Gtk.Stack):

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_FIRST, None,
                    (str,))
    }

    def __init__ (self):
        super(EditableEntry, self).__init__()

        self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.set_transition_duration(150)

        self.label = Gtk.Label()
        self.entry = Gtk.Entry()
        self.button = Gtk.Button()

        self.button.set_alignment(1.0, 0.5)
        self.button.set_relief(Gtk.ReliefStyle.NONE)
        self.add_named(self.button, "button");
        self.add_named(self.entry, "entry");
        self.set_visible_child_name("button")
        self.editable = False
        self.current_text = None
        self.show_all()

        self.button.connect("released", self._on_button_clicked)
        self.button.connect("activate", self._on_button_clicked)
        self.entry.connect("activate", self._on_entry_validated)
        self.entry.connect("changed", self._on_entry_changed)
        self.entry.connect("focus-out-event", self._on_focus_lost)

    def set_text(self, text):
        self.button.set_label(text)
        self.entry.set_text(text)
        self.current_text = text

    def _on_focus_lost(self, widget, event):
        self.button.set_label(self.current_text)
        self.entry.set_text(self.current_text)

        self.set_editable(False)

    def _on_button_clicked(self, button):
        self.set_editable(True)
        self.entry.grab_focus()

    def _on_entry_validated(self, entry):
        self.set_editable(False)
        self.emit("changed", entry.get_text())
        self.current_text = entry.get_text()

    def _on_entry_changed(self, entry):
        self.button.set_label(entry.get_text())

    def set_editable(self, editable):
        if (editable):
            self.set_visible_child_name("entry")
        else:
            self.set_visible_child_name("button")
        self.editable = editable

    def set_tooltip_text(self, tooltip):
        self.button.set_tooltip_text(tooltip)

    def get_editable(self):
        return self.editable

    def get_text(self):
        return self.entry.get_text()

class SettingsStack(Gtk.Stack):
    def __init__(self):
        Gtk.Stack.__init__(self)
        self.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.set_transition_duration(150)
        self.expand = True

class SettingsRevealer(Gtk.Revealer):
    def __init__(self, schema=None, key=None, values=None, check_func=None):
        Gtk.Revealer.__init__(self)

        self.check_func = check_func

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        Gtk.Revealer.add(self, self.box)

        self.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.set_transition_duration(150)

        if schema:
            self.settings = Gio.Settings.new(schema)
            # if there aren't values or a function provided to determine visibility we can do a simple bind
            if values is None and check_func is None:
                self.settings.bind(key, self, "reveal-child", Gio.SettingsBindFlags.GET)
            else:
                self.values = values
                self.settings.connect("changed::" + key, self.on_settings_changed)
                self.on_settings_changed(self.settings, key)

    def add(self, widget):
        self.box.pack_start(widget, False, True, 0)

    #only used when checking values
    def on_settings_changed(self, settings, key):
        value = settings.get_value(key).unpack()
        if self.check_func is None:
            self.set_reveal_child(value in self.values)
        else:
            self.set_reveal_child(self.check_func(value, self.values))

class SettingsPage(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(30)
        self.set_margin_left(80)
        self.set_margin_right(80)
        self.set_margin_top(15)
        self.set_margin_bottom(15)

    def add_section(self, title=None, subtitle=None):
        section = SettingsSection(title, subtitle)
        self.pack_start(section, False, False, 0)

        return section

    def add_reveal_section(self, title, schema=None, key=None, values=None, revealer=None):
        section = SettingsSection(title)
        if revealer is None:
            revealer = SettingsRevealer(schema, key, values)
        revealer.add(section)
        section._revealer = revealer
        self.pack_start(revealer, False, False, 0)

        return section

class SettingsSection(Gtk.Box):
    def __init__(self, title=None, subtitle=None):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.set_spacing(10)

        self.always_show = False
        self.revealers = []

        if title or subtitle:
            header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            header_box.set_spacing(5)
            self.add(header_box)

            if title:
                label = Gtk.Label()
                label.set_markup("<b>%s</b>" % title)
                label.set_alignment(0, 0.5)
                header_box.add(label)

            if subtitle:
                sub = Gtk.Label()
                sub.set_text(subtitle)
                sub.get_style_context().add_class("dim-label")
                sub.set_alignment(0, 0.5)
                header_box.add(sub)

        self.frame = Gtk.Frame()
        self.frame.set_no_show_all(True)
        self.frame.set_shadow_type(Gtk.ShadowType.IN)
        frame_style = self.frame.get_style_context()
        frame_style.add_class("view")
        self.size_group = Gtk.SizeGroup()
        self.size_group.set_mode(Gtk.SizeGroupMode.VERTICAL)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.frame.add(self.box)
        self.add(self.frame)

        self.need_separator = False

    def add_row(self, widget):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        if self.need_separator:
            vbox.add(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        row = Gtk.ListBoxRow(can_focus=False)
        row.add(widget)
        if isinstance(widget, Switch):
            list_box.connect("row-activated", widget.clicked)
        list_box.add(row)
        vbox.add(list_box)
        self.box.add(vbox)

        self.update_always_show_state()

        self.need_separator = True

    def add_reveal_row(self, widget, schema=None, key=None, values=None, check_func=None, revealer=None):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        if self.need_separator:
            vbox.add(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        row = Gtk.ListBoxRow(can_focus=False)
        row.add(widget)
        if isinstance(widget, Switch):
            list_box.connect("row-activated", widget.clicked)
        list_box.add(row)
        vbox.add(list_box)
        if revealer is None:
            revealer = SettingsRevealer(schema, key, values, check_func)
        widget.revealer = revealer
        revealer.add(vbox)
        self.box.add(revealer)

        self.need_separator = True

        self.revealers.append(revealer)
        if not self.always_show:
            revealer.notify_id = revealer.connect('notify::child-revealed', self.check_reveal_state)
            self.check_reveal_state()

        return revealer

    def add_note(self, text):
        label = Gtk.Label()
        label.set_alignment(0, 0.5)
        label.set_markup(text)
        label.set_line_wrap(True)
        self.add(label)
        return label

    def update_always_show_state(self):
        if self.always_show:
            return

        self.frame.set_no_show_all(False)
        self.frame.show_all()
        self.always_show = True

        for revealer in self.revealers:
            revealer.disconnect(revealer.notify_id)

    def check_reveal_state(self, *args):
        for revealer in self.revealers:
            if revealer.props.child_revealed:
                self.box.show_all()
                self.frame.show()
                return

        self.frame.hide()

class SettingsWidget(Gtk.Box):
    def __init__(self, dep_key=None):
        Gtk.Box.__init__(self)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_spacing(20)
        self.set_border_width(5)
        self.set_margin_left(20)
        self.set_margin_right(20)

        if dep_key:
            self.set_dep_key(dep_key)

    def set_dep_key(self, dep_key):
        flag = Gio.SettingsBindFlags.GET
        if dep_key[0] == "!":
            dep_key = dep_key[1:]
            flag |= Gio.SettingsBindFlags.INVERT_BOOLEAN

        split = dep_key.split("/")
        dep_settings = Gio.Settings.new(split[0])
        dep_settings.bind(split[1], self, "sensitive", flag)

    def add_to_size_group(self, group):
        group.add_widget(self.content_widget)

    def fill_row(self):
        self.set_border_width(0)
        self.set_margin_left(0)
        self.set_margin_right(0)

    def get_settings(self, schema):
        global settings_objects
        try:
            return settings_objects[schema]
        except:
            settings_objects[schema] = Gio.Settings.new(schema)
            return settings_objects[schema]

class SettingsLabel(Gtk.Label):
    def __init__(self, text=None):
        Gtk.Label.__init__(self)
        if text:
            self.set_label(text)

        self.set_alignment(0.0, 0.5)
        self.set_line_wrap(True)

    def set_label_text(self, text):
        self.set_label(text)

class Switch(SettingsWidget):
    bind_prop = "active"
    bind_dir = Gio.SettingsBindFlags.DEFAULT

    def __init__(self, label, dep_key=None, tooltip=""):
        super(Switch, self).__init__(dep_key=dep_key)

        self.content_widget = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.label = SettingsLabel(label)
        self.pack_start(self.label, False, False, 0)
        self.pack_end(self.content_widget, False, False, 0)

        self.set_tooltip_text(tooltip)

    def clicked(self, *args):
        if self.is_sensitive():
            self.content_widget.set_active(not self.content_widget.get_active())

class SpinButton(SettingsWidget):
    bind_prop = "value"
    bind_dir = Gio.SettingsBindFlags.GET

    def __init__(self, label, units="", mini=None, maxi=None, step=1, page=None, size_group=None, dep_key=None, tooltip=""):
        super(SpinButton, self).__init__(dep_key=dep_key)

        self.timer = None

        if units:
            label += " (%s)" % units
        self.label = SettingsLabel(label)
        self.content_widget = Gtk.SpinButton()

        self.pack_start(self.label, False, False, 0)
        self.pack_end(self.content_widget, False, False, 0)

        range = self.get_range()
        if mini == None or maxi == None:
            mini = range[0]
            maxi = range[1]
        elif range is not None:
            mini = max(mini, range[0])
            maxi = min(maxi, range[1])

        if not page:
            page = step

        self.content_widget.set_range(mini, maxi)
        self.content_widget.set_increments(step, page)

        digits = 0
        if (step and '.' in str(step)):
            digits = len(str(step).split('.')[1])
        self.content_widget.set_digits(digits)

        self.content_widget.connect("value-changed", self.apply_later)

        self.set_tooltip_text(tooltip)

        if size_group:
            self.add_to_size_group(size_group)

    def apply_later(self, *args):
        def apply(self):
            self.set_value(self.content_widget.get_value())
            self.timer = None

        if self.timer:
            GLib.source_remove(self.timer)
        self.timer = GLib.timeout_add(300, apply, self)

class Entry(SettingsWidget):
    bind_prop = "text"
    bind_dir = Gio.SettingsBindFlags.DEFAULT

    def __init__(self, label, expand_width=False, size_group=None, dep_key=None, tooltip=""):
        super(Entry, self).__init__(dep_key=dep_key)

        self.label = SettingsLabel(label)
        self.content_widget = Gtk.Entry()
        self.content_widget.set_valign(Gtk.Align.CENTER)

        self.pack_start(self.label, False, False, 0)
        self.pack_end(self.content_widget, expand_width, expand_width, 0)

        self.set_tooltip_text(tooltip)

        if size_group:
            self.add_to_size_group(size_group)

class TextView(SettingsWidget):
    bind_prop = "text"
    bind_dir = Gio.SettingsBindFlags.DEFAULT

    def __init__(self, label, height=200, dep_key=None, tooltip=""):
        super(TextView, self).__init__(dep_key=dep_key)

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(8)

        self.label = Gtk.Label.new(label)
        self.label.set_halign(Gtk.Align.CENTER)

        self.scrolledwindow = Gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        self.scrolledwindow.set_size_request(width=-1, height=height)
        self.scrolledwindow.set_policy(hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                       vscrollbar_policy=Gtk.PolicyType.AUTOMATIC)
        self.scrolledwindow.set_shadow_type(type=Gtk.ShadowType.ETCHED_IN)
        self.content_widget = Gtk.TextView()
        self.content_widget.set_border_width(3)
        self.content_widget.set_wrap_mode(wrap_mode=Gtk.WrapMode.NONE)
        self.bind_object = self.content_widget.get_buffer()

        self.pack_start(self.label, False, False, 0)
        self.add(self.scrolledwindow)
        self.scrolledwindow.add(self.content_widget)
        self._value_changed_timer = None

class FontButton(SettingsWidget):
    bind_prop = "font-name"
    bind_dir = Gio.SettingsBindFlags.DEFAULT

    def __init__(self, label, level=(Gtk.FontChooserLevel.STYLE | Gtk.FontChooserLevel.SIZE), size_group=None, dep_key=None, tooltip=""):
        super(FontButton, self).__init__(dep_key=dep_key)

        self.label = SettingsLabel(label)

        self.content_widget = Gtk.FontButton()
        self.content_widget.set_valign(Gtk.Align.CENTER)

        self.pack_start(self.label, False, False, 0)
        self.pack_end(self.content_widget, False, False, 0)

        self.set_tooltip_text(tooltip)

        if size_group:
            self.add_to_size_group(size_group)

        if not (level & Gtk.FontChooserLevel.STYLE):
            # the level mechanism is broken in gtk - choosing a level that doesn't include styles (italics, bold, etc)
            # results in a list that only has one variant per family, but in many cases the selected font is bold or
            # italicized (but not consistenly), which is not only confusing, but kind of defeats the purpose. To work
            # around that, we supply our own filter function that removes the variants correctly. If it ever gets fixed
            # in gtk, this parsing function can be removed and the level argument added directly to the font button.
            def filter_func(fam, face):
                face_text = face.get_face_name().lower()
                for keyword in ['bold', 'italic', 'oblique']:
                    if keyword in face_text:
                        return False

                return True

            self.content_widget.set_filter_func(filter_func)

            # add the style level to avoid the issues above - it's because we're already filtering them out manually
            level |= Gtk.FontChooserLevel.STYLE

        self.content_widget.set_level(level)

class Range(SettingsWidget):
    bind_prop = "value"
    bind_dir = Gio.SettingsBindFlags.GET | Gio.SettingsBindFlags.NO_SENSITIVITY

    def __init__(self, label, min_label="", max_label="", mini=None, maxi=None, step=None, invert=False, log=False, show_value=True, dep_key=None, tooltip="", flipped=False, units="", digits=1):
        super(Range, self).__init__(dep_key=dep_key)

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(0)

        self.log = log
        self.invert = invert
        self.flipped = flipped
        self.timer = None
        self.value = 0
        self.digits = digits
        self.units = units

        hbox = Gtk.Box()

        self.label = Gtk.Label.new(label)
        self.label.set_halign(Gtk.Align.CENTER)

        self.min_label= Gtk.Label()
        self.max_label = Gtk.Label()
        self.min_label.set_alignment(1.0, 0.75)
        self.max_label.set_alignment(1.0, 0.75)
        self.min_label.set_margin_right(6)
        self.max_label.set_margin_left(6)
        self.min_label.set_markup("<i><small>%s</small></i>" % min_label)
        self.max_label.set_markup("<i><small>%s</small></i>" % max_label)

        range = self.get_range()
        if mini == None or maxi == None:
            mini = range[0]
            maxi = range[1]
        elif range is not None:
            mini = max(mini, range[0])
            maxi = min(maxi, range[1])

        if log:
            mini = math.log(mini)
            maxi = math.log(maxi)
            if self.flipped:
                self.map_get = lambda x: -1 * (math.log(x))
                self.map_set = lambda x: math.exp(x)
            else:
                self.map_get = lambda x: math.log(x)
                self.map_set = lambda x: math.exp(x)
        elif self.flipped:
            self.map_get = lambda x: x * -1
            self.map_set = lambda x: x * -1

        if self.flipped:
            tmp_mini = mini
            mini = maxi * -1
            maxi = tmp_mini * -1

        if step is None:
            self.step = (maxi - mini) * 0.02
        else:
            self.step = math.log(step) if log else step

        self.content_widget = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, mini, maxi, self.step)
        self.content_widget.set_inverted(invert)
        self.content_widget.set_draw_value(show_value and not self.flipped)
        self.bind_object = self.content_widget.get_adjustment()

        if self.units != "":
            def format_value(scale, value, data=None):
                return "{0:0.{prec}f}{1}".format(value, self.units, prec=self.digits)

            self.content_widget.connect("format-value", format_value)

        if invert:
            self.step *= -1 # Gtk.Scale.new_with_range want a positive value, but our custom scroll handler wants a negative value

        hbox.pack_start(self.min_label, False, False, 0)
        hbox.pack_start(self.content_widget, True, True, 0)
        hbox.pack_start(self.max_label, False, False, 0)

        self.pack_start(self.label, False, False, 0)
        self.pack_start(hbox, True, True, 6)

        self.content_widget.connect("scroll-event", self.on_scroll_event)
        self.content_widget.connect("value-changed", self.apply_later)

        if (not log) and self.step % 1 == 0:
            self.content_widget.connect("change-value", self.round_value_to_step)

        self.set_tooltip_text(tooltip)

    def round_value_to_step(self, widget, scroll, value, data=None):
        if value % self.step != 0:
            widget.set_value(round(value / self.step) * self.step)
            return True
        return False

    def apply_later(self, *args):
        def apply(self):
            if self.log:
                self.set_value(math.exp(abs(self.content_widget.get_value())))
            else:
                if self.flipped:
                    self.set_value(self.content_widget.get_value() * -1)
                else:
                    self.set_value(self.content_widget.get_value())
            self.timer = None

        if self.timer:
            GLib.source_remove(self.timer)
        self.timer = GLib.timeout_add(300, apply, self)

    def on_scroll_event(self, widget, event):
        found, delta_x, delta_y = event.get_scroll_deltas()

        # If you scroll up, delta_y < 0. This is a weird world
        widget.set_value(widget.get_value() - delta_y * self.step)

        return True

    def add_mark(self, value, position, markup):
        if self.log:
            self.content_widget.add_mark(math.log(value), position, markup)
        else:
            self.content_widget.add_mark(value, position, markup)

    def set_rounding(self, digits):
        if not self.log:
            self.digits = digits
            self.content_widget.set_round_digits(digits)
            self.content_widget.set_digits(digits)

class ComboBox(SettingsWidget):
    bind_dir = None

    def __init__(self, label, options=[], valtype=None, separator=None, size_group=None, dep_key=None, tooltip=""):
        super(ComboBox, self).__init__(dep_key=dep_key)

        self.valtype = valtype
        self.separator = separator
        self.option_map = {}

        self.label = SettingsLabel(label)

        self.content_widget = Gtk.ComboBox()
        renderer_text = Gtk.CellRendererText()
        self.content_widget.pack_start(renderer_text, True)
        self.content_widget.add_attribute(renderer_text, "text", 1)

        self.pack_start(self.label, False, False, 0)
        self.pack_end(self.content_widget, False, False, 0)
        self.content_widget.set_valign(Gtk.Align.CENTER)

        self.set_options(options)

        if separator:
            self.content_widget.set_row_separator_func(self.is_separator_row)

        self.set_tooltip_text(tooltip)

        if size_group:
            self.add_to_size_group(size_group)

    def on_my_value_changed(self, widget):
        tree_iter = widget.get_active_iter()
        if tree_iter != None:
            self.value = self.model[tree_iter][0]
            self.set_value(self.value)

    def on_setting_changed(self, *args):
        self.value = self.get_value()
        try:
            self.content_widget.set_active_iter(self.option_map[self.value])
        except:
            self.content_widget.set_active_iter(None)

    def connect_widget_handlers(self, *args):
        self.content_widget.connect('changed', self.on_my_value_changed)

    def set_options(self, options):
        if self.valtype is not None:
            var_type = self.valtype
        else:
            # assume all keys are the same type (mixing types is going to cause an error somewhere)
            var_type = type(options[0][0])
        self.model = Gtk.ListStore(var_type, str)

        for option in options:
            self.option_map[option[0]] = self.model.append([option[0], option[1]])

        self.content_widget.set_model(self.model)
        self.content_widget.set_id_column(0)

    def is_separator_row(self, model, tree_iter):
        if model[tree_iter][0] == self.separator:
            return True
        else:
            return False

class ColorChooser(SettingsWidget):
    bind_dir = None

    def __init__(self, label, legacy_string=False, size_group=None, dep_key=None, tooltip=""):
        super(ColorChooser, self).__init__(dep_key=dep_key)
        # note: Gdk.Color is deprecated in favor of Gdk.RGBA, but as the hex format is still used
        # in some places (most notably the desktop background handling in cinnamon-desktop) we
        # still support it for now by adding the legacy_string argument
        self.legacy_string = legacy_string

        self.label = SettingsLabel(label)
        self.content_widget = Gtk.ColorButton()
        self.content_widget.set_use_alpha(True)
        self.pack_start(self.label, False, False, 0)
        self.pack_end(self.content_widget, False, False, 0)

        self.set_tooltip_text(tooltip)

        if size_group:
            self.add_to_size_group(size_group)

    def on_setting_changed(self, *args):
        color_string = self.get_value()
        rgba = Gdk.RGBA()
        rgba.parse(color_string)
        self.content_widget.set_rgba(rgba)

    def connect_widget_handlers(self, *args):
        self.content_widget.connect('color-set', self.on_my_value_changed)

    def on_my_value_changed(self, widget):
        if self.legacy_string:
            color_string = self.content_widget.get_color().to_string()
        else:
            color_string = self.content_widget.get_rgba().to_string()
        self.set_value(color_string)

class FileChooser(SettingsWidget):
    bind_dir = None

    def __init__(self, label, dir_select=False, size_group=None, dep_key=None, tooltip=""):
        super(FileChooser, self).__init__(dep_key=dep_key)
        if dir_select:
            action = Gtk.FileChooserAction.SELECT_FOLDER
        else:
            action = Gtk.FileChooserAction.OPEN

        self.label = SettingsLabel(label)
        self.content_widget = Gtk.FileChooserButton(action=action)
        self.pack_start(self.label, False, False, 0)
        self.pack_end(self.content_widget, False, False, 0)

        self.set_tooltip_text(tooltip)

        if size_group:
            self.add_to_size_group(size_group)

    def on_file_selected(self, *args):
        self.set_value(self.content_widget.get_uri())

    def on_setting_changed(self, *args):
        self.content_widget.set_uri(self.get_value())

    def connect_widget_handlers(self, *args):
        self.content_widget.connect("file-set", self.on_file_selected)

class IconChooser(SettingsWidget):
    bind_prop = "icon"
    bind_dir = Gio.SettingsBindFlags.DEFAULT

    def __init__(self, label, default_icon=None, icon_categories=[], default_category=None, expand_width=False, size_group=None, dep_key=None, tooltip=""):
        super(IconChooser, self).__init__(dep_key=dep_key)

        self.label = SettingsLabel(label)

        self.content_widget = XApp.IconChooserButton()
        self.content_widget.set_icon_size(Gtk.IconSize.BUTTON)

        dialog = self.content_widget.get_dialog()
        if default_icon:
            dialog.set_default_icon(default_icon)

        for category in icon_categories:
            dialog.add_custom_category(category['name'], category['icons'])

        if default_category is not None:
            self.content_widget.set_default_category(default_category)

        self.pack_start(self.label, False, False, 0)
        self.pack_end(self.content_widget, expand_width, expand_width, 0)

        self.set_tooltip_text(tooltip)

        if size_group:
            self.add_to_size_group(size_group)

class Button(SettingsWidget):
    def __init__(self, label, callback=None):
        super(Button, self).__init__()
        self.label = label
        self.callback = callback

        self.content_widget = Gtk.Button(label=label)
        self.pack_start(self.content_widget, True, True, 0)
        self.content_widget.connect("clicked", self._on_button_clicked)

    def _on_button_clicked(self, *args):
        if self.callback is not None:
            self.callback(self)
        elif hasattr(self, "on_activated"):
            self.on_activated()
        else:
            print("warning: button '%s' does nothing" % self.label)

    def set_label(self, label):
        self.label = label
        self.content_widget.set_label(label)

class Text(SettingsWidget):
    def __init__(self, label, align=Gtk.Align.START):
        super(Text, self).__init__()
        self.label = label

        if align == Gtk.Align.END:
            xalign = 1.0
            justification = Gtk.Justification.RIGHT
        elif align == Gtk.Align.CENTER:
            xalign = 0.5
            justification = Gtk.Justification.CENTER
        else: # START and FILL align left
            xalign = 0
            justification = Gtk.Justification.LEFT

        self.content_widget = Gtk.Label(label, halign=align, xalign=xalign, justify=justification)
        self.content_widget.set_line_wrap(True)
        self.pack_start(self.content_widget, True, True, 0)
