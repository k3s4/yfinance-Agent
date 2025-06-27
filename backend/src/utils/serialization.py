"""
シリアライズユーティリティ - 複雑なPythonオブジェクトをJSONシリアライズ可能な形式に変換する
"""

import json
from typing import Any, Dict
from datetime import datetime, UTC


def serialize_agent_state(state: Dict) -> Dict:
    """
    AgentStateオブジェクトをJSONシリアライズ可能な辞書に変換する

    引数:
        state: Agentの状態を表す辞書。JSONにシリアライズできないオブジェクトを含む可能性がある

    戻り値:
        JSONフレンドリーな形式に変換された辞書
    """
    if not state:
        return {}

    try:
        return _convert_to_serializable(state)
    except Exception as e:
        return {
            "error": f"状態のシリアライズに失敗しました: {str(e)}",
            "serialization_error": True,
            "timestamp": datetime.now(UTC).isoformat()
        }


def _convert_to_serializable(obj: Any) -> Any:
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, 'content') and hasattr(obj, 'type'):
        return {
            "content": _convert_to_serializable(obj.content),
            "type": obj.type
        }
    elif hasattr(obj, '__dict__'):
        return _convert_to_serializable(obj.__dict__)
    elif isinstance(obj, (int, float, bool, str, type(None))):
        return obj
    elif isinstance(obj, (list, tuple)):
        return [_convert_to_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {str(key): _convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return str(obj)
