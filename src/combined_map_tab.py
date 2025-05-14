from textual.timer import Timer
from textual.widgets import Static

from .metro_api import (
    fetch_vehicle_positions,
    get_coordinates_list,
    get_station_coordinates,
)


class CombinedMapTab(Static):
    refresh_timer: Timer | None = None
    # Updated marker styles for better visibility
    BLUE_MARKER_STYLES = {
        "track": "[blue]║[/]",
        "station": "[blue]║[/]",
        "train": "[cyan on blue]⬤[/]",
        "north": "[cyan on blue]▲[/]",
        "south": "[magenta on blue]▼[/]",
    }
    GREEN_MARKER_STYLES = {
        "track": "[green]║[/]",
        "station": "[green]║[/]",
        "train": "[green]⬤[/]",
        "east": "[green]▶[/]",
        "west": "[magenta on green]◀[/]",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blue_vehicle_cache = {}
        self.blue_direction_cache = {}
        self.green_vehicle_cache = {}
        self.green_direction_cache = {}
        self.last_refresh_time = None

    def on_show(self):
        if not hasattr(self, "refresh_timer") or self.refresh_timer is None:
            self.refresh_timer = self.set_interval(5, self.refresh_map)
        self.refresh_map()

    def on_hide(self):
        if hasattr(self, "refresh_timer") and self.refresh_timer is not None:
            self.refresh_timer.stop()
            self.refresh_timer = None

    def render_station_line(self, blue_data, green_data, max_label_len=20):
        station_name, blue_marker = blue_data if blue_data else ("", "")
        green_station, green_marker = green_data if green_data else ("", "")

        # Format station names with consistent width
        blue_label = (
            f"[bright_white]{station_name:<{max_label_len}}[/]"
            if station_name
            else " " * max_label_len
        )
        green_label = (
            f"[bright_white]{green_station:<{max_label_len}}[/]"
            if green_station
            else " " * max_label_len
        )

        # Create track/marker visualization
        blue_vis = (
            self.BLUE_MARKER_STYLES.get(blue_marker, self.BLUE_MARKER_STYLES["track"])
            if blue_marker
            else " "
        )
        green_vis = (
            self.GREEN_MARKER_STYLES.get(
                green_marker, self.GREEN_MARKER_STYLES["track"]
            )
            if green_marker
            else " "
        )

        # Combine into single line with padding
        return f"{blue_label} {blue_vis}   {green_vis} {green_label}"

    def render_legend(self):
        blue_legend = (
            f"{self.BLUE_MARKER_STYLES['station']}: Station  "
            f"{self.BLUE_MARKER_STYLES['train']}: Train  "
            f"{self.BLUE_MARKER_STYLES['north']}: Northbound  "
            f"{self.BLUE_MARKER_STYLES['south']}: Southbound"
        )
        green_legend = (
            f"{self.GREEN_MARKER_STYLES['station']}: Station  "
            f"{self.GREEN_MARKER_STYLES['train']}: Train  "
            f"{self.GREEN_MARKER_STYLES['east']}: Eastbound  "
            f"{self.GREEN_MARKER_STYLES['west']}: Westbound"
        )
        return f"{blue_legend}\n{green_legend}"

    def refresh_map(self):
        from datetime import datetime

        # Get station data
        blue_stations = [station["name"] for station in get_station_coordinates("blue")]
        green_stations = [
            station["name"] for station in get_station_coordinates("green")
        ]

        # Get vehicle positions
        vehicles = fetch_vehicle_positions()
        blue_vehicles = [v for v in vehicles if v["route_id"] == "901"]
        green_vehicles = [v for v in vehicles if v["route_id"] == "902"]

        # Get coordinates for distance calculations
        blue_coords = get_coordinates_list("blue")
        green_coords = get_coordinates_list("green")

        def get_vehicle_at_station(coords, vehicles, station_idx):
            if not vehicles:
                return "station"

            station_lat, station_lon = coords[station_idx]
            for vehicle in vehicles:
                dlat = station_lat - vehicle["latitude"]
                dlon = station_lon - vehicle["longitude"]
                dist = dlat * dlat + dlon * dlon

                if dist < 0.0001:  # Threshold for considering a vehicle at a station
                    # Determine direction based on position relative to previous station
                    if station_idx > 0:
                        prev_lat, prev_lon = coords[station_idx - 1]
                        if abs(vehicle["latitude"] - prev_lat) > abs(
                            vehicle["longitude"] - prev_lon
                        ):
                            return (
                                "north" if vehicle["latitude"] > prev_lat else "south"
                            )
                        else:
                            return "east" if vehicle["longitude"] > prev_lon else "west"
                    return "train"
            return "station"

        # Build the map display
        lines = []
        max_label_len = max(
            max(len(name) for name in blue_stations),
            max(len(name) for name in green_stations),
        )

        # Add header
        lines.append(
            "[bold blue]Blue Line[/]"
            + " " * (max_label_len * 2)
            + "[bold green]Green Line[/]"
        )
        lines.append("-" * (max_label_len * 2 + 20))

        # Create station lines
        max_stations = max(len(blue_stations), len(green_stations))
        for i in range(max_stations):
            blue_data = (
                (
                    blue_stations[i],
                    get_vehicle_at_station(blue_coords, blue_vehicles, i),
                )
                if i < len(blue_stations)
                else None
            )
            green_data = (
                (
                    green_stations[i],
                    get_vehicle_at_station(green_coords, green_vehicles, i),
                )
                if i < len(green_stations)
                else None
            )
            lines.append(self.render_station_line(blue_data, green_data, max_label_len))

        # Add legend
        lines.append("")
        lines.append(self.render_legend())

        # Update display
        self.update("\n".join(lines))

        # Update status bar
        now = datetime.now()
        bar = self.app.query_one("#combined_map_status_bar")
        bar.update_refresh_time(now)
