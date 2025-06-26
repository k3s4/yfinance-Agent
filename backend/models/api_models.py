"""
APIモデル定義
バックエンドAPIで使用するデータモデルを定義します。
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Dict, List, Optional, Generic, TypeVar

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """APIレスポンスの共通フォーマット"""
    success: bool = Field(True, description="処理が成功したかどうか")
    message: str = Field("", description="メッセージ（エラー時の詳細など）")
    data: Optional[T] = Field(None, description="レスポンスデータ")


class AgentInfo(BaseModel):
    """エージェント情報"""
    name: str = Field(..., description="エージェント名")
    description: str = Field("", description="エージェントの説明")
    state: str = Field("idle", description="現在の状態（idle, running, completed, error）")
    last_run: Optional[datetime] = Field(None, description="最後の実行時刻")


class RunInfo(BaseModel):
    """実行情報"""
    run_id: str = Field(..., description="実行ID")
    start_time: datetime = Field(..., description="実行開始時刻")
    end_time: Optional[datetime] = Field(None, description="実行終了時刻")
    status: str = Field("running", description="実行ステータス（running, completed, failed）")
    agents: List[str] = Field(default_factory=list, description="この実行に参加したエージェント一覧")


class StockAnalysisRequest(BaseModel):
    """株式分析リクエスト"""
    ticker: str = Field(..., description="株式ティッカーシンボル")
    analysis_type: str = Field("comprehensive", description="分析タイプ")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="追加パラメータ")


class StockAnalysisResponse(BaseModel):
    """株式分析レスポンス"""
    ticker: str = Field(..., description="株式ティッカーシンボル")
    analysis_result: Dict[str, Any] = Field(..., description="分析結果")
    timestamp: datetime = Field(..., description="分析実行時刻")
    run_id: str = Field(..., description="実行ID")