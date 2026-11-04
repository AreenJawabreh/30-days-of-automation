from datetime import datetime
from pathlib import Path

log_file = Path(__file__).parent / "log.txt"
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(log_file, "a", encoding="utf-8") as f:
    f.write(f"Hello from my first automation! Ran at {now}\n")

print("Done:", now)