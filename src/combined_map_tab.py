from textual.widgets import Static
from textual.timer import Timer
from metro_api import get_blue_line_map, get_green_line_map, fetch_vehicle_positions
from datetime import datetime

class CombinedMapTab(Static):
    refresh_timer: Timer | None = None
    # Marker styles for easy customization
    BLUE_MARKER_STYLES = {
        "│": "[blue]│[/]",
        "■": "[yellow]■[/]",
        "▲": "[cyan]▲[/]",
        "▼": "[magenta]▼[/]",
    }
    GREEN_MARKER_STYLES = {
        "│": "[green]│[/]",
        "■": "[yellow]■[/]",
        "▲": "[green]▲[/]",
        "▼": "[magenta]▼[/]",
    }
    marker_col = 30  # Center marker (1-based)
    label_width = marker_col - 4
    width = 80
    label_on_left = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blue_vehicle_cache = {}
        self.blue_direction_cache = {}
        self.green_vehicle_cache = {}
        self.green_direction_cache = {}
        self.last_refresh_time = None

    def on_show(self):
        if not hasattr(self, 'refresh_timer') or self.refresh_timer is None:
            self.refresh_timer = self.set_interval(5, self.refresh_map)
        self.refresh_map()

    def on_hide(self):
        if hasattr(self, 'refresh_timer') and self.refresh_timer is not None:
            self.refresh_timer.stop()
            self.refresh_timer = None


    def render_map_line(self, blue_stop, blue_marker, blue_is_train, green_marker, green_is_train, green_stop, label_pad=0):
        import re
        def strip_markup(s):
            return re.sub(r'\[/?[a-zA-Z0-9 _]+\]', '', s)
        blue_marker_colored = self.BLUE_MARKER_STYLES.get(blue_marker, blue_marker)
        green_marker_colored = self.GREEN_MARKER_STYLES.get(green_marker, green_marker)
        blue_label = f"[b]{blue_stop}[/]"
        green_label = f"[b]{green_stop}[/]"
        blue_label_bg = "[black on bright_white]"
        green_label_bg = "[black on bright_white]"
        blue_label_fmt = f"{blue_label_bg}{blue_label}[/]"
        green_label_fmt = f"{green_label_bg}{green_label}[/]"
        if blue_is_train:
            blue_label_fmt = f"[reverse]{blue_label_fmt}[/]"
        if green_is_train:
            green_label_fmt = f"[reverse]{green_label_fmt}[/]"
        blue_plain_label = strip_markup(blue_stop)
        green_plain_label = strip_markup(green_stop)
        # Pad blue label to align marker/track
        blue_label_padded = blue_label_fmt + ' ' * (label_pad - len(blue_plain_label))
        green_label_padded = green_label_fmt + ' ' * (label_pad - len(green_plain_label))
        # Compose the combined line: blue label | blue marker | green marker | green label
        line = f"{blue_label_padded} {blue_marker_colored}   {green_marker_colored} {green_label_padded}"
        return line

    def render_legend(self):
        return (
            f"[b]{self.BLUE_MARKER_STYLES['■']}[/b]: Stationary  "
            f"[b]{self.BLUE_MARKER_STYLES['▲']}[/b]: Northbound  "
            f"[b]{self.BLUE_MARKER_STYLES['▼']}[/b]: Southbound  "
            f"[b]{self.GREEN_MARKER_STYLES['▲']}[/b]: Eastbound  "
            f"[b]{self.GREEN_MARKER_STYLES['▼']}[/b]: Westbound  "
            f"[b]{self.BLUE_MARKER_STYLES['│']}[/b]: Blue Line Track  "
            f"[b]{self.GREEN_MARKER_STYLES['│']}[/b]: Green Line Track"
        )

    def refresh_map(self):
        from metro_api import fetch_vehicle_positions
        from datetime import datetime
        # Get static maps
        blue_line_map = get_blue_line_map()
        green_line_map = get_green_line_map()
        blue_stations = [stop for stop, _ in blue_line_map]
        green_stations = [stop for stop, _ in green_line_map]
        # Static station coordinates (copied from metro_api.py)
        blue_line_stations = [
            {"name": "Target Field", "latitude": 44.98273774554354, "longitude": -93.2771229326485},
            {"name": "Warehouse District", "latitude": 44.980014848747246, "longitude": -93.27308434620137},
            {"name": "Nicollet Mall", "latitude": 44.97859138358841, "longitude": -93.26996730048722},
            {"name": "Government Plaza", "latitude": 44.97682283272789, "longitude": -93.26587417721858},
            {"name": "US Bank Stadium", "latitude": 44.97497444892588, "longitude": -93.25997912687492},
            {"name": "Cedar Riverside", "latitude": 44.96826934496696, "longitude": -93.25096004322353},
            {"name": "Franklin Ave", "latitude": 44.962606137796016, "longitude": -93.24707575602082},
            {"name": "Lake Street", "latitude": 44.94837340247245, "longitude": -93.2389128467151},
            {"name": "E 38th St", "latitude": 44.93472240439674, "longitude": -93.22950278794424},
            {"name": "E 46th St", "latitude": 44.920800325853165, "longitude": -93.21992949097658},
            {"name": "E 50th St", "latitude": 44.912364183788824, "longitude": -93.21009193673245},
            {"name": "Fort Snelling", "latitude": 44.893258537602065, "longitude": -93.1980795103267},
            {"name": "Terminal 1 Lindbergh", "latitude": 44.88073555392563, "longitude": -93.20493031246059},
            {"name": "Terminal 2 Humphrey", "latitude": 44.87415531952441, "longitude": -93.22414366084229},
            {"name": "American Blvd. E", "latitude": 44.85872035632548, "longitude": -93.22316877441781},
            {"name": "Bloomington Central", "latitude": 44.8563874755882, "longitude": -93.22640706749567},
            {"name": "30th Ave", "latitude": 44.855843564898116, "longitude": -93.23157700023783},
            {"name": "Mall of America", "latitude": 44.85421891854283, "longitude": -93.2388844110575},
        ]
        green_line_stations = [
            {"name": "Target Field", "latitude": 44.98273774554354, "longitude": -93.2771229326485},
            {"name": "Warehouse District", "latitude": 44.980014848747246, "longitude": -93.27308434620137},
            {"name": "Nicollet Mall", "latitude": 44.97859138358841, "longitude": -93.26996730048722},
            {"name": "Government Plaza", "latitude": 44.97682283272789, "longitude": -93.26587417721858},
            {"name": "US Bank Stadium", "latitude": 44.97497444892588, "longitude": -93.25997912687492},
            {"name": "West Bank", "latitude": 44.97358033375315, "longitude": -93.24327694824411},
            {"name": "East Bank", "latitude": 44.97239212668269, "longitude": -93.2358258120996},
            {"name": "Stadium Village", "latitude": 44.97239212668269, "longitude": -93.22497335430691},
            {"name": "Prospect Park", "latitude": 44.971739958929184, "longitude": -93.21526851217766},
            {"name": "Westgate", "latitude": 44.96749418594883, "longitude": -93.20650482681971},
            {"name": "Raymond Ave", "latitude": 44.96308872510821, "longitude": -93.19542804653175},
            {"name": "Fairview", "latitude": 44.95640241986024, "longitude": -93.17871653792054},
            {"name": "Snelling Ave", "latitude": 44.955670967365386, "longitude": -93.16699608189725},
            {"name": "Lexington Pkwy", "latitude": 44.95561534413747, "longitude": -93.1465576641505},
            {"name": "Victoria St", "latitude": 44.95553260886939, "longitude": -93.13297734221652},
            {"name": "Dale St", "latitude": 44.95548613234419, "longitude": -93.12369004564545},
            {"name": "Western Ave", "latitude": 44.9554408663451, "longitude": -93.11734185895557},
            {"name": "Robert St", "latitude": 44.94893285666344, "longitude": -93.09923749370954},
            {"name": "10th St", "latitude": 44.94866632452591, "longitude": -93.09466742023244},
            {"name": "Central", "latitude": 44.94850503452919, "longitude": -93.09214576888003},
            {"name": "Union Depot", "latitude": 44.948197817711616, "longitude": -93.08681430434538},
        ]
        blue_coords = [(s["latitude"], s["longitude"]) for s in blue_line_stations]
        green_coords = [(s["latitude"], s["longitude"]) for s in green_line_stations]
        # Fetch vehicles and filter by line
        vehicles = fetch_vehicle_positions()
        blue_vehicles = [v for v in vehicles if v["route_id"] == "901"]
        green_vehicles = [v for v in vehicles if v["route_id"] == "902"]
        # Find train indices and marker types for both lines
        def get_train_indices(stations, coords, vehicles, is_green=False):
            train_indices = {}
            for v in vehicles:
                min_dist = float("inf")
                closest_idx = None
                for i, (lat, lon) in enumerate(coords):
                    dlat = lat - v["latitude"]
                    dlon = lon - v["longitude"]
                    dist = dlat * dlat + dlon * dlon
                    if dist < min_dist:
                        min_dist = dist
                        closest_idx = i
                if closest_idx is not None:
                    # Determine marker by direction
                    direction = v.get("direction", "stationary")
                    if direction == "stationary":
                        marker = "■"
                    elif is_green:
                        marker = "▲" if v.get("bearing", 90) > 90 else "▼"  # crude east/west
                    else:
                        marker = "▲" if v.get("bearing", 0) < 180 else "▼"  # crude north/south
                    train_indices[closest_idx] = marker
            return train_indices
        blue_trains = get_train_indices(blue_stations, blue_coords, blue_vehicles)
        green_trains = get_train_indices(green_stations, green_coords, green_vehicles, is_green=True)
        # Compose map lines
        now = datetime.now()
        bar = self.app.query_one("#combined_map_status_bar")
        bar.update_refresh_time(now)
        lines = []
        import re
        def strip_markup(s):
            return re.sub(r'\[/?[a-zA-Z0-9 _]+\]', '', s)
        max_label_len = max(
            max(len(strip_markup(stop)) for stop in blue_stations),
            max(len(strip_markup(stop)) for stop in green_stations)
        )
        max_len = max(len(blue_stations), len(green_stations))
        for idx in range(max_len):
            blue_stop = blue_stations[idx] if idx < len(blue_stations) else ""
            green_stop = green_stations[idx] if idx < len(green_stations) else ""
            # Blue marker logic
            if blue_stop:
                if idx in blue_trains:
                    blue_marker = blue_trains[idx]
                    blue_is_train = True
                else:
                    blue_marker = "│"
                    blue_is_train = False
            else:
                blue_marker = ""
                blue_is_train = False
            # Green marker logic
            if green_stop:
                if idx in green_trains:
                    green_marker = green_trains[idx]
                    green_is_train = True
                else:
                    green_marker = "│"
                    green_is_train = False
            else:
                green_marker = ""
                green_is_train = False
            lines.append(self.render_map_line(blue_stop, blue_marker, blue_is_train, green_marker, green_is_train, green_stop, label_pad=max_label_len))
        lines.append("")
        lines.append(self.render_legend())
        self.update("\n".join(lines))
