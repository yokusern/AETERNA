"""
growth_agent.py — 帝国の第3の心臓（分析・進化・自己修復）
analyzer, evolver, self_modifier を統合。
帝国の適応力、進化速度、堅牢性を司る。
"""
import sys
import json
import os
import ast
import subprocess
import tempfile
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core import llm_client, state_manager, memory

JST = timezone(timedelta(hours=9))
AGENTS_DIR = ROOT / "agents"
DATA_DIR = ROOT / "data"

def run(params: dict) -> dict:
    """brainから呼ばれるメインエントリポイント"""
    action_type = params.get("type")
    
    if action_type == "ANALYZE":
        return {"status": "ok", "trends": _get_trends()}
    
    elif action_type == "INITIATE":
        return _initiate_project(params.get("spec", {}))

    elif action_type == "EVOLVE":
        return {"status": "ok", "path": _create_agent(params.get("spec", {}))}
        
    elif action_type == "REPAIR":
        return {"status": "ok", "fixes": _self_repair(params.get("target"), params.get("error"))}
        
    elif action_type == "OPTIMIZE_PROMPTS":
        return {"status": "ok", "detail": _optimize_prompts()}
        
    return {"status": "error", "message": f"Unknown action: {action_type}"}

def _initiate_project(spec: dict) -> dict:
    """新プロジェクトのディレクトリ作成と初期スクリプト生成"""
    name = spec.get("name", "new_project").replace(" ", "_")
    project_dir = ROOT / name
    project_dir.mkdir(exist_ok=True)
    
    prompt = f"""あなたは起業家AIです。新しいプロジェクト「{name}」を立ち上げます。
目標: {spec.get('goal')}
計画: {spec.get('plan')}

このプロジェクトを自律的に進行させるための、初期Pythonスクリプト(main.py)を生成してください。
AETERNAのcoreモジュール(llm_client, state_manager)を利用可能です。
修正後のコードのみを、Markdownコードブロックなしで出力してください。"""

    code = llm_client.call(prompt, max_tokens=3000)
    (project_dir / "main.py").write_text(code, encoding="utf-8")
    
    # 帝国のディレクトリ構造を維持
    (project_dir / "data").mkdir(exist_ok=True)
    
    return {"status": "initiated", "path": str(project_dir)}

# --- 1. 市場分析 (Analyzer) ---
def _get_trends() -> list:
    state = state_manager.load()
    mem_summary = memory.summarize_for_prompt(limit=10)
    
    prompt = f"""
# 過去の記憶
{mem_summary}

# 現在の売上状況
{json.dumps(state.get('revenue'), ensure_ascii=False)}

上記を分析し、AETERNAが次に参入すべきトレンド領域を5つ特定してください。
JSON配列のみで出力してください。"""
    return llm_client.call_json(prompt)

# --- 2. エージェント生成 (Evolver) ---
def _create_agent(spec: dict) -> str:
    name = spec.get("name", "new_agent").replace("-", "_").replace(" ", "_")
    prompt = f"以下の仕様でPythonエージェントを作成してください。\n{json.dumps(spec, indent=2)}"
    code = llm_client.call(prompt, max_tokens=2000)
    
    # シンプルな抽出と保存
    if "```python" in code: code = code.split("```python")[1].split("```")[0].strip()
    
    path = AGENTS_DIR / f"{name}.py"
    path.write_text(code, encoding="utf-8")
    return str(path)

# --- 3. 自己修復 (Self-Modifier / Improver) ---
def _self_repair(target: str = None, error: str = None) -> list:
    """システムの不具合を特定し、コードを書き換えて修正する"""
    results = []
    
    if target:
        # 特定のファイルを修正
        fix_res = _improve_code(target, error or "不明なエラー")
        results.append({"file": target, "result": fix_res})
    else:
        # 全体をスキャンして脆弱性を修正
        for agent_file in AGENTS_DIR.glob("*.py"):
            try:
                ast.parse(agent_file.read_text())
            except SyntaxError as e:
                fix_res = _improve_code(agent_file.name, str(e))
                results.append({"file": agent_file.name, "result": fix_res})
                
    return results

def _improve_code(filename: str, context: str) -> str:
    """LLMによるコード改善実行"""
    path = AGENTS_DIR / filename
    if not path.exists(): return "File not found"
    
    old_code = path.read_text()
    prompt = f"""以下のPythonコードを修正・改善してください。
ファイル名: {filename}
背景/エラー: {context}

コード:
{old_code}

修正後のコードのみを、Markdownコードブロックなしで出力してください。"""

    new_code = llm_client.call(prompt, max_tokens=4000)
    
    # 構文チェック後に保存
    try:
        ast.parse(new_code)
        path.write_text(new_code, encoding="utf-8")
        return "SUCCESS"
    except Exception as e:
        return f"FAILURE: {e}"

# --- 4. プロンプト進化 (Prompt Engineering) ---
def _optimize_prompts() -> str:
    """過去の成功事例から、各エージェントのプロンプトを自動調整する"""
    mem_summary = memory.summarize_for_prompt(limit=20)
    
    # ProductAgentのプロンプトを最適化対象にする
    target_path = AGENTS_DIR / "product_agent.py"
    if not target_path.exists(): return "Target not found"
    
    old_code = target_path.read_text()
    
    prompt = f"""
# 過去の活動ログ
{mem_summary}

# ターゲットコード
{old_code}

上記のログから「売れた商品の傾向」や「生成の失敗パターン」を分析し、
product_agent.py 内の 'CONTENT_PROMPT' または 'CRITIQUE_PROMPT' をより効果的なものに書き換えてください。
コード全体を、Markdownコードブロックなしで返してください。"""

    new_code = llm_client.call(prompt, max_tokens=4000)
    
    try:
        ast.parse(new_code)
        target_path.write_text(new_code, encoding="utf-8")
        return "Prompts optimized based on memory"
    except Exception as e:
        return f"Optimization failed: {e}"
