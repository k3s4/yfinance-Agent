from typing import Dict, Any, List
import pandas as pd
from datetime import datetime, timedelta
import json
import numpy as np
import os
from dotenv import load_dotenv
import yfinance as yf
from src.utils.logging_config import setup_logger

# 環境変数を読み込み
load_dotenv()

# ログ記録を設定
logger = setup_logger('api')

# yfinanceクライアントは関数内で使用

def safe_float(value, default=0.0):
    """安全に数値に変換する"""
    try:
        if pd.isna(value) or value is None:
            return default
        return float(value)
    except:
        return default


def calculate_growth_rate(financial_statements: pd.DataFrame, column_name: str) -> float:
    """財務データから成長率を計算する"""
    try:
        if financial_statements.empty or len(financial_statements) < 2:
            return 0.0
        
        # 日付でソートして最新と過去の値を取得
        sorted_data = financial_statements.sort_values('date', ascending=True)
        
        if column_name not in sorted_data.columns:
            return 0.0
        
        # 最新値と1年前の値を取得
        current_value = safe_float(sorted_data.iloc[-1].get(column_name, 0))
        previous_value = safe_float(sorted_data.iloc[0].get(column_name, 0))
        
        if previous_value == 0:
            return 0.0
        
        # 成長率を計算（年率）
        growth_rate = (current_value - previous_value) / previous_value
        return growth_rate
        
    except Exception as e:
        logger.warning(f"成長率計算エラー ({column_name}): {e}")
        return 0.0


def get_financial_metrics(symbol: str) -> Dict[str, Any]:
    """yfinanceを使用して財務指標データを取得する"""
    logger.info(f"{symbol}の財務指標を取得しています...")
    
    try:
        # yfinanceでティッカーオブジェクトを作成
        ticker = yf.Ticker(symbol)
        
        # 財務データを取得
        info = ticker.info
        
        # 現在価格を取得
        current_price = safe_float(info.get('currentPrice', 0))
        if current_price == 0:
            current_price = safe_float(info.get('regularMarketPrice', 0))
        
        logger.info("✓ 最新の株価データを取得しました")

        # 財務諸表データを取得
        try:
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet
            cashflow = ticker.cashflow
            quarterly_financials = ticker.quarterly_financials
            
            if not financials.empty:
                logger.info("✓ 財務諸表データを取得しました")
            else:
                logger.warning("財務諸表データが見つかりません")
                financials = pd.DataFrame()
                
        except Exception as e:
            logger.warning(f"財務データ取得エラー: {e}")
            financials = pd.DataFrame()
            balance_sheet = pd.DataFrame()
            cashflow = pd.DataFrame()

        # 指標を構築
        logger.info("指標を構築しています...")
        try:
            def safe_ratio(numerator, denominator, default=0.0):
                """安全に比率を計算する"""
                try:
                    num = safe_float(numerator)
                    den = safe_float(denominator)
                    if den == 0:
                        return default
                    return num / den
                except:
                    return default

            # yfinance infoから財務指標を取得
            market_cap = safe_float(info.get('marketCap', 0))
            enterprise_value = safe_float(info.get('enterpriseValue', 0))
            total_revenue = safe_float(info.get('totalRevenue', 0))
            net_income = safe_float(info.get('netIncomeToCommon', 0))
            total_debt = safe_float(info.get('totalDebt', 0))
            total_cash = safe_float(info.get('totalCash', 0))
            book_value = safe_float(info.get('bookValue', 0))
            shares_outstanding = safe_float(info.get('sharesOutstanding', 0))
            
            # EPSとその他の指標
            eps = safe_float(info.get('trailingEps', 0))
            forward_eps = safe_float(info.get('forwardEps', 0))
            
            # 財務健全性指標
            current_ratio = safe_float(info.get('currentRatio', 1.0))
            debt_to_equity = safe_float(info.get('debtToEquity', 0)) / 100 if info.get('debtToEquity') else 0
            
            # 収益性指標
            return_on_equity = safe_float(info.get('returnOnEquity', 0))
            return_on_assets = safe_float(info.get('returnOnAssets', 0))
            profit_margins = safe_float(info.get('profitMargins', 0))
            operating_margins = safe_float(info.get('operatingMargins', 0))
            
            # 成長率指標
            revenue_growth = safe_float(info.get('revenueGrowth', 0))
            earnings_growth = safe_float(info.get('earningsGrowth', 0))
            
            # フリーキャッシュフロー
            free_cash_flow = safe_float(info.get('freeCashflow', 0))
            operating_cash_flow = safe_float(info.get('operatingCashflow', 0))
            
            agent_metrics = {
                # 収益性指標
                "return_on_equity": return_on_equity,
                "net_margin": profit_margins,
                "operating_margin": operating_margins,

                # 成長指標
                "revenue_growth": revenue_growth,
                "earnings_growth": earnings_growth,
                "book_value_growth": 0.0,  # yfinanceから直接取得できないため0に設定

                # 財務健全性指標
                "current_ratio": current_ratio,
                "debt_to_equity": debt_to_equity,
                "free_cash_flow_per_share": safe_ratio(free_cash_flow, shares_outstanding),
                "earnings_per_share": eps,

                # 評価比率
                "pe_ratio": safe_float(info.get('trailingPE', 0)),
                "price_to_book": safe_float(info.get('priceToBook', 0)),
                "price_to_sales": safe_float(info.get('priceToSalesTrailing12Months', 0)),
            }

            logger.info("✓ 指標の構築に成功しました")

            # デバッグ情報を出力
            logger.debug("\nエージェントに渡す指標データ：")
            for key, value in agent_metrics.items():
                logger.debug(f"{key}: {value}")

            return [agent_metrics]

        except Exception as e:
            logger.error(f"指標の構築エラー: {e}")
            return [{}]

    except Exception as e:
        logger.error(f"財務指標の取得エラー: {e}")
        return [{}]


def get_financial_statements(symbol: str) -> Dict[str, Any]:
    """yfinanceを使用して財務諸表データを取得する"""
    logger.info(f"{symbol}の財務諸表を取得しています...")
    
    try:
        # yfinanceでティッカーオブジェクトを作成
        ticker = yf.Ticker(symbol)
        
        # 財務諸表データを取得
        financials = ticker.financials
        cashflow = ticker.cashflow
        
        if financials.empty:
            logger.warning("財務諸表データが見つかりません")
            default_item = {
                "net_income": 0,
                "operating_revenue": 0,
                "operating_profit": 0,
                "working_capital": 0,
                "depreciation_and_amortization": 0,
                "capital_expenditure": 0,
                "free_cash_flow": 0
            }
            return [default_item, default_item]

        def safe_float(value, default=0.0):
            """安全に数値に変換する"""
            try:
                if pd.isna(value) or value is None:
                    return default
                return float(value)
            except:
                return default

        line_items = []
        
        # 利用可能なデータから最大2つの期間を処理
        num_periods = min(2, len(financials.columns))
        
        for i in range(num_periods):
            period_data = financials.iloc[:, i]
            cashflow_data = cashflow.iloc[:, i] if not cashflow.empty and i < len(cashflow.columns) else pd.Series()
            
            # 財務データを構築
            net_income = safe_float(period_data.get("Net Income", 0))
            total_revenue = safe_float(period_data.get("Total Revenue", 0))
            operating_income = safe_float(period_data.get("Operating Income", 0))
            
            # キャッシュフローデータ
            operating_cash_flow = safe_float(cashflow_data.get("Operating Cash Flow", 0))
            capital_expenditure = safe_float(cashflow_data.get("Capital Expenditure", 0))
            free_cash_flow = operating_cash_flow + capital_expenditure  # CapExは通常負の値
            
            item = {
                "net_income": net_income,
                "operating_revenue": total_revenue,
                "operating_profit": operating_income,
                "working_capital": 0,  # yfinanceから直接計算が困難
                "depreciation_and_amortization": safe_float(cashflow_data.get("Depreciation", 0)),
                "capital_expenditure": abs(capital_expenditure),  # 正の値に変換
                "free_cash_flow": free_cash_flow
            }
            line_items.append(item)
            
        # 少なくとも2つの期間を返すために、不足分をコピー
        if len(line_items) == 1:
            line_items.append(line_items[0].copy())
        elif len(line_items) == 0:
            default_item = {
                "net_income": 0,
                "operating_revenue": 0,
                "operating_profit": 0,
                "working_capital": 0,
                "depreciation_and_amortization": 0,
                "capital_expenditure": 0,
                "free_cash_flow": 0
            }
            line_items = [default_item, default_item]

        logger.info("✓ 財務諸表データの処理に成功しました")
        return line_items

    except Exception as e:
        logger.error(f"財務諸表の取得エラー: {e}")
        default_item = {
            "net_income": 0,
            "operating_revenue": 0,
            "operating_profit": 0,
            "working_capital": 0,
            "depreciation_and_amortization": 0,
            "capital_expenditure": 0,
            "free_cash_flow": 0
        }
        return [default_item, default_item]


def get_market_data(symbol: str) -> Dict[str, Any]:
    """yfinanceを使用して市場データを取得する"""
    logger.info(f"{symbol}の市場データを取得しています...")
    
    try:
        # yfinanceでティッカーオブジェクトを作成
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 直近の価格データを取得（過去30日）
        hist = ticker.history(period="1mo")
        
        if hist.empty:
            logger.warning(f"{symbol}の価格データが見つかりません")
            return {}
        
        # 52週間のデータを取得
        hist_52w = ticker.history(period="52wk")
        
        if hist_52w.empty:
            hist_52w = hist  # フォールバック
            
        def safe_float(value, default=0.0):
            """安全に数値に変換する"""
            try:
                if pd.isna(value) or value is None:
                    return default
                return float(value)
            except:
                return default
        
        # 市場データを構築
        current_price = safe_float(hist['Close'].iloc[-1])
        volume = safe_float(hist['Volume'].iloc[-1])
        
        # 52週間の高値・安値を計算
        high_52w = safe_float(hist_52w['High'].max())
        low_52w = safe_float(hist_52w['Low'].min())
        
        # 平均出来高を計算（過去20営業日）
        average_volume = safe_float(hist['Volume'].tail(20).mean())
        
        # 時価総額を取得
        market_cap = safe_float(info.get('marketCap', 0))
        
        market_data = {
            "market_cap": market_cap,
            "volume": volume,
            "average_volume": average_volume,
            "fifty_two_week_high": high_52w,
            "fifty_two_week_low": low_52w
        }
        
        logger.info("✓ 市場データの取得に成功しました")
        return market_data

    except Exception as e:
        logger.error(f"市場データの取得エラー: {e}")
        return {}


def get_price_history(symbol: str, start_date: str = None, end_date: str = None, adjust: str = "qfq") -> pd.DataFrame:
    """yfinanceを使用して過去の価格データを取得する

    Args:
        symbol: ティッカーシンボル
        start_date: 開始日、フォーマット：YYYY-MM-DD、Noneの場合は過去1年間のデータを取得
        end_date: 終了日、フォーマット：YYYY-MM-DD、Noneの場合は昨日を終了日として使用
        adjust: 権利調整の種類（yfinanceでは自動的に調整済みデータを提供）

    Returns:
        以下の列を含むDataFrame：
        - date: 日付
        - open: 始値
        - high: 高値
        - low: 安値
        - close: 終値
        - volume: 出来高（株数）
        - amount: 売買代金（円）
        - amplitude: 振幅（%）
        - pct_change: 騰落率（%）
        - change_amount: 騰落額（円）
        - turnover: 回転率（%）

        テクニカル指標：
        - momentum_1m: 1ヶ月モメンタム
        - momentum_3m: 3ヶ月モメンタム
        - momentum_6m: 6ヶ月モメンタム
        - volume_momentum: 出来高モメンタム
        - historical_volatility: ヒストリカルボラティリティ
        - volatility_regime: ボラティリティ区間
        - volatility_z_score: ボラティリティZスコア
        - atr_ratio: ATR比率
        - hurst_exponent: ハースト指数
        - skewness: 歪度
        - kurtosis: 尖度
    """
    logger.info(f"{symbol}の価格履歴を取得しています...")
    
    try:
        # yfinanceでティッカーオブジェクトを作成
        ticker = yf.Ticker(symbol)
        
        # 現在の日付と昨日の日付を取得
        current_date = datetime.now()
        yesterday = current_date - timedelta(days=1)

        # 日付が提供されていない場合、デフォルトで昨日を終了日として使用
        if not end_date:
            end_date = yesterday
        else:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            if end_date > yesterday:
                end_date = yesterday

        if not start_date:
            start_date = end_date - timedelta(days=365)  # デフォルトで1年分のデータを取得
        else:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")

        logger.info(f"開始日: {start_date.strftime('%Y-%m-%d')}")
        logger.info(f"終了日: {end_date.strftime('%Y-%m-%d')}")

        def get_and_process_data(start_date, end_date):
            """yfinanceからデータを取得し、処理を行う"""
            hist = ticker.history(start=start_date, end=end_date)

            if hist.empty:
                return pd.DataFrame()

            # 列名を標準化
            df = hist.copy()
            df = df.reset_index()
            
            # 列名を標準的な名前にマッピング
            df = df.rename(columns={
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume"
            })

            # 日付列をdatetime型に変換
            df["date"] = pd.to_datetime(df["date"])
            
            # 売買代金を推定（価格 × 出来高）
            df["amount"] = df["close"] * df["volume"]
            
            # 基本的な計算指標を追加
            df["pct_change"] = df["close"].pct_change() * 100  # パーセント変化
            df["change_amount"] = df["close"].diff()  # 騰落額
            df["amplitude"] = ((df["high"] - df["low"]) / df["close"].shift(1)) * 100  # 振幅
            df["turnover"] = 0.0  # yfinanceから直接取得できないため0に設定

            return df

        # 過去の相場データを取得
        df = get_and_process_data(start_date, end_date)

        if df is None or df.empty:
            logger.warning(f"警告: {symbol}の価格履歴データが見つかりません")
            return pd.DataFrame()

        # データ量が十分か確認
        min_required_days = 120  # 少なくとも120営業日のデータが必要
        if len(df) < min_required_days:
            logger.warning(f"警告: 全てのテクニカル指標を計算するにはデータが不十分です（{len(df)}日分）")
            logger.info("より多くのデータを取得しようと試みます...")

            # 期間を2年間に拡大
            start_date = end_date - timedelta(days=730)
            df = get_and_process_data(start_date, end_date)

            if len(df) < min_required_days:
                logger.warning(f"警告: 期間を拡大してもデータが不十分です（{len(df)}日分）")

        # 数値型の列を確実に変換
        numeric_columns = ["open", "high", "low", "close", "volume", "amount"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # モメンタム指標を計算
        df["momentum_1m"] = df["close"].pct_change(periods=20)  # 20営業日は約1ヶ月
        df["momentum_3m"] = df["close"].pct_change(periods=60)  # 60営業日は約3ヶ月
        df["momentum_6m"] = df["close"].pct_change(periods=120)  # 120営業日は約6ヶ月

        # 出来高モメンタムを計算（20日移動平均出来高に対する変化）
        df["volume_ma20"] = df["volume"].rolling(window=20).mean()
        df["volume_momentum"] = df["volume"] / df["volume_ma20"]

        # ボラティリティ指標を計算
        # 1. ヒストリカルボラティリティ (20日)
        returns = df["close"].pct_change()
        df["historical_volatility"] = returns.rolling(window=20).std() * np.sqrt(252)  # 年率換算

        # 2. ボラティリティ区間 (過去120日間のボラティリティにおける位置)
        volatility_120d = returns.rolling(window=120).std() * np.sqrt(252)
        vol_min = volatility_120d.rolling(window=120).min()
        vol_max = volatility_120d.rolling(window=120).max()
        vol_range = vol_max - vol_min
        df["volatility_regime"] = np.where(
            vol_range > 0,
            (df["historical_volatility"] - vol_min) / vol_range,
            0  # 範囲が0の場合は0を返す
        )

        # 3. ボラティリティZスコア
        vol_mean = df["historical_volatility"].rolling(window=120).mean()
        vol_std = df["historical_volatility"].rolling(window=120).std()
        df["volatility_z_score"] = (df["historical_volatility"] - vol_mean) / vol_std

        # 4. ATR比率
        tr = pd.DataFrame()
        tr["h-l"] = df["high"] - df["low"]
        tr["h-pc"] = abs(df["high"] - df["close"].shift(1))
        tr["l-pc"] = abs(df["low"] - df["close"].shift(1))
        tr["tr"] = tr[["h-l", "h-pc", "l-pc"]].max(axis=1)
        df["atr"] = tr["tr"].rolling(window=14).mean()
        df["atr_ratio"] = df["atr"] / df["close"]

        # 統計的裁定指標を計算
        # 1. ハースト指数 (過去120日のデータを使用)
        def calculate_hurst(series):
            """ハースト指数を計算する"""
            try:
                series = series.dropna()
                if len(series) < 30:
                    return np.nan

                # 対数収益率を使用
                log_returns = np.log(series / series.shift(1)).dropna()
                if len(log_returns) < 30:
                    return np.nan

                # lag範囲を2-10日に設定
                lags = range(2, min(11, len(log_returns) // 4))

                # 各lagの標準偏差を計算
                tau = []
                for lag in lags:
                    std = log_returns.rolling(window=lag).std().dropna()
                    if len(std) > 0:
                        tau.append(np.mean(std))

                if len(tau) < 3:
                    return np.nan

                # 対数回帰を使用
                lags_log = np.log(list(lags))
                tau_log = np.log(tau)

                # 回帰係数を計算
                reg = np.polyfit(lags_log, tau_log, 1)
                hurst = reg[0] / 2.0

                if np.isnan(hurst) or np.isinf(hurst):
                    return np.nan

                return hurst

            except Exception as e:
                return np.nan

        # 対数収益率を使用してハースト指数を計算
        log_returns = np.log(df["close"] / df["close"].shift(1))
        df["hurst_exponent"] = log_returns.rolling(
            window=120,
            min_periods=60
        ).apply(calculate_hurst)

        # 2. 歪度 (20日)
        df["skewness"] = returns.rolling(window=20).skew()

        # 3. 尖度 (20日)
        df["kurtosis"] = returns.rolling(window=20).kurt()

        # 日付で昇順にソート
        df = df.sort_values("date")

        # インデックスをリセット
        df = df.reset_index(drop=True)

        logger.info(f"価格履歴データの取得に成功しました（{len(df)}件）")

        # NaN値を確認し報告（momentum指標のNaN値は正常）
        nan_columns = df.isna().sum()
        if nan_columns.any():
            logger.info("\n情報: 以下の指標にNaN値が含まれています（momentum指標の初期期間は正常な動作）:")
            for col, nan_count in nan_columns[nan_columns > 0].items():
                if col.startswith('momentum_') or col in ['volume_ma20', 'historical_volatility', 'hurst_exponent']:
                    logger.info(f"- {col}: {nan_count} 件 (計算期間不足による正常なNaN)")
                else:
                    logger.warning(f"- {col}: {nan_count} 件 (要確認)")

        return df

    except Exception as e:
        logger.error(f"価格履歴の取得エラー: {e}")
        return pd.DataFrame()


def prices_to_df(prices):
    """yfinance価格データを標準化された列名のDataFrameに変換する"""
    try:
        df = pd.DataFrame(prices)

        # yfinance用の列名マッピング
        column_mapping = {
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }

        # 列名を変更
        for yf_col, std_col in column_mapping.items():
            if yf_col in df.columns:
                df[std_col] = df[yf_col]

        # 必要な列が存在することを確認
        required_columns = ['close', 'open', 'high', 'low', 'volume']
        for col in required_columns:
            if col not in df.columns:
                df[col] = 0.0  # 不足している必要な列を0で埋める

        # 売買代金を推定
        if 'amount' not in df.columns and 'close' in df.columns and 'volume' in df.columns:
            df['amount'] = df['close'] * df['volume']

        return df
    except Exception as e:
        logger.error(f"価格データの変換エラー: {str(e)}")
        # 必要な列を含む空のDataFrameを返す
        return pd.DataFrame(columns=['close', 'open', 'high', 'low', 'volume', 'amount'])


def get_short_selling_data(symbol: str) -> Dict[str, Any]:
    """空売り情報を取得する（yfinanceでは限定的な情報のみ）"""
    logger.info(f"{symbol}の空売り情報を取得しています...")
    
    try:
        # yfinanceでティッカーオブジェクトを作成
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # yfinanceから取得可能な限定的な空売り関連データ
        shares_short = safe_float(info.get('sharesShort', 0))
        shares_outstanding = safe_float(info.get('sharesOutstanding', 1))
        short_ratio = safe_float(info.get('shortRatio', 0))
        short_percent_of_float = safe_float(info.get('shortPercentOfFloat', 0))
        
        # 空売り比率を計算
        short_percent = (shares_short / shares_outstanding) if shares_outstanding > 0 else 0
        
        # データを構造化
        short_data = {
            "short_balance": shares_short,
            "short_ratio": short_percent,
            "sector_short_ratio": 0.0,  # yfinanceから取得不可
            "short_trend": "neutral",
            "market_sentiment": "neutral"
        }
        
        # 空売り比率から市場センチメントを判定
        if short_percent > 0.1:  # 10%以上
            short_data["market_sentiment"] = "bearish"
            short_data["short_trend"] = "high"
        elif short_percent > 0.05:  # 5-10%
            short_data["market_sentiment"] = "neutral"
            short_data["short_trend"] = "moderate"
        else:  # 5%未満
            short_data["market_sentiment"] = "bullish"
            short_data["short_trend"] = "low"
        
        logger.info("✓ 空売り情報を取得しました")
        return short_data
        
    except Exception as e:
        logger.error(f"空売り情報取得エラー: {e}")
        return {
            "short_balance": 0,
            "short_ratio": 0,
            "sector_short_ratio": 0,
            "short_trend": "unknown",
            "market_sentiment": "neutral"
        }


def get_investment_sector_data(symbol: str) -> Dict[str, Any]:
    """投資部門別情報を取得する（yfinanceでは限定的な情報のみ）"""
    logger.info(f"{symbol}の投資部門別情報を取得しています...")
    
    try:
        # yfinanceでティッカーオブジェクトを作成
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # yfinanceから取得可能な限定的なデータ
        institutional_holders = ticker.institutional_holders
        major_holders = ticker.major_holders
        
        # デフォルト値で構造化
        sector_data = {
            "proprietary_net": 0,
            "individual_net": 0,
            "foreign_net": 0,
            "institution_net": 0,
            "investment_trust_net": 0,
            "pension_fund_net": 0,
            "dominant_investor": "unknown",
            "foreign_ownership_trend": "neutral",
            "institutional_sentiment": "neutral"
        }
        
        # 機関投資家情報が利用可能な場合
        if not institutional_holders.empty and len(institutional_holders) > 0:
            # 機関投資家の総保有比率を計算
            total_institutional = institutional_holders['% Out'].sum() if '% Out' in institutional_holders.columns else 0
            sector_data["institution_net"] = total_institutional
            
            if total_institutional > 60:  # 60%以上
                sector_data["institutional_sentiment"] = "bullish"
                sector_data["dominant_investor"] = "institution"
            elif total_institutional < 30:  # 30%未満
                sector_data["institutional_sentiment"] = "bearish"
        
        # major_holdersから追加情報を取得
        if not major_holders.empty and len(major_holders) > 0:
            try:
                # 内部関係者の保有比率
                if len(major_holders) > 0:
                    insider_pct = float(str(major_holders.iloc[0, 1]).replace('%', ''))
                    if insider_pct > 10:
                        sector_data["individual_net"] = insider_pct
            except:
                pass
        
        logger.info("✓ 投資部門別情報を取得しました")
        return sector_data
        
    except Exception as e:
        logger.error(f"投資部門別情報取得エラー: {e}")
        return {
            "proprietary_net": 0,
            "individual_net": 0,
            "foreign_net": 0,
            "institution_net": 0,
            "investment_trust_net": 0,
            "pension_fund_net": 0,
            "dominant_investor": "unknown",
            "foreign_ownership_trend": "neutral",
            "institutional_sentiment": "neutral"
        }


def get_sp500_data() -> Dict[str, Any]:
    """S&P 500指数データを取得する（yfinanceを使用）"""
    logger.info("S&P 500指数データを取得しています...")
    
    try:
        # S&P 500のティッカーシンボル（^GSPC）
        sp500_ticker = yf.Ticker("^GSPC")
        
        # 過去30日のデータを取得
        hist = sp500_ticker.history(period="1mo")
        
        if not hist.empty:
            latest_sp500 = hist.iloc[-1]
            previous_sp500 = hist.iloc[-2] if len(hist) > 1 else latest_sp500
            
            current_value = safe_float(latest_sp500['Close'])
            previous_value = safe_float(previous_sp500['Close'])
            
            sp500_info = {
                "current_value": current_value,
                "daily_change": current_value - previous_value,
                "daily_change_pct": (current_value - previous_value) / previous_value if previous_value > 0 else 0,
                "volume": safe_float(latest_sp500['Volume']),
                "market_trend": "neutral",
                "market_strength": "moderate"
            }
            
            # マーケットトレンドを判定
            if sp500_info["daily_change_pct"] > 0.01:  # 1%以上上昇
                sp500_info["market_trend"] = "bullish"
                sp500_info["market_strength"] = "strong"
            elif sp500_info["daily_change_pct"] < -0.01:  # 1%以上下落
                sp500_info["market_trend"] = "bearish" 
                sp500_info["market_strength"] = "weak"
            
            logger.info("✓ S&P 500指数データを取得しました")
            return sp500_info
        else:
            logger.warning("S&P 500データが見つかりません")
            return {}
            
    except Exception as e:
        logger.error(f"S&P 500データ取得エラー: {e}")
        return {}


def get_credit_balance_data(symbol: str) -> Dict[str, Any]:
    """信用取引残高情報を取得する（yfinanceでは限定的な情報のみ）"""
    logger.info(f"{symbol}の信用取引残高を取得しています...")
    
    try:
        # yfinanceでティッカーオブジェクトを作成
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # yfinanceから取得可能な限定的なデータ
        shares_short = safe_float(info.get('sharesShort', 0))
        float_shares = safe_float(info.get('floatShares', 1))
        short_ratio = safe_float(info.get('shortRatio', 0))
        
        # 信用取引関連データを構造化
        credit_info = {
            "margin_buy_balance": 0,  # yfinanceから直接取得不可
            "margin_sell_balance": shares_short,
            "margin_ratio": 0,
            "credit_sentiment": "neutral",
            "leverage_risk": "moderate"
        }
        
        # 空売りベースでの信用センチメント判定
        short_percent = shares_short / float_shares if float_shares > 0 else 0
        
        if short_percent > 0.1:  # 10%以上の空売り
            credit_info["credit_sentiment"] = "bearish"
            credit_info["leverage_risk"] = "high"
        elif short_percent > 0.05:  # 5-10%の空売り
            credit_info["credit_sentiment"] = "neutral"
            credit_info["leverage_risk"] = "moderate"
        else:  # 5%未満の空売り
            credit_info["credit_sentiment"] = "bullish"
            credit_info["leverage_risk"] = "low"
        
        logger.info("✓ 信用取引残高を取得しました")
        return credit_info
        
    except Exception as e:
        logger.error(f"信用取引残高取得エラー: {e}")
        return {}


def get_price_data(
    ticker: str,
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """株価データを取得する

    Args:
        ticker: ティッカーシンボル
        start_date: 開始日、フォーマット：YYYY-MM-DD
        end_date: 終了日、フォーマット：YYYY-MM-DD

    Returns:
        価格データを含むDataFrame
    """
    return get_price_history(ticker, start_date, end_date)