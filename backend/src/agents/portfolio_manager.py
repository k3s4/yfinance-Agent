from langchain_core.messages import HumanMessage
from ..tools.openrouter_config import get_chat_completion
from .state import AgentState, show_agent_reasoning, show_workflow_status
from ..utils.logging_config import setup_logger
from ..utils.api_utils import agent_endpoint, log_llm_interaction

# ロガーを初期化
logger = setup_logger('portfolio_manager_agent')


@agent_endpoint("portfolio_management", "ポートフォリオ管理エージェント：総合分析に基づき最終的な投資判断と取引推奨を行う")
def portfolio_management_agent(state: AgentState):
    """ポートフォリオ管理と最終投資判断を担当する"""
    show_workflow_status("ポートフォリオ管理エージェント")
    show_reasoning = state["metadata"]["show_reasoning"]

    messages = state["messages"]
    data = state["data"]
    ticker = data["ticker"]
    portfolio = data.get("portfolio", {})

    @log_llm_interaction(state)
    def make_investment_decision():
        # 全エージェントからの分析結果を統合
        technical_data = data.get("technical_analysis", {})
        fundamental_data = data.get("fundamental_analysis", {})
        sentiment_data = data.get("sentiment_analysis", {})
        valuation_data = data.get("valuation_analysis", {})
        risk_data = data.get("risk_analysis", {})
        debate_data = data.get("debate_analysis", {})
        
        prompt = f"""
        株式シンボル {ticker} の最終投資判断を行ってください。

        統合分析データ：
        - テクニカル分析: {technical_data}
        - ファンダメンタル分析: {fundamental_data}
        - バリュエーション分析: {valuation_data}
        - センチメント分析: {sentiment_data}
        - リスク分析: {risk_data}
        - 議論の要約: {debate_data}
        
        US市場データ：
        - 空売り情報: {data.get('short_selling_data', {})}
        - 投資部門別フロー: {data.get('investment_sector_data', {})}
        - S&P 500市場トレンド: {data.get('sp500_data', {})}
        - 信用取引残高: {data.get('credit_balance_data', {})}
        
        現在のポートフォリオ: {portfolio}

        全ての分析を総合し、以下を決定してください：
        1. 投資判断 (BUY/SELL/HOLD)
        2. 推奨ポジションサイズ
        3. エントリー価格目標
        4. 利益確定目標
        5. 損切り水準
        6. 投資期間の推奨
        7. 主要なリスク要因と対策

        論理的で具体的な推奨を提供してください。
        """
        
        messages = [{"role": "user", "content": prompt}]
        return get_chat_completion(messages, model="openai/gpt-4o")

    try:
        decision_result = make_investment_decision()
        
        # 投資判断を構造化
        portfolio_recommendation = {
            "action": "HOLD",  # BUY, SELL, HOLD
            "confidence": 0.6,
            "position_size": 0.05,  # ポートフォリオの5%
            "target_price": 0.0,
            "stop_loss": 0.0,
            "profit_target": 0.0,
            "time_horizon": "medium_term",  # short_term, medium_term, long_term
            "risk_level": "moderate",
            "expected_return": 0.0,
            "max_position_size": 0.10,
            "diversification_notes": "適度な分散を維持",
            "rebalancing_frequency": "monthly"
        }

        if show_reasoning:
            show_agent_reasoning("ポートフォリオ管理エージェント", {
                "final_decision": decision_result,
                "recommendation": portfolio_recommendation,
                "portfolio_impact": f"現在のポートフォリオへの影響分析"
            })

        # LLMの回答から具体的な推奨値を抽出・更新
        if decision_result is not None:
            portfolio_recommendation = _parse_llm_decision(decision_result, portfolio_recommendation)
        else:
            logger.warning("LLMからの投資判断結果がNoneです。デフォルト推奨値を使用します。")
        
        # 構造化された最終メッセージを作成
        final_message_data = {
            "action": portfolio_recommendation['action'],
            "confidence": portfolio_recommendation['confidence'],
            "position_size": portfolio_recommendation['position_size'],
            "target_price": portfolio_recommendation.get('target_price', 0.0),
            "stop_loss": portfolio_recommendation.get('stop_loss', 0.0),
            "profit_target": portfolio_recommendation.get('profit_target', 0.0),
            "time_horizon": portfolio_recommendation.get('time_horizon', 'medium_term'),
            "risk_level": portfolio_recommendation.get('risk_level', 'moderate'),
            "reasoning": decision_result,
            "ticker": ticker,
            "analysis_summary": _create_analysis_summary(data)
        }
        
        # 表示用の最終メッセージ
        decision_text = decision_result if decision_result is not None else "LLM分析を取得できませんでした。保守的な判断として上記の推奨値を使用してください。"
        final_display_message = f"""
        【最終投資判断】
        銘柄: {ticker}
        判断: {portfolio_recommendation['action']}
        信頼度: {portfolio_recommendation['confidence']:.1%}
        推奨ポジション: {portfolio_recommendation['position_size']:.1%}
        
        {decision_text}
        """

        # メッセージとデータを更新
        updated_messages = messages + [HumanMessage(content=final_display_message)]
        updated_data = data.copy()
        updated_data["final_recommendation"] = final_message_data
        updated_data["investment_decision"] = decision_result

        return {
            "messages": updated_messages,
            "data": updated_data,
            "metadata": state["metadata"]
        }

    except Exception as e:
        logger.error(f"ポートフォリオ管理エラー: {e}")
        # エラー時のフォールバック
        fallback_recommendation = {
            "action": "HOLD",
            "confidence": 0.0,
            "position_size": 0.0,
            "risk_level": "high",
            "error": str(e)
        }

        error_message = f"ポートフォリオ管理でエラーが発生しました。保守的な判断として HOLD を推奨します。エラー: {str(e)}"
        
        updated_messages = messages + [HumanMessage(content=error_message)]
        updated_data = data.copy()
        updated_data["final_recommendation"] = fallback_recommendation

        return {
            "messages": updated_messages,
            "data": updated_data,
            "metadata": state["metadata"]
        }


def _parse_llm_decision(decision_text: str, base_recommendation: dict) -> dict:
    """
    LLMの判断テキストから具体的な推奨値を抽出する
    
    Args:
        decision_text: LLMからの決定テキスト
        base_recommendation: ベースとなる推奨データ
        
    Returns:
        更新された推奨データ
    """
    import re
    
    recommendation = base_recommendation.copy()
    
    # None チェックを追加
    if decision_text is None:
        logger.warning("LLM判断テキストがNoneです。ベース推奨値を返します。")
        return recommendation
    
    # 文字列型チェックを追加
    if not isinstance(decision_text, str):
        logger.warning(f"LLM判断テキストが文字列ではありません: {type(decision_text)}。ベース推奨値を返します。")
        return recommendation
    
    try:
        # BUY/SELL/HOLD の抽出
        action_pattern = r'(?:投資判断|判断|アクション)[\s:：]*([A-Z]+|買い|売り|保有|ホールド)'
        action_match = re.search(action_pattern, decision_text, re.IGNORECASE)
        if action_match:
            action_text = action_match.group(1).upper()
            if 'BUY' in action_text or '買い' in action_text:
                recommendation['action'] = 'BUY'
            elif 'SELL' in action_text or '売り' in action_text:
                recommendation['action'] = 'SELL'
            else:
                recommendation['action'] = 'HOLD'
        
        # 信頼度の抽出
        confidence_pattern = r'(?:信頼度|confidence)[\s:：]*(\d+(?:\.\d+)?%?)'
        confidence_match = re.search(confidence_pattern, decision_text, re.IGNORECASE)
        if confidence_match:
            conf_text = confidence_match.group(1).replace('%', '')
            confidence = float(conf_text)
            if confidence > 1:
                confidence /= 100  # パーセンテージを小数点に変換
            recommendation['confidence'] = confidence
        
        # ポジションサイズの抽出
        position_pattern = r'(?:ポジション|position)[\s:：]*(\d+(?:\.\d+)?%?)'
        position_match = re.search(position_pattern, decision_text, re.IGNORECASE)
        if position_match:
            pos_text = position_match.group(1).replace('%', '')
            position = float(pos_text)
            if position > 1:
                position /= 100  # パーセンテージを小数点に変換
            recommendation['position_size'] = position
            
    except Exception as e:
        logger.warning(f"LLM判断の解析中にエラー: {e}")
    
    return recommendation


def _create_analysis_summary(data: dict) -> dict:
    """
    各分析の要約を作成する
    
    Args:
        data: 全エージェントのデータ
        
    Returns:
        分析サマリー
    """
    summary = {}
    
    # 各分析からの主要な結果を抽出
    analysis_keys = [
        'technical_analysis',
        'fundamental_analysis',
        'sentiment_analysis', 
        'valuation_analysis',
        'risk_analysis',
        'debate_analysis'
    ]
    
    for key in analysis_keys:
        if key in data:
            analysis_data = data[key]
            if isinstance(analysis_data, dict):
                # 主要な指標を抽出
                extracted = {}
                if 'signal' in analysis_data:
                    extracted['signal'] = analysis_data['signal']
                if 'confidence' in analysis_data:
                    extracted['confidence'] = analysis_data['confidence']
                if 'score' in analysis_data:
                    extracted['score'] = analysis_data['score']
                if 'risk_level' in analysis_data:
                    extracted['risk_level'] = analysis_data['risk_level']
                    
                summary[key] = extracted
    
    return summary