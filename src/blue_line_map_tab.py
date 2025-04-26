from textual.widgets import Static
from textual.containers import Container
from metro_api import get_blue_line_map

class BlueLineMapTab(Static):
    def on_mount(self):
        self.refresh_map()

    def refresh_map(self):
        line_map = get_blue_line_map()
        # Build ASCII map string
        lines = []
        for stop, is_train in line_map:
            marker = "O" if is_train else "|"
            lines.append(f"{marker} {stop}")
        self.update("\n".join(lines))
