from textual.widgets import Static
from textual.containers import Container
from metro_api import get_blue_line_map

from textual.timer import Timer

class BlueLineMapTab(Static):
    refresh_timer: Timer | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vehicle_lat_cache = {}  # {vehicle_id: [prev_lat, curr_lat]}
        self.last_refresh_time = None

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
            # Determine marker
            if len(prevs) < 2:
                marker = "O"
            else:
                prev_lat, curr_lat = prevs
                if curr_lat > prev_lat:
                    marker = "▲"  # northbound
                elif curr_lat < prev_lat:
                    marker = "▼"  # southbound
                else:
                    marker = "O"  # stationary
            stop_markers[closest_idx] = marker
        # Compose map lines
        lines = []
        lines.append(f"Last refreshed: {self.last_refresh_time}")
        for idx, (stop, is_train) in enumerate(line_map):
            marker = stop_markers[idx] if is_train else "|"
            lines.append(f"{marker} {stop}")
        self.update("\n".join(lines))


