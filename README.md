# US Stock Investment Agent System

AI-driven US stock investment analysis system using yfinance to retrieve stock data and conduct comprehensive analysis through multiple agents.

## Features

- **yfinance Integration**: Retrieve stock prices, financial statements, and company information (optimized for US stocks)
- **Multi-Agent Analysis**: Technical analysis, fundamental analysis, sentiment analysis, etc.
- **FastAPI WebAPI**: RESTful API for analysis task management
- **Real-time Processing**: Asynchronous task execution and status monitoring

## Requirements

- Python 3.9+
- Poetry (dependency management)

## Setup Instructions

### 1. Repository Clone and Dependency Installation

```bash
git clone <repository_url>
cd AI-finance-backend
poetry install
```

### 2. Data Source Configuration

This system uses yfinance to retrieve stock data.
yfinance is free to use and requires no additional API keys.

**Note**: yfinance is primarily optimized for US stocks and provides comprehensive data for:
- US stock exchanges (NYSE, NASDAQ)
- Real-time and historical price data
- Comprehensive financial statements
- Options data and institutional holdings
- Analyst recommendations

### 3. Gemini API Setup (Required)

Used as the LLM analysis engine.

1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set environment variables:

```bash
# Create .env file
cp .env.example .env

# Add to .env file
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Model specification (default: gemini-1.5-flash)
GEMINI_MODEL=gemini-1.5-flash
```

## Usage

### Command Line Execution

```bash
# Basic analysis execution (US stocks)
poetry run python src/main.py --ticker AAPL --show-reasoning

# Technology stocks
poetry run python src/main.py --ticker MSFT --show-reasoning

# Detailed options
poetry run python src/main.py \
  --ticker AAPL \
  --start-date 2024-01-01 \
  --end-date 2024-03-20 \
  --show-reasoning \
  --initial-capital 1000000
```

### Web API Usage

```bash
# Start server (automatically starts on port 8000)
poetry run python src/main.py --ticker AAPL

# Make analysis request from another terminal
curl -X POST "http://localhost:8000/api/analysis/start" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "show_reasoning": true,
    "initial_capital": 1000000.0,
    "initial_position": 0
  }'
```

## API Specification

### Main Endpoints

- **POST /api/analysis/start**: Start analysis task
- **GET /api/analysis/{run_id}/status**: Check task status
- **GET /api/analysis/{run_id}/result**: Get analysis results
- **GET /api/agents/**: List agents
- **GET /api/workflow/**: Workflow status

For details, check Swagger UI at `http://localhost:8000/docs`.

## Agent Architecture

```
market_data_agent (Data Collection)
    ↓ Parallel Execution
┌─ technical_analyst_agent (Technical Analysis)
├─ fundamentals_agent (Fundamental Analysis)  
├─ sentiment_agent (Sentiment Analysis)
└─ valuation_agent (Valuation Analysis)
    ↓ Integration & Discussion
researcher_bull_agent & researcher_bear_agent
    ↓
debate_room_agent (Discussion Integration)
    ↓
risk_management_agent (Risk Management)
    ↓
portfolio_management_agent (Final Investment Decision)
```

## Troubleshooting

### Data Retrieval Errors

```bash
# Check logs
poetry run python src/main.py --ticker AAPL --show-reasoning

# Example error message:
# WARNING: Price history data not found
```

**Solutions**:
1. Verify ticker symbol is correct (use standard US ticker symbols like AAPL, MSFT, GOOGL)
2. Check internet connection
3. Verify yfinance server status (temporary outages possible)
4. Check if markets are open (latest data may not be available during holidays or after hours)

### Supported US Stock Examples

**Technology Stocks**:
- AAPL (Apple Inc.)
- MSFT (Microsoft Corporation)
- GOOGL (Alphabet Inc.)
- AMZN (Amazon.com Inc.)
- META (Meta Platforms Inc.)

**Financial Stocks**:
- JPM (JPMorgan Chase & Co.)
- BAC (Bank of America Corp.)
- WFC (Wells Fargo & Company)

**Market Indices**:
- SPY (SPDR S&P 500 ETF)
- QQQ (Invesco QQQ Trust)

### Dependency Errors

```bash
# Reinstall dependencies
poetry install --no-cache

# Recreate virtual environment
poetry env remove python
poetry install
```

## Development & Extensions

### Adding New Agents

1. Create agent file in `src/agents/`
2. Add to workflow in `src/main.py`:

```python
from src.agents.your_agent import your_agent
workflow.add_node("your_agent", your_agent)
workflow.add_edge("previous_agent", "your_agent")
```

### Adding Custom Data Sources

Implement new data retrieval functions in `src/tools/api.py`. Currently implemented with yfinance for US market focus.

## US Market Features

This system is optimized for US stock markets and provides:

- **Real-time US market data** via yfinance
- **S&P 500 market trend analysis** for overall market sentiment
- **USD-based financial calculations** and reporting
- **US trading hours and market calendar** considerations
- **Comprehensive fundamental data** for US listed companies
- **Options and institutional holdings** data (US stocks only)

## License

[MIT License](LICENSE)

## Support

- Issue reporting: GitHub Issues
- Documentation: `docs/` directory
- API specification: `http://localhost:8000/docs`