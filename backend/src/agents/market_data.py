from langchain_core.messages import HumanMessage
from ..tools.openrouter_config import get_chat_completion
from .state import AgentState, show_agent_reasoning, show_workflow_status
from ..tools.api import (
    get_financial_metrics, get_financial_statements, get_market_data, get_price_history,
    get_short_selling_data, get_investment_sector_data, get_sp500_data, get_credit_balance_data
)
from ..utils.logging_config import setup_logger
from ..utils.api_utils import agent_endpoint, log_llm_interaction

from datetime import datetime, timedelta
import pandas as pd

# ロガーを初期化
logger = setup_logger('market_data_agent')


@agent_endpoint("market_data", "市場データ収集エージェント：株価履歴、財務指標、市場情報を取得・前処理する役割を担う")
def market_data_agent(state: AgentState):
    """市場データの収集と前処理を担当する"""
    show_workflow_status("市場データエージェント")
    show_reasoning = state["metadata"]["show_reasoning"]

    messages = state["messages"]
    data = state["data"]

    # デフォルトの日付を設定
    current_date = datetime.now()
    yesterday = current_date - timedelta(days=1)
    end_date = data["end_date"] or yesterday.strftime('%Y-%m-%d')

    # 終了日が未来にならないように調整
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    if end_date_obj > yesterday:
        end_date = yesterday.strftime('%Y-%m-%d')
        end_date_obj = yesterday

    if not data["start_date"]:
        # 終了日の1年前をデフォルト開始日にする
        start_date = end_date_obj - timedelta(days=365)
        start_date = start_date.strftime('%Y-%m-%d')
    else:
        start_date = data["start_date"]

    # ティッカーを取得
    ticker = data["ticker"]

    # 株価データを取得し、検証
    prices_df = get_price_history(ticker, start_date, end_date)
    if prices_df is None or prices_df.empty:
        logger.warning(f"警告：{ticker} の株価データが取得できませんでした。空データで継続します。")
        prices_df = pd.DataFrame(
            columns=['close', 'open', 'high', 'low', 'volume'])

    # 財務指標を取得
    try:
        financial_metrics = get_financial_metrics(ticker)
    except Exception as e:
        logger.error(f"財務指標の取得に失敗しました: {str(e)}")
        financial_metrics = {}

    # 財務諸表を取得
    try:
        financial_line_items = get_financial_statements(ticker)
    except Exception as e:
        logger.error(f"財務諸表の取得に失敗しました: {str(e)}")
        financial_line_items = {}

    # 市場データを取得
    try:
        market_data = get_market_data(ticker)
    except Exception as e:
        logger.error(f"市場データの取得に失敗しました: {str(e)}")
        market_data = {"market_cap": 0}

    # yfinance専用データを取得
    logger.info("yfinance専用データを取得しています...")
    
    # 空売り情報を取得
    try:
        short_selling_data = get_short_selling_data(ticker)
    except Exception as e:
        logger.error(f"空売り情報の取得に失敗しました: {str(e)}")
        short_selling_data = {}
    
    # 投資部門別情報を取得
    try:
        investment_sector_data = get_investment_sector_data(ticker)
    except Exception as e:
        logger.error(f"投資部門別情報の取得に失敗しました: {str(e)}")
        investment_sector_data = {}
    
    # S&P 500指数を取得（市場全体のトレンド把握）
    try:
        sp500_data = get_sp500_data()
    except Exception as e:
        logger.error(f"S&P 500データの取得に失敗しました: {str(e)}")
        sp500_data = {}
    
    # 信用取引残高を取得
    try:
        credit_balance_data = get_credit_balance_data(ticker)
    except Exception as e:
        logger.error(f"信用取引残高の取得に失敗しました: {str(e)}")
        credit_balance_data = {}

    # データ形式の検証
    if not isinstance(prices_df, pd.DataFrame):
        prices_df = pd.DataFrame(
            columns=['close', 'open', 'high', 'low', 'volume'])

    # 株価データを辞書形式に変換
    prices_dict = prices_df.to_dict('records')

    # 推論情報を metadata に保存（API用）
    market_data_summary = {
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "data_collected": {
            "price_history": len(prices_dict) > 0,
            "financial_metrics": len(financial_metrics) > 0,
            "financial_statements": len(financial_line_items) > 0,
            "market_data": len(market_data) > 0,
            "short_selling": len(short_selling_data) > 0,
            "investment_sector": len(investment_sector_data) > 0,
            "sp500_data": len(sp500_data) > 0,
            "credit_balance": len(credit_balance_data) > 0
        },
        "summary": f"{ticker} の包括的市場データを {start_date} から {end_date} まで収集しました。株価履歴、財務指標、空売り情報、投資部門別データ、S&P 500、信用取引残高を含みます（yfinance使用）。"
    }

    if show_reasoning:
        show_agent_reasoning(market_data_summary, "市場データエージェント")
        state["metadata"]["agent_reasoning"] = market_data_summary

    return {
        "messages": messages,
        "data": {
            **data,
            "prices": prices_dict,
            "start_date": start_date,
            "end_date": end_date,
            "financial_metrics": financial_metrics,
            "financial_line_items": financial_line_items,
            "market_cap": market_data.get("market_cap", 0),
            "market_data": market_data,
            # yfinance専用データ
            "short_selling_data": short_selling_data,
            "investment_sector_data": investment_sector_data,
            "sp500_data": sp500_data,
            "credit_balance_data": credit_balance_data,
        },
        "metadata": state["metadata"],
    }
