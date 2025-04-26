from textual.widgets import Static
from datetime import datetime

class StatusBar(Static):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_refresh_time = None
        self._legend = self._make_legend()
        self._timer = None

    def on_mount(self):
        # Update every second
        self._timer = self.set_interval(1, self.update_message)

    def on_unmount(self):
        if self._timer:
            self._timer.stop()
            self._timer = None

    def update_refresh_time(self, dt: datetime):
        self.last_refresh_time = dt
        self._legend = self._make_legend()
        self.update_message()

    def _make_legend(self):
        now = datetime.now()
        if self.last_refresh_time:
            seconds_ago = int((now - self.last_refresh_time).total_seconds())
            ago_str = f"Last updated {seconds_ago} seconds ago"
            ts_str = self.last_refresh_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            ago_str = "Last updated just now"
            ts_str = now.strftime("%Y-%m-%d %H:%M:%S")
        # Return as a tuple for the footer legend
        return ("Last refreshed:", f"{ts_str} ({ago_str})")

    def update_message(self):
        now = datetime.now()
        if self.last_refresh_time:
            seconds_ago = int((now - self.last_refresh_time).total_seconds())
            ago_str = f"Last updated {seconds_ago} seconds ago"
            ts_str = self.last_refresh_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            ago_str = "Last updated just now"
            ts_str = now.strftime("%Y-%m-%d %H:%M:%S")
        self.update(f"[b]Last refreshed:[/] [cyan]{ts_str}[/]    [green]{ago_str}[/]")

    def get_legend(self):
        return self._legend
