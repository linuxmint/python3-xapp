#!/usr/bin/python3
"""
GTK3 List Editor Widget
A reusable widget for managing a list of strings with add, remove, edit, and reorder functionality.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject
from gi.repository import Pango

import gettext
_ = lambda s: gettext.dgettext("python-xapp", s)

class ListEditor(Gtk.Box):
    """A GTK3 widget for managing a list of strings."""

    __gsignals__ = {
        'list-changed': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Create the list store (model)
        self.list_store = Gtk.ListStore(str)

        # Validation and duplicate settings - all False by default
        self._validation_func = None
        self._allow_duplicates = False
        self._allow_ordering = False
        self._allow_add = False
        self._add_action = ""
        self._add_hint = ""
        self._allow_remove = False
        self._remove_action = ""
        self._allow_edit = False
        self._edit_action = ""
        self._edit_hint = ""
        self._allow_clear = False
        self._sort_func = lambda s: s.lower()
        self._auto_sort = True

        # Create main stack for view/edit modes
        self.main_stack = Gtk.Stack()
        self.main_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.main_stack.set_transition_duration(200)

        # VIEW MODE - List and toolbar
        self._create_view_mode()

        # EDIT MODE - Entry for add/edit
        self._create_edit_mode()

        # Add both modes to stack
        self.main_stack.add_named(self.view_box, "view")
        self.main_stack.add_named(self.edit_box, "edit")
        self.main_stack.set_visible_child_name("view")

        self.pack_start(self.main_stack, True, True, 0)

        # State tracking
        self._current_mode = "view"
        self._editing_item_path = None
        self._editing_iter = None

        # Apply initial visibility based on default settings
        self._update_button_visibility()

        # Initial button state
        self._update_button_sensitivity()

        # Apply initial sort
        self._apply_sort()

        self.show_all()

    def _create_view_mode(self):
        """Create the view mode layout with list and toolbar."""
        self.view_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Create the tree view
        self.tree_view = Gtk.TreeView(model=self.list_store)
        self.tree_view.set_headers_visible(False)

        # Create renderer and column
        self.text_renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("String", self.text_renderer, text=0)
        self.tree_view.append_column(column)

        # Enable drag and drop for reordering (initially disabled)
        self.tree_view.set_reorderable(False)
        self.tree_view.connect("drag-end", self._on_drag_end)
        self.tree_view.connect("row-activated", self._on_row_activated)

        # Create selection
        self.selection = self.tree_view.get_selection()
        self.selection.connect("changed", self._on_selection_changed)

        # Create scrolled window for tree view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        scrolled.add(self.tree_view)

        # Create toolbar for view mode
        self._create_view_toolbar()

        # Build view mode layout
        list_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        list_container.get_style_context().add_class("linked")
        list_container.pack_start(scrolled, True, True, 0)
        list_container.pack_start(self.view_toolbar, False, False, 0)

        self.view_box.pack_start(list_container, True, True, 0)

    def _create_view_toolbar(self):
        """Create the toolbar for view mode."""
        self.view_toolbar = Gtk.Toolbar()
        self.view_toolbar.get_style_context().add_class("inline-toolbar")
        self.view_toolbar.set_no_show_all(True)

        # Create tool item container
        tool_item = Gtk.ToolItem()
        tool_item.set_expand(True)
        tool_item.show()

        # Create button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        # Group 1: Add/Edit/Remove buttons (linked)
        button_group1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        button_group1.get_style_context().add_class("linked")

        self.btn_add = Gtk.Button()
        self.btn_add.set_image(Gtk.Image.new_from_icon_name("xsi-list-add-symbolic", Gtk.IconSize.BUTTON))
        self.btn_add.connect("clicked", self._on_add_clicked)
        self.btn_add.set_no_show_all(True)

        self.btn_edit = Gtk.Button()
        self.btn_edit.set_image(Gtk.Image.new_from_icon_name("xsi-document-edit-symbolic", Gtk.IconSize.BUTTON))
        self.btn_edit.connect("clicked", self._on_edit_clicked)
        self.btn_edit.set_no_show_all(True)

        self.btn_remove = Gtk.Button()
        self.btn_remove.set_image(Gtk.Image.new_from_icon_name("xsi-list-remove-symbolic", Gtk.IconSize.BUTTON))
        self.btn_remove.connect("clicked", self._on_remove_clicked)
        self.btn_remove.set_no_show_all(True)

        button_group1.pack_start(self.btn_add, False, False, 0)
        button_group1.pack_start(self.btn_edit, False, False, 0)
        button_group1.pack_start(self.btn_remove, False, False, 0)
        button_group1.show()

        # Group 2: Move buttons (linked)
        button_group2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        button_group2.get_style_context().add_class("linked")

        self.btn_move_up = Gtk.Button()
        self.btn_move_up.set_image(Gtk.Image.new_from_icon_name("xsi-go-up-symbolic", Gtk.IconSize.BUTTON))
        self.btn_move_up.set_tooltip_text(_("Move up"))
        self.btn_move_up.connect("clicked", self._on_move_up_clicked)
        self.btn_move_up.set_no_show_all(True)

        self.btn_move_down = Gtk.Button()
        self.btn_move_down.set_image(Gtk.Image.new_from_icon_name("xsi-go-down-symbolic", Gtk.IconSize.BUTTON))
        self.btn_move_down.set_tooltip_text(_("Move down"))
        self.btn_move_down.connect("clicked", self._on_move_down_clicked)
        self.btn_move_down.set_no_show_all(True)

        button_group2.pack_start(self.btn_move_up, False, False, 0)
        button_group2.pack_start(self.btn_move_down, False, False, 0)
        button_group2.show()

        # Group 3: Clear button (standalone but can be linked if other buttons added later)
        button_group3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        button_group3.get_style_context().add_class("linked")

        self.btn_clear = Gtk.Button()
        self.btn_clear.set_image(Gtk.Image.new_from_icon_name("xsi-user-trash-symbolic", Gtk.IconSize.BUTTON))
        self.btn_clear.connect("clicked", self._on_clear_clicked)
        self.btn_clear.set_no_show_all(True)

        button_group3.pack_start(self.btn_clear, False, False, 0)
        button_group3.show()

        # Pack all button groups
        button_box.pack_start(button_group1, False, False, 0)
        button_box.pack_start(button_group2, False, False, 0)
        button_box.pack_end(button_group3, False, False, 0)
        button_box.show()

        # Add button box to tool item
        tool_item.add(button_box)
        self.view_toolbar.insert(tool_item, -1)

    def _create_edit_mode(self):
        """Create the edit mode layout with entry and controls."""
        self.edit_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        # Entry area
        entry_frame = Gtk.Frame()
        entry_frame.set_shadow_type(Gtk.ShadowType.IN)

        self.title = Gtk.Label()
        attributes = Pango.AttrList()
        weight = Pango.attr_weight_new(Pango.Weight.BOLD)
        attributes.insert(weight)
        self.title.set_attributes(attributes)
        self.title.set_halign(Gtk.Align.START)

        self.hint = Gtk.Label()
        self.hint.set_halign(Gtk.Align.START)

        entry_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        entry_box.set_border_width(12)

        self.entry = Gtk.Entry()
        self.entry.connect("changed", self._on_entry_changed)
        self.entry.connect("activate", self._on_entry_activate)

        # Error label
        self.error_label = Gtk.Label()
        self.error_label.set_halign(Gtk.Align.START)
        self.error_label.set_no_show_all(True)

        # Action buttons
        action_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        action_buttons.set_halign(Gtk.Align.END)

        self.btn_cancel = Gtk.Button(label=_("Cancel"))
        self.btn_cancel.connect("clicked", self._on_cancel_clicked)

        self.btn_save = Gtk.Button(label=_("Save"))
        self.btn_save.get_style_context().add_class("suggested-action")
        self.btn_save.set_sensitive(False)
        self.btn_save.connect("clicked", self._on_save_clicked)

        action_buttons.pack_start(self.btn_cancel, False, False, 0)
        action_buttons.pack_start(self.btn_save, False, False, 0)

        entry_box.pack_start(self.title, False, False, 0)
        entry_box.pack_start(self.hint, False, False, 0)
        entry_box.pack_start(self.entry, False, False, 0)
        entry_box.pack_start(self.error_label, False, False, 0)
        entry_box.pack_start(action_buttons, False, False, 0)

        entry_frame.add(entry_box)

        self.edit_box.pack_start(entry_frame, True, True, 0)

    def _switch_to_view_mode(self):
        """Switch back to view mode."""
        self.main_stack.set_visible_child_name("view")
        self._current_mode = "view"
        self._editing_item_path = None
        self.entry.set_text("")
        self.error_label.hide()

    def _switch_to_edit_mode(self, mode="add", item_path=None, current_text=""):
        """Switch to edit mode."""
        self.main_stack.set_visible_child_name("edit")
        self._current_mode = "edit"
        self._editing_item_path = item_path

        if mode == "add":
            self.title.set_text(self._add_action)
            self.hint.set_text(self._add_hint)
            self.entry.set_text("")
        else:
            self.title.set_text(self._edit_action)
            self.hint.set_text(self._edit_hint)
            self.entry.set_text(current_text)

        self._validate_current_entry()
        self.entry.grab_focus()

    def _validate_current_entry(self):
        """Validate the current entry content and update UI."""
        text = self.entry.get_text()
        stripped_text = text.strip()

        if not stripped_text:
            self.entry.get_style_context().remove_class("error")
            self.error_label.hide()
            self.btn_save.set_sensitive(False)
            return

        is_valid, error = self._validate_entry(text,
            exclude_iter=self.list_store.get_iter(self._editing_item_path) if self._editing_item_path else None)

        if is_valid:
            self.entry.get_style_context().remove_class("error")
            self.error_label.hide()
            self.btn_save.set_sensitive(True)
        else:
            self.entry.get_style_context().add_class("error")
            self.error_label.set_markup(f'<span color="red">{error}</span>')
            self.error_label.show()
            self.btn_save.set_sensitive(False)

    def _save_current_entry(self):
        """Save the current entry based on mode."""
        text = self.entry.get_text()
        stripped_text = text.strip()
        if not stripped_text:
            return

        if self._editing_item_path:
            iter = self.list_store.get_iter(self._editing_item_path)
            self.list_store.set_value(iter, 0, text)

            if self._auto_sort and not self._allow_ordering:
                self._apply_sort()
        else:
            iter = self.list_store.append([text])

            if self._auto_sort and not self._allow_ordering:
                self._apply_sort()
                for row in self.list_store:
                    if row[0] == text:
                        self.selection.select_iter(row.iter)
                        break
            else:
                self.selection.select_iter(iter)

        self.emit('list-changed', self.get_strings())
        self._switch_to_view_mode()

    # Public API methods
    def set_validation_function(self, func):
        """
        Set a validation function for new/edited entries.

        The function should accept a string and return:
        - None if validation passes
        - An error string if validation fails
        """
        self._validation_func = func

    def set_allow_duplicates(self, allow):
        """Set whether duplicate entries are allowed."""
        self._allow_duplicates = allow

    def set_allow_ordering(self, allow):
        """Set whether manual ordering is allowed."""
        self._allow_ordering = allow
        self.tree_view.set_reorderable(allow)
        self._update_button_visibility()
        self._update_button_sensitivity()
        if not allow and self._auto_sort:
            self._apply_sort()

    def set_allow_add(self, allow, action=_("Add"), hint=""):
        """Set whether adding new items is allowed."""
        self._allow_add = allow
        self._add_action = action
        self._add_hint = hint
        self.btn_add.set_tooltip_text(action)
        self._update_button_visibility()

    def set_allow_remove(self, allow, action=_("Remove")):
        """Set whether removing items is allowed."""
        self._allow_remove = allow
        self._remove_action = action
        self.btn_remove.set_tooltip_text(action)
        self._update_button_visibility()

    def set_allow_edit(self, allow, action=_("Edit"), hint=""):
        """Set whether editing items is allowed."""
        self._allow_edit = allow
        self._edit_action = action
        self._edit_hint = hint
        self.btn_edit.set_tooltip_text(action)
        self._update_button_visibility()

    def set_allow_clear(self, allow, action=_("Remove all")):
        """Set whether clearing all items is allowed."""
        self._allow_clear = allow
        self.btn_clear.set_tooltip_text(action)
        self._update_button_visibility()

    def set_sort_function(self, func):
        """Set a sort function to keep the list sorted."""
        if func is False:
            self._auto_sort = False
            self._sort_func = None
        elif func is None:
            self._auto_sort = True
            self._sort_func = lambda s: s.lower()
        else:
            self._auto_sort = True
            self._sort_func = func

        if self._auto_sort:
            self._apply_sort()

    def get_strings(self):
        """Get all strings in the list as a Python list."""
        return [row[0] for row in self.list_store]

    def set_strings(self, strings):
        """Set the list content from a Python list of strings."""
        self.list_store.clear()
        valid_strings = []

        for string in strings:
            is_valid, error = self._validate_entry(string)
            if is_valid:
                valid_strings.append(string)

        if self._auto_sort and not self._allow_ordering and self._sort_func:
            try:
                valid_strings = sorted(valid_strings, key=self._sort_func)
            except:
                valid_strings = sorted(valid_strings, key=lambda s: s.lower())

        for string in valid_strings:
            self.list_store.append([string])

        self._update_button_sensitivity()
        self.emit('list-changed', self.get_strings())

    def add_string(self, string):
        """Add a single string to the list."""
        is_valid, error = self._validate_entry(string)
        if is_valid:
            self.list_store.append([string])

            if self._auto_sort and not self._allow_ordering:
                self._apply_sort()

            self._update_button_sensitivity()
            self.emit('list-changed', self.get_strings())
            return True
        return False

    # Internal methods
    def _update_button_visibility(self):
        """Update visibility of button groups based on allow settings."""
        self.btn_add.set_visible(self._allow_add)
        self.btn_edit.set_visible(self._allow_edit)
        self.btn_remove.set_visible(self._allow_remove)
        self.btn_move_up.set_visible(self._allow_ordering)
        self.btn_move_down.set_visible(self._allow_ordering)
        self.btn_clear.set_visible(self._allow_clear)
        self.view_toolbar.set_visible(self._allow_add or self._allow_edit or self._allow_remove
            or self._allow_ordering or self._allow_clear)

    def _apply_sort(self):
        """Apply sorting to the list if auto-sort is enabled."""
        if not self._auto_sort or not self._sort_func:
            return

        items = [row[0] for row in self.list_store]
        try:
            sorted_items = sorted(items, key=self._sort_func)
        except Exception:
            sorted_items = sorted(items, key=lambda s: s.lower())

        if items != sorted_items:
            self.list_store.clear()
            for item in sorted_items:
                self.list_store.append([item])

    def _validate_entry(self, text, exclude_iter=None):
        """Validate an entry based on custom validation and duplicate checking."""
        if not text:
            return (False, "")

        # Custom validation function
        if self._validation_func:
            try:
                result = self._validation_func(text)
                if result is not None:  # Validation failed - result is error message
                    return (False, result)
            except Exception as e:
                return (False, "")

        # Duplicate checking
        if not self._allow_duplicates:
            for row in self.list_store:
                if exclude_iter and self.list_store.get_path(row.iter) == self.list_store.get_path(exclude_iter):
                    continue
                if row[0] == text:
                    return (False, _("'%s' is already in the list.") % text)

        return (True, None)

    def _update_button_sensitivity(self):
        """Enable/disable buttons based on selection and list state."""
        model, iter = self.selection.get_selected()
        has_selection = iter is not None
        has_items = len(self.list_store) > 0

        if self._allow_remove:
            self.btn_remove.set_sensitive(has_selection)
        if self._allow_edit:
            self.btn_edit.set_sensitive(has_selection)
        if self._allow_clear:
            self.btn_clear.set_sensitive(has_items)

        if self._allow_ordering and has_selection:
            path = model.get_path(iter)
            index = path.get_indices()[0]
            self.btn_move_up.set_sensitive(index > 0)
            self.btn_move_down.set_sensitive(index < len(model) - 1)
        else:
            self.btn_move_up.set_sensitive(False)
            self.btn_move_down.set_sensitive(False)

    # Event handlers
    def _on_add_clicked(self, button):
        """Switch to add mode."""
        if self._allow_add:
            self._switch_to_edit_mode("add")

    def _on_edit_clicked(self, button):
        """Switch to edit mode for selected item."""
        if not self._allow_edit:
            return

        model, iter = self.selection.get_selected()
        if iter:
            path = model.get_path(iter)
            current_text = model.get_value(iter, 0)
            self._switch_to_edit_mode("edit", path, current_text)

    def _on_cancel_clicked(self, button):
        """Cancel editing and return to view mode."""
        self._switch_to_view_mode()

    def _on_save_clicked(self, button):
        """Save the current entry."""
        self._save_current_entry()

    def _on_entry_changed(self, entry):
        """Validate entry as user types."""
        self._validate_current_entry()

    def _on_entry_activate(self, entry):
        """Handle Enter key in entry."""
        if self.btn_save.get_sensitive():
            self._save_current_entry()

    def _on_drag_end(self, widget, context):
        if self._allow_ordering:
            self.emit('list-changed', self.get_strings())

    def _on_row_activated(self, tree_view, path, column):
        if self._allow_edit:
            current_text = self.list_store[path][0]
            self._switch_to_edit_mode("edit", path, current_text)

    def _on_selection_changed(self, selection):
        self._update_button_sensitivity()

    def _on_remove_clicked(self, button):
        if not self._allow_remove:
            return

        model, iter = self.selection.get_selected()
        if iter:
            item_text = model.get_value(iter, 0)

            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=_("Remove?")
            )
            dialog.format_secondary_text(_("Are you sure you want to remove '%s'?") % item_text)

            response = dialog.run()
            dialog.destroy()

            if response == Gtk.ResponseType.YES:
                next_iter = model.iter_next(iter)
                model.remove(iter)

                if next_iter:
                    self.selection.select_iter(next_iter)
                elif len(model) > 0:
                    last_path = Gtk.TreePath(len(model) - 1)
                    self.selection.select_path(last_path)

                self.emit('list-changed', self.get_strings())

        self._update_button_sensitivity()

    def _on_move_up_clicked(self, button):
        if not self._allow_ordering:
            return

        model, iter = self.selection.get_selected()
        if iter:
            path = model.get_path(iter)
            prev_path = Gtk.TreePath(path.get_indices()[0] - 1)
            prev_iter = model.get_iter(prev_path)
            model.swap(iter, prev_iter)
            self._update_button_sensitivity()
            self.emit('list-changed', self.get_strings())

    def _on_move_down_clicked(self, button):
        if not self._allow_ordering:
            return

        model, iter = self.selection.get_selected()
        if iter:
            next_iter = model.iter_next(iter)
            if next_iter:
                model.swap(iter, next_iter)
                self._update_button_sensitivity()
                self.emit('list-changed', self.get_strings())

    def _on_clear_clicked(self, button):
        if not self._allow_clear:
            return

        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=_("Remove all?")
        )
        dialog.format_secondary_text(_("This will remove all items from the list."))

        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            self.list_store.clear()
            self._update_button_sensitivity()
            self.emit('list-changed', self.get_strings())

        dialog.destroy()


class DemoWindow(Gtk.Window):
    """Demo window to showcase the StringListWidget."""

    def __init__(self):
        super().__init__(title="XApp.widgets.ListEditor() Demo")
        self.set_default_size(700, 600)
        self.set_border_width(12)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        self.string_list = ListEditor()
        self.string_list.connect("list-changed", self._on_list_changed)

        sample_strings = ["Zebra", "Apple", "Mango", "Banana", "Cherry"]
        self.string_list.set_strings(sample_strings)

        main_box.pack_start(self.string_list, True, True, 0)

        controls_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        controls_frame = Gtk.Frame(label="Controls")
        controls_frame.add(controls_box)

        order_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.ordering_check = Gtk.CheckButton(label="Allow manual ordering")
        self.ordering_check.set_active(False)
        self.ordering_check.connect("toggled", self._on_ordering_toggled)
        order_box.pack_start(self.ordering_check, False, False, 6)

        sort_label = Gtk.Label(label="Sort mode:")
        order_box.pack_start(sort_label, False, False, 0)

        self.sort_combo = Gtk.ComboBoxText()
        self.sort_combo.append("alpha", "Alphabetical")
        self.sort_combo.append("length", "By length")
        self.sort_combo.append("reverse", "Reverse alphabetical")
        self.sort_combo.append("none", "No auto-sort")
        self.sort_combo.set_active_id("alpha")
        self.sort_combo.connect("changed", self._on_sort_changed)
        order_box.pack_start(self.sort_combo, False, False, 0)

        controls_box.pack_start(order_box, False, False, 6)

        self.duplicate_check = Gtk.CheckButton(label="Allow duplicates")
        self.duplicate_check.set_active(False)
        self.duplicate_check.connect("toggled", self._on_duplicate_toggled)
        controls_box.pack_start(self.duplicate_check, False, False, 6)

        # Add controls for other allow options
        allow_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        self.add_check = Gtk.CheckButton(label="Allow add")
        self.add_check.set_active(False)
        self.add_check.connect("toggled", self._on_add_toggled)
        allow_box.pack_start(self.add_check, False, False, 0)

        self.remove_check = Gtk.CheckButton(label="Allow remove")
        self.remove_check.set_active(False)
        self.remove_check.connect("toggled", self._on_remove_toggled)
        allow_box.pack_start(self.remove_check, False, False, 0)

        self.edit_check = Gtk.CheckButton(label="Allow edit")
        self.edit_check.set_active(False)
        self.edit_check.connect("toggled", self._on_edit_toggled)
        allow_box.pack_start(self.edit_check, False, False, 0)

        self.clear_check = Gtk.CheckButton(label="Allow clear")
        self.clear_check.set_active(False)
        self.clear_check.connect("toggled", self._on_clear_toggled)
        allow_box.pack_start(self.clear_check, False, False, 0)

        controls_box.pack_start(allow_box, False, False, 6)

        val_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        val_label = Gtk.Label(label="Validation: No R letters allowed!")
        val_box.pack_start(val_label, False, False, 0)

        self.string_list.set_validation_function(self.no_r_allowed)

        controls_box.pack_start(val_box, False, False, 6)

        main_box.pack_start(controls_frame, False, False, 0)

        self.info_label = Gtk.Label()
        self._update_info_label()
        main_box.pack_start(self.info_label, False, False, 0)

        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        btn_get = Gtk.Button(label="Get List Content")
        btn_get.connect("clicked", self._on_get_content)
        status_box.pack_start(btn_get, False, False, 0)

        self.change_label = Gtk.Label()
        self.change_label.set_markup('<span color="gray">No changes yet</span>')
        status_box.pack_end(self.change_label, False, False, 0)

        main_box.pack_start(status_box, False, False, 0)

        self.add(main_box)
        self.connect("destroy", Gtk.main_quit)
        self.show_all()

    def no_r_allowed(self, text):
        if "r" in text.lower():
            return "There is an R in the text!!"
        return None

    def _update_info_label(self):
        if self.ordering_check.get_active():
            info = "Manual ordering enabled - use drag & drop or buttons"
        else:
            sort_mode = self.sort_combo.get_active_id()
            if sort_mode == "none":
                info = "Manual ordering disabled, no auto-sort"
            else:
                info = f"Auto-sorted: {self.sort_combo.get_active_text()}"

        self.info_label.set_markup(f'<span color="blue">{info}</span>')

    def _on_ordering_toggled(self, button):
        allow = button.get_active()
        self.string_list.set_allow_ordering(allow)
        self.sort_combo.set_sensitive(not allow)
        self._update_info_label()

    def _on_add_toggled(self, button):
        self.string_list.set_allow_add(button.get_active(), "Add a new thing", "Don't add rubbish now..")

    def _on_remove_toggled(self, button):
        self.string_list.set_allow_remove(button.get_active())

    def _on_edit_toggled(self, button):
        self.string_list.set_allow_edit(button.get_active(), "Edit this thing", "careful now..")

    def _on_clear_toggled(self, button):
        self.string_list.set_allow_clear(button.get_active())

    def _on_sort_changed(self, combo):
        sort_id = combo.get_active_id()

        if sort_id == "alpha":
            self.string_list.set_sort_function(lambda s: s.lower())
        elif sort_id == "length":
            self.string_list.set_sort_function(lambda s: (len(s), s.lower()))
        elif sort_id == "reverse":
            self.string_list.set_sort_function(lambda s: s.lower())
            self.string_list._sort_func = lambda s: ''.join(chr(255-ord(c)) for c in s.lower())
        elif sort_id == "none":
            self.string_list.set_sort_function(False)

        self._update_info_label()

    def _on_duplicate_toggled(self, button):
        self.string_list.set_allow_duplicates(button.get_active())

    def _on_list_changed(self, widget, strings):
        count = len(strings)
        self.change_label.set_markup(
            f'<span color="green">List changed! {count} items</span>'
        )
        GObject.timeout_add(2000, self._reset_change_label)

    def _reset_change_label(self):
        self.change_label.set_markup('<span color="gray">Waiting for changes...</span>')
        return False

    def _on_get_content(self, button):
        strings = self.string_list.get_strings()
        message = "Current list content:\n\n"
        if strings:
            message += "\n".join(f"• {s}" for s in strings)
        else:
            message += "(Empty list)"

        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="List Content"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()


if __name__ == "__main__":
    window = DemoWindow()
    Gtk.main()