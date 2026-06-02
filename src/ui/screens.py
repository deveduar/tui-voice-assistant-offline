from textual.screen import Screen
from textual.widgets import (
    Header, Footer, Label, ListView,
    ListItem, Button, DataTable,
)

from ..commands import registry


class MicConfigScreen(Screen):
    def __init__(self, mics):
        super().__init__()
        self.mics = mics

    def compose(self):
        yield Header("Seleccionar Microfono")
        yield Label("Elige un microfono (flechas + Enter):", id="mic-label")
        yield ListView(id="mic-list")
        yield Button("Confirmar", variant="primary", id="confirm-btn")
        yield Footer()

    def on_mount(self):
        lv = self.query_one("#mic-list", ListView)
        for idx, name in self.mics:
            lv.append(ListItem(Label(f"  [{idx}] {name}")))
        if self.mics:
            lv.index = 0

    def on_list_view_selected(self, event):
        lv = event.list_view
        if lv.index is not None and 0 <= lv.index < len(self.mics):
            self.dismiss(self.mics[lv.index][0])

    def on_button_pressed(self, event):
        if event.button.id == "confirm-btn":
            lv = self.query_one("#mic-list", ListView)
            if lv.index is not None and 0 <= lv.index < len(self.mics):
                self.dismiss(self.mics[lv.index][0])


class HelpScreen(Screen):
    def __init__(self, show_disabled=True):
        super().__init__()
        self.show_disabled = show_disabled

    def compose(self):
        yield Header("Ayuda - Comandos del Asistente")
        yield DataTable(id="help-table")
        yield Button("Cerrar", variant="primary", id="close-btn")
        yield Footer()

    def on_mount(self):
        table = self.query_one("#help-table", DataTable)
        table.add_columns("Comando", "Accion")
        for cmd in registry.all():
            if not self.show_disabled and not cmd.enabled:
                continue
            patterns_str = ", ".join(cmd.patterns)
            label = patterns_str if cmd.enabled else f"{patterns_str} (desactivado)"
            table.add_row(label, cmd.description)
        table.focus()

    def on_data_table_row_selected(self, event):
        self.dismiss()

    def on_button_pressed(self, event):
        if event.button.id == "close-btn":
            self.dismiss()

    def key_escape(self):
        self.dismiss()
