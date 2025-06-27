# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Financial Agent built with Next.js 15, featuring a chat interface for financial research and stock analysis. The application uses generative UI to display stock prices, fundamentals, and financial data through conversational interactions.

**Key Technologies:**
- Next.js 15 with App Router and experimental PPR (Partial Prerendering)
- TypeScript with strict mode
- Drizzle ORM with PostgreSQL database
- AI SDK by Vercel for LLM integration
- Tailwind CSS + shadcn/ui components
- Biome for linting and formatting
- Financial Datasets API for market data

## Common Development Commands

```bash
# Development
pnpm dev                    # Start development server with Turbo
pnpm build                  # Run migrations and build for production
pnpm start                  # Start production server

# Code Quality
pnpm lint                   # ESLint + Biome lint with auto-fix
pnpm lint:fix              # Fix linting issues
pnpm format                # Format code with Biome

# Database Management
pnpm db:generate           # Generate Drizzle migrations
pnpm db:migrate            # Run database migrations
pnpm db:studio             # Open Drizzle Studio
pnpm db:push               # Push schema changes to database
pnpm db:pull               # Pull schema from database
```

## Architecture Overview

### App Structure (Next.js App Router)
- `app/(chat)/` - Main chat interface with sidebar layout
- `components/` - Reusable React components
- `lib/` - Core utilities, database, and AI configuration

### Database Schema (PostgreSQL + Drizzle)
Key entities:
- `Chat` - Chat sessions with visibility (public/private)
- `Message` - Individual chat messages with JSON content
- `Document` - Document storage with text/code types
- `Suggestion` - AI-generated suggestions for documents

### AI Integration
- **Model Configuration**: `lib/ai/models.ts` defines available OpenAI models
- **Custom Middleware**: `lib/ai/custom-middleware.ts` for AI SDK customization
- **Financial Tools**: Chat API supports specialized financial analysis tools:
  - `getStockPrices`, `getIncomeStatements`, `getBalanceSheets`
  - `getCashFlowStatements`, `getFinancialMetrics`, `searchStocksByFilters`
  - `getNews` for financial news integration
- **System Prompts**: Defined in `lib/ai/prompts.ts`

### API Routes Structure
- `app/(chat)/api/chat/route.ts` - Main chat endpoint with streaming
- `app/(chat)/api/history/route.ts` - Chat history management
- `app/(chat)/api/document/route.ts` - Document management
- `app/(chat)/api/suggestions/route.ts` - AI suggestions
- `app/(chat)/api/files/upload/route.ts` - File upload handling
- Financial data integration via Financial Datasets API

### Component Architecture
- **Chat Components**: `components/chat.tsx`, `components/message.tsx`, `components/messages.tsx`
- **Financial UI**: `components/financials-table.tsx`, `components/stock-screener-table.tsx`
- **Editor Components**: Rich text editing with ProseMirror integration
- **Sidebar**: `components/app-sidebar.tsx`, `components/sidebar-history.tsx`
- **UI System**: shadcn/ui components in `components/ui/`

## Environment Configuration

Required environment variables (see `.env.example`):
- `OPENAI_API_KEY` - OpenAI API access
- `FINANCIAL_DATASETS_API_KEY` - Financial data provider
- `LANGCHAIN_API_KEY` - LangSmith tracing (optional)
- `POSTGRES_URL` - Database connection
- `BLOB_READ_WRITE_TOKEN` - Vercel Blob storage

## Development Notes

### Code Style & Linting
- Uses Biome for consistent formatting (2-space indents, single quotes)
- ESLint integration with Next.js config
- Strict TypeScript configuration with path aliases (`@/*`)

### Database Migrations
- Always run `pnpm db:generate` after schema changes
- Production builds automatically run migrations via `tsx lib/db/migrate`
- Use Drizzle Studio for database inspection

### Testing Financial Features
- Free data available for: AAPL, GOOGL, MSFT, NVDA, TSLA
- Test financial tools through chat interface
- Monitor API usage via LangSmith integration

### Component Development
- Follow existing patterns in `components/` directory
- Use shadcn/ui components for consistency
- Implement responsive design with Tailwind CSS
- Financial components should handle loading and error states

### Simplified Architecture Notes
- No authentication system - all chats are publicly accessible
- No user management or session handling
- Chat history is global, not user-specific
- No voting or feedback system for messages
- Focus is purely on financial analysis and AI interactions