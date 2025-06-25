"""
APIツールモジュール - Agentが共有するAPI機能コンポーネントを提供

このモジュールは、グローバルなFastAPIアプリケーションインスタンスとルーティング登録メカニズムを定義し、
各Agentに統一されたAPI公開方法を提供します。

注意: ほとんどの機能はbackendディレクトリにリファクタリングされており、このモジュールは後方互換性のためにのみ保持されています。
"""

from fastapi import APIRouter
from backend.main import app  # このインポートを復元
import json  # 暗黙的に使用されているため維持
import logging
import functools
# import uuid # 未使用
import threading  # サーバー停止イベントに使用
import time  # サーバー停止イベントに使用
import inspect  # log_llm_interaction（デコレータモード）で使用
from typing import Dict, List, Any, Optional, Callable, TypeVar  # 必要な型を維持
from datetime import datetime, UTC  # 必要なdatetimeオブジェクトを維持
# from contextlib import contextmanager # 未使用
# from concurrent.futures import ThreadPoolExecutor, Future # 未使用
import uvicorn  # start_api_serverで使用
# from functools import wraps # functools経由でインポートされているため冗長
# import builtins # 未使用
import sys
import io

# リファクタリングされたモジュールをインポート
from backend.models.api_models import (
    # ApiResponse, AgentInfo, # おそらく未使用
    RunInfo,  # 維持
    # StockAnalysisRequest, StockAnalysisResponse # おそらく未使用
)
from backend.state import api_state
from backend.utils.api_utils import (
    # serialize_for_api, # 未使用
    safe_parse_json,  # 維持
    format_llm_request,  # 維持
    format_llm_response  # 維持
)
# from backend.utils.context_managers import workflow_run # 未使用
# from backend.services import execute_stock_analysis # 未使用
from backend.schemas import LLMInteractionLog  # 維持
from backend.schemas import AgentExecutionLog  # 維持
from src.utils.serialization import serialize_agent_state  # 維持

# ロガーをインポート
try:
    # log_agent_executionはここでは不要
    from src.utils.llm_interaction_logger import set_global_log_storage  # 維持
    from backend.dependencies import get_log_storage
    _has_log_system = True
except ImportError:
    _has_log_system = False
    # インポート失敗時にダミーのset_global_log_storageを定義

    def set_global_log_storage(storage):
        pass
    # インポート失敗時にダミーのget_log_storageを定義

    def get_log_storage():
        return None

# _has_log_systemに関わらず、ここでロガーを一元的に定義
logger = logging.getLogger("api_utils")

# グローバルなログストレージを設定
if _has_log_system:
    try:
        storage = get_log_storage()
        set_global_log_storage(storage)
    except Exception as e:
        # この時点でloggerは必ず定義されている
        logger.warning(f"グローバルログストレージの設定に失敗しました: {str(e)}")

# 型定義
T = TypeVar('T')

# 各AgentのLLM呼び出しを追跡するためのグローバル辞書を追加
_agent_llm_calls = {}

# -----------------------------------------------------------------------------
# FastAPIアプリケーション
# -----------------------------------------------------------------------------

# backendからFastAPIアプリケーションをインポート

# これらのルーターはもはや使用されておらず、後方互換性のためにのみ定義を保持
agents_router = APIRouter(tags=["Agents"])
runs_router = APIRouter(tags=["Runs"])
workflow_router = APIRouter(tags=["Workflow"])

# -----------------------------------------------------------------------------
# デコレータとユーティリティ関数
# -----------------------------------------------------------------------------


def log_llm_interaction(state):
    """LLMの相互作用を記録するデコレータ関数

    この関数は2つの方法で使用できます：
    1. デコレータファクトリとして：log_llm_interaction(state)(llm_func)
    2. 直接呼び出し関数として：既存のlog_llm_interaction互換モード用
    """
    # 直接関数呼び出しモード（後方互換）かどうかをチェック
    if isinstance(state, str) and len(state) > 0:
        # 元の直接呼び出し方式と互換性を持たせる
        agent_name = state  # 最初の引数はagent_name

        def direct_logger(request_data, response_data):
            # フォーマットされたリクエストとレスポンスを保存
            formatted_request = format_llm_request(request_data)
            formatted_response = format_llm_response(response_data)

            timestamp = datetime.now(UTC)

            # 現在の実行IDを取得
            run_id = api_state.current_run_id

            api_state.update_agent_data(
                agent_name, "llm_request", formatted_request)
            api_state.update_agent_data(
                agent_name, "llm_response", formatted_response)

            # 相互作用のタイムスタンプを記録
            api_state.update_agent_data(
                agent_name, "llm_timestamp", timestamp.isoformat())

            # 同時にBaseLogStorageにも保存（/logsエンドポイントが空を返す問題の解決）
            try:
                # log_storageインスタンスを取得
                if _has_log_system:
                    log_storage = get_log_storage()
                    # LLMInteractionLogオブジェクトを作成
                    log_entry = LLMInteractionLog(
                        agent_name=agent_name,
                        run_id=run_id,
                        request_data=formatted_request,
                        response_data=formatted_response,
                        timestamp=timestamp
                    )
                    # ストレージに追加
                    log_storage.add_log(log_entry)
                    logger.debug(f"直接呼び出しのLLM相互作用をログストレージに保存しました: {agent_name}")
            except Exception as log_err:
                logger.warning(f"直接呼び出しのLLM相互作用をログストレージに保存するのに失敗しました: {str(log_err)}")

            return response_data

        return direct_logger

    # デコレータファクトリモード
    def decorator(llm_func):
        @functools.wraps(llm_func)
        def wrapper(*args, **kwargs):
            # 関数呼び出し情報を取得し、より良いリクエスト記録を行う
            caller_frame = inspect.currentframe().f_back
            caller_info = {
                "function": llm_func.__name__,
                "file": caller_frame.f_code.co_filename,
                "line": caller_frame.f_lineno
            }

            # 元の関数を実行して結果を取得
            result = llm_func(*args, **kwargs)

            # stateからagent_nameとrun_idを抽出
            agent_name = None
            run_id = None

            # state引数からの抽出を試みる
            if isinstance(state, dict):
                agent_name = state.get("metadata", {}).get(
                    "current_agent_name")
                run_id = state.get("metadata", {}).get("run_id")

            # stateになければ、コンテキスト変数からの取得を試みる
            if not agent_name:
                try:
                    from src.utils.llm_interaction_logger import current_agent_name_context, current_run_id_context
                    agent_name = current_agent_name_context.get()
                    run_id = current_run_id_context.get()
                except (ImportError, AttributeError):
                    pass

            # それでもなければ、api_stateから現在の実行中のエージェントを取得する
            if not agent_name and hasattr(api_state, "current_agent_name"):
                agent_name = api_state.current_agent_name
                run_id = api_state.current_run_id

            if agent_name:
                timestamp = datetime.now(UTC)

                # messages引数を抽出
                messages = None
                if "messages" in kwargs:
                    messages = kwargs["messages"]
                elif args and len(args) > 0:
                    messages = args[0]

                # その他の引数を抽出
                model = kwargs.get("model")
                client_type = kwargs.get("client_type", "auto")

                # フォーマットされたリクエストデータを準備
                formatted_request = {
                    "caller": caller_info,
                    "messages": messages,
                    "model": model,
                    "client_type": client_type,
                    "arguments": format_llm_request(args),
                    "kwargs": format_llm_request(kwargs) if kwargs else {}
                }

                # フォーマットされたレスポンスデータを準備
                formatted_response = format_llm_response(result)

                # APIステートに記録
                api_state.update_agent_data(
                    agent_name, "llm_request", formatted_request)
                api_state.update_agent_data(
                    agent_name, "llm_response", formatted_response)
                api_state.update_agent_data(
                    agent_name, "llm_timestamp", timestamp.isoformat())

                # 同時にBaseLogStorageにも保存（/logsエンドポイントが空を返す問題の解決）
                try:
                    # log_storageインスタンスを取得
                    if _has_log_system:
                        log_storage = get_log_storage()
                        # LLMInteractionLogオブジェクトを作成
                        log_entry = LLMInteractionLog(
                            agent_name=agent_name,
                            run_id=run_id,
                            request_data=formatted_request,
                            response_data=formatted_response,
                            timestamp=timestamp
                        )
                        # ストレージに追加
                        log_storage.add_log(log_entry)
                        logger.debug(f"デコレータが捕捉したLLM相互作用をログストレージに保存しました: {agent_name}")
                except Exception as log_err:
                    logger.warning(f"デコレータが捕捉したLLM相互作用をログストレージに保存するのに失敗しました: {str(log_err)}")

            return result
        return wrapper
    return decorator


def agent_endpoint(agent_name: str, description: str = ""):
    """
    AgentのAPIエンドポイントを作成するデコレータ

    使用方法:
    @agent_endpoint("sentiment")
    def sentiment_agent(state: AgentState) -> AgentState:
        ...
    """
    def decorator(agent_func):
        # Agentを登録
        api_state.register_agent(agent_name, description)

        # このAgentのLLM呼び出し追跡を初期化
        _agent_llm_calls[agent_name] = False

        @functools.wraps(agent_func)
        def wrapper(state):
            # Agentの状態を実行中に更新
            api_state.update_agent_state(agent_name, "running")

            # 現在のAgent名を状態のメタデータに追加
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["current_agent_name"] = agent_name

            # run_idがメタデータにあることを確認（ログ記録に重要）
            run_id = state.get("metadata", {}).get("run_id")
            # 入力状態を記録
            timestamp_start = datetime.now(UTC)
            serialized_input = serialize_agent_state(state)
            api_state.update_agent_data(
                agent_name, "input_state", serialized_input)

            result = None
            error = None
            terminal_outputs = []  # ターミナル出力をキャプチャ

            # Agent実行中の標準出力/標準エラーとログをキャプチャ
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            log_stream = io.StringIO()
            log_handler = logging.StreamHandler(log_stream)
            log_handler.setLevel(logging.INFO)
            root_logger = logging.getLogger()
            root_logger.addHandler(log_handler)

            redirect_stdout = io.StringIO()
            redirect_stderr = io.StringIO()
            sys.stdout = redirect_stdout
            sys.stderr = redirect_stderr

            try:
                # --- Agentのコアロジックを実行 ---
                # 元のagent_funcを直接呼び出す
                result = agent_func(state)
                # --------------------------

                timestamp_end = datetime.now(UTC)

                # 標準出力/エラーを復元
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                root_logger.removeHandler(log_handler)

                # キャプチャした出力を取得
                stdout_content = redirect_stdout.getvalue()
                stderr_content = redirect_stderr.getvalue()
                log_content = log_stream.getvalue()
                if stdout_content:
                    terminal_outputs.append(stdout_content)
                if stderr_content:
                    terminal_outputs.append(stderr_content)
                if log_content:
                    terminal_outputs.append(log_content)

                # 出力状態をシリアライズ
                serialized_output = serialize_agent_state(result)
                api_state.update_agent_data(
                    agent_name, "output_state", serialized_output)

                # 状態から推論の詳細を抽出（もしあれば）
                reasoning_details = None
                if result.get("metadata", {}).get("show_reasoning", False):
                    if "agent_reasoning" in result.get("metadata", {}):
                        reasoning_details = result["metadata"]["agent_reasoning"]
                        api_state.update_agent_data(
                            agent_name,
                            "reasoning",
                            reasoning_details
                        )

                # Agentの状態を完了に更新
                api_state.update_agent_state(agent_name, "completed")

                # --- Agent実行ログをBaseLogStorageに追加 ---
                try:
                    if _has_log_system:
                        log_storage = get_log_storage()
                        if log_storage:
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
                            log_storage.add_agent_log(log_entry)
                            logger.debug(
                                f"Agent実行ログをストレージに保存しました: {agent_name}, run_id: {run_id}")
                        else:
                            logger.warning(
                                f"ログストレージインスタンスを取得できず、Agent実行ログの記録をスキップします: {agent_name}")
                except Exception as log_err:
                    logger.error(
                        f"Agent実行ログをストレージに保存するのに失敗しました: {agent_name}, {str(log_err)}")
                # -----------------------------------------

                return result
            except Exception as e:
                # エラー時も終了時刻を記録
                timestamp_end = datetime.now(UTC)
                error = str(e)
                # 標準出力/エラーを復元
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                root_logger.removeHandler(log_handler)
                # キャプチャした出力を取得
                stdout_content = redirect_stdout.getvalue()
                stderr_content = redirect_stderr.getvalue()
                log_content = log_stream.getvalue()
                if stdout_content:
                    terminal_outputs.append(stdout_content)
                if stderr_content:
                    terminal_outputs.append(stderr_content)
                if log_content:
                    terminal_outputs.append(log_content)

                # Agentの状態をエラーに更新
                api_state.update_agent_state(agent_name, "error")
                # エラー情報を記録
                api_state.update_agent_data(agent_name, "error", error)

                # --- エラーログをBaseLogStorageに追加 ---
                try:
                    if _has_log_system:
                        log_storage = get_log_storage()
                        if log_storage:
                            log_entry = AgentExecutionLog(
                                agent_name=agent_name,
                                run_id=run_id,
                                timestamp_start=timestamp_start,
                                timestamp_end=timestamp_end,
                                input_state=serialized_input,
                                output_state={"error": error},
                                reasoning_details=None,
                                terminal_outputs=terminal_outputs
                            )
                            log_storage.add_agent_log(log_entry)
                            logger.debug(
                                f"Agentエラーログをストレージに保存しました: {agent_name}, run_id: {run_id}")
                        else:
                            logger.warning(
                                f"ログストレージインスタンスを取得できず、Agentエラーログの記録をスキップします: {agent_name}")
                except Exception as log_err:
                    logger.error(
                        f"Agentエラーログをストレージに保存するのに失敗しました: {agent_name}, {str(log_err)}")
                # --------------------------------------

                # 例外を再スロー
                raise

        return wrapper
    return decorator


# APIサーバーを起動する関数
def start_api_server(host="0.0.0.0", port=8000, stop_event=None):
    """独立したスレッドでAPIサーバーを起動する"""
    if stop_event:
        # グレースフルシャットダウンをサポートする設定を使用
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_config=None,
            # ctrl+c処理を有効化
            use_colors=True
        )
        server = uvicorn.Server(config)

        # サーバーを実行し、別スレッドでstop_eventを監視
        def check_stop_event():
            # バックグラウンドでstop_eventをチェック
            while not stop_event.is_set():
                time.sleep(0.5)
            # stop_eventが設定されたら、サーバーに終了を要求
            logger.info("停止シグナルを受信しました。APIサーバーをシャットダウンしています...")
            server.should_exit = True

        # stop_event監視スレッドを起動
        stop_monitor = threading.Thread(
            target=check_stop_event,
            daemon=True
        )
        stop_monitor.start()

        # サーバーを実行（ブロッキング呼び出しだが、should_exitフラグに応答する）
        try:
            server.run()
        except KeyboardInterrupt:
            # それでもKeyboardInterruptを受け取った場合は、stop_eventも設定されていることを確認
            stop_event.set()
        logger.info("APIサーバーがシャットダウンしました")
    else:
        # デフォルトの方法で起動、外部からの停止制御はサポートしないがCtrl+Cには応答
        uvicorn.run(app, host=host, port=port, log_config=None)
