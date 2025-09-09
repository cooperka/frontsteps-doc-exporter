# FRONTSTEPS document exporter

Third-party software to export your documents out of https://frontsteps.com community portals.

## Usage

### Prerequisites

- Requires [python 3](https://www.python.org/) if you don't already have it.
- `pip install python-dotenv`

### Downloading your files

1. Clone this repository onto your computer
1. Rename [`.env.example`](/.env.example) to `.env` and edit the file by following the instructions inside
1. Execute `python export.py`

The script will now log in using your cookie, find your folders, and download all the documents from each folder onto your local computer.
