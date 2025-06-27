from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List

from .routers import logs, runs
# 新しいルーターのインポート
from .routers import agents, workflow, analysis, api_runs, chat

# FastAPIアプリケーションのインスタンスを作成
app = FastAPI(
    title="A株投資エージェント - バックエンド",
    description="エージェントワークフロー内のLLMインタラクションを監視するためのAPI",
    version="0.1.0"
)

# CORS（クロスオリジンリソース共有）の設定
# この例ではすべてのオリジンからのリクエストを許可
# 本番環境では適宜オリジンを制限してください
origins = ["*"]  # すべてのオリジンを許可

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # 全HTTPメソッドを許可
    allow_headers=["*"],  # 全HTTPヘッダーを許可
)

# 旧APIルーターを登録
app.include_router(logs.router)
app.include_router(runs.router)

# 新APIルーターを登録
app.include_router(agents.router)
app.include_router(workflow.router)
app.include_router(analysis.router)
app.include_router(api_runs.router)
app.include_router(chat.router)

# ルートエンドポイント：APIナビゲーション情報を提供
@app.get("/")
def read_root():
    return {
        "message": "A株投資エージェントのバックエンドAPIへようこそ！詳細は /docs をご覧ください。",
        "api_navigation": {
            "ドキュメント": "/docs",
            "新API": {
                "説明": "標準化されたApiResponse形式を採用した新しいAPI群",
                "エンドポイント": {
                    "Agent": "/api/agents/",
                    "分析": "/api/analysis/",
                    "実行": "/api/runs/",
                    "ワークフロー": "/api/workflow/",
                    "チャット": "/api/chat/"
                }
            },
            "旧API": {
                "説明": "後方互換のために残された旧式API",
                "エンドポイント": {
                    "ログ": "/logs/",
                    "実行履歴": "/runs/"
                }
            }
        }
    }

# APIナビゲーション（/api）
@app.get("/api")
def api_navigation():
    """APIの構成情報を提供するナビゲーションエンドポイント"""
    return {
        "message": "A株投資エージェントのAPIナビゲーション",
        "api_sections": {
            "/api/agents": "各Agentの状態・データを取得",
            "/api/analysis": "株式分析タスクの実行および結果取得",
            "/api/runs": "実行中または過去のランの情報（api_stateベース）",
            "/api/workflow": "現在のワークフロー状態の取得",
            "/api/chat": "リアルタイムチャット（マルチエージェント統合）"
        },
        "legacy_api": {
            "/logs": "過去のLLM対話ログの取得",
            "/runs": "詳細な実行履歴・Agent実行情報の取得（BaseLogStorageベース）"
        },
        "documentation": {
            "OpenAPIドキュメント": "/docs",
            "ReDocドキュメント": "/redoc"
        }
    }
