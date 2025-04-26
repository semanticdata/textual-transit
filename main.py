from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable, TabbedContent, TabPane
from textual.containers import Container
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from metro_api import MetroTransitAPI, fetch_service_alerts


class AlertsTable(DataTable):
    def update_alerts(self, alerts):
        self.clear()
        self.add_columns("Time", "Header", "Effect", "Cause", "Routes", "Description")
        for alert in alerts:
            if "error" in alert:
                self.add_row("-", alert["error"], "-", "-", "-", "-")
            else:
                self.add_row(
                    alert["timestamp"],
                    alert["header"],
                    alert["effect"],
                    alert["cause"],
                    (
                        ", ".join(alert["affected_routes"])
                        if alert["affected_routes"]
                        else "-"
                    ),
                    alert["description"],
                )


class RoutesTable(DataTable):
    def update_routes(self, routes):
        self.clear()
        self.add_columns("Route ID", "Route Label")
        for route in routes:
            self.add_row(route["route_id"], route["route_label"])

    def on_button_pressed(self, event):
        if event.button.id == "routes_btn":
            self.app.push_screen(RoutesScreen())


class TripUpdatesTable(DataTable):
    def update_trip_updates(self, updates):
        self.clear()
        self.add_columns(
            "Trip ID", "Route ID", "Schedule", "Stop ID", "Arrival", "Departure"
        )
        for update in updates:
            self.add_row(
                update["trip_id"],
                update["route_id"],
                str(update["schedule"]),
                update["stop_id"],
                update["arrival"],
                update["departure"],
            )


class VehiclePositionsTable(DataTable):
    def update_vehicle_positions(self, vehicles):
        self.clear()
        self.add_columns(
            "Vehicle ID",
            "Trip ID",
            "Route ID",
            "Latitude",
            "Longitude",
            "Speed",
            "Timestamp",
        )
        for v in vehicles:
            self.add_row(
                v["vehicle_id"],
                v["trip_id"],
                v["route_id"],
                str(v["latitude"]),
                str(v["longitude"]),
                str(v["speed"]),
                v["timestamp"],
            )


class TransitApp(App):
    CSS_PATH = None
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh alerts"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent():
            yield TabPane("Service Alerts", self._alerts_tab(), id="alerts_tab")
            yield TabPane("Routes", self._routes_tab(), id="routes_tab")
            yield TabPane(
                "Trip Updates", self._trip_updates_tab(), id="trip_updates_tab"
            )
            yield TabPane(
                "Vehicle Positions",
                self._vehicle_positions_tab(),
                id="vehicle_positions_tab",
            )
        yield Footer()

    def _alerts_tab(self):
        container = Container(
            Static("Transit Service Alerts", id="title", classes="bold"),
            AlertsTable(id="alerts_table"),
        )
        return container

    def _routes_tab(self):
        container = Container(
            Static("Available Transit Routes", id="title", classes="bold"),
            RoutesTable(id="routes_table"),
        )
        return container

    def _trip_updates_tab(self):
        container = Container(
            Static("Trip Updates", id="title", classes="bold"),
            TripUpdatesTable(id="trip_updates_table"),
        )
        return container

    def _vehicle_positions_tab(self):
        container = Container(
            Static("Vehicle Positions", id="title", classes="bold"),
            VehiclePositionsTable(id="vehicle_positions_table"),
        )
        return container

    def on_mount(self):
        self.refresh_alerts()
        self.refresh_routes()
        self.refresh_trip_updates()
        self.refresh_vehicle_positions()

    def on_tabbed_content_tab_activated(self, event):
        if event.tab.id == "alerts_tab":
            self.refresh_alerts()
        elif event.tab.id == "routes_tab":
            self.refresh_routes()
        elif event.tab.id == "trip_updates_tab":
            self.refresh_trip_updates()
        elif event.tab.id == "vehicle_positions_tab":
            self.refresh_vehicle_positions()

    def refresh_alerts(self):
        alerts = fetch_service_alerts()
        alerts_table = self.query_one("#alerts_table", AlertsTable)
        alerts_table.update_alerts(alerts)

    def refresh_routes(self):
        api = MetroTransitAPI()
        try:
            routes = api.get_routes()
        except Exception as e:
            routes = [{"route_id": "ERROR", "route_label": str(e)}]
        routes_table = self.query_one("#routes_table", RoutesTable)
        routes_table.update_routes(routes)

    def refresh_trip_updates(self):
        from metro_api import get_trip_updates

        updates = get_trip_updates()
        trip_updates_table = self.query_one("#trip_updates_table", TripUpdatesTable)
        trip_updates_table.update_trip_updates(updates)

    def refresh_vehicle_positions(self):
        from metro_api import fetch_vehicle_positions

        vehicles = fetch_vehicle_positions()
        vehicle_positions_table = self.query_one(
            "#vehicle_positions_table", VehiclePositionsTable
        )
        vehicle_positions_table.update_vehicle_positions(vehicles)


if __name__ == "__main__":
    TransitApp().run()
