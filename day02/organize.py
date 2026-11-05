"""
Day 2 - #30DaysOfAutomation
Organize a messy folder (like Downloads) by file type and month.

Example result:
    Downloads/
        Images/2026-11/photo.jpg
        PDFs/2026-10/invoice.pdf
        Documents/2026-11/notes.docx

Usage:
    python organize.py                           -> dry run on your Downloads (shows what WOULD happen)
    python organize.py --apply                   -> really organizes your Downloads
    python organize.py --folder "D:\\Other"       -> dry run on another folder
    python organize.py --folder "D:\\Other" --apply
"""

import argparse
import logging
import shutil
from datetime import datetime
from pathlib import Path

# Which extensions go to which folder
CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".svg"],
    "PDFs": [".pdf"],
    "Documents": [".doc", ".docx", ".txt", ".odt", ".rtf", ".md"],
    "Spreadsheets": [".xls", ".xlsx", ".csv"],
    "Presentations": [".ppt", ".pptx"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv"],
    "Audio": [".mp3", ".wav", ".m4a", ".ogg"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Installers": [".exe", ".msi"],
    "Code": [".py", ".js", ".html", ".css", ".json", ".ipynb"],
}

# Files still downloading - never touch them
SKIP_EXTENSIONS = [".crdownload", ".part", ".tmp", ".download"]


def get_category(file_path: Path) -> str:
    """Return the category name for a file based on its extension."""
    ext = file_path.suffix.lower()
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category
    return "Others"


def get_month_folder(file_path: Path) -> str:
    """Return 'YYYY-MM' from the file's last modified date."""
    modified = datetime.fromtimestamp(file_path.stat().st_mtime)
    return modified.strftime("%Y-%m")


def unique_destination(destination: Path) -> Path:
    """If a file with the same name exists, add _1, _2, ... so nothing is overwritten."""
    if not destination.exists():
        return destination
    counter = 1
    while True:
        new_path = destination.with_name(f"{destination.stem}_{counter}{destination.suffix}")
        if not new_path.exists():
            return new_path
        counter += 1


def organize(folder: Path, apply: bool) -> None:
    mode = "APPLY" if apply else "DRY RUN"
    logging.info(f"===== Start ({mode}) on: {folder} =====")

    moved = {}  # category -> count
    skipped = 0

    for item in folder.iterdir():
        # Skip folders (including the ones we created before)
        if item.is_dir():
            continue
        # Skip unfinished downloads and hidden/system files
        if item.suffix.lower() in SKIP_EXTENSIONS or item.name.startswith(".") or item.name == "desktop.ini":
            skipped += 1
            continue

        category = get_category(item)
        month = get_month_folder(item)
        target_dir = folder / category / month
        destination = unique_destination(target_dir / item.name)

        if apply:
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(item), str(destination))
                logging.info(f"Moved: {item.name}  ->  {category}/{month}/{destination.name}")
            except Exception as error:  # e.g. the file is open in another program
                logging.error(f"Could not move {item.name}: {error}")
                skipped += 1
                continue
        else:
            logging.info(f"Would move: {item.name}  ->  {category}/{month}/{destination.name}")

        moved[category] = moved.get(category, 0) + 1

    total = sum(moved.values())
    logging.info(f"===== Done: {total} files {'moved' if apply else 'to move'}, {skipped} skipped =====")
    for category, count in sorted(moved.items(), key=lambda x: -x[1]):
        logging.info(f"   {category}: {count}")
    if not apply:
        logging.info("This was a DRY RUN. Nothing was moved. Add --apply to really move the files.")


def main() -> None:
    script_dir = Path(__file__).parent

    parser = argparse.ArgumentParser(description="Organize a folder by file type and month.")
    parser.add_argument("--folder", default=str(Path.home() / "Downloads"),
                        help="Folder to organize (default: your Downloads folder)")
    parser.add_argument("--apply", action="store_true",
                        help="Really move the files. Without it, the script only shows what it would do.")
    args = parser.parse_args()

    # Log to the screen AND to a file next to the script
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(script_dir / "organize.log", encoding="utf-8"),
        ],
    )

    folder = Path(args.folder)
    if not folder.exists():
        logging.error(f"Folder not found: {folder}")
        return

    organize(folder, args.apply)


if __name__ == "__main__":
    main()