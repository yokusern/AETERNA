#!/usr/bin/env python3
"""04_folder_organizer.py - Auto-organize files by type and date"""
import shutil, argparse
from pathlib import Path
from datetime import datetime

TYPES = {
    "Images":    {".jpg",".jpeg",".png",".gif",".webp",".heic"},
    "Docs":      {".pdf",".doc",".docx",".txt",".md",".xlsx",".csv"},
    "Videos":    {".mp4",".mov",".avi",".mkv"},
    "Audio":     {".mp3",".wav",".flac",".aac"},
    "Code":      {".py",".js",".ts",".html",".css",".json"},
    "Archives":  {".zip",".tar",".gz",".rar"},
}

def organize(folder, by_date=False, dry_run=True):
    count = 0
    for f in Path(folder).iterdir():
        if not f.is_file() or f.name.startswith("."): continue
        cat = next((c for c,exts in TYPES.items() if f.suffix.lower() in exts), "Other")
        dest = Path(folder)/cat/(datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m") if by_date else "")
        if dry_run: print(f"[DRY] {f.name} -> {cat}/")
        else: dest.mkdir(parents=True, exist_ok=True); shutil.move(str(f), dest/f.name); print(f"Moved: {f.name}")
        count += 1
    print(f"{'Would move' if dry_run else 'Moved'} {count} files.")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("folder"); p.add_argument("--by-date", action="store_true")
    p.add_argument("--go", action="store_true")
    a = p.parse_args(); organize(a.folder, a.by_date, not a.go)
