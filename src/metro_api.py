import requests
from typing import Dict, List
from google.transit import gtfs_realtime_pb2
from datetime import datetime


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

def get_blue_line_map(direction_id=0):
    """Return a list of (stop_name, is_train_present) for the Blue Line as a simple line map, using a static list of stations and coordinates."""
    # Static list of Blue Line stations and their coordinates
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
    stop_names = [station["name"] for station in blue_line_stations]
    stop_coords = [(station["latitude"], station["longitude"]) for station in blue_line_stations]

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
    line_map = [(name, idx in train_stop_indices) for idx, name in enumerate(stop_names)]
    return line_map


