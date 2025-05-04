from textual.widgets import Static
from textual.timer import Timer
from .metro_api import get_blue_line_map, DirectionDetector

class HorizontalMapTab(Static):
    refresh_timer: Timer | None = None
    # Marker styles for easy customization
    MARKER_STYLES = {
        "─": "[blue]─[/]",  # Horizontal line for tracks
        "●": "[yellow]●[/]",  # Circle for stationary
        "►": "[cyan]►[/]",  # Right arrow for eastbound
        "◄": "[magenta]◄[/]",  # Left arrow for westbound
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.direction_detector = DirectionDetector()
        self.last_refresh_time = None

    def render_map_line(self, stations_data):
        """Render a horizontal map line showing all stations and trains."""
        # Create the track line with stations
        track = ""
        labels = ""
        max_label_len = max(len(stop) for stop, _ in stations_data)
        
        for i, (stop, is_train) in enumerate(stations_data):
            # Add track segment
            if i > 0:
                track += self.MARKER_STYLES["─"] * 3
            
            # Add station marker
            marker = "●" if is_train else "─"
            track += self.MARKER_STYLES[marker]
            
            # Format station label
            label = f"[b]{stop}[/]"
            if is_train:
                label = f"[reverse]{label}[/]"
            
            # Pad label to align with station marker
            padded_label = f"{label:─^{max_label_len}}"
            labels += padded_label + " " * 3
        
        return f"{track}\n{labels}"

    def render_legend(self):
        return (
            f"[b]{self.MARKER_STYLES['●']}[/b]: Train at station  "
            f"[b]{self.MARKER_STYLES['►']}[/b]: Eastbound  "
            f"[b]{self.MARKER_STYLES['◄']}[/b]: Westbound  "
            f"[b]{self.MARKER_STYLES['─']}[/b]: Track"
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
        from .metro_api import (
            get_blue_line_map,
            fetch_vehicle_positions,
            get_station_coordinates,
            get_coordinates_list,
        )
        from datetime import datetime

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
            direction = self.direction_detector.detect_horizontal_direction(vehicle_id, lon)
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