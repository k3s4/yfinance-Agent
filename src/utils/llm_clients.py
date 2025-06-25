import os
import time
import backoff
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from src.utils.logging_config import setup_logger, SUCCESS_ICON, ERROR_ICON, WAIT_ICON

# ログ記録を設定
logger = setup_logger('llm_clients')


class LLMClient(ABC):
    """LLMクライアントの抽象基底クラス"""

    @abstractmethod
    def get_completion(self, messages, **kwargs):
        """モデルの回答を取得する"""
        pass


class GeminiClient(LLMClient):
    """Google Gemini API クライアント"""

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        if not self.api_key:
            logger.error(f"{ERROR_ICON} GEMINI_API_KEY 環境変数が見つかりません")
            raise ValueError(
                "GEMINI_API_KEYが環境変数に見つかりません")

        # Geminiクライアントを初期化
        self.client = genai.Client(api_key=self.api_key)
        logger.info(f"{SUCCESS_ICON} Geminiクライアントの初期化に成功しました")

    @backoff.on_exception(
        backoff.expo,
        (Exception),
        max_tries=5,
        max_time=300,
        giveup=lambda e: "AFC is enabled" not in str(e)
    )
    def generate_content_with_retry(self, contents, config=None):
        """リトライメカニズム付きのコンテンツ生成関数"""
        try:
            logger.info(f"{WAIT_ICON} Gemini APIを呼び出しています...")
            logger.debug(f"リクエスト内容: {contents}")
            logger.debug(f"リクエスト設定: {config}")

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config
            )

            logger.info(f"{SUCCESS_ICON} APIの呼び出しに成功しました")
            logger.debug(f"レスポンス内容: {response.text[:500]}...")
            return response
        except Exception as e:
            error_msg = str(e)
            if "location" in error_msg.lower():
                logger.info(
                    f"\033[91m❗ Gemini APIの地理的位置制限エラー: アメリカのノードを持つVPNを使用して再試行してください\033[0m")
                logger.error(f"詳細なエラー: {error_msg}")
            elif "AFC is enabled" in error_msg:
                logger.warning(
                    f"{ERROR_ICON} API制限に抵触しました、リトライを待機しています... エラー: {error_msg}")
                time.sleep(5)
            else:
                logger.error(f"{ERROR_ICON} APIの呼び出しに失敗しました: {error_msg}")
            raise e

    def get_completion(self, messages, max_retries=3, initial_retry_delay=1, **kwargs):
        """チャットの完了結果を取得する、リトライロジックを含む"""
        try:
            logger.info(f"{WAIT_ICON} Geminiモデルを使用: {self.model}")
            logger.debug(f"メッセージ内容: {messages}")

            for attempt in range(max_retries):
                try:
                    # メッセージ形式を変換
                    prompt = ""
                    system_instruction = None

                    for message in messages:
                        role = message["role"]
                        content = message["content"]
                        if role == "system":
                            system_instruction = content
                        elif role == "user":
                            prompt += f"User: {content}\n"
                        elif role == "assistant":
                            prompt += f"Assistant: {content}\n"

                    # 設定を準備
                    config = {}
                    if system_instruction:
                        config['system_instruction'] = system_instruction

                    # APIを呼び出し
                    response = self.generate_content_with_retry(
                        contents=prompt.strip(),
                        config=config
                    )

                    if response is None:
                        logger.warning(
                            f"{ERROR_ICON} 試行 {attempt + 1}/{max_retries}: APIが空の値を返しました")
                        if attempt < max_retries - 1:
                            retry_delay = initial_retry_delay * (2 ** attempt)
                            logger.info(
                                f"{WAIT_ICON} {retry_delay}秒待機して再試行します...")
                            time.sleep(retry_delay)
                            continue
                        return None

                    logger.debug(f"APIの生のレスポンス: {response.text}")
                    logger.info(f"{SUCCESS_ICON} Geminiのレスポンス取得に成功しました")

                    # テキスト内容を直接返す
                    return response.text

                except Exception as e:
                    logger.error(
                        f"{ERROR_ICON} 試行 {attempt + 1}/{max_retries} 失敗: {str(e)}")
                    if attempt < max_retries - 1:
                        retry_delay = initial_retry_delay * (2 ** attempt)
                        logger.info(f"{WAIT_ICON} {retry_delay}秒待機して再試行します...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"{ERROR_ICON} 最終的なエラー: {str(e)}")
                        return None

        except Exception as e:
            logger.error(f"{ERROR_ICON} get_completionでエラーが発生しました: {str(e)}")
            return None


class OpenAICompatibleClient(LLMClient):
    """OpenAI互換APIクライアント"""

    def __init__(self, api_key=None, base_url=None, model=None):
        self.api_key = api_key or os.getenv("OPENAI_COMPATIBLE_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_COMPATIBLE_BASE_URL")
        self.model = model or os.getenv("OPENAI_COMPATIBLE_MODEL")

        if not self.api_key:
            logger.error(f"{ERROR_ICON} OPENAI_COMPATIBLE_API_KEY 環境変数が見つかりません")
            raise ValueError(
                "OPENAI_COMPATIBLE_API_KEYが環境変数に見つかりません")

        if not self.base_url:
            logger.error(f"{ERROR_ICON} OPENAI_COMPATIBLE_BASE_URL 環境変数が見つかりません")
            raise ValueError(
                "OPENAI_COMPATIBLE_BASE_URLが環境変数に見つかりません")

        if not self.model:
            logger.error(f"{ERROR_ICON} OPENAI_COMPATIBLE_MODEL 環境変数が見つかりません")
            raise ValueError(
                "OPENAI_COMPATIBLE_MODELが環境変数に見つかりません")

        # OpenAIクライアントを初期化
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        logger.info(f"{SUCCESS_ICON} OpenAI互換クライアントの初期化に成功しました")

    @backoff.on_exception(
        backoff.expo,
        (Exception),
        max_tries=5,
        max_time=300
    )
    def call_api_with_retry(self, messages, stream=False):
        """リトライメカニズム付きのAPI呼び出し関数"""
        try:
            logger.info(f"{WAIT_ICON} OpenAI互換APIを呼び出しています...")
            logger.debug(f"リクエスト内容: {messages}")
            logger.debug(f"モデル: {self.model}, ストリーム: {stream}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=stream
            )

            logger.info(f"{SUCCESS_ICON} APIの呼び出しに成功しました")
            return response
        except Exception as e:
            error_msg = str(e)
            logger.error(f"{ERROR_ICON} APIの呼び出しに失敗しました: {error_msg}")
            raise e

    def get_completion(self, messages, max_retries=3, initial_retry_delay=1, **kwargs):
        """チャットの完了結果を取得する、リトライロジックを含む"""
        try:
            logger.info(f"{WAIT_ICON} OpenAI互換モデルを使用: {self.model}")
            logger.debug(f"メッセージ内容: {messages}")

            for attempt in range(max_retries):
                try:
                    # APIを呼び出し
                    response = self.call_api_with_retry(messages)

                    if response is None:
                        logger.warning(
                            f"{ERROR_ICON} 試行 {attempt + 1}/{max_retries}: APIが空の値を返しました")
                        if attempt < max_retries - 1:
                            retry_delay = initial_retry_delay * (2 ** attempt)
                            logger.info(
                                f"{WAIT_ICON} {retry_delay}秒待機して再試行します...")
                            time.sleep(retry_delay)
                            continue
                        return None

                    # デバッグ情報を出力
                    content = response.choices[0].message.content
                    logger.debug(f"APIの生のレスポンス: {content[:500]}...")
                    logger.info(f"{SUCCESS_ICON} OpenAI互換のレスポンス取得に成功しました")

                    # テキスト内容を直接返す
                    return content

                except Exception as e:
                    logger.error(
                        f"{ERROR_ICON} 試行 {attempt + 1}/{max_retries} 失敗: {str(e)}")
                    if attempt < max_retries - 1:
                        retry_delay = initial_retry_delay * (2 ** attempt)
                        logger.info(f"{WAIT_ICON} {retry_delay}秒待機して再試行します...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"{ERROR_ICON} 最終的なエラー: {str(e)}")
                        return None

        except Exception as e:
            logger.error(f"{ERROR_ICON} get_completionでエラーが発生しました: {str(e)}")
            return None


class LLMClientFactory:
    """LLMクライアントファクトリークラス"""

    @staticmethod
    def create_client(client_type="auto", **kwargs):
        """
        LLMクライアントを作成する

        Args:
            client_type: クライアントタイプ ("auto", "gemini", "openai_compatible")
            **kwargs: 特定のクライアントの設定パラメータ

        Returns:
            LLMClient: インスタンス化されたLLMクライアント
        """
        # "auto"に設定されている場合、利用可能なクライアントを自動で検出
        if client_type == "auto":
            # OpenAI互換API関連の設定が提供されているかチェック
            if (kwargs.get("api_key") and kwargs.get("base_url") and kwargs.get("model")) or \
               (os.getenv("OPENAI_COMPATIBLE_API_KEY") and os.getenv("OPENAI_COMPATIBLE_BASE_URL") and os.getenv("OPENAI_COMPATIBLE_MODEL")):
                client_type = "openai_compatible"
                logger.info(f"{WAIT_ICON} 自動的にOpenAI互換APIを選択しました")
            else:
                client_type = "gemini"
                logger.info(f"{WAIT_ICON} 自動的にGemini APIを選択しました")

        if client_type == "gemini":
            return GeminiClient(
                api_key=kwargs.get("api_key"),
                model=kwargs.get("model")
            )
        elif client_type == "openai_compatible":
            return OpenAICompatibleClient(
                api_key=kwargs.get("api_key"),
                base_url=kwargs.get("base_url"),
                model=kwargs.get("model")
            )
        else:
            raise ValueError(f"サポートされていないクライアントタイプです: {client_type}")
        