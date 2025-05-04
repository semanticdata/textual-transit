import requests
from typing import Dict, List
from google.transit import gtfs_realtime_pb2
from datetime import datetime
from .station_data import BLUE_LINE_STATIONS, GREEN_LINE_STATIONS


class MetroTransitAPI:
    def __init__(self):
        self.base_url = "https://svc.metrotransit.org/nextripv2"

    def get_routes(self) -> List[Dict]:
        """Get all available routes"""
        response = requests.get(f"{self.base_url}/routes")
        response.raise_for_status()
        return response.json()

    def get_directions(self, route_id: str) -> List[Dict]:
        """Get directions for a specific route"""
        response = requests.get(f"{self.base_url}/directions/{route_id}")
        response.raise_for_status()
        return response.json()

    def get_stops(self, route_id: str, direction_id: int) -> List[Dict]:
        """Get stops for a route and direction"""
        response = requests.get(f"{self.base_url}/stops/{route_id}/{direction_id}")
        response.raise_for_status()
        return response.json()


class DirectionDetector:
    """Handles direction detection for transit vehicles using coordinate history"""

    def __init__(self):
        self.position_cache = {}  # {vehicle_id: [prev_pos, curr_pos]}
        self.direction_cache = {}  # {vehicle_id: current_direction}
        self.threshold = (
            0.0001  # Threshold to prevent small fluctuations from changing direction
        )

    def detect_direction(
        self, vehicle_id: str, coord: float, is_latitude: bool = True
    ) -> str:
        """Detect vehicle direction based on coordinate changes.

        Args:
            vehicle_id: The unique identifier of the vehicle
            coord: The current coordinate (latitude or longitude)
            is_latitude: If True, detect north/south, else detect east/west

        Returns:
            Direction as string: 'northbound'/'southbound' for latitude,
            'eastbound'/'westbound' for longitude, or 'stationary'
        """
        if vehicle_id in self.position_cache:
            prevs = self.position_cache[vehicle_id]
            if len(prevs) == 2:
                prevs = [prevs[1], coord]
            else:
                prevs.append(coord)
            self.position_cache[vehicle_id] = prevs
        else:
            self.position_cache[vehicle_id] = [coord]
            return self.direction_cache.get(vehicle_id, "stationary")

        prevs = self.position_cache[vehicle_id]
        if len(prevs) < 2:
            return self.direction_cache.get(vehicle_id, "stationary")

        prev_coord, curr_coord = prevs
        old_direction = self.direction_cache.get(vehicle_id, "stationary")
        coord_diff = curr_coord - prev_coord

        if abs(coord_diff) < self.threshold:
            return old_direction  # Maintain previous direction if change is small

        if is_latitude:
            # Latitude: increasing = northbound, decreasing = southbound
            if coord_diff > self.threshold:
                new_direction = "northbound"
            elif coord_diff < -self.threshold:
                new_direction = "southbound"
            else:
                return old_direction
        else:
            # Longitude: increasing = eastbound, decreasing = westbound
            if coord_diff > self.threshold:
                new_direction = "eastbound"
            elif coord_diff < -self.threshold:
                new_direction = "westbound"
            else:
                return old_direction

        if old_direction != new_direction:
            self.direction_cache[vehicle_id] = new_direction

        return new_direction

    def detect_horizontal_direction(self, vehicle_id: str, coord: float) -> str:
        """Detect vehicle direction based on longitude changes for horizontal display.

        Args:
            vehicle_id: The unique identifier of the vehicle
            coord: The current longitude coordinate

        Returns:
            Direction as string: 'eastbound', 'westbound', or 'stationary'
        """
        if vehicle_id in self.position_cache:
            prevs = self.position_cache[vehicle_id]
            if len(prevs) == 2:
                prevs = [prevs[1], coord]
            else:
                prevs.append(coord)
            self.position_cache[vehicle_id] = prevs
        else:
            self.position_cache[vehicle_id] = [coord]
            return self.direction_cache.get(vehicle_id, "stationary")

        prevs = self.position_cache[vehicle_id]
        if len(prevs) < 2:
            return self.direction_cache.get(vehicle_id, "stationary")

        prev_coord, curr_coord = prevs
        old_direction = self.direction_cache.get(vehicle_id, "stationary")
        coord_diff = curr_coord - prev_coord

        # Using a smaller threshold for longitude since changes are typically smaller
        threshold = 0.00005

        if abs(coord_diff) < threshold:
            return old_direction

        new_direction = "eastbound" if coord_diff > threshold else "westbound"
        
        if old_direction != new_direction:
            self.direction_cache[vehicle_id] = new_direction

        return new_direction

    def get_marker(self, direction: str) -> str:
        """Convert a direction to its corresponding marker symbol.

        Args:
            direction: One of 'northbound', 'southbound', 'eastbound', 'westbound', or 'stationary'

        Returns:
            The marker symbol to use for that direction
        """
        if direction == "stationary":
            return "●"
        elif direction in ("northbound", "eastbound"):
            return "▲"
        elif direction in ("southbound", "westbound"):
            return "▼"
        return "●"  # Default to stationary marker

    def get_horizontal_marker(self, direction: str) -> str:
        """Convert a direction to its corresponding horizontal marker symbol.

        Args:
            direction: One of 'eastbound', 'westbound', or 'stationary'

        Returns:
            The marker symbol to use for that direction
        """
        if direction == "stationary":
            return "●"
        elif direction == "eastbound":
            return "►"
        elif direction == "westbound":
            return "◄"
        return "●"  # Default to stationary marker


def fetch_service_alerts():
    """Fetch service alerts from Metro Transit GTFS realtime feed"""
    url = "https://svc.metrotransit.org/mtgtfs/alerts.pb"
    alerts_data = []
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        for entity in feed.entity:
            alert = entity.alert
            alert_data = {
                "id": entity.id,
                "header": (
                    alert.header_text.translation[0].text
                    if alert.header_text.translation
                    else "No header"
                ),
                "description": (
                    alert.description_text.translation[0].text
                    if alert.description_text.translation
                    else "No description"
                ),
                "effect": str(alert.effect) if alert.effect else "UNKNOWN_EFFECT",
                "cause": str(alert.cause) if alert.cause else "UNKNOWN_CAUSE",
                "affected_routes": [
                    ie.route_id for ie in alert.informed_entity if ie.route_id
                ],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            alerts_data.append(alert_data)
        return alerts_data
    except requests.exceptions.RequestException as e:
        return [{"error": f"Error fetching alerts: {e}"}]
    except Exception as e:
        return [{"error": f"Error processing alerts: {e}"}]


def fetch_trip_updates():
    """Fetch GTFS realtime trip updates from Metro Transit"""
    url = "https://svc.metrotransit.org/mtgtfs/tripupdates.pb"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        return feed
    except Exception as e:
        return None


def format_timestamp(timestamp):
    """Convert POSIX timestamp to readable datetime"""
    return datetime.fromtimestamp(timestamp).strftime("%I:%M %p")


def get_trip_updates():
    """Get trip updates in a format suitable for display"""
    feed = fetch_trip_updates()
    if not feed:
        return []
    updates = []
    for entity in feed.entity:
        if entity.HasField("trip_update"):
            trip = entity.trip_update.trip
            stop_time = None
            if entity.trip_update.stop_time_update:
                stop_time = entity.trip_update.stop_time_update[0]
            update = {
                "trip_id": trip.trip_id,
                "route_id": getattr(trip, "route_id", "N/A"),
                "schedule": getattr(trip, "schedule_relationship", "SCHEDULED"),
                "stop_id": stop_time.stop_id if stop_time else "N/A",
                "arrival": (
                    format_timestamp(stop_time.arrival.time)
                    if stop_time and stop_time.HasField("arrival")
                    else "N/A"
                ),
                "departure": (
                    format_timestamp(stop_time.departure.time)
                    if stop_time and stop_time.HasField("departure")
                    else "N/A"
                ),
            }
            updates.append(update)
    return updates


def fetch_vehicle_positions():
    """Fetch and parse vehicle position data from Metro Transit"""
    url = "https://svc.metrotransit.org/mtgtfs/vehiclepositions.pb"
    vehicles = []
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        for entity in feed.entity:
            vehicle = entity.vehicle
            timestamp = datetime.fromtimestamp(vehicle.timestamp)
            vehicle_data = {
                "vehicle_id": vehicle.vehicle.id,
                "trip_id": vehicle.trip.trip_id,
                "route_id": vehicle.trip.route_id,
                "latitude": vehicle.position.latitude,
                "longitude": vehicle.position.longitude,
                "speed": (
                    vehicle.position.speed
                    if vehicle.position.HasField("speed")
                    else "N/A"
                ),
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            }
            vehicles.append(vehicle_data)
        return vehicles
    except requests.RequestException as e:
        return []
    except Exception as e:
        return []


def get_station_coordinates(line_type: str):
    """Get station data for a specific line type.

    Args:
        line_type: Either 'blue' or 'green'

    Returns:
        List of station dictionaries with name, latitude, and longitude
    """
    if line_type.lower() == "blue":
        return BLUE_LINE_STATIONS
    elif line_type.lower() == "green":
        return GREEN_LINE_STATIONS
    else:
        raise ValueError("line_type must be either 'blue' or 'green'")


def get_coordinates_list(line_type: str):
    """Get a list of (latitude, longitude) tuples for a line.

    Args:
        line_type: Either 'blue' or 'green'

    Returns:
        List of (latitude, longitude) tuples
    """
    stations = get_station_coordinates(line_type)
    return [(station["latitude"], station["longitude"]) for station in stations]


def get_blue_line_map(direction_id=0):
    """Return a list of (stop_name, is_train_present) for the Blue Line as a simple line map, using a static list of stations and coordinates."""
    stop_names = [station["name"] for station in BLUE_LINE_STATIONS]
    stop_coords = [
        (station["latitude"], station["longitude"]) for station in BLUE_LINE_STATIONS
    ]

    route_id = "901"  # Blue Line
    # Get vehicle positions for Blue Line
    vehicles = fetch_vehicle_positions()
    blue_line_vehicles = [v for v in vehicles if v["route_id"] == route_id]
    # Find closest stop for each train
    train_stop_indices = set()
    for vehicle in blue_line_vehicles:
        min_dist = float("inf")
        closest_idx = None
        for i, (lat, lon) in enumerate(stop_coords):
            if lat is None or lon is None:
                continue
            dlat = lat - vehicle["latitude"]
            dlon = lon - vehicle["longitude"]
            dist = dlat * dlat + dlon * dlon
            if dist < min_dist:
                min_dist = dist
                closest_idx = i
        if closest_idx is not None:
            train_stop_indices.add(closest_idx)
    # Build map: list of (stop_name, is_train_present)
    line_map = [
        (name, idx in train_stop_indices) for idx, name in enumerate(stop_names)
    ]
    return line_map


def get_green_line_map(direction_id=0):
    """Return a list of (stop_name, is_train_present) for the Green Line as a simple line map, using a static list of stations and coordinates."""
    route_id = "902"  # Green Line
    stop_names = [station["name"] for station in GREEN_LINE_STATIONS]
    stop_coords = [
        (station["latitude"], station["longitude"]) for station in GREEN_LINE_STATIONS
    ]

    vehicles = fetch_vehicle_positions()
    green_line_vehicles = [v for v in vehicles if v["route_id"] == route_id]
    train_stop_indices = set()
    for vehicle in green_line_vehicles:
        min_dist = float("inf")
        closest_idx = None
        for i, (lat, lon) in enumerate(stop_coords):
            if lat is None or lon is None:
                continue
            dlat = lat - vehicle["latitude"]
            dlon = lon - vehicle["longitude"]
            dist = dlat * dlat + dlon * dlon
            if dist < min_dist:
                min_dist = dist
                closest_idx = i
        if closest_idx is not None:
            train_stop_indices.add(closest_idx)

    # Determine direction for each train (eastbound/westbound) by comparing longitude
    # Attach direction info for downstream use (e.g., GreenLineMapTab)
    # We'll return a list of (stop_name, is_train_present, direction) for clarity
    # But for now, preserve the original return signature
    return [(stop_names[i], i in train_stop_indices) for i in range(len(stop_names))]
