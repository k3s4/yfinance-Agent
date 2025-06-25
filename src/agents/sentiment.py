from langchain_core.messages import HumanMessage
from src.tools.openrouter_config import get_chat_completion
from src.agents.state import AgentState, show_agent_reasoning, show_workflow_status
from src.utils.logging_config import setup_logger
from src.utils.api_utils import agent_endpoint, log_llm_interaction

# ロガーを初期化
logger = setup_logger('sentiment_agent')


@agent_endpoint("sentiment", "センチメント分析エージェント：ニュースや市場センチメントを分析し投資判断に反映する")
def sentiment_agent(state: AgentState):
    """センチメント分析を担当する"""
    show_workflow_status("センチメント分析エージェント")
    show_reasoning = state["metadata"]["show_reasoning"]

    messages = state["messages"]
    data = state["data"]
    ticker = data["ticker"]
    num_of_news = data.get("num_of_news", 5)

    def analyze_sentiment():
        # US市場データから市場センチメント指標を取得
        short_selling_data = data.get("short_selling_data", {})
        investment_sector_data = data.get("investment_sector_data", {})
        credit_balance_data = data.get("credit_balance_data", {})
        sp500_data = data.get("sp500_data", {})
        
        prompt = f"""
        株式シンボル {ticker} の包括的センチメント分析を実行してください。

        利用可能な市場データ：
        1. 空売り情報：
           - 空売り比率: {short_selling_data.get('short_ratio', 0):.2%}
           - 業種別空売り比率: {short_selling_data.get('sector_short_ratio', 0):.2%}
           - 空売りトレンド: {short_selling_data.get('short_trend', 'unknown')}
           
        2. 投資部門別情報：
           - 機関投資家ネット: ${investment_sector_data.get('institution_net', 0):,.0f}
           - 個人投資家ネット: ${investment_sector_data.get('individual_net', 0):,.0f}
           - 個人投資家ネット: ¥{investment_sector_data.get('individual_net', 0):,.0f}
           - 主要投資家: {investment_sector_data.get('dominant_investor', 'unknown')}
           
        3. 信用取引情報：
           - 信用買い残高: ¥{credit_balance_data.get('margin_buy_balance', 0):,.0f}
           - 信用売り残高: ¥{credit_balance_data.get('margin_sell_balance', 0):,.0f}
           - 信用センチメント: {credit_balance_data.get('credit_sentiment', 'neutral')}
           
        4. TOPIX市場トレンド：
           - 日次変化率: {topix_data.get('daily_change_pct', 0):.2%}
           - マーケットトレンド: {topix_data.get('market_trend', 'neutral')}

        これらの実際の市場データに基づいて、以下を分析してください：
        1. 空売り比率から読み取れる市場参加者の悲観度
        2. 投資部門別フローから見る資金の流れとセンチメント
        3. 信用取引残高から見るレバレッジと投機的動向
        4. TOPIX との相関による全体市場との関係性
        5. 外国人投資家の動向とその影響

        以下の形式で回答してください：
        - overall_sentiment: "positive", "negative", "neutral"のいずれか
        - confidence_score: 0-1の信頼度
        - key_factors: センチメントの主要要因のリスト
        - market_impact: 市場への影響度評価
        - data_driven_insights: 実際のデータから得られた洞察
        """
        
        return get_chat_completion(prompt, model="openai/gpt-4o")

    try:
        sentiment_result = analyze_sentiment()
        
        # US市場データに基づくセンチメント分析結果を構造化
        short_selling_data = data.get("short_selling_data", {})
        investment_sector_data = data.get("investment_sector_data", {})
        credit_balance_data = data.get("credit_balance_data", {})
        
        sentiment_data = {
            "overall_sentiment": short_selling_data.get("market_sentiment", "neutral"),
            "confidence_score": 0.7,  # データドリブンなので高い信頼度
            "key_factors": [
                f"空売り比率: {short_selling_data.get('short_trend', 'unknown')}",
                f"機関投資家動向: {investment_sector_data.get('institutional_sentiment', 'neutral')}",
                f"信用取引センチメント: {credit_balance_data.get('credit_sentiment', 'neutral')}",
                f"機関投資家センチメント: {investment_sector_data.get('institutional_sentiment', 'neutral')}"
            ],
            "market_impact": "high",  # 実際の取引データに基づく
            "analysis_timestamp": data.get("end_date", ""),
            "data_sources": ["空売り残高", "投資部門別", "信用取引", "TOPIX"],
            "short_selling_ratio": short_selling_data.get("short_ratio", 0),
            "foreign_net_flow": investment_sector_data.get("foreign_net", 0),
            "credit_sentiment": credit_balance_data.get("credit_sentiment", "neutral")
        }

        if show_reasoning:
            show_agent_reasoning("センチメント分析エージェント", {
                "analysis": sentiment_result,
                "structured_data": sentiment_data
            })

        # メッセージとデータを更新
        updated_messages = messages + [HumanMessage(content=f"センチメント分析完了: {sentiment_result}")]
        updated_data = data.copy()
        updated_data["sentiment_analysis"] = sentiment_data

        return {
            "messages": updated_messages,
            "data": updated_data,
            "metadata": state["metadata"]
        }

    except Exception as e:
        logger.error(f"センチメント分析エラー: {e}")
        # エラー時のフォールバック
        fallback_data = {
            "overall_sentiment": "neutral",
            "confidence_score": 0.0,
            "key_factors": ["分析エラーのため中立評価"],
            "market_impact": "low",
            "error": str(e)
        }

        updated_messages = messages + [HumanMessage(content="センチメント分析でエラーが発生しました。中立的評価を適用します。")]
        updated_data = data.copy()
        updated_data["sentiment_analysis"] = fallback_data

        return {
            "messages": updated_messages,
            "data": updated_data,
            "metadata": state["metadata"]
        }