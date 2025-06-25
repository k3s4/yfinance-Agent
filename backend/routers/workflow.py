"""
ワークフロー関連のルーティングモジュール
このモジュールは、ワークフローの状態、実行、管理に関するAPIエンドポイントを提供します。
"""

from fastapi import APIRouter
from typing import Dict

from ..models.api_models import ApiResponse
from ..state import api_state

# ルーターの作成
router = APIRouter(prefix="/api/workflow", tags=["Workflow"])


@router.get("/status", response_model=ApiResponse[Dict])
async def get_workflow_status():
    """現在実行中のワークフローの状態を取得（メモリ上の状態に基づく）

    このエンドポイントでは、メモリ上の api_state オブジェクトを参照し、
    現在進行中のワークフローのリアルタイムな状態を返します。
    内容には、実行ID、開始時刻、アクティブなAgentの状態などが含まれます。

    ※現在実行中のワークフローがない場合は、"idle" 状態を返します。
    ※この情報はあくまで現在の状態を表すものであり、
      サーバーの再起動などにより失われます。
    """
    current_run_id = api_state.current_run_id
    if not current_run_id:
        return ApiResponse(
            data={
                "status": "idle",
                "message": "現在、実行中のワークフローはありません。"
            }
        )

    run = api_state.get_run(current_run_id)
    agents = api_state.get_all_agents()

    return ApiResponse(
        data={
            "status": run.status,
            "run_id": current_run_id,
            "start_time": run.start_time,
            "agents": [a for a in agents if a["state"] != "idle"]
        }
    )
