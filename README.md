# Textual Transit

A Textual-based TUI (Text User Interface) application for displaying Metro Transit trip updates, vehicle positions, and service alerts in your terminal. It features interactive tables and real-time map tabs for the Blue and Green lines.

![screenshot-1](screenshots/screenshot-1.png)
![screenshot-2](screenshots/screenshot-2.png)

## Features

- View real-time Metro Transit service alerts
- See trip updates and vehicle positions
- Live train maps
- Status bar with last refresh time

## Installation

1. Clone this repository:

   ```sh
   git clone https://github.com/semanticdata/textual-transit.git
   cd textual-transit
   ```

2. Install dependencies (Python 3.9+ recommended):

   ```sh
   pip install -r requirements.txt
   ```

   Required packages include:

   - textual
   - requests
   - protobuf
   - gtfs-realtime-bindings
