"""
APIユーティリティ関数モジュール

このモジュールは、API内で使用される各種ユーティリティ関数（シリアライズ、整形など）を提供します。
"""

import json
from typing import Any, Dict


def safe_parse_json(data):
    """
    JSON形式かもしれない文字列を安全にパースする

    - 文字列でなければそのまま返す
    - JSON文字列っぽければ辞書に変換して返す
    - Markdownのコードブロック（```）で囲まれていても処理可能
    - パースに失敗したらそのまま返す
    """
    if not isinstance(data, str):
        return data

    try:
        # Markdownコードブロックが含まれている場合は除去
        if data.startswith("```") and "```" in data:
            lines = data.split("\n")
            start_idx = 0
            end_idx = len(lines)
            for i, line in enumerate(lines):
                if line.startswith("```") and i == 0:
                    start_idx = 1
                elif line.startswith("```") and i > 0:
                    end_idx = i
                    break
            json_content = "\n".join(lines[start_idx:end_idx])
            return json.loads(json_content)

        return json.loads(data)
    except (json.JSONDecodeError, ValueError):
        return data


def serialize_for_api(obj: Any) -> Any:
    """任意のオブジェクトをAPIレスポンス向けにJSONシリアライズ可能な形式に変換する"""
    if obj is None:
        return None

    # JSON文字列ならまず辞書化
    obj = safe_parse_json(obj)

    if isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_api(x) for x in obj]
    elif isinstance(obj, dict):
        return {str(k): serialize_for_api(v) for k, v in obj.items()}
    elif hasattr(obj, 'dict') and callable(getattr(obj, 'dict')):
        return serialize_for_api(obj.dict())
    elif hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
        return serialize_for_api(obj.to_dict())
    elif hasattr(obj, '__dict__'):
        return serialize_for_api(obj.__dict__)
    else:
        return str(obj)


def format_llm_request(request_data: Any) -> Dict:
    """LLMへのリクエストデータを可読な形式に整形する"""
    if request_data is None:
        return {"message": "LLMリクエストは記録されていません"}

    request_data = safe_parse_json(request_data)

    if isinstance(request_data, tuple):
        # args形式の処理
        if len(request_data) > 0 and isinstance(request_data[0], list):
            messages = request_data[0]
            formatted_messages = []
            message_texts = []

            for msg in messages:
                if isinstance(msg, dict):
                    formatted_msg = msg
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    message_texts.append(f"[{role}] {content}")
                elif hasattr(msg, 'type') and hasattr(msg, 'content'):
                    formatted_msg = {
                        "role": msg.type,
                        "content": msg.content
                    }
                    message_texts.append(f"[{msg.type}] {msg.content}")
                else:
                    formatted_msg = {"content": str(msg)}
                    message_texts.append(str(msg))

                formatted_messages.append(formatted_msg)

            return {
                "messages": formatted_messages,
                "formatted": "\n".join(message_texts)
            }

        return {"args": [serialize_for_api(arg) for arg in request_data]}

    if isinstance(request_data, dict):
        return serialize_for_api(request_data)

    if isinstance(request_data, list):
        try:
            formatted_messages = []
            message_texts = []

            for msg in request_data:
                if isinstance(msg, dict):
                    formatted_msg = msg
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    message_texts.append(f"[{role}] {content}")
                elif hasattr(msg, 'type') and hasattr(msg, 'content'):
                    formatted_msg = {
                        "role": msg.type,
                        "content": msg.content
                    }
                    message_texts.append(f"[{msg.type}] {msg.content}")
                else:
                    formatted_msg = {"content": str(msg)}
                    message_texts.append(str(msg))

                formatted_messages.append(formatted_msg)

            return {
                "messages": formatted_messages,
                "formatted": "\n".join(message_texts)
            }
        except Exception:
            return {"items": [serialize_for_api(item) for item in request_data]}

    return {"data": serialize_for_api(request_data)}


def format_llm_response(response_data: Any) -> Dict:
    """LLMからのレスポンスを可読な形式に整形する"""
    if response_data is None:
        return {"message": "LLMレスポンスは記録されていません"}

    response_data = safe_parse_json(response_data)

    if hasattr(response_data, 'text'):
        return {
            "text": response_data.text,
            "original": serialize_for_api(response_data)
        }

    if isinstance(response_data, str):
        return {"text": response_data}

    if isinstance(response_data, dict):
        if "choices" in response_data and isinstance(response_data["choices"], list):
            try:
                messages = []
                for choice in response_data["choices"]:
                    if "message" in choice:
                        messages.append(choice["message"])
                if messages:
                    return {
                        "messages": messages,
                        "original": serialize_for_api(response_data)
                    }
            except Exception:
                pass

        return serialize_for_api(response_data)

    return serialize_for_api(response_data)
