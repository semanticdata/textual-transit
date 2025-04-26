from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, TabbedContent, TabPane
from textual.containers import Container
from datetime import datetime
from src.status_bar import StatusBar
from src.blue_line_map_tab import BlueLineMapTab
from src.green_line_map_tab import GreenLineMapTab
from src.combined_map_tab import CombinedMapTab
from .metro_api import MetroTransitAPI, fetch_service_alerts
from src.tables import AlertsTable, RoutesTable, TripUpdatesTable, VehiclePositionsTable


class TransitApp(App):
    CSS_PATH = None
    TITLE = "Transit App"
    SUB_TITLE = "Metro Transit in your terminal"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh alerts"),
    ]

    def action_refresh(self):
        self.refresh_alerts()

    def update_status_bar(self, dt):
        bar = self.query_one("#status_bar", StatusBar)
        bar.update_refresh_time(dt)

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
            with TabPane("Live Maps", id="live_maps_tab"):
                with TabbedContent():
                    yield TabPane(
                        "Blue Line Map",
                        self._blue_line_map_tab(),
                        id="blue_line_map_tab",
                    )
                    yield TabPane(
                        "Green Line Map",
                        self._green_line_map_tab(),
                        id="green_line_map_tab",
                    )
                    yield TabPane(
                        "Combined Map", self._combined_map_tab(), id="combined_map_tab"
                    )
        yield Footer()

    def _alerts_tab(self):
        container = Container(
            Static("Transit Service Alerts", id="title", classes="bold"),
            StatusBar(id="alerts_status_bar"),
            AlertsTable(id="alerts_table"),
        )
        return container

    def _routes_tab(self):
        container = Container(
            Static("Available Transit Routes", id="title", classes="bold"),
            StatusBar(id="routes_status_bar"),
            RoutesTable(id="routes_table"),
        )
        return container

    def _trip_updates_tab(self):
        container = Container(
            Static("Trip Updates", id="title", classes="bold"),
            StatusBar(id="trip_updates_status_bar"),
            TripUpdatesTable(id="trip_updates_table"),
        )
        return container

    def _vehicle_positions_tab(self):
        container = Container(
            Static("Vehicle Positions", id="title", classes="bold"),
            StatusBar(id="vehicle_positions_status_bar"),
            VehiclePositionsTable(id="vehicle_positions_table"),
        )
        return container

    def _blue_line_map_tab(self):
        container = Container(
            Static("Blue Line Map", id="title", classes="bold"),
            StatusBar(id="blue_line_map_status_bar"),
            BlueLineMapTab(id="blue_line_map_ascii"),
        )
        return container

    def _green_line_map_tab(self):
        container = Container(
            Static("Green Line Map", id="title", classes="bold"),
            StatusBar(id="green_line_map_status_bar"),
            GreenLineMapTab(id="green_line_map_ascii"),
        )
        return container

    def _combined_map_tab(self):
        container = Container(
            Static("Combined Map", id="title", classes="bold"),
            StatusBar(id="combined_map_status_bar"),
            CombinedMapTab(id="combined_map_ascii"),
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
        now = datetime.now()
        bar = self.query_one("#alerts_status_bar")
        bar.update_refresh_time(now)

    def refresh_routes(self):
        api = MetroTransitAPI()
        try:
            routes = api.get_routes()
        except Exception as e:
            routes = [{"route_id": "ERROR", "route_label": str(e)}]
        routes_table = self.query_one("#routes_table", RoutesTable)
        routes_table.update_routes(routes)
        now = datetime.now()
        bar = self.query_one("#routes_status_bar")
        bar.update_refresh_time(now)

    def refresh_trip_updates(self):
        from .metro_api import get_trip_updates

        updates = get_trip_updates()
        trip_updates_table = self.query_one("#trip_updates_table", TripUpdatesTable)
        trip_updates_table.update_trip_updates(updates)
        now = datetime.now()
        bar = self.query_one("#trip_updates_status_bar")
        bar.update_refresh_time(now)

    def refresh_vehicle_positions(self):
        from .metro_api import fetch_vehicle_positions

        vehicles = fetch_vehicle_positions()
        vehicle_positions_table = self.query_one(
            "#vehicle_positions_table", VehiclePositionsTable
        )
        vehicle_positions_table.update_vehicle_positions(vehicles)
        now = datetime.now()
        bar = self.query_one("#vehicle_positions_status_bar")
        bar.update_refresh_time(now)
