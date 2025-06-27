import os
import time
import logging
from typing import Optional


def setup_logger(name: str, log_dir: Optional[str] = None) -> logging.Logger:
    """統一されたログ設定を行う

    引数:
        name: ロガーの名前
        log_dir: ログファイルのディレクトリ（Noneの場合はデフォルトのlogsディレクトリを使用）
    戻り値:
        設定済みのloggerインスタンス
    """
    # ルートロガーのログレベルをDEBUGに設定
    logging.getLogger().setLevel(logging.DEBUG)

    # ロガーの取得または作成
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # このロガーではDEBUG以上を記録
    logger.propagate = False  # 親ロガーへのログ伝播を防ぐ

    # 既にハンドラがある場合は追加しない
    if logger.handlers:
        return logger

    # コンソール用ハンドラを作成
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # フォーマッタを作成
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # ファイル用ハンドラを作成
    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{name}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # ファイルにはDEBUG以上を記録
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# 事前定義されたアイコン
SUCCESS_ICON = "✓"
ERROR_ICON = "✗"
WAIT_ICON = "🔄"
