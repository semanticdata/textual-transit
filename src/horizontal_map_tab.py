from textual.timer import Timer
from textual.widgets import Static

from .metro_api import DirectionDetector


class HorizontalMapTab(Static):
    refresh_timer: Timer | None = None
    # Marker styles for easy customization
    MARKER_STYLES = {
        "─": "[blue]─[/]",  # Horizontal line for tracks
        "⊖": "[blue]⊖[/]",  # Empty station marker
        "●": "[yellow]●[/]",  # Circle for stationary
        "►": "[cyan]►[/]",  # Right arrow for eastbound
        "◄": "[magenta]◄[/]",  # Left arrow for westbound
    }
    TRACK_SEGMENT_LENGTH = 4  # Spacing between stations

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.direction_detector = DirectionDetector()
        self.last_refresh_time = None

    def render_map_line(self, stations_data):
        """Render a horizontal map line showing all stations and trains."""
        # Create three lines: track, numbers, and station list
        track_line = ""
        number_line = ""
        station_lines = []

        # First create the track with markers and numbers
        for i, (stop, is_train) in enumerate(stations_data):
            # Add track segment with increased spacing
            if i > 0:
                track_line += self.MARKER_STYLES["─"] * self.TRACK_SEGMENT_LENGTH
                number_line += " " * self.TRACK_SEGMENT_LENGTH

            # Add station marker (⊖ for empty station, ● for train)
            marker = "●" if is_train else "⊖"
            track_line += self.MARKER_STYLES[marker]

            # Add station number (centered under marker)
            station_num = f"[blue]{i + 1}[/]"
            number_line += station_num

            # Format station label for the list
            label = f"[b]{stop}[/]"
            if is_train:
                label = f"[reverse]{label}[/]"
            station_lines.append(
                (f"{i + 1}. {label}", len(f"{i + 1}. {stop}"))
            )  # Store actual content length

        # Create the station list in two columns with proper alignment
        station_list = []
        mid_point = (len(station_lines) + 1) // 2
        left_column = station_lines[:mid_point]
        right_column = station_lines[mid_point:]

        # Calculate the maximum width needed for the left column
        # Use the stored content lengths that don't include markup
        max_left_width = max(length for _, length in left_column) + 5  # Add padding

        # Pad shorter column if needed
        while len(right_column) < len(left_column):
            right_column.append(("", 0))

        # Combine columns with calculated spacing
        for (left, left_len), (right, _) in zip(left_column, right_column):
            padding = " " * (max_left_width - left_len)
            if right:
                station_list.append(f"{left}{padding}{right}")
            else:
                station_list.append(left)

        # Combine all elements
        return f"{track_line}\n{number_line}\n\nStations:\n" + "\n".join(station_list)

    def render_legend(self):
        return (
            f"[b]{self.MARKER_STYLES['●']}[/b]: Train at station  "
            f"[b]{self.MARKER_STYLES['►']}[/b]: Eastbound  "
            f"[b]{self.MARKER_STYLES['◄']}[/b]: Westbound  "
            f"[b]{self.MARKER_STYLES['⊖']}[/b]: Empty station"
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
            get_blue_line_map,
            get_coordinates_list,
        )

        # Get both the line map and vehicle positions
        line_map = get_blue_line_map()
        vehicles = fetch_vehicle_positions()
        route_id = "901"  # Blue Line
        blue_line_vehicles = [v for v in vehicles if v["route_id"] == route_id]

        # Get station coordinates from metro_api
        station_coords = get_coordinates_list("blue")

        # Initialize all stops with track markers
        stop_markers = ["─" for _ in line_map]
        stop_directions = ["stationary" for _ in line_map]

        # Update markers based on vehicle positions and directions
        for v in blue_line_vehicles:
            vehicle_id = v["vehicle_id"]
            lon = v["longitude"]
            # Find closest stop index
            closest_idx = None
            min_dist = float("inf")
            for i, (_, s_lon) in enumerate(station_coords):
                dlon = s_lon - lon
                dist = abs(dlon)  # For horizontal map we care mainly about longitude
                if dist < min_dist:
                    min_dist = dist
                    closest_idx = i

            # Use DirectionDetector for horizontal direction detection
            direction = self.direction_detector.detect_horizontal_direction(
                vehicle_id, lon
            )
            marker = self.direction_detector.get_horizontal_marker(direction)

            if closest_idx is not None:
                stop_markers[closest_idx] = marker
                stop_directions[closest_idx] = direction

        # Update display with new markers
        lines = []
        stations_data = [(stop, is_train) for stop, is_train in line_map]
        lines.append(self.render_map_line(stations_data))
        lines.append("")  # Empty line for spacing
        lines.append(self.render_legend())

        # Update the content
        self.update("\n".join(lines))

        # Update the status bar
        now = datetime.now()
        self.last_refresh_time = now.strftime("%Y-%m-%d %H:%M:%S")
        bar = self.app.query_one("#horizontal_map_status_bar")
        bar.update_refresh_time(now)
