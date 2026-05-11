"""
CSV一括加工スクリプト
複数CSVの結合・フィルタリング・集計を自動化する
"""
import os
import glob
import chardet
import pandas as pd
from pathlib import Path
from typing import Union


class CSVProcessor:
    def __init__(self):
        self.encoding_cache = {}

    def _detect_encoding(self, file_path: str) -> str:
        if file_path in self.encoding_cache:
            return self.encoding_cache[file_path]
        with open(file_path, "rb") as f:
            result = chardet.detect(f.read(10000))
        encoding = result.get("encoding", "utf-8") or "utf-8"
        self.encoding_cache[file_path] = encoding
        return encoding

    def _read_csv(self, file_path: str) -> pd.DataFrame:
        encoding = self._detect_encoding(file_path)
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except UnicodeDecodeError:
            return pd.read_csv(file_path, encoding="utf-8-sig")

    def merge(self, input_dir: str, output_file: str, encoding: str = "utf-8-sig") -> pd.DataFrame:
        """指定ディレクトリ内の全CSVを結合する"""
        files = glob.glob(os.path.join(input_dir, "*.csv"))
        if not files:
            raise FileNotFoundError(f"CSVファイルが見つかりません: {input_dir}")

        dfs = []
        for f in sorted(files):
            df = self._read_csv(f)
            df["_source_file"] = os.path.basename(f)
            dfs.append(df)
            print(f"  読み込み: {os.path.basename(f)} ({len(df)}行)")

        merged = pd.concat(dfs, ignore_index=True)
        merged.to_csv(output_file, index=False, encoding=encoding)
        print(f"結合完了: {len(merged)}行 → {output_file}")
        return merged

    def filter(self, input_file: str, output_file: str,
               conditions: dict, encoding: str = "utf-8-sig") -> pd.DataFrame:
        """条件によるフィルタリング
        conditions例: {"status": "完了", "amount": (">", 10000)}
        """
        df = self._read_csv(input_file)
        original_count = len(df)

        for column, condition in conditions.items():
            if column not in df.columns:
                print(f"警告: 列'{column}'が存在しません")
                continue

            if isinstance(condition, tuple):
                op, value = condition
                ops = {">": df[column] > value, "<": df[column] < value,
                       ">=": df[column] >= value, "<=": df[column] <= value,
                       "!=": df[column] != value}
                df = df[ops[op]]
            else:
                df = df[df[column] == condition]

        df.to_csv(output_file, index=False, encoding=encoding)
        print(f"フィルタ完了: {original_count}行 → {len(df)}行 → {output_file}")
        return df

    def aggregate(self, input_file: str, output_file: str,
                  group_by: Union[str, list], agg_columns: dict,
                  encoding: str = "utf-8-sig") -> pd.DataFrame:
        """グループ別集計
        agg_columns例: {"amount": "sum", "count": "count"}
        """
        df = self._read_csv(input_file)

        result = df.groupby(group_by).agg(agg_columns).reset_index()
        result.columns = [
            "_".join(col).strip("_") if isinstance(col, tuple) else col
            for col in result.columns
        ]

        result.to_csv(output_file, index=False, encoding=encoding)
        print(f"集計完了: {len(result)}グループ → {output_file}")
        return result

    def remove_duplicates(self, input_file: str, output_file: str,
                          subset: list = None, encoding: str = "utf-8-sig") -> pd.DataFrame:
        """重複行の削除"""
        df = self._read_csv(input_file)
        original_count = len(df)
        df = df.drop_duplicates(subset=subset)
        df.to_csv(output_file, index=False, encoding=encoding)
        print(f"重複削除: {original_count}行 → {len(df)}行 ({original_count - len(df)}件削除)")
        return df


if __name__ == "__main__":
    processor = CSVProcessor()
    print("CSVProcessorが利用可能です。インポートして使用してください。")
    print("使用例:")
    print("  processor.merge('data/', 'merged.csv')")
    print("  processor.filter('merged.csv', 'filtered.csv', {'status': '完了'})")
    print("  processor.aggregate('merged.csv', 'summary.csv', 'category', {'amount': 'sum'})")
