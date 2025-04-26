from textual.widgets import Static
from textual.containers import Container
from textual.timer import Timer


class GreenLineMapTab(Static):
    refresh_timer: Timer | None = None
    # Marker styles for easy customization
    MARKER_STYLES = {
        "│": "[green]│[/]",
        "■": "[yellow]■[/]",
        "▲": "[green]▲[/]",  # northbound (or eastbound)
        "▼": "[magenta]▼[/]",  # southbound (or westbound)
    }
    marker_col = 30  # Center marker (1-based)
    label_width = marker_col - 4
    width = 60
    label_on_left = True  # Set to True to display label to the left of the marker

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vehicle_lat_cache = {}  # {vehicle_id: [prev_lat, curr_lat]}
        self.vehicle_direction_cache = {}  # {vehicle_id: direction: 'stationary'|'northbound'|'southbound'}
        self.last_refresh_time = None

    def on_show(self):
        if not hasattr(self, "refresh_timer") or self.refresh_timer is None:
            self.refresh_timer = self.set_interval(5, self.refresh_map)
        self.refresh_map()

    def on_hide(self):
        if hasattr(self, "refresh_timer") and self.refresh_timer is not None:
            self.refresh_timer.stop()
            self.refresh_timer = None

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
            f"[b]{self.MARKER_STYLES['■']}[/b]: Stationary  "
            f"[b]{self.MARKER_STYLES['▲']}[/b]: Eastbound  "
            f"[b]{self.MARKER_STYLES['▼']}[/b]: Westbound  "
            f"[b]{self.MARKER_STYLES['│']}[/b]: Track"
        )

    def refresh_map(self):
        from metro_api import get_green_line_map, fetch_vehicle_positions
        from datetime import datetime

        # Get both the line map and vehicle positions
        line_map = get_green_line_map()
        vehicles = fetch_vehicle_positions()
        route_id = "902"  # Green Line
        green_line_vehicles = [v for v in vehicles if v["route_id"] == route_id]

        # For feedback: set last refresh time and update the StatusBar widget
        now = datetime.now()
        self.last_refresh_time = now.strftime("%Y-%m-%d %H:%M:%S")
        bar = self.app.query_one("#green_line_map_status_bar")
        bar.update_refresh_time(now)

        # Get station names from line_map helper
        green_line_stations = [stop for stop, _ in line_map]
        stop_markers = ["|" for _ in green_line_stations]
        cache = self.vehicle_lat_cache
        direction_cache = self.vehicle_direction_cache
        for v in green_line_vehicles:
            vehicle_id = v["vehicle_id"]
            lat = v["latitude"]
            # Find closest stop index
            # Find closest station index using static coordinates
            lon = v["longitude"]
            lat = v["latitude"]
            closest_idx = None
            min_dist = float("inf")
            from metro_api import get_green_line_map

            # Use the same static stop_coords as in get_green_line_map
            green_line_stations = [
                {
                    "name": "Target Field",
                    "latitude": 44.98273774554354,
                    "longitude": -93.2771229326485,
                },
                {
                    "name": "Warehouse District",
                    "latitude": 44.980014848747246,
                    "longitude": -93.27308434620137,
                },
                {
                    "name": "Nicollet Mall",
                    "latitude": 44.97859138358841,
                    "longitude": -93.26996730048722,
                },
                {
                    "name": "Government Plaza",
                    "latitude": 44.97682283272789,
                    "longitude": -93.26587417721858,
                },
                {
                    "name": "US Bank Stadium",
                    "latitude": 44.97497444892588,
                    "longitude": -93.25997912687492,
                },
                {
                    "name": "West Bank",
                    "latitude": 44.97196769934245,
                    "longitude": -93.2461997537969,
                },
                {
                    "name": "East Bank",
                    "latitude": 44.9736831284348,
                    "longitude": -93.2310795958822,
                },
                {
                    "name": "Stadium Village",
                    "latitude": 44.974769032187794,
                    "longitude": -93.22284908650379,
                },
                {
                    "name": "Prospect Park",
                    "latitude": 44.971739958929184,
                    "longitude": -93.21526851217766,
                },
                {
                    "name": "Westgate",
                    "latitude": 44.96749418594883,
                    "longitude": -93.20650482681971,
                },
                {
                    "name": "Raymond Ave",
                    "latitude": 44.96308872510821,
                    "longitude": -93.19542804653175,
                },
                {
                    "name": "Fairview",
                    "latitude": 44.95640241986024,
                    "longitude": -93.17871653792054,
                },
                {
                    "name": "Snelling Ave",
                    "latitude": 44.955670967365386,
                    "longitude": -93.16699608189725,
                },
                {
                    "name": "Hamline Ave",
                    "latitude": 44.95571016984779,
                    "longitude": -93.15686019399725,
                },
                {
                    "name": "Lexington Pkwy",
                    "latitude": 44.95574071525549,
                    "longitude": -93.14663989651139,
                },
                {
                    "name": "Victoria St",
                    "latitude": 44.955728248423426,
                    "longitude": -93.13654287688762,
                },
                {
                    "name": "Dale St",
                    "latitude": 44.955720739133305,
                    "longitude": -93.12630030224975,
                },
                {
                    "name": "Western Ave",
                    "latitude": 44.95575656742864,
                    "longitude": -93.11613231272018,
                },
                {
                    "name": "Capitol / Rice St",
                    "latitude": 44.95572895657827,
                    "longitude": -93.10515789604243,
                },
                {
                    "name": "Robert St",
                    "latitude": 44.95401013976643,
                    "longitude": -93.09747973614937,
                },
                {
                    "name": "10th St E",
                    "latitude": 44.95059283019555,
                    "longitude": -93.0975146533736,
                },
                {
                    "name": "Central Station",
                    "latitude": 44.94619588548721,
                    "longitude": -93.09230931073459,
                },
                {
                    "name": "Union Depot",
                    "latitude": 44.948197817711616,
                    "longitude": -93.08681430434538,
                },
            ]
            stop_coords = [
                (station["latitude"], station["longitude"])
                for station in green_line_stations
            ]
            for i, (s_lat, s_lon) in enumerate(stop_coords):
                dlat = s_lat - lat
                dlon = s_lon - lon
                dist = dlat * dlat + dlon * dlon
                if dist < min_dist:
                    min_dist = dist
                    closest_idx = i
            # Update direction cache: store last two longitudes (for east/west detection)
            lon = v["longitude"]
            if vehicle_id in cache:
                prevs = cache[vehicle_id]
                if len(prevs) == 2:
                    prevs = [prevs[1], lon]
                else:
                    prevs.append(lon)
                cache[vehicle_id] = prevs
            else:
                cache[vehicle_id] = [lon]
            prevs = cache[vehicle_id]
            # Direction logic (eastbound/westbound)
            if len(prevs) < 2:
                direction = direction_cache.get(vehicle_id, "stationary")
            else:
                prev_lon, curr_lon = prevs
                old_direction = direction_cache.get(vehicle_id, "stationary")
                if curr_lon > prev_lon:
                    if old_direction != "eastbound":
                        direction_cache[vehicle_id] = "eastbound"
                    direction = "eastbound"
                elif curr_lon < prev_lon:
                    if old_direction != "westbound":
                        direction_cache[vehicle_id] = "westbound"
                    direction = "westbound"
                else:
                    direction = old_direction
            # Marker assignment
            if direction == "stationary":
                marker = "■"
            elif direction == "eastbound":
                marker = "▲"
            elif direction == "westbound":
                marker = "▼"
            else:
                marker = "■"
            # Only assign marker if closest_idx is valid
            if closest_idx is not None:
                stop_markers[closest_idx] = marker
        now = datetime.now()
        bar = self.app.query_one("#green_line_map_status_bar")
        bar.update_refresh_time(now)
        # Compose map lines
        lines = []
        # For left-label alignment, compute max label width
        if self.label_on_left:
            import re

            def strip_markup(s):
                return re.sub(r"\[/?[a-zA-Z0-9 _]+\]", "", s)

            max_label_len = max(len(strip_markup(stop)) for stop, _ in line_map)
        else:
            max_label_len = 0
        for idx, (stop, is_train) in enumerate(line_map):
            marker = stop_markers[idx] if is_train else "│"
            lines.append(
                self.render_map_line(stop, marker, is_train, label_pad=max_label_len)
            )
        # Legend
        lines.append("")
        lines.append(self.render_legend())
        self.update("\n".join(lines))
