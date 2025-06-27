"""
エージェントデータ収集・蓄積モジュール

このモジュールは、ワークフロー全体の実行中に各エージェントからのデータを収集し、
最終的なサマリーレポート生成のために整理・保存します。
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .logging_config import setup_logger

# ロガーを設定
logger = setup_logger('agent_collector')

# グローバル状態変数
_collected_data: Dict[str, Any] = {}
_final_state: Optional[Dict[str, Any]] = None


def store_final_state(final_state: Dict[str, Any]) -> None:
    """
    ワークフローの最終状態を保存する
    
    Args:
        final_state: ワークフローの最終状態
    """
    global _final_state
    _final_state = final_state.copy() if final_state else {}
    logger.info("最終状態が保存されました")


def get_enhanced_final_state() -> Dict[str, Any]:
    """
    拡張された最終状態を取得する
    
    Returns:
        拡張された最終状態データ
    """
    if not _final_state:
        logger.warning("最終状態が設定されていません")
        return {}
    
    enhanced_state = _final_state.copy()
    
    # エージェントデータの拡張処理
    enhanced_state['processed_agents'] = _extract_agent_summaries(enhanced_state)
    enhanced_state['report_metadata'] = _generate_report_metadata(enhanced_state)
    
    return enhanced_state


def _extract_agent_summaries(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    各エージェントのサマリーデータを抽出する
    
    Args:
        state: ワークフローの状態
        
    Returns:
        エージェントサマリーデータ
    """
    summaries = {}
    
    # データセクションから各エージェントの分析結果を抽出
    data = state.get('data', {})
    
    # 各分析結果を整理
    analysis_types = [
        'technical_analysis',
        'fundamental_analysis', 
        'sentiment_analysis',
        'valuation_analysis',
        'risk_analysis',
        'debate_analysis',
        'final_recommendation'
    ]
    
    for analysis_type in analysis_types:
        if analysis_type in data:
            summaries[analysis_type] = data[analysis_type]
    
    # メッセージから各エージェントの詳細データを抽出
    messages = state.get('messages', [])
    for message in messages:
        if hasattr(message, 'name') and message.name:
            agent_name = message.name
            if hasattr(message, 'content'):
                try:
                    # JSON形式のコンテンツを解析
                    if isinstance(message.content, str) and message.content.strip().startswith('{'):
                        content = json.loads(message.content)
                        summaries[f"{agent_name}_details"] = content
                    else:
                        summaries[f"{agent_name}_message"] = message.content
                except json.JSONDecodeError:
                    summaries[f"{agent_name}_message"] = message.content
    
    return summaries


def _generate_report_metadata(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    レポート用のメタデータを生成する
    
    Args:
        state: ワークフローの状態
        
    Returns:
        レポートメタデータ
    """
    data = state.get('data', {})
    metadata = state.get('metadata', {})
    
    report_metadata = {
        'generated_at': datetime.now().isoformat(),
        'ticker': data.get('ticker', '不明'),
        'analysis_period': {
            'start_date': data.get('start_date'),
            'end_date': data.get('end_date')
        },
        'portfolio_info': data.get('portfolio', {}),
        'run_id': metadata.get('run_id'),
        'workflow_completed': True
    }
    
    # 最終的な投資判断を抽出
    final_rec = data.get('final_recommendation', {})
    if final_rec:
        report_metadata['final_decision'] = {
            'action': final_rec.get('action', 'HOLD'),
            'confidence': final_rec.get('confidence', 0.0),
            'position_size': final_rec.get('position_size', 0.0)
        }
    
    return report_metadata


def collect_agent_data(agent_name: str, agent_data: Any) -> None:
    """
    エージェントデータを収集する
    
    Args:
        agent_name: エージェント名
        agent_data: エージェントのデータ
    """
    global _collected_data
    
    if agent_name not in _collected_data:
        _collected_data[agent_name] = []
    
    _collected_data[agent_name].append({
        'timestamp': datetime.now().isoformat(),
        'data': agent_data
    })
    
    logger.debug(f"エージェント {agent_name} のデータを収集しました")


def get_collected_data() -> Dict[str, Any]:
    """
    収集されたデータを取得する
    
    Returns:
        収集されたエージェントデータ
    """
    return _collected_data.copy()


def clear_collected_data() -> None:
    """
    収集されたデータをクリアする
    """
    global _collected_data, _final_state
    _collected_data = {}
    _final_state = None
    logger.info("収集されたデータをクリアしました")


def extract_key_insights(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    状態から主要な洞察を抽出する
    
    Args:
        state: ワークフローの状態
        
    Returns:
        主要な洞察データ
    """
    insights = {
        'market_sentiment': 'neutral',
        'technical_signal': 'neutral', 
        'fundamental_score': 0.0,
        'risk_level': 'medium',
        'consensus_view': 'hold'
    }
    
    data = state.get('data', {})
    
    # 各分析からの主要指標を抽出
    if 'sentiment_analysis' in data:
        sentiment = data['sentiment_analysis']
        if isinstance(sentiment, dict):
            insights['market_sentiment'] = sentiment.get('signal', 'neutral')
    
    if 'technical_analysis' in data:
        technical = data['technical_analysis']
        if isinstance(technical, dict):
            insights['technical_signal'] = technical.get('signal', 'neutral')
    
    if 'risk_analysis' in data:
        risk = data['risk_analysis']
        if isinstance(risk, dict):
            insights['risk_level'] = risk.get('risk_level', 'medium')
    
    if 'debate_analysis' in data:
        debate = data['debate_analysis']
        if isinstance(debate, dict):
            insights['consensus_view'] = debate.get('signal', 'hold')
    
    if 'final_recommendation' in data:
        final_rec = data['final_recommendation']
        if isinstance(final_rec, dict):
            insights['final_action'] = final_rec.get('action', 'HOLD')
            insights['final_confidence'] = final_rec.get('confidence', 0.0)
    
    return insights