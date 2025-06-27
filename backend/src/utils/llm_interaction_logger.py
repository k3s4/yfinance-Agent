import functools
import io
import sys
import logging
from contextvars import ContextVar
from typing import Any, Callable, List, Optional, Dict, Tuple
from datetime import datetime, UTC

from backend.schemas import LLMInteractionLog, AgentExecutionLog
from backend.storage.base import BaseLogStorage
from ..agents.state import AgentState
from .serialization import serialize_agent_state

# --- コンテキスト変数 ---
# これらの変数は、現在の実行コンテキスト（例：ワークフロー内の単一エージェント実行）に固有の状態を保持します。

# 現在の実行のBaseLogStorageインスタンスを保持します。main.pyで初期化されます。
log_storage_context: ContextVar[Optional[BaseLogStorage]] = ContextVar(
    "log_storage_context", default=None
)

# 現在実行中のエージェントの名前を保持します。デコレータによって設定されます。
current_agent_name_context: ContextVar[Optional[str]] = ContextVar(
    "current_agent_name_context", default=None
)

# ワークフロー全体の実行に対する一意のIDを保持します。main.pyで設定され、状態を介して渡されます。
current_run_id_context: ContextVar[Optional[str]] = ContextVar(
    "current_run_id_context", default=None
)


# --- 出力キャプチャユーティリティ ---

class OutputCapture:
    """標準出力とログをキャプチャするユーティリティクラス"""

    def __init__(self):
        self.outputs = []
        self.stdout_buffer = io.StringIO()
        self.old_stdout = None
        self.log_handler = None
        self.old_log_level = None

    def __enter__(self):
        # 標準出力をキャプチャ
        self.old_stdout = sys.stdout
        sys.stdout = self.stdout_buffer

        # ログをキャプチャ
        self.log_handler = logging.StreamHandler(io.StringIO())
        self.log_handler.setLevel(logging.INFO)
        root_logger = logging.getLogger()
        self.old_log_level = root_logger.level
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(self.log_handler)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 標準出力を復元し、内容をキャプチャ
        sys.stdout = self.old_stdout
        stdout_content = self.stdout_buffer.getvalue()
        if stdout_content.strip():
            self.outputs.append(stdout_content)

        # ログを復元し、内容をキャプチャ
        log_content = self.log_handler.stream.getvalue()
        if log_content.strip():
            self.outputs.append(log_content)

        # ログハンドラをクリーンアップ
        root_logger = logging.getLogger()
        root_logger.removeHandler(self.log_handler)
        root_logger.setLevel(self.old_log_level)


# --- LLM呼び出しのラッパー ---

def wrap_llm_call(original_llm_func: Callable) -> Callable:
    """LLM呼び出し関数（例：get_chat_completion）をラップして、相互作用をログに記録します。

    エージェントデコレータによって設定されたコンテキスト変数を読み取り、エージェント名、
    実行ID、およびストレージインスタンスを取得します。

    Args:
        original_llm_func: LLM呼び出しを行う元の関数。

    Returns:
        元の結果を返す前に相互作用をログに記録するラップされた関数。
    """

    @functools.wraps(original_llm_func)
    def wrapper(*args, **kwargs) -> Any:
        # コンテキスト情報を取得
        storage = log_storage_context.get()
        agent_name = current_agent_name_context.get()
        run_id = current_run_id_context.get()

        # コンテキストが欠落していても元の呼び出しを続行しますが、ログは記録しません
        if not storage or not agent_name:
            # 必要であればここで警告をログに記録することもできます
            return original_llm_func(*args, **kwargs)

        # 通常、最初の引数はメッセージのリストまたはプロンプトであると仮定します
        # ラップされる関数のシグネチャが異なる場合は調整が必要かもしれません
        request_data = args[0] if args else kwargs.get(
            'messages', kwargs)  # 一般的な使用法に基づいて適応

        # 元のLLM呼び出しを実行
        response_data = original_llm_func(*args, **kwargs)

        # ログエントリを作成して保存
        log_entry = LLMInteractionLog(
            agent_name=agent_name,
            run_id=run_id,  # run_idは設定されていない場合はNoneになることがあります
            request_data=request_data,  # 必要であれば複雑なオブジェクトのシリアライズを検討
            response_data=response_data,  # 必要であれば複雑なオブジェクトのシリアライズを検討
            timestamp=datetime.now(UTC)  # ストレージが独自に追加する場合に備えて明示的なタイムスタンプ
        )
        storage.add_log(log_entry)

        return response_data

    return wrapper


# --- エージェント関数のデコレータ ---

def log_agent_execution(agent_name: str):
    """エージェント関数のデコレータで、ロギングコンテキスト変数を設定します。

    エージェントの状態のメタデータからrun_idを取得します。

    Args:
        agent_name: デコレートされるエージェントの名前。
    """

    def decorator(agent_func: Callable[[AgentState], AgentState]):
        @functools.wraps(agent_func)
        def wrapper(state: AgentState) -> AgentState:
            # 状態メタデータからrun_idを取得（main.pyで設定）
            run_id = state.get("metadata", {}).get("run_id")
            storage = log_storage_context.get()

            # コンテキスト変数を設定
            agent_token = current_agent_name_context.set(agent_name)
            run_id_token = current_run_id_context.set(run_id)

            # 開始時刻と入力状態をキャプチャ
            timestamp_start = datetime.now(UTC)
            serialized_input = serialize_agent_state(state)

            # 出力キャプチャの準備
            output_capture = OutputCapture()
            result_state = None
            error = None

            try:
                # 出力キャプチャを使用
                with output_capture:
                    # 元のAgent関数を実行
                    result_state = agent_func(state)

                # 正常に実行、ログを記録
                timestamp_end = datetime.now(UTC)
                terminal_outputs = output_capture.outputs

                if storage and result_state:
                    # 出力状態をシリアライズ
                    serialized_output = serialize_agent_state(result_state)

                    # 推論の詳細を抽出（もしあれば）
                    reasoning_details = None
                    if result_state.get("metadata", {}).get("show_reasoning", False):
                        if "agent_reasoning" in result_state.get("metadata", {}):
                            reasoning_details = result_state["metadata"]["agent_reasoning"]

                    # ログエントリを作成
                    log_entry = AgentExecutionLog(
                        agent_name=agent_name,
                        run_id=run_id,
                        timestamp_start=timestamp_start,
                        timestamp_end=timestamp_end,
                        input_state=serialized_input,
                        output_state=serialized_output,
                        reasoning_details=reasoning_details,
                        terminal_outputs=terminal_outputs
                    )

                    # ログを保存
                    storage.add_agent_log(log_entry)
            except Exception as e:
                # エラーを記録
                error = str(e)
                # 上位層で処理させるために例外を再スロー
                raise
            finally:
                # コンテキスト変数をクリーンアップ
                current_agent_name_context.reset(agent_token)
                current_run_id_context.reset(run_id_token)

                # エラーが発生したがストレージが利用可能な場合、エラーログを記録
                if error and storage:
                    timestamp_end = datetime.now(UTC)
                    log_entry = AgentExecutionLog(
                        agent_name=agent_name,
                        run_id=run_id,
                        timestamp_start=timestamp_start,
                        timestamp_end=timestamp_end,
                        input_state=serialized_input,
                        output_state={"error": error},
                        reasoning_details=None,
                        terminal_outputs=output_capture.outputs
                    )
                    storage.add_agent_log(log_entry)

            return result_state
        return wrapper
    return decorator

# グローバルストレージインスタンスを設定するヘルパー（main.pyから呼び出される）


def set_global_log_storage(storage: BaseLogStorage):
    log_storage_context.set(storage)
