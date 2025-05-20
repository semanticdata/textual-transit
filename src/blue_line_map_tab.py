from textual.timer import Timer
from textual.widgets import Static

from .metro_api import get_blue_line_map


class BlueLineMapTab(Static):
    refresh_timer: Timer | None = None
    # Marker styles for easy customization
    MARKER_STYLES = {
        "║": "[blue]║[/]",  # Double vertical line for tracks
        "●": "[yellow]●[/]",  # Circle for stationary
        "▲": "[cyan]▲[/]",  # Up arrow for northbound
        "▼": "[magenta]▼[/]",  # Down arrow for southbound
    }
    marker_col = 30  # Center marker (1-based)
    label_width = marker_col - 4
    width = 60
    label_on_left = True  # Set to True to display label to the left of the marker

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .metro_api import DirectionDetector

        self.direction_detector = DirectionDetector()
        self.last_refresh_time = None

    def render_map_line(self, stop, marker, is_train, label_pad=0):
        import re

        def strip_markup(s):
            return re.sub(r"\[/?[a-zA-Z0-9 _]+\]", "", s)

        marker_colored = self.MARKER_STYLES.get(marker, marker)
        label = f"[b]{stop}[/]"
        label_bg = "[black on bright_white]"
        label_fmt = f"{label_bg}{label}[/]"
        if is_train:
            label_fmt = f"[reverse]{label_fmt}[/]"
        plain_label = strip_markup(stop)
        if self.label_on_left:
            # Pad label to align marker/track
            label_padded = label_fmt + " " * (label_pad - len(plain_label))
            plain_line = f"{label_padded} {marker}"
            line = plain_line.replace(marker, marker_colored, 1)
        else:
            # Marker left, label right (default)
            left = " " * (self.marker_col - 1)
            right = f"   {plain_label}"
            plain_line = f"{left}{marker}{right}"
            line = plain_line.replace(marker, marker_colored, 1)
            line = line.replace(plain_label, label_fmt, 1)
        return line

    def render_legend(self):
        return (
            f"[b]{self.MARKER_STYLES['●']}[/b]: Stationary  "
            f"[b]{self.MARKER_STYLES['▲']}[/b]: Northbound  "
            f"[b]{self.MARKER_STYLES['▼']}[/b]: Southbound  "
            f"[b]{self.MARKER_STYLES['║']}[/b]: Track"
        )

    def on_show(self):
        if not hasattr(self, "refresh_timer") or self.refresh_timer is None:
            self.refresh_timer = self.set_interval(5, self.refresh_map)
        self.refresh_map()

    def on_hide(self):
        if hasattr(self, "refresh_timer") and self.refresh_timer is not None:
            self.refresh_timer.stop()
            self.refresh_timer = None

    def refresh_map(self):
        from datetime import datetime

        from .metro_api import (
            fetch_vehicle_positions,
            get_coordinates_list,
        )

        # Get both the line map and vehicle positions
        line_map = get_blue_line_map()
        vehicles = fetch_vehicle_positions()
        route_id = "901"  # Blue Line
        blue_line_vehicles = [v for v in vehicles if v["route_id"] == route_id]

        # For feedback: set last refresh time and update the StatusBar widget
        now = datetime.now()
        self.last_refresh_time = now.strftime("%Y-%m-%d %H:%M:%S")
        bar = self.app.query_one("#blue_line_map_status_bar")
        bar.update_refresh_time(now)

        # Get station names from line_map helper
        blue_line_stations = [stop for stop, _ in line_map]
        stop_markers = ["║" for _ in blue_line_stations]  # Initialize with track markers

        # Get station coordinates from metro_api
        station_coords = get_coordinates_list("blue")

        for v in blue_line_vehicles:
            vehicle_id = v["vehicle_id"]
            lat = v["latitude"]
            # Find closest stop index
            closest_idx = None
            min_dist = float("inf")
            for i, (s_lat, s_lon) in enumerate(station_coords):
                dlat = s_lat - lat
                dlon = s_lon - v["longitude"]
                dist = dlat * dlat + dlon * dlon
                if dist < min_dist:
                    min_dist = dist
                    closest_idx = i

            # Use DirectionDetector for direction detection
            direction = self.direction_detector.detect_direction(vehicle_id, lat, is_latitude=True)
            marker = self.direction_detector.get_marker(direction)

            if closest_idx is not None:
                stop_markers[closest_idx] = marker

        # Update display
        lines = []
        if self.label_on_left:
            import re

            def strip_markup(s):
                return re.sub(r"\[/?[a-zA-Z0-9 _]+\]", "", s)

            max_label_len = max(len(strip_markup(stop)) for stop, _ in line_map)
        else:
            max_label_len = 0

        for idx, (stop, is_train) in enumerate(line_map):
            marker = stop_markers[idx]
            lines.append(self.render_map_line(stop, marker, is_train, label_pad=max_label_len))

        # Legend
        lines.append("")
        lines.append(self.render_legend())
        self.update("\n".join(lines))
