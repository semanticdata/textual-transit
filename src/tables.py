from textual.widgets import DataTable


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
                rows.append(
                    (
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
                )
        self.update_table(columns, rows)


class RoutesTable(BaseTable):
    def update_routes(self, routes):
        columns = ["Route ID", "Route Label"]
        rows = [(route["route_id"], route["route_label"]) for route in routes]
        self.update_table(columns, rows)


class TripUpdatesTable(BaseTable):
    def update_trip_updates(self, updates):
        columns = ["Trip ID", "Route ID", "Schedule", "Stop ID", "Arrival", "Departure"]
        rows = [
            (
                update["trip_id"],
                update["route_id"],
                str(update["schedule"]),
                update["stop_id"],
                update["arrival"],
                update["departure"],
            )
            for update in updates
        ]
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
        rows = [
            (
                v["vehicle_id"],
                v["trip_id"],
                v["route_id"],
                str(v["latitude"]),
                str(v["longitude"]),
                str(v["speed"]),
                v["timestamp"],
            )
            for v in vehicles
        ]
        self.update_table(columns, rows)
