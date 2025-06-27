# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a hybrid AI-powered financial analysis system consisting of:
- **Backend**: Python multi-agent system using LangGraph for US stock investment analysis (FastAPI)
- **Frontend**: Next.js 15 web application with conversational AI interface (Pure UI + Data Storage)
- **Integration**: Frontend connects to backend via REST API for all financial analysis
- **Purpose**: Educational/research-only financial analysis tool optimized for US stock markets

## Common Development Commands

### Python Backend (Poetry)
```bash
# Main execution
poetry run python src/main.py --ticker AAPL --show-reasoning

# Development
poetry install                    # Install dependencies
poetry run black src/            # Format code
poetry run flake8 src/           # Lint code
poetry run pytest               # Run tests (none currently exist)

# Web API server
poetry run python src/main.py --ticker AAPL  # Starts FastAPI server on port 8000
```

### Next.js Frontend (in AI-finance-agent/)
```bash
# Development
pnpm dev                    # Start development server with Turbo
pnpm build                  # Run migrations and build for production
pnpm start                  # Start production server

# Code Quality
pnpm lint                   # ESLint + Biome lint with auto-fix
pnpm format                # Format code with Biome

# Database Management
pnpm db:generate           # Generate Drizzle migrations
pnpm db:migrate            # Run database migrations
pnpm db:studio             # Open Drizzle Studio
```

## Architecture Overview

### Multi-Agent System (Backend)
The system uses LangGraph to orchestrate financial analysis through specialized agents:

```
market_data_agent (Data Collection via yfinance)
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

### Key Components
- **Entry Point**: `src/main.py` - CLI interface and FastAPI server
- **Agent State**: TypedDict-based state management with message passing
- **Data Sources**: yfinance for US stock data (free, no API key required)
- **LLM Integration**: Google Gemini (primary) and OpenAI GPT support
- **API Layer**: FastAPI backend with async task processing

### Frontend Architecture (AI-finance-agent/)
- **Next.js 15**: App Router with experimental PPR
- **Database**: PostgreSQL with Drizzle ORM (Chat history only)
- **Backend Integration**: REST API calls to Python FastAPI
- **UI**: Tailwind CSS + shadcn/ui components
- **Role**: Pure UI + Chat storage (no AI processing)

### Integrated Data Flow
```
User Input → Next.js Frontend → FastAPI Backend → Multi-Agent System
    ↑                               ↓
Chat History ← Database ← Streaming Response ← Analysis Results
```

**Key Integration Points:**
- `/api/chat` endpoint forwards all requests to backend
- Real-time streaming via Server-Sent Events
- Chat history stored in PostgreSQL (frontend)
- All financial analysis performed by Python agents

## Environment Configuration

### Backend (.env)
```bash
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash  # Optional, defaults to gemini-1.5-flash
```

### Frontend (AI-finance-agent/.env)
```bash
# Backend connection
BACKEND_URL=http://localhost:8000  # For local development

# Database
POSTGRES_URL=your-database-url
BLOB_READ_WRITE_TOKEN=your-vercel-blob-token

# Optional (legacy, may be removed in future)
OPENAI_API_KEY=your-openai-api-key
FINANCIAL_DATASETS_API_KEY=your-financial-datasets-api-key
LANGCHAIN_API_KEY=your-langsmith-api-key
```

## Development Notes

### Adding New Agents
1. Create agent file in `src/agents/`
2. Follow existing agent patterns with TypedDict state
3. Add to workflow in `src/main.py`:
```python
from src.agents.your_agent import your_agent
workflow.add_node("your_agent", your_agent)
workflow.add_edge("previous_agent", "your_agent")
```

### Data Sources
- **Primary**: yfinance (free, US stock focus)
- **Custom Tools**: `src/tools/api.py` for data retrieval
- **Supported Tickers**: US stocks (AAPL, MSFT, GOOGL, etc.)

### Testing
- **Critical Gap**: No testing framework currently implemented
- **Recommended**: Add pytest for backend, Jest/Vitest for frontend
- **Manual Testing**: Use well-known US tickers like AAPL, MSFT, TSLA

### Code Quality
- **Backend**: Black formatting, Flake8 linting
- **Frontend**: Biome formatting/linting, ESLint integration
- **Always run linting before commits**

### Financial Data Notes
- Free data available for: AAPL, GOOGL, MSFT, NVDA, TSLA (Financial Datasets API)
- yfinance provides comprehensive US market data at no cost
- System optimized for US trading hours and market calendars
- Includes real-time prices, financial statements, options data

### Security Considerations
- **Educational Use Only**: Not for real trading
- **API Keys**: Store in .env files, never commit
- **CORS**: Currently wide-open in development
- **No Authentication**: Frontend has no user management system

## Project Structure

```
/Users/keitosaegusa/yfinance/
├── src/                       # Python Multi-Agent System
│   ├── agents/                # Individual AI agents
│   ├── tools/                 # Data retrieval utilities
│   ├── utils/                 # Logging and system utilities
│   └── main.py                # Entry point and FastAPI server
├── AI-finance-agent/          # Next.js Frontend
│   ├── app/                   # Next.js App Router
│   ├── components/            # React components
│   ├── lib/                   # Database and AI configuration
│   └── package.json           # Frontend dependencies
├── backend/                   # FastAPI Backend
├── docs/                      # Documentation
├── pyproject.toml             # Python dependencies
└── README.md                  # Project documentation
```

## Integration Testing

### Development Setup
1. **Start Backend**: `poetry run python src/main.py --ticker AAPL`
2. **Start Frontend**: `cd AI-finance-agent && pnpm dev`
3. **Test Integration**: Visit `http://localhost:3000` and ask about stocks

### Key Integration Points to Test
- Chat messages reach backend multi-agent system
- Streaming responses work correctly
- Chat history saves properly
- Error handling between frontend/backend

This system demonstrates advanced AI agent orchestration for financial analysis but requires significant hardening for any production use.