from langchain_core.messages import HumanMessage
from ..utils.logging_config import setup_logger

from .state import AgentState, show_agent_reasoning, show_workflow_status
from ..utils.api_utils import agent_endpoint, log_llm_interaction

import json

# ロガーの初期化
logger = setup_logger('fundamentals_agent')

##### 基本面分析エージェント #####


@agent_endpoint("fundamentals", "基本面分析エージェント：企業の財務指標、収益性、成長性を分析します")
def fundamentals_agent(state: AgentState):
    """企業のファンダメンタルズ（基礎的経営指標）を分析する役割を担います"""
    show_workflow_status("ファンダメンタル分析中")
    show_reasoning = state["metadata"]["show_reasoning"]
    data = state["data"]
    
    # 財務指標の安全な取得
    financial_metrics_list = data.get("financial_metrics", [])
    if not financial_metrics_list:
        logger.warning("財務指標データが取得できませんでした。デフォルト値を使用します。")
        metrics = {}
    else:
        metrics = financial_metrics_list[0] if len(financial_metrics_list) > 0 else {}

    # 各分析軸ごとのシグナルを初期化
    signals = []
    reasoning = {}

    # 1. 収益性の分析
    return_on_equity = metrics.get("return_on_equity", 0)
    net_margin = metrics.get("net_margin", 0)
    operating_margin = metrics.get("operating_margin", 0)

    thresholds = [
        (return_on_equity, 0.15),  # ROEが15%以上なら高収益性
        (net_margin, 0.20),        # 純利益率が20%以上なら健全
        (operating_margin, 0.15)   # 営業利益率が15%以上なら効率的
    ]
    profitability_score = sum(
        metric is not None and metric > threshold
        for metric, threshold in thresholds
    )

    signals.append('bullish' if profitability_score >= 2 else 'bearish' if profitability_score == 0 else 'neutral')
    reasoning["profitability_signal"] = {
        "signal": signals[0],
        "details": (
            f"ROE: {metrics.get('return_on_equity', 0):.2%}" if metrics.get("return_on_equity") is not None else "ROE: 該当なし"
        ) + ", " + (
            f"純利益率: {metrics.get('net_margin', 0):.2%}" if metrics.get("net_margin") is not None else "純利益率: 該当なし"
        ) + ", " + (
            f"営業利益率: {metrics.get('operating_margin', 0):.2%}" if metrics.get("operating_margin") is not None else "営業利益率: 該当なし"
        )
    }

    # 2. 成長性の分析
    revenue_growth = metrics.get("revenue_growth", 0)
    earnings_growth = metrics.get("earnings_growth", 0)
    book_value_growth = metrics.get("book_value_growth", 0)

    thresholds = [
        (revenue_growth, 0.10),      # 売上高成長率10%以上
        (earnings_growth, 0.10),     # 利益成長率10%以上
        (book_value_growth, 0.10)    # 純資産成長率10%以上
    ]
    growth_score = sum(
        metric is not None and metric > threshold
        for metric, threshold in thresholds
    )

    signals.append('bullish' if growth_score >= 2 else 'bearish' if growth_score == 0 else 'neutral')
    reasoning["growth_signal"] = {
        "signal": signals[1],
        "details": (
            f"売上成長率: {metrics.get('revenue_growth', 0):.2%}" if metrics.get("revenue_growth") is not None else "売上成長率: 該当なし"
        ) + ", " + (
            f"利益成長率: {metrics.get('earnings_growth', 0):.2%}" if metrics.get("earnings_growth") is not None else "利益成長率: 該当なし"
        )
    }

    # 3. 財務健全性
    current_ratio = metrics.get("current_ratio", 0)
    debt_to_equity = metrics.get("debt_to_equity", 0)
    free_cash_flow_per_share = metrics.get("free_cash_flow_per_share", 0)
    earnings_per_share = metrics.get("earnings_per_share", 0)

    health_score = 0
    if current_ratio and current_ratio > 1.5:  # 流動比率が高い = 健全
        health_score += 1
    if debt_to_equity and debt_to_equity < 0.5:  # 負債比率が低い = 安全
        health_score += 1
    if (free_cash_flow_per_share and earnings_per_share and
            free_cash_flow_per_share > earnings_per_share * 0.8):  # FCFがEPSの80%以上 = 資金繰り良好
        health_score += 1

    signals.append('bullish' if health_score >= 2 else 'bearish' if health_score == 0 else 'neutral')
    reasoning["financial_health_signal"] = {
        "signal": signals[2],
        "details": (
            f"流動比率: {metrics.get('current_ratio', 0):.2f}" if metrics.get("current_ratio") is not None else "流動比率: 該当なし"
        ) + ", " + (
            f"D/E比率: {metrics.get('debt_to_equity', 0):.2f}" if metrics.get("debt_to_equity") is not None else "D/E比率: 該当なし"
        )
    }

    # 4. 株価指標（PER, PBR, PSR）
    pe_ratio = metrics.get("pe_ratio", 0)
    price_to_book = metrics.get("price_to_book", 0)
    price_to_sales = metrics.get("price_to_sales", 0)

    thresholds = [
        (pe_ratio, 25),           # 妥当なPER
        (price_to_book, 3),       # 妥当なPBR
        (price_to_sales, 5)       # 妥当なPSR
    ]
    price_ratio_score = sum(
        metric is not None and metric < threshold
        for metric, threshold in thresholds
    )

    signals.append('bullish' if price_ratio_score >= 2 else 'bearish' if price_ratio_score == 0 else 'neutral')
    reasoning["price_ratios_signal"] = {
        "signal": signals[3],
        "details": (
            f"PER: {pe_ratio:.2f}" if pe_ratio else "PER: 該当なし"
        ) + ", " + (
            f"PBR: {price_to_book:.2f}" if price_to_book else "PBR: 該当なし"
        ) + ", " + (
            f"PSR: {price_to_sales:.2f}" if price_to_sales else "PSR: 該当なし"
        )
    }

    # 全体シグナルの決定
    bullish_signals = signals.count('bullish')
    bearish_signals = signals.count('bearish')

    if bullish_signals > bearish_signals:
        overall_signal = 'bullish'
    elif bearish_signals > bullish_signals:
        overall_signal = 'bearish'
    else:
        overall_signal = 'neutral'

    # 信頼度の計算（bull/bearの多い方の割合）
    total_signals = len(signals)
    confidence = max(bullish_signals, bearish_signals) / total_signals

    message_content = {
        "signal": overall_signal,
        "confidence": f"{round(confidence * 100)}%",
        "reasoning": reasoning
    }

    # ファンダメンタル分析メッセージを作成
    message = HumanMessage(
        content=json.dumps(message_content),
        name="fundamentals_agent",
    )

    # フラグが立っていれば、推論内容を表示
    if show_reasoning:
        show_agent_reasoning(message_content, "ファンダメンタル分析エージェント")
        # 推論をメタデータに保存（API向け）
        state["metadata"]["agent_reasoning"] = message_content

    show_workflow_status("ファンダメンタル分析", "完了")
    return {
        "messages": [message],
        "data": {
            **data,
            "fundamental_analysis": message_content
        },
        "metadata": state["metadata"],
    }
