"""
実行履歴に関するルーター（APIエンドポイント）
このモジュールは、ワークフローの実行履歴に関するAPIエンドポイントを提供します。
"""

from fastapi import APIRouter, Query
from typing import Dict, List

from ..models.api_models import ApiResponse, RunInfo
from ..state import api_state

# ルーターの作成
router = APIRouter(prefix="/api/runs", tags=["Runs"])


@router.get("/", response_model=List[RunInfo])
async def list_runs(limit: int = Query(10, ge=1, le=100)):
    """実行履歴一覧を取得（インメモリ状態に基づく）

    このエンドポイントはメモリ内の api_state オブジェクトを参照し、
    実行の概要情報を一覧で返します。
    最近の実行や進行中の実行を確認するのに適しています。
    """
    runs = api_state.get_all_runs()
    # 開始時刻の降順にソートして、件数制限をかける
    runs.sort(key=lambda x: x.start_time, reverse=True)
    return runs[:limit]


@router.get("/{run_id}", response_model=ApiResponse[RunInfo])
async def get_run_info(run_id: str):
    """指定された実行IDの情報を取得（インメモリ状態に基づく）

    このエンドポイントはメモリ内の api_state オブジェクトを参照し、
    特定の run_id に対応する実行情報を返します。
    """
    run = api_state.get_run(run_id)
    if not run:
        return ApiResponse(
            success=False,
            message=f"実行 '{run_id}' は存在しません",
            data=None
        )
    return ApiResponse(data=run)
