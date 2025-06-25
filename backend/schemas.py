from pydantic import BaseModel, Field
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional


class LLMInteractionLog(BaseModel):
    """LLMとの対話ログのスキーマ"""
    agent_name: str = Field(..., description="この対話を行ったAgentの名前")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="このログの記録時刻"
    )
    request_data: Any = Field(..., description="LLMに送信されたデータ")
    response_data: Any = Field(..., description="LLMから返されたデータ")
    run_id: Optional[str] = Field(
        None, description="この対話が属するワークフロー実行ID（任意）"
    )

    class Config:
        # request_data / response_data に任意の型を許容（後に厳密化可能）
        arbitrary_types_allowed = True
        from_attributes = True  # 将来的なORM統合を想定


class AgentExecutionLog(BaseModel):
    """Agentの実行ログ"""
    agent_name: str = Field(..., description="Agentの名前")
    run_id: str = Field(..., description="この実行に対応する実行ID")
    timestamp_start: datetime = Field(..., description="実行開始時刻")
    timestamp_end: datetime = Field(..., description="実行終了時刻")
    input_state: Optional[Dict[str, Any]] = Field(None, description="入力状態（state）")
    output_state: Optional[Dict[str, Any]] = Field(None, description="出力状態（state）")
    reasoning_details: Optional[Any] = Field(None, description="推論過程の詳細情報")
    terminal_outputs: List[str] = Field(default_factory=list, description="ターミナルへの出力ログ")


class RunSummary(BaseModel):
    """ワークフロー実行全体の概要"""
    run_id: str = Field(..., description="実行ID")
    start_time: datetime = Field(..., description="実行開始時刻")
    end_time: datetime = Field(..., description="実行終了時刻")
    agents_executed: List[str] = Field(..., description="この実行で動作したAgentの一覧")
    status: str = Field(..., description="実行ステータス（例：completed, in_progress, failed）")


class AgentSummary(BaseModel):
    """Agentの実行概要"""
    agent_name: str = Field(..., description="Agentの名前")
    start_time: datetime = Field(..., description="実行開始時刻")
    end_time: datetime = Field(..., description="実行終了時刻")
    execution_time_seconds: float = Field(..., description="実行時間（秒）")
    status: str = Field(..., description="実行ステータス（例：completed, failed）")


class AgentDetail(AgentSummary):
    """Agentの実行詳細"""
    input_state: Optional[Dict[str, Any]] = Field(None, description="入力状態（state）")
    output_state: Optional[Dict[str, Any]] = Field(None, description="出力状態（state）")
    reasoning: Optional[Dict[str, Any]] = Field(None, description="推論の詳細情報")
    llm_interactions: List[str] = Field(default_factory=list, description="関連するLLM対話のID一覧")


class StateTransition(BaseModel):
    """状態遷移（エージェント間のデータ移動）情報"""
    from_agent: str = Field(..., description="遷移元のAgent名")
    to_agent: str = Field(..., description="遷移先のAgent名")
    state_size: int = Field(..., description="遷移する状態データのサイズ（文字数ベースなど）")
    timestamp: str = Field(..., description="遷移が行われた時刻（ISO文字列）")


class WorkflowFlow(BaseModel):
    """ワークフロー全体のデータフロー構造"""
    run_id: str = Field(..., description="実行ID")
    start_time: datetime = Field(..., description="ワークフローの開始時刻")
    end_time: datetime = Field(..., description="ワークフローの終了時刻")
    agents: Dict[str, AgentSummary] = Field(..., description="各Agentの実行概要（Agent名→要約）")
    state_transitions: List[Dict] = Field(..., description="状態遷移の一覧（時系列順）")
    final_decision: Optional[str] = Field(None, description="最終的な判断・出力（存在する場合）")
