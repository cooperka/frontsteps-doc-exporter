import os
import re
import json
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
MANIFEST_FILE = os.path.join(DOWNLOAD_DIR, "manifest.json")
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

def load_manifest():
    """Load manifest JSON if it exists."""
    if os.path.exists(MANIFEST_FILE):
        print("Loaded previous manifest, will NOT re-download files")
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    # Otherwise, start fresh.
    manifest = {"file_urls": {}}
    save_manifest(manifest)
    return manifest

def save_manifest(manifest):
    """Save manifest to disk."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

def file_in_manifest(file_url, manifest):
    """Check if file exists in manifest."""
    return file_url in manifest["file_urls"]

def save_file(file_url, file_name, date_str, folder_path, manifest):
    """Download and save file with metadata, unless it's already marked as downloaded."""
    os.makedirs(folder_path, exist_ok=True)

    if file_in_manifest(file_url, manifest):
        print(f"Skipping already-downloaded file: {file_name}")
        return

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

    manifest["file_urls"][file_url] = folder_path

    print(f"Saved file: {full_path}")

    time.sleep(ANTI_SPAM_DURATION_SEC)

def scrape_folder(url, folder_path, manifest):
    """Recursively scrape folders and download files."""
    print(f"Getting files from {folder_path.replace(DOWNLOAD_DIR, "") or "root"}...")
    r = session.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Skip root directory, which lists ALL files but without folder information.
    # It doesn't seem like files can actually be stored here, they need to be in a folder.
    if folder_path != DOWNLOAD_DIR:
        # Process files in this folder.
        for row in soup.select("table.documents tr"):
            anchor = row.select_one("td:nth-of-type(1) a")
            if anchor:
                file_name = anchor.text.strip()
                download_url = anchor.get("data-path") or urljoin(BASE_URL, anchor.get("href"))
                date_cell = row.select_one("td:nth-of-type(3)")
                date_str = date_cell.text.strip() if date_cell else ""
                save_file(download_url, file_name, date_str, folder_path, manifest)

    # Save manifest occasionally in case of crash.
    save_manifest(manifest)

    # Process subfolders.
    for anchor in soup.select(".folder-listing .folder-title a"):
        folder_name = anchor.text.strip()
        subfolder_url = urljoin(BASE_URL, anchor["href"])
        new_path = os.path.join(folder_path, sanitize_filename(folder_name))
        scrape_folder(subfolder_url, new_path, manifest)

def main():
    login()
    manifest = load_manifest()
    scrape_folder(FILES_URL, DOWNLOAD_DIR, manifest)

main()
