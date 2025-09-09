import os
import re
import requests
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load configs from .env file
load_dotenv()

COOKIE_VALUE = os.getenv("COOKIE_VALUE")
COMMUNITY_NAME = os.getenv("COMMUNITY_NAME")
BASE_URL = f"https://{COMMUNITY_NAME}.frontsteps.com"
FILES_URL = f"{BASE_URL}/folders/"
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR")
ANTI_SPAM_DURATION_SEC = float(os.getenv("ANTI_SPAM_DURATION_SEC"))

session = requests.Session()

def login():
    """Skip login by directly setting the Cookie header."""
    session.headers.update({
        "Cookie": COOKIE_VALUE,
        "User-Agent": "Mozilla/5.0"
    })

    # Test that the cookie works.
    r = session.get(FILES_URL)
    r.raise_for_status()
    if "Logout" not in r.text:
        print("Warning: Cookie may have expired")
    else:
        print("Logged in")

def sanitize_filename(name):
    """Make safe filenames for OS."""
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def get_extension_from_url(url):
    """Given something like example.com/file.pdf?foo=bar, returns 'pdf'."""
    path = urlparse(url).path
    return os.path.splitext(os.path.basename(path))[1]

def save_file(file_url, file_name, date_str, folder_path):
    """Download and save file with metadata."""
    os.makedirs(folder_path, exist_ok=True)
    r = session.get(file_url, allow_redirects=True)
    r.raise_for_status()

    # Get extension AFTER redirects.
    ext = get_extension_from_url(r.url) or ".dat"
    full_path = os.path.join(folder_path, sanitize_filename(file_name) + ext)

    with open(full_path, "wb") as f:
        f.write(r.content)

    # Parse and set file metadata based on Frontsteps timestamp.
    try:
        created_time = datetime.strptime(date_str, "%I:%M:%S %p %b %d %Y")
        ts = time.mktime(created_time.timetuple())
        os.utime(full_path, (ts, ts))
    except Exception:
        print(f"Warning: couldn't set date '{date_str}' for '{file_name}'")

    print(f"Saved file: {full_path}")

def scrape_folder(url, folder_path):
    """Recursively scrape folders and download files."""
    print(f"Getting files from {folder_path.replace(DOWNLOAD_DIR, "") or "root"}...")
    r = session.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Skip root directory, which lists ALL files but without folder information.
    # It doesn't seem like files can actually be stored here, they need to be in a folder.
    if folder_path != DOWNLOAD_DIR:
        # Process files in this folder.
        # TODO: handle manifest for caching
        for row in soup.select("table.documents tr"):
            anchor = row.select_one("td:nth-of-type(1) a")
            if anchor:
                file_name = anchor.text.strip()
                download_url = anchor["data-path"] or urljoin(BASE_URL, anchor["href"])
                date_cell = row.select_one("td:nth-of-type(3)")
                date_str = date_cell.text.strip() if date_cell else ""
                save_file(download_url, file_name, date_str, folder_path)

                time.sleep(ANTI_SPAM_DURATION_SEC)

    # Process subfolders.
    for anchor in soup.select(".folder-listing .folder-title a"):
        folder_name = anchor.text.strip()
        subfolder_url = urljoin(BASE_URL, anchor["href"])
        new_path = os.path.join(folder_path, sanitize_filename(folder_name))
        scrape_folder(subfolder_url, new_path)

def main():
    login()
    scrape_folder(FILES_URL, DOWNLOAD_DIR)

main()
