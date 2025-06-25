"""
株式分析サービスモジュール
株式分析に関連するバックエンドの機能サービスを提供します
1つの分析リクエストに対してワークフローを起動しログを管理する仕組み
"""

import logging
from typing import Dict, Any
from datetime import datetime, UTC

from ..models.api_models import StockAnalysisRequest
from ..utils.context_managers import workflow_run
from ..state import api_state
from ..schemas import AgentExecutionLog
from ..dependencies import get_log_storage

logger = logging.getLogger("analysis_service")


def execute_stock_analysis(request: StockAnalysisRequest, run_id: str) -> Dict[str, Any]:
    """株式分析タスクを実行する"""
    from src.main import run_hedge_fund  # 循環インポートを避けるためにここで読み込み

    try:
        # ログストレージの取得
        log_storage = get_log_storage()

        # 初期ポートフォリオのセットアップ
        portfolio = {
            "cash": request.initial_capital,
            "stock": request.initial_position
        }

        # 分析の開始ログを出力
        logger.info(f"株式 {request.ticker} の分析を開始します（実行ID: {run_id}）")

        # ワークフローの実行ログ（開始時）を作成
        workflow_log = AgentExecutionLog(
            agent_name="workflow_manager",
            run_id=run_id,
            timestamp_start=datetime.now(UTC),
            timestamp_end=datetime.now(UTC),  # とりあえず同じ値で初期化、後で更新
            input_state={"request": request.dict()},
            output_state=None  # 実行結果を後で記録
        )

        # まだストレージに追加しない。処理が完了してから登録する
        with workflow_run(run_id):
            result = run_hedge_fund(
                run_id=run_id,
                ticker=request.ticker,
                start_date=None,  # システムのデフォルト値を使用
                end_date=None,    # システムのデフォルト値を使用
                portfolio=portfolio,
                show_reasoning=request.show_reasoning,
                num_of_news=request.num_of_news
            )

            # ↓以下を使えばログの終了時刻と出力を更新できる
            # workflow_log.timestamp_end = datetime.now(UTC)
            # workflow_log.output_state = result

            # ↓ログストレージに追加する処理
            # log_storage.add_agent_log(workflow_log)

        logger.info(f"株式分析が完了しました（実行ID: {run_id}）")
        return result

    except Exception as e:
        logger.error(f"株式分析中にエラーが発生しました: {str(e)}")

        # エラー時もログに記録しておくことが望ましい
        # try:
        #     workflow_log.timestamp_end = datetime.now(UTC)
        #     workflow_log.output_state = {"error": str(e)}
        #     log_storage.add_agent_log(workflow_log)
        # except Exception as log_err:
        #     logger.error(f"エラーログの記録中に例外が発生しました: {str(log_err)}")

        # 実行状態を「エラー」で完了としてマーク
        api_state.complete_run(run_id, "error")
        raise
