#!/usr/bin/env python3
"""01_bulk_rename.py - Batch file renamer with regex"""
import argparse, re
from pathlib import Path

def rename(folder, pattern, replacement, dry_run=True):
    count = 0
    for f in Path(folder).iterdir():
        if not f.is_file(): continue
        new = re.sub(pattern, replacement, f.name)
        if new != f.name:
            if dry_run: print(f"[DRY] {f.name} -> {new}")
            else: f.rename(f.parent / new); print(f"Renamed: {f.name} -> {new}")
            count += 1
    print(f"{'Would rename' if dry_run else 'Renamed'} {count} files.")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("folder"); p.add_argument("--pattern", default=" ")
    p.add_argument("--replace", default="_"); p.add_argument("--go", action="store_true")
    a = p.parse_args(); rename(a.folder, a.pattern, a.replace, not a.go)
