"""Download the two training datasets into ml/data/raw/.

    python scripts/download_datasets.py

AI4I 2020 comes straight from the UCI repository. The support-tickets dataset comes from
Kaggle through kagglehub; if Kaggle asks for a login, put your API token in
%USERPROFILE%\\.kaggle\\kaggle.json (Kaggle > Settings > API > Create New Token) and rerun.
"""

import io
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "ml" / "data" / "raw"

AI4I_URL = "https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip"
AI4I_FILE = RAW_DIR / "ai4i2020.csv"

TICKETS_DATASET = "tobiasbueck/multilingual-customer-support-tickets"
TICKETS_DIR = RAW_DIR / "customer_support_tickets"


def download_ai4i() -> None:
    if AI4I_FILE.exists():
        print(f"AI4I 2020: already present at {AI4I_FILE}")
        return
    print("AI4I 2020: downloading from UCI...")
    with urllib.request.urlopen(AI4I_URL, timeout=60) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    csv_name = next(name for name in archive.namelist() if name.lower().endswith(".csv"))
    AI4I_FILE.write_bytes(archive.read(csv_name))
    print(f"AI4I 2020: saved to {AI4I_FILE}")


def download_tickets() -> None:
    if TICKETS_DIR.exists() and any(TICKETS_DIR.glob("*.csv")):
        print(f"Support tickets: already present in {TICKETS_DIR}")
        return
    import kagglehub

    print("Support tickets: downloading from Kaggle...")
    cache_dir = Path(kagglehub.dataset_download(TICKETS_DATASET))
    TICKETS_DIR.mkdir(parents=True, exist_ok=True)
    for csv_file in cache_dir.rglob("*.csv"):
        shutil.copy2(csv_file, TICKETS_DIR / csv_file.name)
    print(f"Support tickets: saved to {TICKETS_DIR}")


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = False
    for step in (download_ai4i, download_tickets):
        try:
            step()
        except Exception as error:  # Report and carry on so one failure doesn't block the other dataset.
            failed = True
            print(f"{step.__name__} failed: {error}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
