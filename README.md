# FRONTSTEPS document exporter

Third-party software to export your documents out of https://frontsteps.com community portals.

## Usage

### Prerequisites

1. Install [Python 3](https://www.python.org/) if you don't already have it.
1. Install packages: `pip install python-dotenv`

### Downloading your files

1. Clone this repository onto your computer.
1. Rename [`.env.example`](/.env.example) to `.env` and edit the file by following the instructions inside.
1. Run the program: `python export.py`

The script will log in using your browser cookie, find all folders you have access to, and download the documents from each folder onto your local computer.

### Notes

Files will be named according to the user-facing name specified in FRONTSTEPS, which may be different from the original filename using the "download" button online. For example, if a user uploaded `DCIM_01.jpg` and named it `Rainbow`, the file saved by this program will be `Rainbow.jpg`.

File metadata will be set so that the created/modified date of the file is the "uploaded at" timestamp on FRONTSTEPS.
