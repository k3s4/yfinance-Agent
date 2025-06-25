from langchain_core.messages import HumanMessage
from src.agents.state import AgentState, show_agent_reasoning, show_workflow_status
from src.utils.api_utils import agent_endpoint, log_llm_interaction
import json
import ast


@agent_endpoint("researcher_bull", "買方研究員，市場データを多角的に分析し、投資判断を提供")
def researcher_bull_agent(state: AgentState):
    """Analyzes signals from a bullish perspective and generates optimistic investment thesis."""
    show_workflow_status("Bullish Researcher")
    show_reasoning = state["metadata"]["show_reasoning"]

    # Fetch messages from analysts
    technical_message = next(
        (msg for msg in state["messages"] if msg.name == "technical_analyst_agent"), None)
    fundamentals_message = next(
        (msg for msg in state["messages"] if msg.name == "fundamentals_agent"), None)
    sentiment_message = next(
        (msg for msg in state["messages"] if msg.name == "sentiment_agent"), None)
    valuation_message = next(
        (msg for msg in state["messages"] if msg.name == "valuation_agent"), None)

    # メッセージが存在しない場合のハンドリング
    if not technical_message or not fundamentals_message or not sentiment_message or not valuation_message:
        # フォールバック: データから直接読み取り
        sentiment_data = state["data"].get("sentiment_analysis", {})
        fundamental_signals = {"signal": "neutral", "confidence": "50%"}
        technical_signals = {"signal": "neutral", "confidence": "50%"}
        sentiment_signals = {
            "signal": sentiment_data.get("overall_sentiment", "neutral"),
            "confidence": f"{int(sentiment_data.get('confidence_score', 0.5) * 100)}%"
        }
        valuation_signals = {"signal": "neutral", "confidence": "50%"}
    else:
        try:
            fundamental_signals = json.loads(fundamentals_message.content)
            technical_signals = json.loads(technical_message.content)
            sentiment_signals = json.loads(sentiment_message.content)
            valuation_signals = json.loads(valuation_message.content)
        except Exception as e:
            try:
                fundamental_signals = ast.literal_eval(fundamentals_message.content)
                technical_signals = ast.literal_eval(technical_message.content)
                sentiment_signals = ast.literal_eval(sentiment_message.content)
                valuation_signals = ast.literal_eval(valuation_message.content)
            except Exception as fallback_error:
                # フォールバック: データから直接読み取り
                sentiment_data = state["data"].get("sentiment_analysis", {})
                fundamental_signals = {"signal": "neutral", "confidence": "50%"}
                technical_signals = {"signal": "neutral", "confidence": "50%"}
                sentiment_signals = {
                    "signal": sentiment_data.get("overall_sentiment", "neutral"),
                    "confidence": f"{int(sentiment_data.get('confidence_score', 0.5) * 100)}%"
                }
                valuation_signals = {"signal": "neutral", "confidence": "50%"}

    # Analyze from bullish perspective
    bullish_points = []
    confidence_scores = []

    # Technical Analysis
    if technical_signals["signal"] == "bullish":
        bullish_points.append(
            f"Technical indicators show bullish momentum with {technical_signals['confidence']} confidence")
        confidence_scores.append(
            float(str(technical_signals["confidence"]).replace("%", "")) / 100)
    else:
        bullish_points.append(
            "Technical indicators may be conservative, presenting buying opportunities")
        confidence_scores.append(0.3)

    # Fundamental Analysis
    if fundamental_signals["signal"] == "bullish":
        bullish_points.append(
            f"Strong fundamentals with {fundamental_signals['confidence']} confidence")
        confidence_scores.append(
            float(str(fundamental_signals["confidence"]).replace("%", "")) / 100)
    else:
        bullish_points.append(
            "Company fundamentals show potential for improvement")
        confidence_scores.append(0.3)

    # Sentiment Analysis
    if sentiment_signals["signal"] == "bullish":
        bullish_points.append(
            f"Positive market sentiment with {sentiment_signals['confidence']} confidence")
        confidence_scores.append(
            float(str(sentiment_signals["confidence"]).replace("%", "")) / 100)
    else:
        bullish_points.append(
            "Market sentiment may be overly pessimistic, creating value opportunities")
        confidence_scores.append(0.3)

    # Valuation Analysis
    if valuation_signals["signal"] == "bullish":
        bullish_points.append(
            f"Stock appears undervalued with {valuation_signals['confidence']} confidence")
        confidence_scores.append(
            float(str(valuation_signals["confidence"]).replace("%", "")) / 100)
    else:
        bullish_points.append(
            "Current valuation may not fully reflect growth potential")
        confidence_scores.append(0.3)

    # Calculate overall bullish confidence
    avg_confidence = sum(confidence_scores) / len(confidence_scores)

    message_content = {
        "perspective": "bullish",
        "confidence": avg_confidence,
        "thesis_points": bullish_points,
        "reasoning": "Bullish thesis based on comprehensive analysis of technical, fundamental, sentiment, and valuation factors"
    }

    message = HumanMessage(
        content=json.dumps(message_content),
        name="researcher_bull_agent",
    )

    if show_reasoning:
        show_agent_reasoning(message_content, "Bullish Researcher")
        state["metadata"]["agent_reasoning"] = message_content

    show_workflow_status("Bullish Researcher", "completed")
    return {
        "messages": state["messages"] + [message],
        "data": state["data"],
        "metadata": state["metadata"],
    }
