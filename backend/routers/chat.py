"""
チャットAPI - フロントエンドとバックエンドマルチエージェントシステムの統合
"""

import json
import uuid
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..models.api_models import ApiResponse
from ..state import api_state
from ..services.analysis import execute_stock_analysis
from ..utils.api_utils import serialize_for_api, safe_parse_json

# Multi-agent system imports
from ..src.main import run_hedge_fund

logger = logging.getLogger("chat_router")

router = APIRouter(prefix="/api/chat", tags=["Chat"])


class Message(BaseModel):
    """チャットメッセージモデル"""
    role: str = Field(..., description="メッセージの役割 (user, assistant, system)")
    content: str = Field(..., description="メッセージ内容")
    id: Optional[str] = Field(None, description="メッセージID")
    createdAt: Optional[datetime] = Field(None, description="作成日時")


class ChatRequest(BaseModel):
    """チャットリクエストモデル"""
    id: str = Field(..., description="チャットセッションID")
    messages: List[Message] = Field(..., description="チャットメッセージ履歴")
    modelId: str = Field(default="gemini-1.5-flash", description="使用するモデルID")


def extract_ticker_from_message(content: str) -> Optional[str]:
    """メッセージからティッカーシンボルを抽出する簡単な関数"""
    import re
    # 一般的なティッカーパターンを検索（大文字3-5文字）
    ticker_pattern = r'\b[A-Z]{2,5}\b'
    matches = re.findall(ticker_pattern, content)
    
    # 一般的な株式ティッカーを優先
    common_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'BAC', 'WFC']
    for ticker in matches:
        if ticker in common_tickers:
            return ticker
    
    # 最初に見つかったティッカーを返す
    return matches[0] if matches else None


def determine_analysis_type(content: str) -> str:
    """メッセージ内容から分析タイプを判定"""
    content_lower = content.lower()
    
    if any(word in content_lower for word in ['price', '価格', 'chart', 'チャート', 'technical']):
        return 'technical'
    elif any(word in content_lower for word in ['earnings', '決算', 'revenue', '売上', 'fundamental']):
        return 'fundamental'
    elif any(word in content_lower for word in ['news', 'ニュース', 'sentiment', '感情']):
        return 'sentiment'
    elif any(word in content_lower for word in ['risk', 'リスク', 'portfolio', 'ポートフォリオ']):
        return 'risk'
    else:
        return 'comprehensive'


async def process_chat_with_agents(messages: List[Message], chat_id: str) -> str:
    """マルチエージェントシステムでチャット処理"""
    
    # 最新のユーザーメッセージを取得
    user_messages = [msg for msg in messages if msg.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="ユーザーメッセージが見つかりません")
    
    latest_message = user_messages[-1].content
    
    # ティッカーシンボルを抽出
    ticker = extract_ticker_from_message(latest_message)
    if not ticker:
        ticker = "AAPL"  # デフォルト
    
    # 分析タイプを判定
    analysis_type = determine_analysis_type(latest_message)
    
    try:
        # マルチエージェントシステムを実行
        portfolio = {
            "cash": 100000.0,
            "stock": 0
        }
        
        result = run_hedge_fund(
            run_id=chat_id,
            ticker=ticker,
            start_date="2024-01-01",
            end_date="2024-12-31", 
            portfolio=portfolio,
            show_reasoning=True,
            num_of_news=5,
            show_summary=False
        )
        
        return result
    
    except Exception as e:
        logger.error(f"マルチエージェントシステム実行エラー: {str(e)}")
        return f"申し訳ございません。{ticker}の分析中にエラーが発生しました: {str(e)}"


@router.post("")
async def chat_endpoint(request: ChatRequest):
    """
    チャットエンドポイント - マルチエージェントシステムと統合
    ストリーミングレスポンスを返す
    """
    try:
        chat_id = request.id
        messages = request.messages
        
        # マルチエージェントシステムで処理
        async def generate_response():
            message_id = str(uuid.uuid4())
            yield f"data: {json.dumps({'type': 'message-start', 'message': {'id': message_id, 'role': 'assistant'}})}\n\n"
            
            try:
                # 処理中であることを通知
                start_message = '\n🔍 分析を開始しています...\n\n'
                yield f"data: {json.dumps({'type': 'text-delta', 'textDelta': start_message})}\n\n"
                
                # マルチエージェントシステムを実行
                result = await process_chat_with_agents(messages, chat_id)
                
                # 結果を段階的にストリーミング（文字単位ではなく、チャンク単位で）
                chunk_size = 50  # 文字数単位
                current_pos = 0
                
                while current_pos < len(result):
                    end_pos = min(current_pos + chunk_size, len(result))
                    chunk = result[current_pos:end_pos]
                    
                    yield f"data: {json.dumps({'type': 'text-delta', 'textDelta': chunk})}\n\n"
                    current_pos = end_pos
                    
                    # 少し遅延を入れて自然なストリーミング感を演出
                    await asyncio.sleep(0.02)
                
                yield f"data: {json.dumps({'type': 'message-stop'})}\n\n"
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                error_msg = f"\n❌ エラーが発生しました: {str(e)}\n\n詳細についてはサーバーログを確認してください。"
                yield f"data: {json.dumps({'type': 'text-delta', 'textDelta': error_msg})}\n\n"
                yield f"data: {json.dumps({'type': 'message-stop'})}\n\n"
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        logger.error(f"チャットエンドポイントエラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"チャット処理中にエラーが発生しました: {str(e)}")


@router.delete("")
async def delete_chat(chat_id: str):
    """チャット削除エンドポイント"""
    try:
        # チャット関連のデータを削除
        api_state.remove_run(chat_id)
        
        return ApiResponse(
            success=True,
            message="チャットが削除されました",
            data={"id": chat_id}
        )
    except Exception as e:
        logger.error(f"チャット削除エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"チャット削除中にエラーが発生しました: {str(e)}")