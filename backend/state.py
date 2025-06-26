"""
API状態管理モジュール

このモジュールは、Agentの状態・実行履歴などを一元的に管理する
グローバルなAPI状態管理機能を提供します。
"""

import threading
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, UTC
from concurrent.futures import ThreadPoolExecutor, Future

from backend.models.api_models import RunInfo

logger = logging.getLogger("api_state")


class ApiState:
    """APIの全体状態を管理するクラス（スレッドセーフ）"""

    def __init__(self):
        self._lock = threading.RLock()
        self._agent_data: Dict[str, Dict] = {}
        self._runs: Dict[str, RunInfo] = {}
        self._current_run_id: Optional[str] = None
        self._executor = ThreadPoolExecutor(max_workers=5)
        self._analysis_tasks: Dict[str, Future] = {}  # 分析タスクの追跡用

    @property
    def current_run_id(self) -> Optional[str]:
        """現在アクティブな実行IDを取得する"""
        with self._lock:
            return self._current_run_id

    @current_run_id.setter
    def current_run_id(self, run_id: str):
        """現在アクティブな実行IDを設定する"""
        with self._lock:
            self._current_run_id = run_id

    def register_agent(self, agent_name: str, description: str = ""):
        """Agentを登録する（初回のみ）"""
        with self._lock:
            if agent_name not in self._agent_data:
                self._agent_data[agent_name] = {
                    "info": {
                        "name": agent_name,
                        "description": description,
                        "state": "idle",
                        "last_run": None
                    },
                    "latest": {
                        "input_state": None,
                        "output_state": None,
                        "llm_request": None,
                        "llm_response": None,
                        "reasoning": None,
                        "timestamp": None
                    },
                    "history": []  # 実行履歴の記録
                }

    def update_agent_state(self, agent_name: str, state: str):
        """Agentの現在状態（例: running, completed, errorなど）を更新する"""
        with self._lock:
            if agent_name in self._agent_data:
                self._agent_data[agent_name]["info"]["state"] = state
                if state in ["completed", "error"]:
                    self._agent_data[agent_name]["info"]["last_run"] = datetime.now(UTC)

    def update_agent_data(self, agent_name: str, field: str, data: Any):
        """Agentの入力・出力・推論内容などのデータを更新する"""
        with self._lock:
            if agent_name in self._agent_data:
                self._agent_data[agent_name]["latest"][field] = data
                self._agent_data[agent_name]["latest"]["timestamp"] = datetime.now(UTC)

                # 実行履歴に追記
                if self._current_run_id:
                    history_entry = {
                        "run_id": self._current_run_id,
                        "timestamp": datetime.now(UTC),
                        field: data
                    }
                    self._agent_data[agent_name]["history"].append(history_entry)

    def get_agent_info(self, agent_name: str) -> Optional[Dict]:
        """指定したAgentの基本情報を取得する"""
        with self._lock:
            return self._agent_data.get(agent_name, {}).get("info")

    def get_agent_data(self, agent_name: str, field: str = None) -> Optional[Dict]:
        """指定したAgentの最新データを取得する（field指定ありなら該当項目のみ）"""
        with self._lock:
            if agent_name in self._agent_data:
                if field:
                    return self._agent_data[agent_name]["latest"].get(field)
                return self._agent_data[agent_name]["latest"]
            return None

    def get_all_agents(self) -> List[Dict]:
        """全Agentの基本情報をリストで取得する"""
        with self._lock:
            return [data["info"] for data in self._agent_data.values()]

    def register_run(self, run_id: str):
        """新しい実行(run)を登録する（開始タイミング）"""
        with self._lock:
            self._runs[run_id] = RunInfo(
                run_id=run_id,
                start_time=datetime.now(UTC),
                status="running"
            )
            self._current_run_id = run_id

    def complete_run(self, run_id: str, status: str = "completed"):
        """指定した実行を完了扱いにし、状態と終了時刻を更新する"""
        with self._lock:
            if run_id in self._runs:
                self._runs[run_id].end_time = datetime.now(UTC)
                self._runs[run_id].status = status

                # このrunに参加したAgentを収集
                agents = set()
                for agent_name, agent_data in self._agent_data.items():
                    for entry in agent_data["history"]:
                        if entry["run_id"] == run_id:
                            agents.add(agent_name)
                            break
                self._runs[run_id].agents = list(agents)

    def get_run(self, run_id: str) -> Optional[RunInfo]:
        """指定されたrun_idの実行情報を取得する"""
        with self._lock:
            return self._runs.get(run_id)

    def get_all_runs(self) -> List[RunInfo]:
        """すべての実行履歴（RunInfo）を取得する"""
        with self._lock:
            return list(self._runs.values())

    def register_analysis_task(self, run_id: str, future: Future):
        """分析タスクを非同期で登録・管理する（run_idごと）"""
        with self._lock:
            self._analysis_tasks[run_id] = future

    def get_analysis_task(self, run_id: str) -> Optional[Future]:
        """指定されたrun_idに対応する分析タスク（Future）を取得する"""
        with self._lock:
            return self._analysis_tasks.get(run_id)


# グローバルな状態インスタンス（他モジュールからインポートして利用）
api_state = ApiState()
