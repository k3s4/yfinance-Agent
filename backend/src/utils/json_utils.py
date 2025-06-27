import json
import re
import ast
from typing import Optional, Dict, Any
from .logging_config import setup_logger

logger = setup_logger('json_utils')

def clean_json_string(text: str) -> str:
    """
    JSON文字列をクリーニングする
    - 全角クォートを半角に変換
    - その他の問題のある文字を修正
    """
    if not isinstance(text, str):
        return text
    
    # 全角クォートを半角に変換
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    # その他の全角文字を半角に変換
    text = text.replace('：', ':').replace('，', ',')
    
    return text

def extract_json_from_text(text: str) -> Optional[str]:
    """
    テキストからJSON部分を抽出する
    """
    if not isinstance(text, str):
        return None
    
    # JSONブロックを探す（コードブロック内も含む）
    json_patterns = [
        r'```json\n(.*?)\n```',
        r'```\n(\{.*?\})\n```',
        r'(\{.*?\})',
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()
    
    return text.strip()

def safe_parse_json(text: str, fallback_value: Any = None) -> Any:
    """
    安全にJSONをパースする
    - 複数の方法でパースを試行
    - 失敗時はフォールバック値を返す
    """
    if not isinstance(text, str):
        logger.warning(f"JSONパース: 文字列以外の型を受信: {type(text)}")
        return fallback_value
    
    original_text = text
    
    try:
        # 1. 直接JSONパース
        return json.loads(text)
    except (json.JSONDecodeError, TypeError) as e:
        logger.debug(f"直接JSONパース失敗: {e}")
    
    try:
        # 2. テキストクリーニング後にJSONパース
        cleaned_text = clean_json_string(text)
        return json.loads(cleaned_text)
    except (json.JSONDecodeError, TypeError) as e:
        logger.debug(f"クリーニング後JSONパース失敗: {e}")
    
    try:
        # 3. JSON部分を抽出してパース
        json_text = extract_json_from_text(text)
        if json_text:
            cleaned_json = clean_json_string(json_text)
            return json.loads(cleaned_json)
    except (json.JSONDecodeError, TypeError) as e:
        logger.debug(f"抽出後JSONパース失敗: {e}")
    
    try:
        # 4. ast.literal_evalを使用
        return ast.literal_eval(text)
    except (ValueError, SyntaxError, TypeError) as e:
        logger.debug(f"ast.literal_eval失敗: {e}")
    
    # 5. 辞書形式の文字列を解析する最後の試み
    try:
        # 簡単な辞書パターンをチェック
        if text.strip().startswith('{') and text.strip().endswith('}'):
            # 簡単な正規表現で key: value ペアを抽出
            result = {}
            pattern = r'"([^"]+)":\s*"([^"]*)"'
            matches = re.findall(pattern, text)
            for key, value in matches:
                result[key] = value
            
            # 数値パターンもチェック
            number_pattern = r'"([^"]+)":\s*([0-9.]+)'
            number_matches = re.findall(number_pattern, text)
            for key, value in number_matches:
                try:
                    result[key] = float(value) if '.' in value else int(value)
                except ValueError:
                    result[key] = value
            
            if result:
                logger.info(f"正規表現によるJSONパース成功")
                return result
    except Exception as e:
        logger.debug(f"正規表現パース失敗: {e}")
    
    logger.error(f"全てのJSONパース方法が失敗しました。元のテキスト: {original_text[:200]}...")
    return fallback_value

def parse_llm_response(response_text: str, expected_keys: Optional[list] = None) -> Dict[str, Any]:
    """
    LLMからの応答を安全にパースし、期待されるキーが含まれているかチェックする
    """
    if not isinstance(response_text, str):
        logger.error(f"LLM応答パース: 文字列以外の型: {type(response_text)}")
        return {}
    
    parsed_data = safe_parse_json(response_text, {})
    
    if not isinstance(parsed_data, dict):
        logger.warning(f"LLM応答パース: 辞書以外の型を取得: {type(parsed_data)}")
        return {}
    
    # 期待されるキーがあるかチェック
    if expected_keys:
        missing_keys = [key for key in expected_keys if key not in parsed_data]
        if missing_keys:
            logger.warning(f"LLM応答パース: 期待されるキーが不足: {missing_keys}")
    
    return parsed_data