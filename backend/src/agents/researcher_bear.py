from langchain_core.messages import HumanMessage
from .state import AgentState, show_agent_reasoning, show_workflow_status
from ..utils.api_utils import agent_endpoint, log_llm_interaction
import json
import ast


@agent_endpoint("researcher_bear", "売方研究員，ベア視点で市場データを分析し、リスクを提示します")
def researcher_bear_agent(state: AgentState):
    """Analyzes signals from a bearish perspective and generates cautionary investment thesis."""
    show_workflow_status("Bearish Researcher")
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

    # Analyze from bearish perspective
    bearish_points = []
    confidence_scores = []

    # Technical Analysis
    if technical_signals["signal"] == "bearish":
        bearish_points.append(
            f"Technical indicators show bearish momentum with {technical_signals['confidence']} confidence")
        confidence_scores.append(
            float(str(technical_signals["confidence"]).replace("%", "")) / 100)
    else:
        bearish_points.append(
            "Technical rally may be temporary, suggesting potential reversal")
        confidence_scores.append(0.3)

    # Fundamental Analysis
    if fundamental_signals["signal"] == "bearish":
        bearish_points.append(
            f"Concerning fundamentals with {fundamental_signals['confidence']} confidence")
        confidence_scores.append(
            float(str(fundamental_signals["confidence"]).replace("%", "")) / 100)
    else:
        bearish_points.append(
            "Current fundamental strength may not be sustainable")
        confidence_scores.append(0.3)

    # Sentiment Analysis
    if sentiment_signals["signal"] == "bearish":
        bearish_points.append(
            f"Negative market sentiment with {sentiment_signals['confidence']} confidence")
        confidence_scores.append(
            float(str(sentiment_signals["confidence"]).replace("%", "")) / 100)
    else:
        bearish_points.append(
            "Market sentiment may be overly optimistic, indicating potential risks")
        confidence_scores.append(0.3)

    # Valuation Analysis
    if valuation_signals["signal"] == "bearish":
        bearish_points.append(
            f"Stock appears overvalued with {valuation_signals['confidence']} confidence")
        confidence_scores.append(
            float(str(valuation_signals["confidence"]).replace("%", "")) / 100)
    else:
        bearish_points.append(
            "Current valuation may not fully reflect downside risks")
        confidence_scores.append(0.3)

    # Calculate overall bearish confidence
    avg_confidence = sum(confidence_scores) / len(confidence_scores)

    message_content = {
        "perspective": "bearish",
        "confidence": avg_confidence,
        "thesis_points": bearish_points,
        "reasoning": "Bearish thesis based on comprehensive analysis of technical, fundamental, sentiment, and valuation factors"
    }

    message = HumanMessage(
        content=json.dumps(message_content),
        name="researcher_bear_agent",
    )

    if show_reasoning:
        show_agent_reasoning(message_content, "Bearish Researcher")
        state["metadata"]["agent_reasoning"] = message_content

    show_workflow_status("Bearish Researcher", "completed")
    return {
        "messages": state["messages"] + [message],
        "data": state["data"],
        "metadata": state["metadata"],
    }
