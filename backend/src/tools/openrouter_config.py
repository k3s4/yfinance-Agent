import os
import time
from google import genai
from dotenv import load_dotenv
from dataclasses import dataclass
import backoff
from ..utils.logging_config import setup_logger, SUCCESS_ICON, ERROR_ICON, WAIT_ICON
from ..utils.llm_clients import LLMClientFactory

# ログ設定
logger = setup_logger('api_calls')


@dataclass
class ChatMessage:
    content: str


@dataclass
class ChatChoice:
    message: ChatMessage


@dataclass
class ChatCompletion:
    choices: list[ChatChoice]


# プロジェクトのルートディレクトリを取得
project_root = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')

# 環境変数の読み込み
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
    logger.info(f"{SUCCESS_ICON} 環境変数を読み込みました: {env_path}")
else:
    logger.warning(f"{ERROR_ICON} 環境変数ファイルが見つかりません: {env_path}")

# 環境変数の検証
api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL")

if not api_key:
    logger.error(f"{ERROR_ICON} GEMINI_API_KEY が環境変数に見つかりません")
    raise ValueError("GEMINI_API_KEY not found in environment variables")
if not model:
    model = "gemini-1.5-flash"
    logger.info(f"{WAIT_ICON} デフォルトモデルを使用します: {model}")

# Gemini クライアントの初期化
client = genai.Client(api_key=api_key)
logger.info(f"{SUCCESS_ICON} Gemini クライアントが正常に初期化されました")


@backoff.on_exception(
    backoff.expo,
    (Exception),
    max_tries=5,
    max_time=300,
    giveup=lambda e: "AFC is enabled" not in str(e)
)
def generate_content_with_retry(model, contents, config=None):
    """再試行付きで Gemini API を呼び出してコンテンツ生成を行う"""
    try:
        logger.info(f"{WAIT_ICON} Gemini API を呼び出し中...")
        logger.debug(f"リクエスト内容: {contents}")
        logger.debug(f"リクエスト設定: {config}")

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )

        logger.info(f"{SUCCESS_ICON} API 呼び出し成功")
        logger.debug(f"応答内容: {response.text[:500]}...")
        return response
    except Exception as e:
        error_msg = str(e)
        if "AFC is enabled" in error_msg:
            logger.warning(f"{ERROR_ICON} API制限により一時停止中。再試行します... エラー: {error_msg}")
            time.sleep(5)
        else:
            logger.error(f"{ERROR_ICON} API 呼び出しに失敗しました: {error_msg}")
        raise e


def get_chat_completion(messages, model=None, max_retries=3, initial_retry_delay=1,
                        client_type="auto", api_key=None, base_url=None):
    """
    チャット形式での回答を取得（自動リトライ付き）

    引数:
        messages: OpenAI 形式のメッセージリスト
        model: 使用するモデル名（任意）
        max_retries: 最大リトライ回数
        initial_retry_delay: 初回リトライの待機時間（秒）
        client_type: クライアントの種類 ("auto", "gemini", "openai_compatible")
        api_key: APIキー（任意。OpenAI互換APIのみ）
        base_url: APIのベースURL（任意。OpenAI互換APIのみ）

    戻り値:
        str: モデルからの回答。エラー時は None を返す
    """
    try:
        # クライアントを作成
        client = LLMClientFactory.create_client(
            client_type=client_type,
            api_key=api_key,
            base_url=base_url,
            model=model
        )

        # 回答を取得
        return client.get_completion(
            messages=messages,
            max_retries=max_retries,
            initial_retry_delay=initial_retry_delay
        )
    except Exception as e:
        logger.error(f"{ERROR_ICON} get_chat_completion 中にエラーが発生しました: {str(e)}")
        return None
