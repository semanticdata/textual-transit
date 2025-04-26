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
