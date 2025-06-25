"""
WebAPIのルーター定義
各エージェントの状態やデータを取得・監視するためのAPIを実装
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List
import logging

from ..models.api_models import ApiResponse, AgentInfo
from ..state import api_state
from ..utils.api_utils import serialize_for_api

logger = logging.getLogger("agents_router")

router = APIRouter(prefix="/api/agents", tags=["Agents"])

@router.get("/", response_model=List[AgentInfo])
async def list_agents():
    """すべてのエージェントの一覧を取得"""
    agents = api_state.get_all_agents()
    return agents


@router.get("/{agent_name}", response_model=ApiResponse[Dict])
async def get_agent_info(agent_name: str):
    """指定されたエージェントの情報を取得"""
    info = api_state.get_agent_info(agent_name)
    if not info:
        return ApiResponse(
            success=False,
            message=f"エージェント '{agent_name}' は存在しません",
            data=None
        )
    return ApiResponse(data=info)


@router.get("/{agent_name}/latest_input", response_model=ApiResponse[Dict])
async def get_latest_input(agent_name: str):
    """エージェントの最新の入力状態を取得"""
    data = api_state.get_agent_data(agent_name, "input_state")
    return ApiResponse(data=serialize_for_api(data))


@router.get("/{agent_name}/latest_output", response_model=ApiResponse[Dict])
async def get_latest_output(agent_name: str):
    """エージェントの最新の出力状態を取得"""
    data = api_state.get_agent_data(agent_name, "output_state")
    return ApiResponse(data=serialize_for_api(data))


@router.get("/{agent_name}/reasoning", response_model=ApiResponse[Dict])
async def get_reasoning(agent_name: str):
    """エージェントの推論内容を取得"""
    try:
        data = api_state.get_agent_data(agent_name, "reasoning")

        if data is None:
            return ApiResponse(
                success=False,
                message=f"{agent_name} の推論記録が見つかりません",
                data={"message": f"エージェント {agent_name} に推論データが存在しません"}
            )

        serialized_data = serialize_for_api(data)

        if not isinstance(serialized_data, dict):
            return ApiResponse(
                data={"content": serialized_data, "type": "raw_content"}
            )

        return ApiResponse(data=serialized_data)
    except Exception as e:
        logger.error(f"{agent_name} の推論データをシリアライズ中にエラー: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"{agent_name} の推論データを処理できませんでした: {str(e)}",
            data={"error": str(e), "original_type": str(type(data))}
        )


@router.get("/{agent_name}/latest_llm_request", response_model=ApiResponse[Dict])
async def get_latest_llm_request(agent_name: str):
    """エージェントの最新のLLMリクエストを取得"""
    try:
        data = api_state.get_agent_data(agent_name, "llm_request")

        if data is None:
            return ApiResponse(
                success=True,
                message=f"{agent_name} の LLMリクエスト記録が見つかりません",
                data={"message": f"{agent_name} の LLMリクエスト記録が見つかりません"}
            )

        serialized_data = serialize_for_api(data)

        if not isinstance(serialized_data, dict):
            serialized_data = {
                "content": serialized_data, "type": "raw_content"}

        return ApiResponse(data=serialized_data)
    except Exception as e:
        logger.error(f"{agent_name} の LLMリクエストデータ処理中にエラー: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"{agent_name} の LLMリクエストデータを処理できませんでした: {str(e)}",
            data={"error": str(e)}
        )


@router.get("/{agent_name}/latest_llm_response", response_model=ApiResponse[Dict])
async def get_latest_llm_response(agent_name: str):
    """エージェントの最新のLLM応答を取得"""
    try:
        data = api_state.get_agent_data(agent_name, "llm_response")

        if data is None:
            return ApiResponse(
                success=True,
                message=f"{agent_name} の LLM応答記録が見つかりません",
                data={"message": f"{agent_name} の LLM応答記録が見つかりません"}
            )

        serialized_data = serialize_for_api(data)

        if not isinstance(serialized_data, dict):
            serialized_data = {
                "content": serialized_data, "type": "raw_content"}

        return ApiResponse(data=serialized_data)
    except Exception as e:
        logger.error(f"{agent_name} の LLM応答データ処理中にエラー: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"{agent_name} の LLM応答データを処理できませんでした: {str(e)}",
            data={"error": str(e)}
        )
