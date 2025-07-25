# AI Financial Agent 🤖
This is a proof of conncept AI financial agent.  The goal of this project is to explore the use of AI for investment research.  This project is for **educational** purposes only and is not intended for real trading or investment.

## Disclaimer

This project is for **educational and research purposes only**.

- Not intended for real trading or investment
- No warranties or guarantees provided
- Past performance does not indicate future results
- Creator assumes no liability for financial losses
- Consult a financial advisor for investment decisions

By using this software, you agree to use it solely for learning purposes.

## Table of Contents 📖
- [Features](#features)
- [Setup](#setup)
- [Run the Agent](#run-the-agent)
- [Financial Data API](#financial-data-api)
- [Deploy Your Own Agent](#deploy-your-own-agent)

## Features
- [AI Financial Agent](https://chat.financialdatasets.ai)
  - Productized version of this project
  - Chat assistant for financial research, stock analysis, and more
  - Uses generative UI to display stock prices, fundamentals, and more
- [Financial Datasets API](https://financialdatasets.ai)
  - Access to real-time and historical stock market data
  - Data is optimized for AI financial agents
  - 30+ years of financial data with 100% market coverage
  - Documentation available [here](https://docs.financialdatasets.ai)

## Setup

```bash
git clone https://github.com/virattt/ai-financial-agent.git
cd ai-financial-agent
```

> If you do not have npm installed, please install it from [here](https://nodejs.org/en/download/).

1. Install pnpm (if not already installed):
```bash
npm install -g pnpm
```

2. Install dependencies:
```bash
pnpm install
```

3. Set up your environment variables:
```bash
# Create .env file for your API keys
cp .env.example .env
```

**Important**: You should not commit your `.env` file or it will expose secrets that will allow others to control access to your various OpenAI and authentication provider accounts.

## Run the Agent

After completing the steps above, simply run the following command to start the development server:
```bash
pnpm dev
```

Your app template should now be running on [localhost:3000](http://localhost:3000/).
