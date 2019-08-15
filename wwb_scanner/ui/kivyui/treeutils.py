from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.treeview import TreeView, TreeViewNode
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import (
    ObjectProperty,
    DictProperty,
    StringProperty,
    ListProperty,
    BooleanProperty,
    OptionProperty,
)

class SortableNode(TreeViewNode):
    tree_view = ObjectProperty(None, allownone=True)
    sort_property_name = StringProperty('__index__')
    sort_property_uids = DictProperty()
    descending = BooleanProperty(False)
    def __init__(self, **kwargs):
        self._trigger_sort = None
        super(SortableNode, self).__init__(**kwargs)
        trigger = Clock.create_trigger(self._sort_children, 0)
        trigger()
        self._trigger_sort = trigger
    def on_nodes(self, *args):
        need_sort = False
        keys = set()
        for node in self.nodes:
            key = hash(node)
            keys.add(key)
            if key not in self.sort_property_uids:
                need_sort = True
                self._bind_child_prop(node)
        to_remove = keys - set(self.sort_property_uids.keys())
        for key in to_remove:
            uid, prop, node = self.sort_property_uids[key]
            self._unbind_child_prop(node)
        if need_sort and self._trigger_sort is not None:
            self._trigger_sort()
    def on_sort_property_name(self, instance, prop):
        if self._trigger_sort is None:
            return
        for node in self.nodes:
            self._unbind_child_prop(node)
            self._bind_child_prop(node)
        self._trigger_sort()
    def on_descending(self, instance, value):
        if self._trigger_sort is None:
            return
        self._trigger_sort()
    def _bind_child_prop(self, node):
        prop = self.sort_property_name
        if prop == '__index__':
            return
        key = hash(node)
        if key in self.sort_property_uids:
            return
        uid = node.fbind(prop, self.on_child_sort_property_value, property_name=prop)
        self.sort_property_uids[key] = (uid, prop, node)
    def _unbind_child_prop(self, node):
        key = hash(node)
        val = self.sort_property_uids.get(key)
        if val is None:
            return
        del self.sort_property_uids[key]
        uid, prop, node = val
        node.unbind_uid(prop, uid)
    def on_child_sort_property_value(self, instance, value, **kwargs):
        prop = kwargs.get('property_name')
        if prop != self.sort_property_name:
            return
        self._trigger_sort()
    def _sort_children(self, *args, **kwargs):
        tv = self.tree_view
        if tv is None:
            return
        prop = self.sort_property_name
        if prop == '__index__':
            return
        def iter_vals():
            vals = {getattr(n, prop) for n in self.nodes}
            if self.descending:
                it = reversed(sorted(vals))
            else:
                it = sorted(vals)
            for v in it:
                yield v
        def iter_nodes():
            yielded = set()
            nodes = set(self.nodes)
            for v in iter_vals():
                for n in nodes.copy():
                    if getattr(n, prop) != v:
                        continue
                    yield n
                    nodes.discard(n)

        nodes = [n for n in iter_nodes()]
        self.nodes = nodes
        tv._trigger_layout()

class SortableTreeViewLabel(Label, SortableNode):
    pass

class SortableTreeView(TreeView):
    def add_node(self, node, parent=None):
        if getattr(self, '_root', None) is None:
            node = SortableTreeViewLabel(text='Root', is_open=True, level=0)
            for key, value in self.root_options.items():
                setattr(node, key, value)
        node.tree_view = self
        super(SortableTreeView, self).add_node(node, parent)
        parent = node.parent_node
        if parent is not None:
            parent._bind_child_prop(node)
            parent._trigger_sort()
        return node
    def remove_node(self, node):
        node.tree_view = None
        super(SortableTreeView, self).remove_node(node)

class SortHeader(BoxLayout):
    cells = ListProperty()
    active_cell = ObjectProperty(None, allownone=True)
    descending = BooleanProperty(False)
    def add_widget(self, widget, index=0):
        super(SortHeader, self).add_widget(widget, index)
        if isinstance(widget, SortHeaderCell):
            self.cells.append(widget)
            widget.bind(
                selected=self.on_cell_selected,
                descending=self.on_cell_descending,
            )
    def on_active_cell(self, instance, cell):
        for w in self.cells:
            if w is cell:
                continue
            w.selected = False
        self.descending = cell.descending
    def on_cell_selected(self, instance, value):
        if not value:
            return
        self.active_cell = instance
    def on_cell_descending(self, instance, value):
        if not instance.selected:
            return
        self.descending = value

class SortHeaderCell(ButtonBehavior, BoxLayout):
    text = StringProperty()
    sort_property = StringProperty()
    selected = BooleanProperty(False)
    descending = BooleanProperty(False)
    icon_name = StringProperty('fa-sort')
    _inactive_icon_name = 'fa-sort'
    _active_icon_names = {True: 'fa-sort-desc', False: 'fa-sort-asc'}
    #_inactive_icon_name = u'\u21c5'
    #_active_icon_names = {True:u'\u25b2', False:u'\u25bc'}
    direction = OptionProperty('None', options=['up', 'down', 'None'])
    def on_release(self, *args):
        if self.selected:
            self.descending = not self.descending
        else:
            self.selected = True
    def on_selected(self, instance, value):
        if not value:
            self.descending = False
            self.direction = 'None'
            self.icon_name = self._inactive_icon_name
        else:
            if self.descending:
                self.direction = 'down'
            else:
                self.direction = 'up'
            self.icon_name = self._active_icon_names.get(self.descending)
    def on_descending(self, instance, value):
        if self.selected:
            if value:
                self.direction = 'down'
            else:
                self.direction = 'up'
            self.icon_name = self._active_icon_names.get(value)
