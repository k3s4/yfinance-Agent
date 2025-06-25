"""
コンテキストマネージャーモジュール

API関連の各種コンテキストマネージャを提供する
"""

from contextlib import contextmanager
import logging

from ..state import api_state

logger = logging.getLogger("context_managers")


@contextmanager
def workflow_run(run_id: str):
    """
    ワークフロー実行用のコンテキストマネージャ

    使用例:
    with workflow_run(run_id):
        # ワークフローの処理を実行
    """
    api_state.register_run(run_id)
    try:
        yield
        api_state.complete_run(run_id, "completed")
    except Exception as e:
        api_state.complete_run(run_id, "error")
        raise
