from typing import Dict
from src.utils.logging_config import setup_logger

from langchain_core.messages import HumanMessage

from src.agents.state import AgentState, show_agent_reasoning, show_workflow_status
from src.utils.api_utils import agent_endpoint, log_llm_interaction

import json
import pandas as pd
import numpy as np

from src.tools.api import prices_to_df

# ロガーを初期化
logger = setup_logger('technical_analyst_agent')


##### テクニカルアナリスト #####
@agent_endpoint("technical_analyst", "テクニカルアナリスト、価格動向、指標、テクニカルパターンに基づいた取引シグナルを提供")
def technical_analyst_agent(state: AgentState):
    """
    複数の取引戦略を組み合わせた高度なテクニカル分析システム：
    1. トレンドフォロー (Trend Following)
    2. 平均回帰 (Mean Reversion)
    3. モメンタム (Momentum)
    4. ボラティリティ分析 (Volatility Analysis)
    5. 統計的裁定シグナル (Statistical Arbitrage Signals)
    """
    logger.info("\n--- DEBUG: テクニカルアナリストエージェント START ---")
    show_workflow_status("テクニカルアナリスト")
    show_reasoning = state["metadata"]["show_reasoning"]
    data = state["data"]
    prices = data["prices"]
    prices_df = prices_to_df(prices)


    # 1. トレンドフォロー戦略
    trend_signals = calculate_trend_signals(prices_df)

    # 2. 平均回帰戦略
    mean_reversion_signals = calculate_mean_reversion_signals(prices_df)

    # 3. モメンタム戦略
    momentum_signals = calculate_momentum_signals(prices_df)

    # 4. ボラティリティ戦略
    volatility_signals = calculate_volatility_signals(prices_df)

    # 5. 統計的裁定シグナル
    stat_arb_signals = calculate_stat_arb_signals(prices_df)

    # 加重アンサンブルアプローチを用いて全てのシグナルを結合
    strategy_weights = {
        'trend': 0.30,
        'mean_reversion': 0.25,  # 平均回帰の重みを増加
        'momentum': 0.25,
        'volatility': 0.15,
        'stat_arb': 0.05
    }

    combined_signal = weighted_signal_combination({
        'trend': trend_signals,
        'mean_reversion': mean_reversion_signals,
        'momentum': momentum_signals,
        'volatility': volatility_signals,
        'stat_arb': stat_arb_signals
    }, strategy_weights)

    # 詳細な分析レポートを生成
    analysis_report = {
        "総合シグナル": combined_signal['signal'],
        "信頼度": f"{round(combined_signal['confidence'] * 100)}%",
        "戦略別シグナル": {
            "トレンドフォロー": {
                "シグナル": trend_signals['signal'],
                "信頼度": f"{round(trend_signals['confidence'] * 100)}%",
                "指標": normalize_pandas(trend_signals['metrics'])
            },
            "平均回帰": {
                "シグナル": mean_reversion_signals['signal'],
                "信頼度": f"{round(mean_reversion_signals['confidence'] * 100)}%",
                "指標": normalize_pandas(mean_reversion_signals['metrics'])
            },
            "モメンタム": {
                "シグナル": momentum_signals['signal'],
                "信頼度": f"{round(momentum_signals['confidence'] * 100)}%",
                "指標": normalize_pandas(momentum_signals['metrics'])
            },
            "ボラティリティ": {
                "シグナル": volatility_signals['signal'],
                "信頼度": f"{round(volatility_signals['confidence'] * 100)}%",
                "指標": normalize_pandas(volatility_signals['metrics'])
            },
            "統計的裁定": {
                "シグナル": stat_arb_signals['signal'],
                "信頼度": f"{round(stat_arb_signals['confidence'] * 100)}%",
                "指標": normalize_pandas(stat_arb_signals['metrics'])
            }
        }
    }

    # テクニカルアナリストのメッセージを作成
    message = HumanMessage(
        content=json.dumps(analysis_report, ensure_ascii=False),
        name="technical_analyst_agent",
    )

    if show_reasoning:
        show_agent_reasoning(analysis_report, "テクニカルアナリスト")
        # 推論情報をstateのmetadataに保存し、APIで利用可能にする
        state["metadata"]["agent_reasoning"] = analysis_report

    show_workflow_status("テクニカルアナリスト", "完了")

    # デバッグ情報：返されるメッセージの名前を出力
    # logger.info(
    # f"--- DEBUG: テクニカルアナリストエージェント RETURN messages: {[msg.name for msg in [message]]} ---")

    return {
        "messages": [message],
        "data": {
            **data,
            "technical_analysis": combined_signal
        },
        "metadata": state["metadata"],
    }


def calculate_trend_signals(prices_df):
    """
    複数の時間枠と指標を使用した高度なトレンドフォロー戦略
    """
    # 複数の時間枠でEMAを計算
    ema_8 = calculate_ema(prices_df, 8)
    ema_21 = calculate_ema(prices_df, 21)
    ema_55 = calculate_ema(prices_df, 55)

    # トレンドの強さを示すADXを計算
    adx = calculate_adx(prices_df, 14)


    # トレンドの方向と強さを判断
    short_trend = ema_8 > ema_21
    medium_trend = ema_21 > ema_55

    # 信頼度の重み付けでシグナルを結合
    trend_strength = adx['adx'].iloc[-1] / 100.0

    if short_trend.iloc[-1] and medium_trend.iloc[-1]:
        signal = 'bullish'
        confidence = trend_strength
    elif not short_trend.iloc[-1] and not medium_trend.iloc[-1]:
        signal = 'bearish'
        confidence = trend_strength
    else:
        signal = 'neutral'
        confidence = 0.5

    return {
        'signal': signal,
        'confidence': confidence,
        'metrics': {
            'adx': float(adx['adx'].iloc[-1]),
            'trend_strength': float(trend_strength),
        }
    }


def calculate_mean_reversion_signals(prices_df):
    """
    統計的指標とボリンジャーバンドを使用した平均回帰戦略
    """
    # 移動平均に対する価格のZスコアを計算
    ma_50 = prices_df['close'].rolling(window=50).mean()
    std_50 = prices_df['close'].rolling(window=50).std()
    z_score = (prices_df['close'] - ma_50) / std_50

    # ボリンジャーバンドを計算
    bb_upper, bb_lower = calculate_bollinger_bands(prices_df)

    # 複数の時間枠でRSIを計算
    rsi_14 = calculate_rsi(prices_df, 14)
    rsi_28 = calculate_rsi(prices_df, 28)

    # 平均回帰シグナル
    extreme_z_score = abs(z_score.iloc[-1]) > 2
    price_vs_bb = (prices_df['close'].iloc[-1] - bb_lower.iloc[-1]
                   ) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])

    # シグナルを結合
    if z_score.iloc[-1] < -2 and price_vs_bb < 0.2:
        signal = 'bullish'
        confidence = min(abs(z_score.iloc[-1]) / 4, 1.0)
    elif z_score.iloc[-1] > 2 and price_vs_bb > 0.8:
        signal = 'bearish'
        confidence = min(abs(z_score.iloc[-1]) / 4, 1.0)
    else:
        signal = 'neutral'
        confidence = 0.5

    return {
        'signal': signal,
        'confidence': confidence,
        'metrics': {
            'z_score': float(z_score.iloc[-1]),
            'price_vs_bb': float(price_vs_bb),
            'rsi_14': float(rsi_14.iloc[-1]),
            'rsi_28': float(rsi_28.iloc[-1])
        }
    }


def calculate_momentum_signals(prices_df):
    """
    保守的な設定を持つ多要素モメンタム戦略
    """
    # 調整されたmin_periodsを持つ価格モメンタム
    returns = prices_df['close'].pct_change()
    mom_1m = returns.rolling(21, min_periods=5).sum()    # 短期モメンタムは少ないデータ点を許容
    mom_3m = returns.rolling(63, min_periods=42).sum()   # 中期モメンタムはより多くのデータ点を要求
    mom_6m = returns.rolling(126, min_periods=63).sum()  # 長期モメンタムは厳格な要求を維持

    # 出来高モメンタム
    volume_ma = prices_df['volume'].rolling(21, min_periods=10).mean()
    volume_momentum = prices_df['volume'] / volume_ma

    # NaN値を処理
    mom_1m = mom_1m.fillna(0)       # 短期モメンタムは0で埋める
    mom_3m = mom_3m.fillna(mom_1m)  # 中期モメンタムは短期モメンタムで埋める
    mom_6m = mom_6m.fillna(mom_3m)  # 長期モメンタムは中期モメンタムで埋める

    # 長期の時間枠に重みを置いたモメンタムスコアを計算
    momentum_score = (
        0.2 * mom_1m +  # 短期の重みを下げる
        0.3 * mom_3m +
        0.5 * mom_6m    # 長期の重みを上げる
    ).iloc[-1]

    # 出来高による確認
    volume_confirmation = volume_momentum.iloc[-1] > 1.0

    if momentum_score > 0.05 and volume_confirmation:
        signal = 'bullish'
        confidence = min(abs(momentum_score) * 5, 1.0)
    elif momentum_score < -0.05 and volume_confirmation:
        signal = 'bearish'
        confidence = min(abs(momentum_score) * 5, 1.0)
    else:
        signal = 'neutral'
        confidence = 0.5

    return {
        'signal': signal,
        'confidence': confidence,
        'metrics': {
            'momentum_1m': float(mom_1m.iloc[-1]),
            'momentum_3m': float(mom_3m.iloc[-1]),
            'momentum_6m': float(mom_6m.iloc[-1]),
            'volume_momentum': float(volume_momentum.iloc[-1])
        }
    }


def calculate_volatility_signals(prices_df):
    """
    より短いルックバック期間で最適化されたボラティリティ計算
    """
    returns = prices_df['close'].pct_change()

    # より短い期間と最小期間要求を使用してヒストリカルボラティリティを計算
    hist_vol = returns.rolling(21, min_periods=10).std() * (252 ** 0.5)

    # より短い期間でボラティリティの平均を計算し、より少ないデータ点を許容
    vol_ma = hist_vol.rolling(42, min_periods=21).mean()
    vol_regime = hist_vol / vol_ma

    # より柔軟な標準偏差計算を使用
    vol_std = hist_vol.rolling(42, min_periods=21).std()
    vol_z_score = (hist_vol - vol_ma) / vol_std.replace(0, np.nan)

    # ATR計算の最適化
    atr = calculate_atr(prices_df, period=14, min_periods=7)
    atr_ratio = atr / prices_df['close']

    # 主要な指標がNaNの場合、中立シグナルを直接返す代わりに代替値を使用
    if pd.isna(vol_regime.iloc[-1]):
        vol_regime.iloc[-1] = 1.0  # 通常のボラティリティ区間にあると仮定
    if pd.isna(vol_z_score.iloc[-1]):
        vol_z_score.iloc[-1] = 0.0  # 平均値の位置にあると仮定

    # ボラティリティレジームに基づいてシグナルを生成
    current_vol_regime = vol_regime.iloc[-1]
    vol_z = vol_z_score.iloc[-1]

    if current_vol_regime < 0.8 and vol_z < -1:
        signal = 'bullish'  # 低ボラティリティレジーム、拡大の可能性
        confidence = min(abs(vol_z) / 3, 1.0)
    elif current_vol_regime > 1.2 and vol_z > 1:
        signal = 'bearish'  # 高ボラティリティレジーム、収縮の可能性
        confidence = min(abs(vol_z) / 3, 1.0)
    else:
        signal = 'neutral'
        confidence = 0.5

    return {
        'signal': signal,
        'confidence': confidence,
        'metrics': {
            'historical_volatility': float(hist_vol.iloc[-1]),
            'volatility_regime': float(current_vol_regime),
            'volatility_z_score': float(vol_z),
            'atr_ratio': float(atr_ratio.iloc[-1])
        }
    }


def calculate_stat_arb_signals(prices_df):
    """
    より短いルックバック期間で最適化された統計的裁定シグナル
    """
    # 価格分布の統計量を計算
    returns = prices_df['close'].pct_change()

    # より短い期間で歪度と尖度を計算
    skew = returns.rolling(42, min_periods=21).skew()
    kurt = returns.rolling(42, min_periods=21).kurt()

    # ハースト指数の計算を最適化
    hurst = calculate_hurst_exponent(prices_df['close'], max_lag=10)

    # NaN値を処理
    if pd.isna(skew.iloc[-1]):
        skew.iloc[-1] = 0.0  # 正規分布を仮定
    if pd.isna(kurt.iloc[-1]):
        kurt.iloc[-1] = 3.0  # 正規分布を仮定

    # 統計的特性に基づいてシグナルを生成
    if hurst < 0.4 and skew.iloc[-1] > 1:
        signal = 'bullish'
        confidence = (0.5 - hurst) * 2
    elif hurst < 0.4 and skew.iloc[-1] < -1:
        signal = 'bearish'
        confidence = (0.5 - hurst) * 2
    else:
        signal = 'neutral'
        confidence = 0.5

    return {
        'signal': signal,
        'confidence': confidence,
        'metrics': {
            'hurst_exponent': float(hurst),
            'skewness': float(skew.iloc[-1]),
            'kurtosis': float(kurt.iloc[-1])
        }
    }


def weighted_signal_combination(signals, weights):
    """
    加重アプローチを用いて複数の取引シグナルを結合する
    """
    # シグナルを数値に変換
    signal_values = {
        'bullish': 1,
        'neutral': 0,
        'bearish': -1
    }

    weighted_sum = 0
    total_confidence = 0

    for strategy, signal in signals.items():
        numeric_signal = signal_values[signal['signal']]
        weight = weights[strategy]
        confidence = signal['confidence']

        weighted_sum += numeric_signal * weight * confidence
        total_confidence += weight * confidence

    # 加重和を正規化
    if total_confidence > 0:
        final_score = weighted_sum / total_confidence
    else:
        final_score = 0

    # シグナルに再変換
    if final_score > 0.2:
        signal = 'bullish'
    elif final_score < -0.2:
        signal = 'bearish'
    else:
        signal = 'neutral'

    return {
        'signal': signal,
        'confidence': abs(final_score)
    }


def normalize_pandas(obj):
    """pandasのSeries/DataFrameをPythonのプリミティブ型に変換する"""
    if isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    elif isinstance(obj, dict):
        return {k: normalize_pandas(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [normalize_pandas(item) for item in obj]
    return obj


def calculate_macd(prices_df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """MACDを計算する"""
    ema_12 = prices_df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = prices_df['close'].ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line, signal_line


def calculate_rsi(prices_df: pd.DataFrame, period: int = 14) -> pd.Series:
    """RSIを計算する"""
    delta = prices_df['close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_bollinger_bands(
    prices_df: pd.DataFrame,
    window: int = 20
) -> tuple[pd.Series, pd.Series]:
    """ボリンジャーバンドを計算する"""
    sma = prices_df['close'].rolling(window).mean()
    std_dev = prices_df['close'].rolling(window).std()
    upper_band = sma + (std_dev * 2)
    lower_band = sma - (std_dev * 2)
    return upper_band, lower_band


def calculate_ema(df: pd.DataFrame, window: int) -> pd.Series:
    """
    指数平滑移動平均 (EMA) を計算する

    Args:
        df: 価格データを含むDataFrame
        window: EMAの期間

    Returns:
        pd.Series: EMAの値
    """
    return df['close'].ewm(span=window, adjust=False).mean()


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    平均方向性指数 (ADX) を計算する

    Args:
        df: OHLCデータを含むDataFrame
        period: 計算期間

    Returns:
        DataFrame: ADXの値を含む
    """
    # 真の変動幅 (True Range) を計算
    df['high_low'] = df['high'] - df['low']
    df['high_close'] = abs(df['high'] - df['close'].shift())
    df['low_close'] = abs(df['low'] - df['close'].shift())
    df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)

    # 方向性変動 (Directional Movement) を計算
    df['up_move'] = df['high'] - df['high'].shift()
    df['down_move'] = df['low'].shift() - df['low']

    df['plus_dm'] = np.where(
        (df['up_move'] > df['down_move']) & (df['up_move'] > 0),
        df['up_move'],
        0
    )
    df['minus_dm'] = np.where(
        (df['down_move'] > df['up_move']) & (df['down_move'] > 0),
        df['down_move'],
        0
    )

    # ADXを計算
    df['+di'] = 100 * (df['plus_dm'].ewm(span=period).mean() /
                       df['tr'].ewm(span=period).mean())
    df['-di'] = 100 * (df['minus_dm'].ewm(span=period).mean() /
                       df['tr'].ewm(span=period).mean())
    df['dx'] = 100 * abs(df['+di'] - df['-di']) / (df['+di'] + df['-di'])
    df['adx'] = df['dx'].ewm(span=period).mean()

    return df[['adx', '+di', '-di']]


def calculate_ichimoku(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """
    一目均衡表の指標を計算する

    Args:
        df: OHLCデータを含むDataFrame

    Returns:
        Dict: 一目均衡表の各要素を含む辞書
    """
    # 転換線: (過去9期間の最高値 + 最安値) / 2
    period9_high = df['high'].rolling(window=9).max()
    period9_low = df['low'].rolling(window=9).min()
    tenkan_sen = (period9_high + period9_low) / 2

    # 基準線: (過去26期間の最高値 + 最安値) / 2
    period26_high = df['high'].rolling(window=26).max()
    period26_low = df['low'].rolling(window=26).min()
    kijun_sen = (period26_high + period26_low) / 2

    # 先行スパンA: (転換線 + 基準線) / 2 を26期間先行させる
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)

    # 先行スパンB: (過去52期間の最高値 + 最安値) / 2 を26期間先行させる
    period52_high = df['high'].rolling(window=52).max()
    period52_low = df['low'].rolling(window=52).min()
    senkou_span_b = ((period52_high + period52_low) / 2).shift(26)

    # 遅行スパン: 当日の終値を26期間過去にずらす
    chikou_span = df['close'].shift(-26)

    return {
        'tenkan_sen': tenkan_sen,
        'kijun_sen': kijun_sen,
        'senkou_span_a': senkou_span_a,
        'senkou_span_b': senkou_span_b,
        'chikou_span': chikou_span
    }


def calculate_atr(df: pd.DataFrame, period: int = 14, min_periods: int = 7) -> pd.Series:
    """
    最小期間パラメータを持つ最適化されたATR計算

    Args:
        df: OHLCデータを含むDataFrame
        period: ATRの計算期間
        min_periods: 必要な最小期間数

    Returns:
        pd.Series: ATRの値
    """
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())

    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)

    return true_range.rolling(period, min_periods=min_periods).mean()


def calculate_hurst_exponent(price_series: pd.Series, max_lag: int = 10) -> float:
    """
    より短いルックバックと改善されたエラーハンドリングを持つ最適化されたハースト指数の計算

    Args:
        price_series: 配列状の価格データ
        max_lag: R/S分析の最大ラグ (20から10に短縮)

    Returns:
        float: ハースト指数
    """
    try:
        # 価格ではなく対数収益率を使用
        returns = np.log(price_series / price_series.shift(1)).dropna()

        # データが不足している場合、0.5（ランダムウォーク）を返す
        if len(returns) < max_lag * 2:
            return 0.5

        lags = range(2, max_lag)
        # より安定した計算方法を使用
        tau = [np.sqrt(np.std(np.subtract(returns[lag:], returns[:-lag])))
               for lag in lags]

        # log(0)を避けるために微小な定数を加える
        tau = [max(1e-8, t) for t in tau]

        # 対数回帰を用いてハースト指数を計算
        reg = np.polyfit(np.log(lags), np.log(tau), 1)
        h = reg[0]

        # ハースト指数を合理的な範囲内に制限
        return max(0.0, min(1.0, h))

    except (ValueError, RuntimeWarning, np.linalg.LinAlgError):
        # 計算に失敗した場合、ランダムウォークを示す0.5を返す
        return 0.5


def calculate_obv(prices_df: pd.DataFrame) -> pd.Series:
    """オンバランスボリューム (OBV) を計算する"""
    obv = [0]
    for i in range(1, len(prices_df)):
        if prices_df['close'].iloc[i] > prices_df['close'].iloc[i - 1]:
            obv.append(obv[-1] + prices_df['volume'].iloc[i])
        elif prices_df['close'].iloc[i] < prices_df['close'].iloc[i - 1]:
            obv.append(obv[-1] - prices_df['volume'].iloc[i])
        else:
            obv.append(obv[-1])
    prices_df['OBV'] = obv
    return prices_df['OBV']