# A株投資エージェントシステム コンポーネント詳細

## システム概要

本システムはFastAPIベースのWebバックエンドと、LangGraphベースのマルチエージェント投資分析ワークフローを統合したシステムです。

## バックエンド (`/backend`)

### メインアプリケーション (`main.py`)
FastAPIアプリケーションのエントリーポイント
- CORS設定
- ルーター登録（新API + レガシーAPI）
- APIナビゲーション機能

### 状態管理 (`state.py`)
- エージェントの実行状態の管理
- ワークフローの状態追跡
- 実行履歴の保持
- APIステートの統合管理

### データモデル (`schemas.py`)
```python
class LLMInteractionLog(BaseModel):
    """LLMとの対話ログのスキーマ"""
    agent_name: str
    timestamp: datetime
    request_data: Any
    response_data: Any
    run_id: Optional[str]

class AgentExecutionLog(BaseModel):
    """Agentの実行ログ"""
    agent_name: str
    run_id: str
    timestamp_start: datetime
    timestamp_end: datetime
    input_state: Optional[Dict[str, Any]]
    output_state: Optional[Dict[str, Any]]
    reasoning_details: Optional[Any]
    terminal_outputs: List[str]

class RunSummary(BaseModel):
    """ワークフロー実行全体の概要"""
    run_id: str
    start_time: datetime
    end_time: datetime
    agents_executed: List[str]
    status: str
```

### APIモデル (`models/api_models.py`)
```python
class ApiResponse(BaseModel, Generic[T]):
    """統一APIレスポンス形式"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[T] = None
    timestamp: datetime

class StockAnalysisRequest(BaseModel):
    """株式分析リクエストモデル"""
    ticker: str
    show_reasoning: bool = True
    initial_capital: float = 100000.0
    initial_position: int = 0

class AgentInfo(BaseModel):
    """エージェント情報モデル"""
    name: str
    description: str
    state: str = "idle"
    last_run: Optional[datetime] = None
```

### APIルーター (`/routers`)

#### エージェントルーター (`agents.py`)
- `/api/agents/`: エージェント一覧取得
- `/api/agents/{agent_name}`: エージェント詳細情報
- `/api/agents/{agent_name}/latest_input`: 最新入力状態
- `/api/agents/{agent_name}/latest_output`: 最新出力状態
- `/api/agents/{agent_name}/reasoning`: 推論内容
- `/api/agents/{agent_name}/latest_llm_request`: 最新LLMリクエスト
- `/api/agents/{agent_name}/latest_llm_response`: 最新LLM応答

#### 分析ルーター (`analysis.py`)
- `/api/analysis/start`: 分析タスク開始
- `/api/analysis/{run_id}/status`: タスク状態取得
- `/api/analysis/{run_id}/result`: 分析結果取得

#### 実行履歴ルーター (`api_runs.py`)
- `/api/runs/`: 実行履歴一覧
- `/api/runs/{run_id}`: 実行詳細

#### ワークフロールーター (`workflow.py`)
- `/api/workflow/`: ワークフロー状態取得

#### レガシールーター
- `logs.py`: LLM対話ログ管理
- `runs.py`: 詳細実行履歴管理

### サービス層 (`/services`)
- `analysis.py`: 株式分析サービスの実装

### ストレージ (`/storage`)
- `base.py`: 基本ストレージ抽象化
- `memory.py`: インメモリストレージ実装

### ユーティリティ (`/utils`)
- `api_utils.py`: API用ユーティリティ関数
- `context_managers.py`: コンテキストマネージャー

## エージェントシステム (`/src`)

### メインワークフロー (`main.py`)
LangGraphベースのワークフロー定義と実行
- FastAPIサーバーのバックグラウンド起動
- エージェント間のフロー定義
- コマンドライン引数処理

### エージェント (`/agents`)

#### 状態定義 (`state.py`)
```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    data: Annotated[Dict[str, Any], merge_dicts]
    metadata: Annotated[Dict[str, Any], merge_dicts]
```

#### 主要エージェント

**1. Market Data Agent (`market_data.py`)**
```python
def market_data_agent(state: AgentState):
    """
    市場データの収集と前処理
    - 価格履歴の取得
    - 財務指標の取得
    - 市場データの取得
    """
```

**2. Technical Analyst Agent (`technicals.py`)**
```python
def technical_analyst_agent(state: AgentState):
    """
    テクニカル分析の実行
    - テクニカル指標の計算
    - トレンド分析
    - 取引量分析
    """
```

**3. Fundamentals Agent (`fundamentals.py`)**
```python
def fundamentals_agent(state: AgentState):
    """
    ファンダメンタル分析の実行
    - 財務諸表の分析
    - 業績指標の分析
    - 企業価値の評価
    """
```

**4. Valuation Agent (`valuation.py`)**
```python
def valuation_agent(state: AgentState):
    """
    バリュエーション分析の実行
    - 企業価値の評価
    - 比較分析
    - 投資判断のサポート
    """
```

**5. Researcher Bull Agent (`researcher_bull.py`)**
```python
def researcher_bull_agent(state: AgentState):
    """
    強気の立場からの投資分析
    """
```

**6. Researcher Bear Agent (`researcher_bear.py`)**
```python
def researcher_bear_agent(state: AgentState):
    """
    弱気の立場からの投資分析
    """
```

**7. Debate Room Agent (`debate_room.py`)**
```python
def debate_room_agent(state: AgentState):
    """
    複数の視点による議論の統合
    """
```

**8. Risk Management Agent**
```python
def risk_management_agent(state: AgentState):
    """
    リスク管理分析
    """
```

**11. Portfolio Management Agent**
```python
def portfolio_management_agent(state: AgentState):
    """
    ポートフォリオ管理（最終決定）
    """
```

### ツール (`/tools`)

#### データ取得ツール (`api.py`)
```python
def get_price_history(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """価格履歴の取得"""

def get_financial_metrics(ticker: str) -> dict:
    """財務指標の取得"""

def get_market_data(ticker: str) -> dict:
    """市場データの取得"""
```

#### データ分析ツール (`data_analyzer.py`)
```python
def calculate_technical_indicators(data: pd.DataFrame) -> dict:
    """テクニカル指標の計算"""

def analyze_fundamentals(data: dict) -> dict:
    """ファンダメンタル分析の実行"""
```

#### LLM設定 (`openrouter_config.py`)
- OpenRouter APIの設定
- チャット補完機能

### ユーティリティ (`/utils`)

#### ロギング (`logging_config.py`)
```python
def setup_logger(name: str) -> logging.Logger:
    """ロガーの設定"""
```

#### LLMクライアント (`llm_clients.py`)
- LLMサービスとの統合

#### 出力管理
- `output_logger.py`: 出力ログ管理
- `structured_terminal.py`: 構造化ターミナル出力
- `serialization.py`: データシリアライゼーション

## ワークフロー構成

### 実行フロー
```
market_data_agent
    ↓ (並列実行)
┌─technical_analyst_agent
├─fundamentals_agent  
├─sentiment_agent
├─valuation_agent
└─macro_news_agent
    ↓
researcher_bull_agent & researcher_bear_agent
    ↓
debate_room_agent
    ↓
risk_management_agent
    ↓
macro_analyst_agent
    ↓
portfolio_management_agent (最終決定)
```

### データ依存関係
- **Market Data Agent**: 全ての分析の基盤となるデータを提供
- **分析エージェント群**: 並列実行でそれぞれの専門分析を実行
- **Research エージェント**: 分析結果を統合して異なる視点から評価
- **Debate Room**: 複数視点を統合
- **最終決定**: リスク分析→マクロ分析→ポートフォリオ管理

## 技術スタック

### フロントエンド/API
- **FastAPI**: Webフレームワーク
- **Pydantic**: データ検証とシリアライゼーション
- **Uvicorn**: ASGIサーバー

### ワークフロー
- **LangGraph**: エージェントワークフロー管理
- **LangChain**: LLM統合

### データ処理
- **Pandas**: データ分析
- **NumPy**: 数値計算
- **AkShare**: 中国株式データ取得
- **yfinance**: 株式データ取得

### LLM統合
- **OpenAI**: LLMサービス
- **Google Generative AI**: LLMサービス

### 開発ツール
- **Poetry**: 依存関係管理
- **pytest**: テストフレームワーク
- **black**: コードフォーマット

## 改善提案

### パフォーマンス最適化
1. **データキャッシュ**
   ```python
   @lru_cache(maxsize=100)
   def get_price_history(ticker: str, start_date: str, end_date: str):
       pass
   ```

2. **非同期処理**
   ```python
   async def fetch_market_data(ticker: str):
       pass
   ```

3. **バッチ処理**
   ```python
   def batch_process_analysis(tickers: List[str]):
       pass
   ```

### 機能拡張
1. **リアルタイムデータ統合**
2. **高度な分析機能の追加**
3. **レポート生成機能の強化**
4. **WebSocket対応**

### 保守性の向上
1. **テストカバレッジの向上**
2. **ドキュメントの充実**
3. **エラーハンドリングの強化**
4. **モニタリング機能の追加** 