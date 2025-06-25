# A株投資エージェントシステム

## プロジェクト概要

A株市場の包括的な分析と投資判断を支援するAI駆動型投資システム。
FastAPIベースのWebバックエンドとLangGraphベースのマルチエージェントワークフローを統合し、
複数の専門エージェントによる分散投資分析を実現します。

## プロジェクト構造

```
AI-finance-backend/
├── backend/                     # FastAPIバックエンド
│   ├── main.py                 # APIエンドポイント・CORS設定
│   ├── state.py                # 状態管理・API状態統合
│   ├── schemas.py              # データモデル定義
│   ├── dependencies.py         # 依存関係管理
│   ├── models/                 # APIモデル
│   │   └── api_models.py       # 統一APIレスポンス形式
│   ├── routers/                # APIルーター
│   │   ├── agents.py           # エージェント関連API
│   │   ├── analysis.py         # 分析タスクAPI
│   │   ├── workflow.py         # ワークフローAPI
│   │   ├── api_runs.py         # 実行履歴API
│   │   ├── logs.py             # レガシーログAPI
│   │   └── runs.py             # レガシー実行API
│   ├── services/               # サービス層
│   │   └── analysis.py         # 株式分析サービス
│   ├── storage/                # ストレージ層
│   │   ├── base.py             # 基本ストレージ抽象化
│   │   └── memory.py           # インメモリストレージ
│   └── utils/                  # ユーティリティ
│       ├── api_utils.py        # API用ユーティリティ
│       └── context_managers.py # コンテキストマネージャー
│
├── src/                        # エージェントシステム
│   ├── main.py                 # メインワークフロー・エントリーポイント
│   ├── agents/                 # エージェント実装
│   │   ├── state.py            # AgentState定義
│   │   ├── market_data.py      # 市場データエージェント
│   │   ├── technicals.py       # テクニカル分析エージェント
│   │   ├── fundamentals.py     # ファンダメンタル分析エージェント
│   │   ├── valuation.py        # バリュエーション分析エージェント
│   │   ├── researcher_bull.py  # 強気分析エージェント
│   │   ├── researcher_bear.py  # 弱気分析エージェント
│   │   └── debate_room.py      # 議論統合エージェント
│   ├── tools/                  # ツール実装
│   │   ├── api.py              # データ取得API
│   │   ├── data_analyzer.py    # データ分析ツール
│   │   └── openrouter_config.py # LLM設定
│   ├── utils/                  # ユーティリティ
│   │   ├── llm_clients.py      # LLMクライアント
│   │   ├── logging_config.py   # ロギング設定
│   │   ├── output_logger.py    # 出力ログ管理
│   │   └── structured_terminal.py # 構造化出力
│   └── data/                   # データファイル
│       └── macro_summary.json  # マクロ経済データ
│
├── docs/                       # ドキュメント
│   ├── API.md                  # APIドキュメント
│   ├── COMPONENTS.md           # コンポーネント詳細
│   └── PROJECT.md              # プロジェクト概要（本ファイル）
│
├── pyproject.toml              # Poetryプロジェクト設定
└── poetry.lock                 # 依存関係ロック
```

## システムアーキテクチャ

### 全体構成
```
Web API (FastAPI)
    ↓
State Management (APIステート)
    ↓
LangGraph Workflow
    ↓
Multi-Agent System (12エージェント)
    ↓
Data Sources & LLM Services
```

### エージェント構成
```
market_data_agent (データ収集)
    ↓ 並列実行
┌─ technical_analyst_agent (テクニカル分析)
├─ fundamentals_agent (ファンダメンタル分析)
├─ sentiment_agent (センチメント分析)
├─ valuation_agent (バリュエーション分析)
└─ macro_news_agent (マクロニュース分析)
    ↓ 統合・議論
researcher_bull_agent & researcher_bear_agent
    ↓
debate_room_agent (議論統合)
    ↓
risk_management_agent (リスク管理)
    ↓
macro_analyst_agent (マクロ分析)
    ↓
portfolio_management_agent (最終投資判断)
```

## 主要機能

### 1. 市場データ収集・分析
- **データソース**: AkShare、yfinance
- **対象**: A株市場、価格履歴、財務データ
- **処理**: リアルタイム取得、前処理、正規化

### 2. マルチエージェント分析システム
#### 専門分析エージェント
- **Technical Analyst**: テクニカル指標、トレンド分析
- **Fundamentals Analyst**: 財務諸表、業績分析
- **Sentiment Analyst**: 市場センチメント、ニュース分析
- **Valuation Analyst**: 企業価値評価、比較分析

#### 統合・意思決定エージェント
- **Researcher Bull/Bear**: 異なる視点からの分析
- **Debate Room**: 複数視点の統合・議論
- **Risk Management**: リスク評価・管理
- **Portfolio Management**: 最終投資判断

### 3. Web API
#### 新API (`/api/`)
- **統一レスポンス形式**: `ApiResponse<T>`
- **エージェント管理**: 状態監視、データ取得
- **分析タスク管理**: 非同期実行、状態追跡
- **実行履歴**: 詳細ログ、結果取得

#### レガシーAPI
- **後方互換性**: 既存システムとの統合
- **ログ管理**: LLM対話履歴
- **実行詳細**: 詳細な実行情報

## 技術スタック

### フロントエンド・API
- **FastAPI 0.115.12**: モダンWebフレームワーク
- **Pydantic**: データ検証・シリアライゼーション
- **Uvicorn 0.34.0**: 高性能ASGIサーバー

### AI・ワークフロー
- **LangGraph 0.2.56**: エージェントワークフロー管理
- **LangChain 0.3.0**: LLM統合フレームワーク
- **OpenAI 1.12.0**: GPTモデル統合
- **Google Generative AI 0.3.0**: Geminiモデル統合

### データ処理・分析
- **Pandas 2.1.0+**: データ分析・処理
- **NumPy 1.24.0+**: 数値計算
- **AkShare 1.11.22+**: 中国株式データ
- **yfinance 0.2.51+**: 国際株式データ

### 開発・運用
- **Poetry**: 依存関係管理
- **Python 3.9+**: プログラミング言語
- **pytest**: テストフレームワーク
- **black**: コードフォーマット

## データフロー

### 1. データ取得フェーズ
```python
# Market Data Agent が基盤データを収集
{
    "ticker": "3350",
    "price_history": DataFrame,
    "financial_metrics": Dict,
    "market_data": Dict
}
```

### 2. 並列分析フェーズ
```python
# 5つのエージェントが並列実行
technical_analysis = {
    "indicators": {...},
    "trends": {...},
    "signals": {...}
}

fundamental_analysis = {
    "ratios": {...},
    "growth": {...},
    "quality": {...}
}
```

### 3. 統合・議論フェーズ
```python
# Bull/Bear エージェントの対立分析
bull_perspective = {
    "strengths": [...],
    "opportunities": [...],
    "recommendation": "BUY"
}

bear_perspective = {
    "weaknesses": [...],
    "threats": [...], 
    "recommendation": "SELL"
}
```

### 4. 最終判断フェーズ
```python
# Portfolio Management Agent の最終決定
final_decision = {
    "action": "BUY|SELL|HOLD",
    "confidence": 0.85,
    "position_size": 0.1,
    "risk_level": "MODERATE",
    "reasoning": "..."
}
```

## セットアップと実行

### 1. 環境構築
```bash
# プロジェクトクローン
git clone <repository_url>
cd AI-finance-backend

# 依存関係インストール
poetry install

# 環境変数設定
cp .env.example .env
# 必要なAPIキーを設定
```

### 2. システム起動
```bash
# メインシステム起動（バックエンド+ワークフロー）
poetry run python src/main.py --ticker 3350 --show-reasoning

# 分析実行例
poetry run python src/main.py \
  --ticker 3350 \
  --start-date 2024-01-01 \
  --end-date 2024-03-20 \
  --show-reasoning \
  --num-of-news 10
```

### 3. API使用例
```bash
# 分析タスク開始
curl -X POST "http://localhost:8000/api/analysis/start" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "3350",
    "show_reasoning": true,
    "initial_capital": 100000.0
  }'

# 結果確認
curl "http://localhost:8000/api/analysis/{run_id}/result"
```

## 設定・カスタマイズ

### 1. エージェント設定
```python
# src/main.py でエージェント追加
workflow.add_node("custom_agent", custom_agent_function)
workflow.add_edge("market_data_agent", "custom_agent")
```

### 2. データソース追加
```python
# src/tools/api.py でデータ取得関数追加
def get_custom_data(ticker: str) -> dict:
    # カスタムデータ取得ロジック
    return data
```

### 3. API拡張
```python
# backend/routers/ に新しいルーター追加
@router.get("/custom")
async def custom_endpoint():
    return {"status": "ok"}
```

## 監視・デバッグ

### 1. ログ確認
- **構造化ログ**: JSON形式での出力
- **エージェント別ログ**: 各エージェントの実行詳細
- **LLM対話ログ**: リクエスト・レスポンス記録

### 2. API監視
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **状態確認**: `/api/workflow/`

### 3. デバッグモード
```bash
# 詳細推論表示
python src/main.py --ticker 3350 --show-reasoning

# サマリーレポート表示
python src/main.py --ticker 3350 --show-summary
```

## 性能・スケーラビリティ

### 現在の制限
- **並行実行**: 5エージェント並列（technical, fundamentals, sentiment, valuation, macro_news）
- **メモリ使用**: インメモリストレージ
- **レート制限**: なし（外部APIの制限に依存）

### 改善案
1. **データベース統合**: PostgreSQL、Redis導入
2. **キャッシュ戦略**: データキャッシュ、結果キャッシュ
3. **非同期処理**: 全エージェントの非同期化
4. **分散実行**: Celery、RQによる分散処理

## セキュリティ

### 現在の状況
- **認証**: 未実装
- **CORS**: 全オリジン許可
- **レート制限**: 未実装

### セキュリティ強化案
1. **認証・認可**: JWT、APIキー
2. **CORS制限**: 本番環境での適切な設定
3. **レート制限**: IP・ユーザーベース制限
4. **データ保護**: 暗号化、アクセス制御

## 拡張性・将来計画

### 短期計画
1. **WebSocket対応**: リアルタイム状態更新
2. **バッチ処理**: 複数銘柄の一括分析
3. **レポート生成**: PDF、Excel出力

### 中期計画
1. **ユーザー管理**: マルチユーザー対応
2. **ポートフォリオ管理**: 複数ポートフォリオ
3. **リアルタイム取引**: 取引所API統合

### 長期計画
1. **機械学習統合**: 独自予測モデル
2. **国際市場対応**: 米国株、日本株
3. **モバイルアプリ**: React Native、Flutter

## コントリビューション

### 開発フロー
1. **Issue作成**: 機能要望、バグ報告
2. **ブランチ作成**: `feature/`, `bugfix/`
3. **テスト実行**: `poetry run pytest`
4. **コード品質**: `poetry run black`, `poetry run flake8`
5. **プルリクエスト**: レビュー後マージ

### 開発ガイドライン
- **コードスタイル**: Black、PEP8準拠
- **ドキュメント**: 関数・クラスのdocstring必須
- **テスト**: 新機能には対応するテスト追加
- **ログ**: 適切なログレベルでの出力 