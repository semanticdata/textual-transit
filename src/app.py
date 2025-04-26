from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable, TabbedContent, TabPane
from textual.containers import Container
from src.blue_line_map_tab import BlueLineMapTab
from src.green_line_map_tab import GreenLineMapTab
from metro_api import MetroTransitAPI, fetch_service_alerts

class BaseTable(DataTable):
    def update_table(self, columns, rows):
        self.clear()
        self.add_columns(*columns)
        for row in rows:
            self.add_row(*row)

class AlertsTable(BaseTable):
    def update_alerts(self, alerts):
        columns = ["Timestamp", "Header", "Effect", "Cause", "Routes", "Description"]
        rows = []
        for alert in alerts:
            if "error" in alert:
                rows.append(("-", alert["error"], "-", "-", "-", "-"))
            else:
                rows.append((
                    alert["timestamp"],
                    alert["header"],
                    alert["effect"],
                    alert["cause"],
                    ", ".join(alert["affected_routes"]) if alert["affected_routes"] else "-",
                    alert["description"],
                ))
        self.update_table(columns, rows)

class RoutesTable(BaseTable):
    def update_routes(self, routes):
        columns = ["Route ID", "Route Label"]
        rows = [(route["route_id"], route["route_label"]) for route in routes]
        self.update_table(columns, rows)

class TripUpdatesTable(BaseTable):
    def update_trip_updates(self, updates):
        columns = ["Trip ID", "Route ID", "Schedule", "Stop ID", "Arrival", "Departure"]
        rows = [(
            update["trip_id"],
            update["route_id"],
            str(update["schedule"]),
            update["stop_id"],
            update["arrival"],
            update["departure"],
        ) for update in updates]
        self.update_table(columns, rows)

class VehiclePositionsTable(BaseTable):
    def update_vehicle_positions(self, vehicles):
        columns = [
            "Vehicle ID",
            "Trip ID",
            "Route ID",
            "Latitude",
            "Longitude",
            "Speed",
            "Timestamp",
        ]
        rows = [(
            v["vehicle_id"],
            v["trip_id"],
            v["route_id"],
            str(v["latitude"]),
            str(v["longitude"]),
            str(v["speed"]),
            v["timestamp"],
        ) for v in vehicles]
        self.update_table(columns, rows)

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
            yield TabPane("Trip Updates", self._trip_updates_tab(), id="trip_updates_tab")
            yield TabPane("Vehicle Positions", self._vehicle_positions_tab(), id="vehicle_positions_tab")
            with TabPane("Live Maps", id="live_maps_tab"):
                with TabbedContent():
                    yield TabPane("Blue Line Map", self._blue_line_map_tab(), id="blue_line_map_tab")
                    yield TabPane("Green Line Map", self._green_line_map_tab(), id="green_line_map_tab")
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

    def _blue_line_map_tab(self):
        container = Container(
            Static("Blue Line Map", id="title", classes="bold"),
            BlueLineMapTab(id="blue_line_map_ascii"),
        )
        return container

    def _green_line_map_tab(self):
        container = Container(
            Static("Green Line Map", id="title", classes="bold"),
            GreenLineMapTab(id="green_line_map_ascii"),
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
        elif event.tab.id == "blue_line_map_tab":
            blue_line_map = self.query_one("#blue_line_map_ascii", BlueLineMapTab)
            blue_line_map.refresh_map()
        elif event.tab.id == "green_line_map_tab":
            green_line_map = self.query_one("#green_line_map_ascii", GreenLineMapTab)
            green_line_map.refresh_map()

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
