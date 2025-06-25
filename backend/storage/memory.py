from typing import List, Optional, Set
from collections import deque
import threading

from .base import BaseLogStorage
from backend.schemas import LLMInteractionLog, AgentExecutionLog

# メモリ上のログが無限に増えないよう、最大サイズを定義
MAX_LOG_SIZE = 1000


class InMemoryLogStorage(BaseLogStorage):
    """dequeを使ったLLM対話ログとAgent実行ログのメモリ上ストレージ"""

    def __init__(self):
        # 高速な追加・削除のためにdequeを使用
        # maxlenを設定し、古いログは自動で破棄される
        self._logs: deque[LLMInteractionLog] = deque(maxlen=MAX_LOG_SIZE)
        # Agent実行ログ用の別のdeque
        self._agent_logs: deque[AgentExecutionLog] = deque(maxlen=MAX_LOG_SIZE)
        # メインアプリとバックエンドの並行アクセスに備えてロックを使用
        self._logs_lock = threading.Lock()
        self._agent_logs_lock = threading.Lock()

    def add_log(self, log: LLMInteractionLog) -> None:
        """LLM対話ログを追加（スレッドセーフ）"""
        with self._logs_lock:
            self._logs.append(log)

    def get_logs(
        self,
        agent_name: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[LLMInteractionLog]:
        """LLM対話ログを取得（任意でagent名・run IDでフィルタ、スレッドセーフ）"""
        with self._logs_lock:
            logs = list(self._logs)  # フィルタリングのためリストに変換

        if agent_name:
            logs = [log for log in logs if log.agent_name == agent_name]
        if run_id:
            logs = [log for log in logs if log.run_id == run_id]

        if limit is not None and limit > 0:
            logs = logs[-limit:]
        elif limit == 0:
            return []

        return logs

    def add_agent_log(self, log: AgentExecutionLog) -> None:
        """Agent実行ログを追加（スレッドセーフ）"""
        with self._agent_logs_lock:
            self._agent_logs.append(log)

    def get_agent_logs(
        self,
        agent_name: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[AgentExecutionLog]:
        """Agent実行ログを取得（任意でagent名・run IDでフィルタ、スレッドセーフ）"""
        with self._agent_logs_lock:
            logs = list(self._agent_logs)  # フィルタリングのためリストに変換

        if agent_name:
            logs = [log for log in logs if log.agent_name == agent_name]
        if run_id:
            logs = [log for log in logs if log.run_id == run_id]

        if limit is not None and limit > 0:
            logs = logs[-limit:]
        elif limit == 0:
            return []

        return logs

    def get_unique_run_ids(self) -> List[str]:
        """存在するすべての実行ID（重複なし）を取得"""
        run_ids = set()

        # LLM対話ログから取得
        with self._logs_lock:
            for log in self._logs:
                if log.run_id:
                    run_ids.add(log.run_id)

        # Agent実行ログからも取得
        with self._agent_logs_lock:
            for log in self._agent_logs:
                if log.run_id:
                    run_ids.add(log.run_id)

        return sorted(list(run_ids))
