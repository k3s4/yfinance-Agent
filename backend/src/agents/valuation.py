from langchain_core.messages import HumanMessage
from ..utils.logging_config import setup_logger
from .state import AgentState, show_agent_reasoning, show_workflow_status
from ..utils.api_utils import agent_endpoint, log_llm_interaction
import json

# ロガーを初期化
logger = setup_logger('valuation_agent')


@agent_endpoint("valuation", "バリュエーション分析担当：DCF法とオーナー利益法を用いて企業の内在価値を評価する")
def valuation_agent(state: AgentState):
    """バリュエーション（企業価値評価）を担当する"""
    show_workflow_status("バリュエーション・エージェント")
    show_reasoning = state["metadata"]["show_reasoning"]
    data = state["data"]
    
    # 財務データの安全な取得
    financial_metrics_list = data.get("financial_metrics", [])
    financial_line_items = data.get("financial_line_items", [{}, {}])
    
    if not financial_metrics_list:
        logger.warning("財務指標データが取得できませんでした。デフォルト値を使用します。")
        metrics = {}
    else:
        metrics = financial_metrics_list[0] if len(financial_metrics_list) > 0 else {}
    
    current_financial_line_item = financial_line_items[0] if len(financial_line_items) > 0 else {}
    previous_financial_line_item = financial_line_items[1] if len(financial_line_items) > 1 else {}
    market_cap = data.get("market_cap", 0)

    reasoning = {}

    # 運転資本の変化を計算
    working_capital_change = (current_financial_line_item.get(
        'working_capital') or 0) - (previous_financial_line_item.get('working_capital') or 0)

    # オーナー利益法によるバリュエーション（バフェット流）
    owner_earnings_value = calculate_owner_earnings_value(
        net_income=current_financial_line_item.get('net_income'),
        depreciation=current_financial_line_item.get('depreciation_and_amortization'),
        capex=current_financial_line_item.get('capital_expenditure'),
        working_capital_change=working_capital_change,
        growth_rate=metrics["earnings_growth"],
        required_return=0.15,
        margin_of_safety=0.25
    )

    # DCF法によるバリュエーション
    dcf_value = calculate_intrinsic_value(
        free_cash_flow=current_financial_line_item.get('free_cash_flow'),
        growth_rate=metrics["earnings_growth"],
        discount_rate=0.10,
        terminal_growth_rate=0.03,
        num_years=5,
    )

    # 両者の平均でバリュエーションギャップを算出
    dcf_gap = (dcf_value - market_cap) / market_cap
    owner_earnings_gap = (owner_earnings_value - market_cap) / market_cap
    valuation_gap = (dcf_gap + owner_earnings_gap) / 2

    if valuation_gap > 0.10:
        signal = 'bullish'
    elif valuation_gap < -0.20:
        signal = 'bearish'
    else:
        signal = 'neutral'

    reasoning["dcf_analysis"] = {
        "signal": "bullish" if dcf_gap > 0.10 else "bearish" if dcf_gap < -0.20 else "neutral",
        "details": f"内在価値: ¥{dcf_value:,.2f}, 時価総額: ¥{market_cap:,.2f}, ギャップ: {dcf_gap:.1%}"
    }

    reasoning["owner_earnings_analysis"] = {
        "signal": "bullish" if owner_earnings_gap > 0.10 else "bearish" if owner_earnings_gap < -0.20 else "neutral",
        "details": f"オーナー利益による価値: ¥{owner_earnings_value:,.2f}, 時価総額: ¥{market_cap:,.2f}, ギャップ: {owner_earnings_gap:.1%}"
    }

    message_content = {
        "signal": signal,
        "confidence": f"{abs(valuation_gap):.0%}",
        "reasoning": reasoning
    }

    message = HumanMessage(
        content=json.dumps(message_content),
        name="valuation_agent",
    )

    if show_reasoning:
        show_agent_reasoning(message_content, "バリュエーション分析エージェント")
        state["metadata"]["agent_reasoning"] = message_content

    show_workflow_status("バリュエーション・エージェント", "completed")

    return {
        "messages": [message],
        "data": {
            **data,
            "valuation_analysis": message_content
        },
        "metadata": state["metadata"],
    }


def calculate_owner_earnings_value(
    net_income: float,
    depreciation: float,
    capex: float,
    working_capital_change: float,
    growth_rate: float = 0.05,
    required_return: float = 0.15,
    margin_of_safety: float = 0.25,
    num_years: int = 5
) -> float:
    """
    改良型オーナー利益法によって企業価値を算出する

    引数:
        net_income: 純利益
        depreciation: 減価償却費
        capex: 設備投資
        working_capital_change: 運転資本の変化
        growth_rate: 成長率の予測
        required_return: 必要な期待利回り
        margin_of_safety: 安全率
        num_years: 予測年数

    戻り値:
        float: 計算された企業価値
    """
    try:
        if not all(isinstance(x, (int, float)) for x in [net_income, depreciation, capex, working_capital_change]):
            return 0

        # 初年度オーナー利益を計算
        owner_earnings = net_income + depreciation - capex - working_capital_change

        if owner_earnings <= 0:
            return 0

        growth_rate = min(max(growth_rate, 0), 0.25)

        # 各年の予測値の現在価値
        future_values = []
        for year in range(1, num_years + 1):
            year_growth = growth_rate * (1 - year / (2 * num_years))
            future_value = owner_earnings * (1 + year_growth) ** year
            discounted_value = future_value / (1 + required_return) ** year
            future_values.append(discounted_value)

        # 永続価値の計算
        terminal_growth = min(growth_rate * 0.4, 0.03)
        terminal_value = future_values[-1] * (1 + terminal_growth) / (required_return - terminal_growth)
        terminal_value_discounted = terminal_value / (1 + required_return) ** num_years

        intrinsic_value = sum(future_values) + terminal_value_discounted
        value_with_safety_margin = intrinsic_value * (1 - margin_of_safety)

        return max(value_with_safety_margin, 0)

    except Exception as e:
        print(f"オーナー利益の計算中にエラー: {e}")
        return 0


def calculate_intrinsic_value(
    free_cash_flow: float,
    growth_rate: float = 0.05,
    discount_rate: float = 0.10,
    terminal_growth_rate: float = 0.02,
    num_years: int = 5,
) -> float:
    """
    改良型DCF（割引キャッシュフロー）法によって内在価値を算出する

    引数:
        free_cash_flow: 自由現金流
        growth_rate: 予測成長率
        discount_rate: 割引率
        terminal_growth_rate: 永続成長率
        num_years: 予測年数

    戻り値:
        float: 内在価値
    """
    try:
        if not isinstance(free_cash_flow, (int, float)) or free_cash_flow <= 0:
            return 0

        growth_rate = min(max(growth_rate, 0), 0.25)
        terminal_growth_rate = min(growth_rate * 0.4, 0.03)

        present_values = []
        for year in range(1, num_years + 1):
            future_cf = free_cash_flow * (1 + growth_rate) ** year
            present_value = future_cf / (1 + discount_rate) ** year
            present_values.append(present_value)

        terminal_year_cf = free_cash_flow * (1 + growth_rate) ** num_years
        terminal_value = terminal_year_cf * (1 + terminal_growth_rate) / (discount_rate - terminal_growth_rate)
        terminal_present_value = terminal_value / (1 + discount_rate) ** num_years

        total_value = sum(present_values) + terminal_present_value

        return max(total_value, 0)

    except Exception as e:
        print(f"DCFの計算中にエラー: {e}")
        return 0


