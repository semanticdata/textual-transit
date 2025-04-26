from textual.widgets import Static
from textual.containers import Container
from metro_api import get_blue_line_map

from textual.timer import Timer

class BlueLineMapTab(Static):
    refresh_timer: Timer | None = None
    # Marker styles for easy customization
    MARKER_STYLES = {
        "│": "[blue]│[/]",
        "■": "[yellow]■[/]",
        "▲": "[cyan]▲[/]",
        "▼": "[magenta]▼[/]",
    }
    marker_col = 30  # Center marker (1-based)
    label_width = marker_col - 4
    width = 60

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vehicle_lat_cache = {}  # {vehicle_id: [prev_lat, curr_lat]}
        self.vehicle_direction_cache = {}  # {vehicle_id: direction: 'stationary'|'northbound'|'southbound'}
        self.last_refresh_time = None

    def render_map_line(self, stop, marker, is_train):
        import re
        def strip_markup(s):
            return re.sub(r'\[/?[a-zA-Z0-9 _]+\]', '', s)
        marker_colored = self.MARKER_STYLES.get(marker, marker)
        label = f"[b]{stop}[/]"
        label_bg = "[black on bright_white]"
        label_fmt = f"{label_bg}{label}[/]"
        if is_train:
            label_fmt = f"[reverse]{label_fmt}[/]"
        plain_label = strip_markup(stop)
        left = ' ' * (self.marker_col - 1)
        right = f"   {plain_label}"
        plain_line = f"{left}{marker}{right}"
        line = plain_line.replace(marker, marker_colored, 1)
        line = line.replace(plain_label, label_fmt, 1)
        return line

    def render_legend(self):
        return (
            f"[b]{self.MARKER_STYLES['■']}[/b]: Stationary  "
            f"[b]{self.MARKER_STYLES['▲']}[/b]: Northbound  "
            f"[b]{self.MARKER_STYLES['▼']}[/b]: Southbound  "
            f"[b]{self.MARKER_STYLES['│']}[/b]: Track"
        )

    def on_mount(self):
        # Start periodic refresh every 5 seconds
        self.set_interval(5, self.refresh_map)
        self.refresh_map()

    def refresh_map(self):
        from metro_api import fetch_vehicle_positions
        from datetime import datetime
        # Get both the line map and vehicle positions
        line_map = get_blue_line_map()
        vehicles = fetch_vehicle_positions()
        route_id = "901"  # Blue Line
        blue_line_vehicles = [v for v in vehicles if v["route_id"] == route_id]

        # For feedback: set last refresh time
        self.last_refresh_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        blue_line_stations = [
            "Target Field", "Warehouse District", "Nicollet Mall", "Government Plaza", "US Bank Stadium", "Cedar Riverside",
            "Franklin Ave", "Lake Street", "E 38th St", "E 46th St", "E 50th St", "Fort Snelling", "Terminal 1 Lindbergh",
            "Terminal 2 Humphrey", "American Blvd. E", "Bloomington Central", "30th Ave", "Mall of America"
        ]
        station_coords = [
            (44.98273774554354, -93.2771229326485),  # Target Field
            (44.980014848747246, -93.27308434620137),
            (44.97859138358841, -93.26996730048722),
            (44.97682283272789, -93.26587417721858),
            (44.97497444892588, -93.25997912687492),
            (44.96826934496696, -93.25096004322353),
            (44.962606137796016, -93.24707575602082),
            (44.94837340247245, -93.2389128467151),
            (44.93472240439674, -93.22950278794424),
            (44.920800325853165, -93.21992949097658),
            (44.912364183788824, -93.21009193673245),
            (44.893258537602065, -93.1980795103267),
            (44.88073555392563, -93.20493031246059),
            (44.87415531952441, -93.22414366084229),
            (44.85872035632548, -93.22316877441781),
            (44.8563874755882, -93.22640706749567),
            (44.855843564898116, -93.23157700023783),
            (44.85421891854283, -93.2388844110575),
        ]
        stop_markers = ["|" for _ in blue_line_stations]
        # Use instance cache
        cache = self.vehicle_lat_cache
        direction_cache = self.vehicle_direction_cache
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
            # Update direction cache: store last two latitudes
            if vehicle_id in cache:
                prevs = cache[vehicle_id]
                if len(prevs) == 2:
                    prevs = [prevs[1], lat]
                else:
                    prevs.append(lat)
                cache[vehicle_id] = prevs
            else:
                cache[vehicle_id] = [lat]
            prevs = cache[vehicle_id]
            # Direction logic
            if len(prevs) < 2:
                direction = direction_cache.get(vehicle_id, 'stationary')
            else:
                prev_lat, curr_lat = prevs
                old_direction = direction_cache.get(vehicle_id, 'stationary')
                if curr_lat > prev_lat:
                    if old_direction != 'northbound':
                        direction_cache[vehicle_id] = 'northbound'
                    direction = 'northbound'
                elif curr_lat < prev_lat:
                    if old_direction != 'southbound':
                        direction_cache[vehicle_id] = 'southbound'
                    direction = 'southbound'
                else:
                    # If already has a direction, keep it; else still stationary
                    direction = old_direction
            # Marker assignment
            if direction == 'stationary':
                marker = "■"
            elif direction == 'northbound':
                marker = "▲"
            elif direction == 'southbound':
                marker = "▼"
            else:
                marker = "■"
            stop_markers[closest_idx] = marker
        # Compose map lines
        import re
        def strip_markup(s):
            return re.sub(r'\[/?[a-zA-Z0-9 _]+\]', '', s)

        lines = []
        # Last refreshed info
        lines.append(f"[b]Last refreshed:[/] [cyan]{self.last_refresh_time}[/]")
        # Map body (no box, no spacing)
        for idx, (stop, is_train) in enumerate(line_map):
            marker = stop_markers[idx] if is_train else "│"
            lines.append(self.render_map_line(stop, marker, is_train))
        # Legend
        lines.append("")
        lines.append(self.render_legend())
        self.update("\n".join(lines))


