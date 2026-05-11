"""
ファイル自動整理スクリプト
拡張子別にファイルをサブフォルダへ移動する
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

CATEGORY_MAP = {
    "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".heic", ".webp", ".svg"],
    "documents": [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".txt", ".md"],
    "videos": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv"],
    "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
    "code": [".py", ".js", ".ts", ".html", ".css", ".json", ".yaml", ".yml", ".sh"],
    "archives": [".zip", ".tar", ".gz", ".rar", ".7z"],
}


class FileOrganizer:
    def __init__(self, source_dir: str, target_dir: str = None, dry_run: bool = False):
        self.source = Path(source_dir).expanduser()
        self.target = Path(target_dir).expanduser() if target_dir else self.source
        self.dry_run = dry_run
        self.log = []

    def _get_category(self, suffix: str) -> str:
        suffix = suffix.lower()
        for category, extensions in CATEGORY_MAP.items():
            if suffix in extensions:
                return category
        return "others"

    def organize(self) -> dict:
        if not self.source.exists():
            raise FileNotFoundError(f"Source directory not found: {self.source}")

        stats = {"moved": 0, "skipped": 0, "errors": 0}

        for file_path in self.source.iterdir():
            if not file_path.is_file() or file_path.name.startswith("."):
                continue

            category = self._get_category(file_path.suffix)
            dest_dir = self.target / category
            dest_file = dest_dir / file_path.name

            # 同名ファイルが既にある場合はタイムスタンプを付加
            if dest_file.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_file = dest_dir / f"{stem}_{timestamp}{suffix}"

            try:
                if not self.dry_run:
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(file_path), str(dest_file))

                self.log.append(f"{'[DRY]' if self.dry_run else '[MOVED]'} {file_path.name} → {category}/")
                stats["moved"] += 1
            except Exception as e:
                self.log.append(f"[ERROR] {file_path.name}: {e}")
                stats["errors"] += 1

        self._print_summary(stats)
        return stats

    def _print_summary(self, stats: dict):
        print(f"\n=== 整理完了 ===")
        print(f"移動: {stats['moved']}件 | スキップ: {stats['skipped']}件 | エラー: {stats['errors']}件")
        if self.dry_run:
            print("※ ドライランモード（実際の移動は行われていません）")
        for entry in self.log[-20:]:
            print(entry)


if __name__ == "__main__":
    import sys
    source = sys.argv[1] if len(sys.argv) > 1 else "."
    target = sys.argv[2] if len(sys.argv) > 2 else None
    organizer = FileOrganizer(source_dir=source, target_dir=target)
    organizer.organize()
