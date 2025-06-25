```

backend/
├── __init__.py              # Initializes the backend package
├── main.py                  # FastAPI application instance and core setup
├── dependencies.py          # Dependency injection setup (e.g., for log storage)
├── state.py                 # In-memory state management (`api_state`) for real-time data
├── schemas.py               # Pydantic models for internal data structures (logs, etc.)
├── models/                  # Pydantic models for API requests/responses (`api_models.py`)
├── routers/                 # FastAPI routers defining API endpoints
│   ├── __init__.py
│   ├── agents.py            # Endpoints for `/api/agents/*`
│   ├── analysis.py          # Endpoints for `/api/analysis/*`
│   ├── api_runs.py          # Endpoints for `/api/runs/*` (memory state based)
│   ├── logs.py              # Endpoints for `/logs/*` (log storage based)
│   ├── runs.py              # Endpoints for `/runs/*` (log storage based)
│   └── workflow.py          # Endpoints for `/api/workflow/*`
├── services/                # Business logic services
│   ├── __init__.py
│   └── analysis.py          # Service for executing stock analysis workflow
├── storage/                 # Data storage implementations
│   ├── __init__.py
│   ├── base.py              # Base class/interface for log storage (`BaseLogStorage`)
│   └── memory.py            # In-memory implementation (`InMemoryLogStorage`)
├── utils/                   # Utility functions specific to the backend
│   ├── __init__.py
│   ├── api_utils.py         # API related helpers (serialization, response formatting)
│   └── context_managers.py  # Context managers (e.g., `workflow_run`)
└── README.md                # This documentation file
```
1. システム概要

このバックエンドは、株式分析を行うAIエージェント群の実行と監視を担うWebサーバーです。主な役割は以下の通りです。

    分析タスクの受付: ユーザー（フロントエンド）からの分析リクエストを受け付け、ワークフローを開始します。

    ワークフローの実行管理: 複数のエージェント（データ収集、テクニカル分析、ファンダメンタル分析など）を順番に実行します。

    状態とログの提供: 実行中のプロセスのリアルタイムな状況や、過去の実行履歴をAPI経由で提供します。

2. APIの構造

APIは提供する情報の種類によって、大きく2つの系統に分かれています。
2.1. リアルタイムAPI (/api/*)

「今、何が起きているか？」を素早く知るためのAPI群です。

    データ源: メモリ上のリアルタイム情報 (api_state)

    特徴:

        レスポンスが高速。

        エージェントの最新の状態や、現在実行中のワークフロー情報を提供。

        サーバーを再起動するとデータは消去されます。

        全てのレスポンスは統一形式 (ApiResponse) で返されます。

2.2. 履歴・詳細ログAPI (/logs/*, /runs/*)

「過去の分析で何が起きたか？」を詳細に調べるためのAPI群です。

    データ源: ログストレージ (BaseLogStorage)

    特徴:

        エージェントの実行ステップやLLMとの全対話など、詳細な履歴を提供。

        デバッグや分析プロセスの再現に役立ちます。

        （現在はメモリ保存ですが）将来的にはデータベース等への永続化が可能です。

3. 主要APIエンドポイント早見表
リアルタイム系 (/api/*)
HTTPメソッド	エンドポイント	説明
POST	/api/analysis/start	**【起点】**新しい株式分析タスクを開始する。
GET	/api/workflow/status	現在実行中のワークフローの全体的な進捗状況を確認する。
GET	/api/agents/	全エージェントの現在のステータス（実行中、完了など）を一覧する。
GET	/api/agents/{agent_name}	特定エージェントの最新情報を取得する。
GET	/api/agents/{agent_name}/latest_llm_request	特定エージェントが最後にLLMに送ったリクエスト内容を見る。
GET	/api/agents/{agent_name}/latest_llm_response	特定エージェントが最後にLLMから受け取ったレスポンス内容を見る。
GET	/api/runs/	メモリに記録されている簡易的な実行履歴の一覧を取得する。
履歴・詳細ログ系 (/logs/*, /runs/*)
HTTPメソッド	エンドポイント	説明
GET	/runs/	**【履歴の起点】**過去の全実行履歴のサマリーを一覧する。
GET	/runs/{run_id}	特定の実行（run_id）のサマリー情報を取得する。
GET	/runs/{run_id}/agents	特定の実行で動作した全エージェントの実行時間などを一覧する。
GET	/runs/{run_id}/agents/{agent_name}	特定の実行における特定エージェントの詳細な分析結果（入出力、結論など）を取得する。
GET	/runs/{run_id}/flow	特定の実行のワークフロー全体図（エージェント間のデータの流れ）を取得する。
GET	/logs/	（デバッグ用）LLMとの全対話ログを検索・取得する。
4. ログ記録の仕組み

このシステムの詳細なログは、Pythonのデコレータ機能によって自動的に記録されます。

    @agent_endpoint: エージェントのメイン関数に付けます。エージェントの開始/終了、入出力などを記録します。

    @log_llm_interaction: LLMを呼び出す関数に付けます。LLMとのリクエスト/レスポンスを全て記録します。

    開発者向け: 新しいエージェントを実装する際は、これらのデコレータを適切な関数に適用することで、本バックエンドの監視・ロギング機能と自動的に連携できます。
    