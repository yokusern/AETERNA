"""
基底エージェントクラス
全てのエージェントの基底クラス
"""

import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class BaseAgent:
    """基底エージェントクラス"""
    
    def __init__(self, name: str, log_dir: str = "agents/logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # ロガー設定
        self.logger = self._setup_logger()
        self.results: Dict[str, Any] = {}
        
        # 状態ファイル
        self.state_file = self.log_dir / f"{name}_state.json"
    
    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)
        
        # ハンドラが既にある場合は追加しない
        if not logger.handlers:
            # ファイルハンドラ
            log_file = self.log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # コンソールハンドラ
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # フォーマッタ
            formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def log(self, message: str, level: str = "info"):
        """ログ出力"""
        if level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "debug":
            self.logger.debug(message)
    
    def save_state(self, state: Dict[str, Any]):
        """状態保存"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            self.log(f"状態保存完了: {self.state_file}")
        except Exception as e:
            self.log(f"状態保存エラー: {e}", "error")
    
    def load_state(self) -> Dict[str, Any]:
        """状態読み込み"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.log(f"状態読み込みエラー: {e}", "error")
        return {}
    
    def record_result(self, key: str, value: Any):
        """結果記録"""
        self.results[key] = value
        self.log(f"結果記録 [{key}]: {value}")
    
    def execute(self) -> bool:
        """エージェント実行（サブクラスでオーバーライド）"""
        raise NotImplementedError("サブクラスで実装してください")
    
    def run(self) -> Dict[str, Any]:
        """エージェント実行ラッパー"""
        start_time = time.time()
        self.log("=" * 60)
        self.log(f"{self.name} 起動")
        self.log("=" * 60)
        
        try:
            success = self.execute()
            elapsed_time = time.time() - start_time
            
            if success:
                self.log(f"✓ {self.name} 完了 ({elapsed_time:.2f}秒)")
            else:
                self.log(f"✗ {self.name} 失敗", "error")
            
            return {
                'status': 'success' if success else 'failure',
                'results': self.results,
                'elapsed_time': elapsed_time
            }
            
        except Exception as e:
            self.log(f"エラー発生: {e}", "error")
            return {
                'status': 'error',
                'error': str(e),
                'results': self.results
            }
