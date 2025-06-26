# A株投資エージェントシステム APIドキュメント

## 概要

投資エージェントシステムのAPIエンドポイント一覧と使用方法。
本システムはFastAPIベースのバックエンドと、LangGraphベースのマルチエージェントワークフローを統合した投資分析システムです。

## ベースURL

```
http://localhost:8000
```

## エンドポイント

### エージェント関連 (`/api/agents`)

#### エージェント一覧の取得
```
GET /api/agents/
```

**レスポンス**
```json
[
    {
        "name": "market_data_agent",
        "description": "市場データの収集と前処理",
        "state": "idle",
        "last_run": "2024-03-20T10:00:00Z"
    },
    {
        "name": "technical_analyst_agent",
        "description": "テクニカル分析の実行",
        "state": "running",
        "last_run": "2024-03-20T10:05:00Z"
    }
]
```

#### エージェントの詳細情報取得
```
GET /api/agents/{agent_name}
```

**パラメータ**
- `agent_name`: エージェント名（例：market_data_agent）

**レスポンス**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "name": "market_data_agent",
        "description": "市場データの収集と前処理",
        "state": "completed",
        "last_run": "2024-03-20T10:00:00Z"
    },
    "timestamp": "2024-03-20T10:00:00Z"
}
```

#### エージェントの入力状態取得
```
GET /api/agents/{agent_name}/latest_input
```

#### エージェントの出力状態取得
```
GET /api/agents/{agent_name}/latest_output
```

#### エージェントの推論内容取得
```
GET /api/agents/{agent_name}/reasoning
```

#### エージェントのLLMリクエスト取得
```
GET /api/agents/{agent_name}/latest_llm_request
```

#### エージェントのLLM応答取得
```
GET /api/agents/{agent_name}/latest_llm_response
```

### 分析タスク (`/api/analysis`)

#### 分析タスクの開始
```
POST /api/analysis/start
```

**リクエストボディ**
```json
{
    "ticker": "3350",
    "show_reasoning": true,
    "initial_capital": 100000.0,
    "initial_position": 0
}
```

**レスポンス**
```json
{
    "success": true,
    "message": "分析タスクの開始に成功しました",
    "data": {
        "run_id": "550e8400-e29b-41d4-a716-446655440000",
        "ticker": "3350",
        "status": "running",
        "message": "分析タスクを開始しました",
        "submitted_at": "2024-03-20T10:00:00Z",
        "completed_at": null
    },
    "timestamp": "2024-03-20T10:00:00Z"
}
```

#### 分析タスクの状態取得
```
GET /api/analysis/{run_id}/status
```

**パラメータ**
- `run_id`: 実行ID

**レスポンス**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "run_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "running",
        "start_time": "2024-03-20T10:00:00Z",
        "end_time": null,
        "is_complete": false
    },
    "timestamp": "2024-03-20T10:00:00Z"
}
```

#### 分析結果の取得
```
GET /api/analysis/{run_id}/result
```

**レスポンス**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "run_id": "550e8400-e29b-41d4-a716-446655440000",
        "ticker": "3350",
        "completion_time": "2024-03-20T10:05:00Z",
        "final_decision": {
            "recommendation": "Buy",
            "confidence": 0.85,
            "price_target": 120.5
        },
        "agent_results": {
            "market_data_agent": { /* ... */ },
            "technical_analyst_agent": { /* ... */ },
            "fundamentals_agent": { /* ... */ }
        }
    },
    "timestamp": "2024-03-20T10:05:00Z"
}
```

### 実行履歴 (`/api/runs`)

#### 実行履歴の取得
```
GET /api/runs/
```

**クエリパラメータ**
- `limit`: 取得件数（デフォルト: 10）
- `offset`: オフセット（デフォルト: 0）

#### 実行詳細の取得
```
GET /api/runs/{run_id}
```

### ワークフロー (`/api/workflow`)

#### ワークフロー状態の取得
```
GET /api/workflow/
```

**レスポンス**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "current_runs": [
            {
                "run_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "running",
                "current_agent": "technical_analyst_agent"
            }
        ],
        "agent_states": {
            "market_data_agent": "completed",
            "technical_analyst_agent": "running"
        }
    },
    "timestamp": "2024-03-20T10:00:00Z"
}
```

## エージェント一覧

システムは以下のエージェントで構成されています：

1. **market_data_agent**: 市場データの収集と前処理
2. **technical_analyst_agent**: テクニカル分析の実行
3. **fundamentals_agent**: ファンダメンタル分析の実行
4. **sentiment_agent**: センチメント分析の実行
5. **valuation_agent**: バリュエーション分析の実行
6. **researcher_bull_agent**: 強気の立場からの分析
7. **researcher_bear_agent**: 弱気の立場からの分析
8. **debate_room_agent**: 複数の視点による議論の統合
9. **risk_management_agent**: リスク管理分析
10. **portfolio_management_agent**: ポートフォリオ管理（最終決定）

## ワークフロー

分析プロセスは以下の順序で実行されます：

```
market_data_agent
    ↓ (並列実行)
┌─technical_analyst_agent
├─fundamentals_agent
├─sentiment_agent
└─valuation_agent
    ↓
researcher_bull_agent & researcher_bear_agent
    ↓
debate_room_agent
    ↓
risk_management_agent
    ↓
portfolio_management_agent (最終決定)
```

## エラーレスポンス

全てのエラーは統一されたApiResponse形式で返されます：

### 400 Bad Request
```json
{
    "success": false,
    "message": "リクエストパラメータが無効です",
    "data": null,
    "timestamp": "2024-03-20T10:00:00Z"
}
```

### 404 Not Found
```json
{
    "success": false,
    "message": "リソースが見つかりません",
    "data": null,
    "timestamp": "2024-03-20T10:00:00Z"
}
```

### 500 Internal Server Error
```json
{
    "success": false,
    "message": "内部サーバーエラー",
    "data": {
        "error": "Error processing market data"
    },
    "timestamp": "2024-03-20T10:00:00Z"
}
```

## 認証

現在のバージョンでは認証は実装されていません。

## レート制限

現在のバージョンではレート制限は実装されていません。

## レガシーAPI

後方互換性のために、以下のエンドポイントも利用可能です：

- `/logs/`: 過去のLLM対話ログの取得
- `/runs/`: 詳細な実行履歴・Agent実行情報の取得

## 使用例

### 基本的な分析の実行

1. 分析タスクを開始：
```bash
curl -X POST "http://localhost:8000/api/analysis/start" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "3350",
    "show_reasoning": true,
    "initial_capital": 100000.0,
    "initial_position": 0
  }'
```

2. 状態を確認：
```bash
curl "http://localhost:8000/api/analysis/{run_id}/status"
```

3. 結果を取得：
```bash
curl "http://localhost:8000/api/analysis/{run_id}/result"
```

## 開発・デバッグ用エンドポイント

### ドキュメント
- OpenAPIドキュメント: `/docs`
- ReDocドキュメント: `/redoc`

### APIナビゲーション
- APIセクション概要: `/api`
- ルート情報: `/` 