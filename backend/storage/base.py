from abc import ABC, abstractmethod
from typing import List, Optional, Set

from backend.schemas import LLMInteractionLog, AgentExecutionLog


class BaseLogStorage(ABC):
    """LLM対話ログの保存に関する抽象基底クラス"""

    @abstractmethod
    def add_log(self, log: LLMInteractionLog) -> None:
        """新しいLLM対話ログを保存する"""
        pass

    @abstractmethod
    def get_logs(
        self,
        agent_name: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[LLMInteractionLog]:
        """LLM対話ログを取得する（agent名やrun IDでのフィルタリングが可能）"""
        pass

    @abstractmethod
    def add_agent_log(self, log: AgentExecutionLog) -> None:
        """Agentの実行ログを保存する"""
        pass

    @abstractmethod
    def get_agent_logs(
        self,
        agent_name: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[AgentExecutionLog]:
        """Agentの実行ログを取得する（agent名やrun IDでのフィルタリングが可能）"""
        pass

    @abstractmethod
    def get_unique_run_ids(self) -> List[str]:
        """登録されたすべてのユニークな実行ID（run_id）の一覧を取得する"""
        pass
