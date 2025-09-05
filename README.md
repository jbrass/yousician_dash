# yousician_dash

Yousician Dash is a web dashboard for visualizing and exploring your exported Yousician gameplay data. Built with Python, Dash, and Plotly, it provides interactive charts and tables to help you analyze your musical progress, practice habits, and song history.

## Features

- **Songs Played:** View counts and details of all songs you've played, filterable by instrument.
- **Practice vs Play:** Compare your practice and play time per song, with session counts and durations.
- **Weekly Practice:** Visualize your practice time by week and instrument.
- **Exercise Heatmap:** Inspect detailed progress and success ratios for individual exercises.
- **Interactive Filters:** Filter data by instrument and explore your history in depth.

## Getting Started

### Prerequisites
- Python 3.8+
- Your exported Yousician data (JSON files). 

### Getting the data
- Go to [https://account.yousician.com/](https://account.yousician.com/) and find the "Download your information" link at the bottom under "Advanced settings"
- click "Download"
- Yousician will email you a link to download your data.

### Installation
1. Clone this repository and place your exported data in the `data/` directory (see below).
2. Install dependencies:
	```bash
	pip install -r requirements.txt
	```
3. Run the app:
	```bash
	python app.py
	```
4. Open your browser to [http://localhost:8050](http://localhost:8050)

## Data Format

Place your exported Yousician JSON files in the `data/` directory. The following files are used:
- `data/yousician/history.json` — Song play history
- `data/yousician/stats.json` — Weekly stats
- `data/yousician/exercise_progress.json` — Exercise progress
- `data/events/ysapi.jsonl` — Event log for detailed song play/practice

The app expects the default folder structure as exported by Yousician. You can override data locations with environment variables:
- `YUSICIAN_DATA_ROOT` (default: `data/yousician`)
- `YUSICIAN_EVENTS_ROOT` (default: `data/events`)

## Project Structure

- `app.py` — Main Dash app and callbacks
- `data_loader.py` — Data loading and preprocessing functions
- `requirements.txt` — Python dependencies
- `data/` — Your exported Yousician data (not tracked in git)

## License

This project is not affiliated with Yousician. For personal use only.

