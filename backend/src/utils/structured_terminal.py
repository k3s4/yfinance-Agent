"""
構造化ターミナル出力モジュール

このモジュールは、エージェントデータを収集し、フォーマットするためのシンプルで柔軟なシステムを提供し、
ワークフローの最後に、美しく構造化された形式で一度に表示します。

バックエンドから完全に独立しており、ターミナル出力のフォーマットのみを担当します。
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .logging_config import setup_logger

# ロガーを設定
logger = setup_logger('structured_terminal')

# フォーマット用記号
SYMBOLS = {
    "border": "═",
    "header_left": "╔",
    "header_right": "╗",
    "footer_left": "╚",
    "footer_right": "╝",
    "separator": "─",
    "vertical": "║",
    "tree_branch": "├─",
    "tree_last": "└─",
    "section_prefix": "● ",
    "bullet": "• ",
}

# ステータスアイコン
STATUS_ICONS = {
    "bearish": "📉",
    "bullish": "📈",
    "neutral": "◽",
    "hold": "⏸️",
    "buy": "🛒",
    "sell": "💰",
    "completed": "✅",
    "in_progress": "🔄",
    "error": "❌",
    "warning": "⚠️",
}

# エージェントのアイコンと名前のマッピング
AGENT_MAP = {
    "market_data_agent": {"icon": "📊", "name": "市場データ"},
    "technical_analyst_agent": {"icon": "📈", "name": "テクニカル"},
    "fundamentals_agent": {"icon": "📝", "name": "ファンダメンタルズ"},
    "sentiment_agent": {"icon": "🔍", "name": "センチメント"},
    "valuation_agent": {"icon": "💰", "name": "バリュエーション"},
    "researcher_bull_agent": {"icon": "🐂", "name": "強気派リサーチ"},
    "researcher_bear_agent": {"icon": "🐻", "name": "弱気派リサーチ"},
    "debate_room_agent": {"icon": "🗣️", "name": "ディベート室"},
    "risk_management_agent": {"icon": "⚠️", "name": "リスク管理"},
    
    "portfolio_management_agent": {"icon": "📂", "name": "ポートフォリオ管理"}
}

# エージェントの表示順序
AGENT_ORDER = [
    "market_data_agent",
    "technical_analyst_agent",
    "fundamentals_agent",
    "sentiment_agent",
    "valuation_agent",
    "researcher_bull_agent",
    "researcher_bear_agent",
    "debate_room_agent",
    "risk_management_agent",
    
    "portfolio_management_agent"
]


class StructuredTerminalOutput:
    """構造化ターミナル出力クラス"""

    def __init__(self):
        """初期化"""
        self.data = {}
        self.metadata = {}

    def set_metadata(self, key: str, value: Any) -> None:
        """メタデータを設定する"""
        self.metadata[key] = value

    def add_agent_data(self, agent_name: str, data: Any) -> None:
        """エージェントデータを追加する"""
        self.data[agent_name] = data

    def _format_value(self, value: Any) -> str:
        """単一の値をフォーマットする"""
        if isinstance(value, bool):
            return "✅" if value else "❌"
        elif isinstance(value, (int, float)):
            # パーセンテージ値を特別に処理
            if -1 <= value <= 1 and isinstance(value, float):
                return f"{value:.2%}"
            return str(value)
        elif value is None:
            return "N/A"
        else:
            return str(value)

    def _format_dict_as_tree(self, data: Dict[str, Any], indent: int = 0) -> List[str]:
        """辞書をツリー構造にフォーマットする"""
        result = []
        items = list(data.items())

        for i, (key, value) in enumerate(items):
            is_last = i == len(items) - 1
            prefix = SYMBOLS["tree_last"] if is_last else SYMBOLS["tree_branch"]
            indent_str = "  " * indent

            if isinstance(value, dict) and value:
                result.append(f"{indent_str}{prefix} {key}:")
                result.extend(self._format_dict_as_tree(value, indent + 1))
            elif isinstance(value, list) and value:
                result.append(f"{indent_str}{prefix} {key}:")
                for j, item in enumerate(value):
                    sub_is_last = j == len(value) - 1
                    sub_prefix = SYMBOLS["tree_last"] if sub_is_last else SYMBOLS["tree_branch"]
                    if isinstance(item, dict):
                        result.append(
                            f"{indent_str}  {sub_prefix} Agent {j+1}:")
                        result.extend(
                            ["  " + line for line in self._format_dict_as_tree(item, indent + 2)])
                    else:
                        result.append(f"{indent_str}  {sub_prefix} {item}")
            else:
                formatted_value = self._format_value(value)
                result.append(f"{indent_str}{prefix} {key}: {formatted_value}")

        return result

    def _format_agent_section(self, agent_name: str, data: Any) -> List[str]:
        """エージェントセクションをフォーマットする"""
        result = []

        # エージェント情報を取得
        agent_info = AGENT_MAP.get(
            agent_name, {"icon": "🔄", "name": agent_name})
        icon = agent_info["icon"]
        display_name = agent_info["name"]

        # ヘッダーを作成
        width = 80
        title = f"{icon} {display_name}分析"
        result.append(
            f"{SYMBOLS['header_left']}{SYMBOLS['border'] * ((width - len(title) - 2) // 2)} {title} {SYMBOLS['border'] * ((width - len(title) - 2) // 2)}{SYMBOLS['header_right']}")

        # 内容を追加
        if isinstance(data, dict):
            # portfolio_management_agentを特別に処理
            if agent_name == "portfolio_management_agent":
                # actionとconfidenceの抽出を試みる
                if "action" in data:
                    action = data.get("action", "")
                    action_icon = STATUS_ICONS.get(action.lower(), "")
                    result.append(
                        f"{SYMBOLS['vertical']} 取引アクション: {action_icon} {action.upper() if action else ''}")

                if "quantity" in data:
                    quantity = data.get("quantity", 0)
                    result.append(f"{SYMBOLS['vertical']} 取引数量: {quantity}")

                if "confidence" in data:
                    conf = data.get("confidence", 0)
                    if isinstance(conf, (int, float)) and conf <= 1:
                        conf_str = f"{conf*100:.0f}%"
                    else:
                        conf_str = str(conf)
                    result.append(f"{SYMBOLS['vertical']} 意思決定の信頼度: {conf_str}")

                # 各エージェントのシグナルを表示
                if "agent_signals" in data:
                    result.append(
                        f"{SYMBOLS['vertical']} {SYMBOLS['section_prefix']}各アナリストの意見:")

                    for signal_info in data["agent_signals"]:
                        agent = signal_info.get("agent", "")
                        signal = signal_info.get("signal", "")
                        conf = signal_info.get("confidence", 1.0)

                        # 空のシグナルはスキップ
                        if not agent or not signal:
                            continue

                        # シグナルアイコンを取得
                        signal_icon = STATUS_ICONS.get(signal.lower(), "")

                        # 信頼度をフォーマット
                        if isinstance(conf, (int, float)) and conf <= 1:
                            conf_str = f"{conf*100:.0f}%"
                        else:
                            conf_str = str(conf)

                        result.append(
                            f"{SYMBOLS['vertical']}   • {agent}: {signal_icon} {signal} (信頼度: {conf_str})")

                # 意思決定の理由
                if "reasoning" in data:
                    reasoning = data["reasoning"]
                    result.append(
                        f"{SYMBOLS['vertical']} {SYMBOLS['section_prefix']}意思決定の理由:")
                    if isinstance(reasoning, str):
                        # 長文を複数行に分割、各行はwidth-4文字を超えない
                        for i in range(0, len(reasoning), width-4):
                            line = reasoning[i:i+width-4]
                            result.append(f"{SYMBOLS['vertical']}   {line}")
            else:
                # 他のエージェントの標準的な処理
                # シグナルと信頼度を抽出（もしあれば）
                if "signal" in data:
                    signal = data.get("signal", "")
                    signal_icon = STATUS_ICONS.get(signal.lower(), "")
                    result.append(
                        f"{SYMBOLS['vertical']} シグナル: {signal_icon} {signal}")

                if "confidence" in data:
                    conf = data.get("confidence", "")
                    if isinstance(conf, (int, float)) and conf <= 1:
                        conf_str = f"{conf*100:.0f}%"
                    else:
                        conf_str = str(conf)
                    result.append(f"{SYMBOLS['vertical']} 信頼度: {conf_str}")

            # その他のデータを追加
            tree_lines = self._format_dict_as_tree(data)
            for line in tree_lines:
                result.append(f"{SYMBOLS['vertical']} {line}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                prefix = SYMBOLS["tree_last"] if i == len(
                    data) - 1 else SYMBOLS["tree_branch"]
                result.append(f"{SYMBOLS['vertical']} {prefix} {item}")
        else:
            result.append(f"{SYMBOLS['vertical']} {data}")

        # フッターを追加
        result.append(
            f"{SYMBOLS['footer_left']}{SYMBOLS['border'] * (width - 2)}{SYMBOLS['footer_right']}")

        return result

    def generate_output(self) -> str:
        """フォーマットされた出力を生成する"""
        width = 80
        result = []

        # タイトルを追加
        ticker = self.metadata.get("ticker", "不明")
        title = f"銘柄コード {ticker} 投資分析レポート"
        result.append(SYMBOLS["border"] * width)
        result.append(f"{title:^{width}}")
        result.append(SYMBOLS["border"] * width)

        # 日付範囲を追加（もしあれば）
        if "start_date" in self.metadata and "end_date" in self.metadata:
            date_range = f"分析期間: {self.metadata['start_date']} から {self.metadata['end_date']}"
            result.append(f"{date_range:^{width}}")
            result.append("")

        # 各エージェントの出力を順に追加
        for agent_name in AGENT_ORDER:
            if agent_name in self.data:
                result.extend(self._format_agent_section(
                    agent_name, self.data[agent_name]))
                result.append("")  # 空行を追加

        # 終了の区切り線を追加
        result.append(SYMBOLS["border"] * width)

        return "\n".join(result)

    def print_output(self) -> None:
        """フォーマットされた出力を表示する"""
        output = self.generate_output()
        # INFOレベルでログに記録し、コンソールに表示されるようにする
        logger.info("\n" + output)


# グローバルインスタンスを作成
terminal = StructuredTerminalOutput()


def extract_agent_data(state: Dict[str, Any], agent_name: str) -> Any:
    """
    状態から指定されたエージェントのデータを抽出する

    Args:
        state: ワークフローの状態
        agent_name: エージェント名

    Returns:
        抽出されたエージェントデータ
    """
    # portfolio_management_agentを特別に処理
    if agent_name == "portfolio_management_agent":
        # 最後のメッセージからデータの取得を試みる
        messages = state.get("messages", [])
        if messages and hasattr(messages[-1], "content"):
            content = messages[-1].content
            # JSONの解析を試みる
            if isinstance(content, str):
                try:
                    # JSON文字列であれば、解析を試みる
                    if content.strip().startswith('{') and content.strip().endswith('}'):
                        return json.loads(content)
                    # 他のテキストに含まれるJSON文字列であれば、抽出して解析を試みる
                    json_start = content.find('{')
                    json_end = content.rfind('}')
                    if json_start >= 0 and json_end > json_start:
                        json_str = content[json_start:json_end+1]
                        return json.loads(json_str)
                except json.JSONDecodeError:
                    # 解析に失敗した場合、元の内容を返す
                    return {"message": content}
            return {"message": content}

    # まずmetadataのall_agent_reasoningからの取得を試みる
    metadata = state.get("metadata", {})
    all_reasoning = metadata.get("all_agent_reasoning", {})

    # 一致するエージェントデータを検索
    for name, data in all_reasoning.items():
        if agent_name in name:
            return data

    # all_agent_reasoningで見つからない場合、agent_reasoningからの取得を試みる
    if agent_name == metadata.get("current_agent_name") and "agent_reasoning" in metadata:
        return metadata["agent_reasoning"]

    # messagesからの取得を試みる
    messages = state.get("messages", [])
    for message in messages:
        if hasattr(message, "name") and message.name and agent_name in message.name:
            # メッセージ内容の解析を試みる
            try:
                if hasattr(message, "content"):
                    content = message.content
                    # JSONの解析を試みる
                    if isinstance(content, str) and (content.startswith('{') or content.startswith('[')):
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError:
                            pass
                    return content
            except Exception:
                pass

    # すべて見つからない場合、Noneを返す
    return None


def process_final_state(state: Dict[str, Any]) -> None:
    """
    最終状態を処理し、すべてのエージェントのデータを抽出する

    Args:
        state: ワークフローの最終状態
    """
    # メタデータを抽出
    data = state.get("data", {})

    # メタデータを設定
    terminal.set_metadata("ticker", data.get("ticker", "不明"))
    if "start_date" in data and "end_date" in data:
        terminal.set_metadata("start_date", data["start_date"])
        terminal.set_metadata("end_date", data["end_date"])

    # 各エージェントのデータを抽出
    for agent_name in AGENT_ORDER:
        agent_data = extract_agent_data(state, agent_name)
        if agent_data:
            terminal.add_agent_data(agent_name, agent_data)


def print_structured_output(state: Dict[str, Any]) -> None:
    """
    最終状態を処理し、構造化された出力を表示する
    Args:
        state: ワークフローの最終状態
    """
    try:
        # 最終状態を処理
        process_final_state(state)

        # 出力を表示
        terminal.print_output()
    except Exception as e:
        logger.error(f"構造化された出力の生成中にエラーが発生しました: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
