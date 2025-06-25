from langchain_core.messages import HumanMessage
from src.tools.openrouter_config import get_chat_completion
from src.agents.state import AgentState, show_agent_reasoning, show_workflow_status
from src.utils.logging_config import setup_logger
from src.utils.api_utils import agent_endpoint, log_llm_interaction

# ロガーを初期化
logger = setup_logger('risk_manager_agent')


@agent_endpoint("risk_management", "リスク管理エージェント：投資リスクを評価し、リスク管理戦略を提案する")
def risk_management_agent(state: AgentState):
    """リスク管理を担当する"""
    show_workflow_status("リスク管理エージェント")
    show_reasoning = state["metadata"]["show_reasoning"]

    messages = state["messages"]
    data = state["data"]
    ticker = data["ticker"]
    portfolio = data.get("portfolio", {})

    @log_llm_interaction
    def analyze_risk():
        # 他のエージェントからの分析結果を取得
        technical_data = data.get("technical_analysis", {})
        fundamental_data = data.get("fundamental_analysis", {})
        sentiment_data = data.get("sentiment_analysis", {})
        
        # US市場データからリスク指標を取得
        short_selling_data = data.get("short_selling_data", {})
        investment_sector_data = data.get("investment_sector_data", {})
        credit_balance_data = data.get("credit_balance_data", {})
        sp500_data = data.get("sp500_data", {})
        
        prompt = f"""
        株式シンボル {ticker} の包括的リスク管理分析を実行してください。

        利用可能なデータ：
        - テクニカル分析結果: {technical_data}
        - ファンダメンタル分析結果: {fundamental_data}
        - センチメント分析結果: {sentiment_data}
        - 現在のポートフォリオ: {portfolio}

        US市場リスク指標：
        1. 空売りリスク：
           - 空売り比率: {short_selling_data.get('short_ratio', 0):.2%}
           - 空売りトレンド: {short_selling_data.get('short_trend', 'unknown')}
           
        2. 流動性・レバレッジリスク：
           - 信用買い残高: ${credit_balance_data.get('margin_buy_balance', 0):,.0f}
           - 信用売り残高: ${credit_balance_data.get('margin_sell_balance', 0):,.0f}
           - レバレッジリスク: {credit_balance_data.get('leverage_risk', 'moderate')}
           
        3. 投資家構成リスク：
           - 機関投資家ネットフロー: ${investment_sector_data.get('institution_net', 0):,.0f}
           - 主要投資家: {investment_sector_data.get('dominant_investor', 'unknown')}
           - 機関投資家センチメント: {investment_sector_data.get('institutional_sentiment', 'neutral')}
           
        4. 市場相関リスク：
           - S&P 500日次変化: {sp500_data.get('daily_change_pct', 0):.2%}
           - 市場トレンド: {sp500_data.get('market_trend', 'neutral')}

        以下のリスク要因を実際のデータに基づいて評価してください：
        1. 空売り圧力による下落リスク
        2. 信用取引による流動性リスクとレバレッジリスク
        3. 機関投資家の資金流出リスク
        4. 市場全体（S&P 500）との相関リスク
        5. 投資家構成の偏りによる集中リスク

        データドリブンなリスク管理戦略を提案し、適切なポジションサイズを推奨してください。
        """
        
        return get_chat_completion(prompt, model="openai/gpt-4o")

    try:
        risk_result = analyze_risk()
        
        # US市場データに基づくリスク分析結果を構造化
        short_selling_data = data.get("short_selling_data", {})
        investment_sector_data = data.get("investment_sector_data", {})
        credit_balance_data = data.get("credit_balance_data", {})
        
        # 空売り比率に基づくリスクレベル判定
        short_ratio = short_selling_data.get("short_ratio", 0)
        if short_ratio > 0.4:
            risk_level = "high"
            risk_score = 0.8
            position_size = 0.03  # 3%に制限
        elif short_ratio > 0.2:
            risk_level = "medium"
            risk_score = 0.6
            position_size = 0.07  # 7%
        else:
            risk_level = "low"
            risk_score = 0.3
            position_size = 0.12  # 12%
        
        # レバレッジリスクによる調整
        leverage_risk = credit_balance_data.get("leverage_risk", "moderate")
        if leverage_risk == "high":
            position_size *= 0.5  # ポジションサイズを半分に
            risk_score += 0.2
        
        # 外国人投資家リスクによる調整
        foreign_trend = investment_sector_data.get("foreign_ownership_trend", "neutral")
        if foreign_trend == "bearish":
            risk_score += 0.1
            position_size *= 0.8
        
        risk_data = {
            "overall_risk_level": risk_level,
            "risk_score": min(risk_score, 1.0),
            "key_risks": [
                f"空売り比率: {short_ratio:.1%} ({short_selling_data.get('short_trend', 'unknown')})",
                f"レバレッジリスク: {leverage_risk}",
                f"外国人投資家動向: {foreign_trend}",
                f"信用取引センチメント: {credit_balance_data.get('credit_sentiment', 'neutral')}"
            ],
            "recommended_position_size": min(position_size, 0.15),  # 最大15%制限
            "stop_loss_level": 0.92 if risk_level == "high" else 0.95,  # リスクレベル応じて調整
            "short_selling_pressure": short_ratio,
            "foreign_flow_risk": abs(investment_sector_data.get("foreign_net", 0)) / 1000000,  # 百万円単位
            "leverage_exposure": credit_balance_data.get("margin_ratio", 0),
            "data_confidence": 0.9  # J-Quantsデータベースなので高信頼度
        }

        if show_reasoning:
            show_agent_reasoning("リスク管理エージェント", {
                "analysis": risk_result,
                "structured_data": risk_data
            })

        # メッセージとデータを更新
        updated_messages = messages + [HumanMessage(content=f"リスク管理分析完了: {risk_result}")]
        updated_data = data.copy()
        updated_data["risk_analysis"] = risk_data

        return {
            "messages": updated_messages,
            "data": updated_data,
            "metadata": state["metadata"]
        }

    except Exception as e:
        logger.error(f"リスク管理分析エラー: {e}")
        # エラー時のフォールバック
        fallback_data = {
            "overall_risk_level": "high",
            "risk_score": 0.8,
            "key_risks": ["分析エラーによる不確実性"],
            "recommended_position_size": 0.05,  # 保守的なポジション
            "stop_loss_level": 0.90,
            "error": str(e)
        }

        updated_messages = messages + [HumanMessage(content="リスク管理分析でエラーが発生しました。保守的なリスク評価を適用します。")]
        updated_data = data.copy()
        updated_data["risk_analysis"] = fallback_data

        return {
            "messages": updated_messages,
            "data": updated_data,
            "metadata": state["metadata"]
        }