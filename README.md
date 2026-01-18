# XE Currency Rate Scraper

A Flask application that scrapes historical USD/CAD exchange rates from XE.com with built-in rate limiting.

## Features

- 📅 **Date Range Selection** — Pick start and end dates to fetch historical rates
- 🛡️ **Rate Limiting** — Built-in throttling (2-5s between requests) to avoid being blocked
- 📊 **Live Progress** — Watch rates get fetched in real-time
- 📋 **Multiple Export Formats** — TSV, CSV, JSON, or Python dict
- 📈 **Statistics** — Average rate, min/max range at a glance
- 🎨 **Dark Mode UI** — Beautiful, modern interface

## Installation

```bash
# Navigate to the project directory
cd /Users/yztpp8/Desktop/XE

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the Flask app
python app.py
```

Then open **http://localhost:5000** in your browser.

## Rate Limiting Details

The scraper implements multiple layers of protection:

| Parameter | Value | Description |
|-----------|-------|-------------|
| Min Delay | 2.5s | Minimum time between requests |
| Max Delay | 5.0s | Maximum time between requests |
| Burst Limit | 5 | Requests before cooldown |
| Burst Cooldown | 20s | Rest period after burst |
| Max Date Range | 90 days | Prevents excessive requests |

The app also:
- Rotates user agents to avoid fingerprinting
- Uses realistic browser headers
- Adds random jitter to request timing

## Export Formats

After fetching rates, copy data in your preferred format:

- **Tab-Separated (TSV)** — Perfect for pasting into Excel/Google Sheets
- **CSV** — Standard comma-separated format
- **JSON** — For API/programmatic use
- **Python Dict** — Ready to paste into Jupyter notebooks

## Project Structure

```
XE/
├── app.py              # Flask app with scraper logic
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html     # Frontend UI
└── README.md          # This file
```

## Disclaimer

This tool is for personal use only. Respect XE.com's terms of service and use responsibly.
