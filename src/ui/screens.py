from textual.screen import Screen
from textual.widgets import (
    Header, Footer, Label, DataTable,
)

from ..commands import registry


_CATEGORIES = [
    ("Generales", "general"),
    ("GlazeWM", "glazewm"),
    ("Sistema", "sistema"),
]


class CommandConfigScreen(Screen):
    BINDINGS = [
        ("q", "noop", ""),
    ]

    def action_noop(self):
        pass

    def compose(self):
        yield Header("Menu Comandos")
        yield Label(
            "Enter para activar/desactivar. Escape para salir.",
            id="config-label",
        )
        yield DataTable(id="cmd-table")
        yield Footer()

    def on_mount(self):
        self._dirty = False
        self._row_to_cmd = []
        table = self.query_one("#cmd-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("", "Comando", "Accion")
        for cat_label, cat_key in _CATEGORIES:
            cmds = [(i, c) for i, c in enumerate(registry.all()) if c.category == cat_key]
            if not cmds:
                continue
            self._row_to_cmd.append(None)
            table.add_row("", f"── {cat_label} ──", "")
            for cmd_idx, cmd in cmds:
                self._row_to_cmd.append(cmd_idx)
                icon = "✔" if cmd.enabled else "✘"
                table.add_row(icon, cmd.patterns[0], cmd.description)

    def on_data_table_row_selected(self, event):
        self._toggle_cursor()

    def _toggle_cursor(self):
        table = self.query_one("#cmd-table", DataTable)
        cursor = table.cursor_row
        if cursor is None or cursor >= len(self._row_to_cmd):
            return
        cmd_idx = self._row_to_cmd[cursor]
        if cmd_idx is None:
            return
        cmd = registry.all()[cmd_idx]
        cmd.enabled = not cmd.enabled
        table.update_cell_at((cursor, 0), "✔" if cmd.enabled else "✘")
        self._dirty = True

    def key_escape(self):
        self.dismiss(self._dirty)
