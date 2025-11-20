# Growbe - AI-Powered Financial Advisory Agent

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/React-19+-61dafb.svg" alt="React Version">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-009688.svg" alt="FastAPI Version">
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o-412991.svg" alt="OpenAI">
  <img src="https://img.shields.io/badge/Strands-Agent_Framework-FF6B35.svg" alt="Strands Framework">
  <img src="https://img.shields.io/badge/SQLite-3-003b57.svg" alt="SQLite">
</p>

<p align="center">
  <strong>🤖 Your Personal AI Financial Advisor - Smart, Secure, and Always Available</strong>
</p>

---

## 🌟 What is Growbe?

**Growbe** is an intelligent conversational AI agent that provides personalized financial advice, calculations, and insights. Built with cutting-edge AI technology, Growbe helps users make informed financial decisions through natural conversation.

### ✨ Key Features

- **💬 Natural Conversations**: Chat naturally about your finances like talking to a trusted advisor
- **🧮 Smart Calculations**: Advanced financial calculators for debt optimization, rent vs. buy analysis, and more
- **📊 Data-Driven Insights**: Access to your financial data with intelligent analysis
- **🔒 Privacy-First**: Your financial data stays secure and private
- **🎯 Personalized Advice**: Tailored recommendations based on your unique situation
- **📈 Market Intelligence**: Real-time market data and financial news integration

### 🎯 Use Cases

- **New Graduates**: Plan your first budget and understand student loan management
- **Young Professionals**: Optimize debt payoff strategies and investment planning
- **Home Buyers**: Compare renting vs. buying scenarios with detailed analysis
- **Debt Management**: Get personalized debt snowball/avalanche strategies
- **Financial Planning**: Long-term wealth building and retirement planning

---

## 🚀 Quick Start

Get Growbe running locally in **5 minutes**:

```bash
# Clone the repository
git clone https://github.com/yourusername/growbe.git
cd growbe

# Setup backend
cd backend
pip install -r requirements.txt
python db_setup.py
python populate_database.py

# Setup frontend
cd ../frontend
npm install

# Run both services
# Terminal 1: Backend
cd backend && python main.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

Visit `http://localhost:3001` and start chatting with Growbe!

---

## 📋 Prerequisites

### System Requirements
- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **Git** for cloning the repository
- **SQLite 3** (comes with Python)

### API Keys Required
- **OpenAI API Key** (for GPT-4 AI responses)
- **Tavily API Key** (optional, for web search functionality)

### Hardware Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB for application, plus database space
- **Network**: Stable internet for OpenAI API calls

---

## 🛠️ Installation & Setup

### Step 1: Clone and Navigate

```bash
git clone https://github.com/yourusername/growbe.git
cd growbe
```

### Step 2: Backend Setup

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Setup database with sample financial data
python db_setup.py
python populate_database.py
```

### Step 3: OpenAI Configuration

Create `.env` file in `backend/` directory:

```bash
cp readme/backend.env.example backend/.env
```

Edit the `.env` file with your API key:

```env
# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Web search functionality
TAVILY_API_KEY=your_tavily_api_key_here

# Database Configuration (Optional - uses defaults)
SQLITE_DB_PATH=./data/financial_data.db
```

**Get your OpenAI API Key:**
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up/Login to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and add it to your `.env` file

### Step 6: Frontend Setup

```bash
cd ../frontend

# Install Node.js dependencies
npm install

# Optional: Configure environment variables
cp .env.example .env.local
```

Edit `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 7: Run the Application

**Start Backend** (Terminal 1):
```bash
cd backend
python main.py
```
Backend will be available at: `http://localhost:8000`

**Start Frontend** (Terminal 2):
```bash
cd frontend
npm run dev
```
Frontend will be available at: `http://localhost:3001`

---

## 💾 Database Schema

Growbe uses SQLite with two main data categories:

### Financial Data Tables
- **`customers`**: User profiles and demographics
- **`accounts`**: Bank accounts, credit cards, loans
- **`transactions`**: Financial transaction history
- **`credit_reports`**: Credit scores and utilization
- **`debts_loans`**: Student loans, auto loans, credit cards
- **`assets`**: Investments, property, savings
- **`monthly_cashflow`**: Income, expenses, savings tracking

### Conversation Tables (Auto-managed)
- **`conversations`**: Chat sessions and metadata
- **`chat_messages`**: Individual messages and tool outputs
- **`conversation_summaries`**: AI-generated conversation summaries

---

## 🛠️ Architecture

### Backend Architecture
```
backend/
├── main.py                 # FastAPI application & routes
├── tools/                  # AI tool implementations
│   ├── debt_optimizer_tool.py
│   ├── financial_summary_tool.py
│   ├── nl2sql_tool.py
│   ├── rent_vs_buy_tool.py
│   └── visualization_tool.py
├── services/               # Business logic
├── hooks/                  # Event-driven enhancements
├── migrations/             # Database schema management
├── prompts/                # AI system prompts
└── data/                   # SQLite databases
```

### Frontend Architecture
```
frontend/
├── src/
│   ├── app/                # Next.js app router
│   ├── components/         # React components
│   └── lib/               # Utilities
├── public/                # Static assets
└── package.json
```

### AI Agent Architecture

**Core Components:**
- **Strands Agent Framework**: Orchestrates AI conversations and tool calls
- **OpenAI GPT-4 Integration**: Powers natural language understanding and responses
- **Tool Registry**: Auto-discovers and manages 12+ financial tools
- **Event Hooks**: Capture calculations, charts, and conversation data
- **RAG System**: Retrieves financial knowledge for evidence-based advice
- **Prompt Engineering**: Specialized prompts for different user scenarios

**Tool Ecosystem:**
- **Financial Calculators**: Debt optimization, rent vs. buy, financial summaries
- **Data Analysis**: NL2SQL queries, automatic visualization generation
- **External APIs**: Web search, market data integration
- **Profile Management**: Customer data updates and persona classification

---

## 🎯 Available Tools & Features

### 💰 Financial Analysis Tools

#### Debt Optimizer
- **Avalanche Method**: Pay highest interest debt first
- **Snowball Method**: Pay smallest balance first
- **Custom Strategies**: Personalized debt payoff plans
- **Scenario Analysis**: Compare different payment strategies

#### Rent vs. Buy Calculator
- **Comprehensive Analysis**: 10-year cost comparison
- **Tax Benefits**: Mortgage interest deductions
- **Appreciation**: Home value growth projections
- **Break-even Analysis**: When buying becomes profitable

#### Financial Summary Tool
- **Net Worth Calculation**: Assets minus liabilities
- **Cash Flow Analysis**: Income vs. expenses
- **Debt-to-Income Ratio**: Lending qualification metrics
- **Credit Health**: Score analysis and improvement tips

#### Investment Analysis
- **Risk Assessment**: Portfolio risk evaluation
- **Asset Allocation**: Diversification recommendations
- **Retirement Planning**: Long-term wealth building
- **Market Intelligence**: Current market data and trends

### 📊 Data & Visualization Tools

#### NL2SQL Query Tool
- **Natural Language Queries**: "Show my spending last month"
- **Intelligent Parsing**: Converts questions to SQL queries
- **Data Security**: Customer-specific data filtering
- **Result Visualization**: Automatic chart generation

#### Chart Generation Tool
- **Spending Breakdown**: Category-based expense analysis
- **Trend Analysis**: Time-series financial data
- **Debt Progress**: Loan payoff visualization
- **Income vs. Expenses**: Budget analysis charts

### 🔍 Research & Intelligence Tools

#### Knowledge Base Search (RAG)
- **Financial Concepts**: Evidence-based advice
- **Strategy Guidance**: Proven financial planning methods
- **Regulatory Compliance**: Current financial regulations
- **Market Analysis**: Economic trends and insights

#### Web Search Integration
- **Current Rates**: Mortgage rates, CD rates, etc.
- **Market News**: Financial news and updates
- **Economic Indicators**: Inflation, employment data
- **Investment Research**: Company and fund analysis

### 👤 Profile Management

#### Customer Assessment
- **Financial Goals**: Short-term and long-term objectives
- **Risk Tolerance**: Investment risk preferences
- **Debt Status**: Current debt situation analysis
- **Employment Info**: Income and job stability

#### Persona Classification
- **High-spending Student Debtor**: Aggressive debt management
- **Aspiring Homebuyer**: Mortgage and savings focus
- **Credit Card Optimizer**: Balance transfer strategies
- **Consistent Saver**: Investment and wealth building

---

## 🔌 API Documentation

### Core Endpoints

#### Health Check
```http
GET /
```
**Response:**
```json
{
  "message": "Growbe Financial Advisor API is running!",
  "version": "1.0.0",
  "status": "healthy"
}
```

#### Start Conversation
```http
POST /api/conversations/start
Content-Type: application/json

{
  "scenario_type": "existing" | "new",
  "customer_id": "C001",  // For existing users
  "session_id": "uuid",   // For new users
  "initial_message": "Hi, I need help with my budget"
}
```

#### Send Message
```http
POST /api/conversations/{conversation_id}/message
Content-Type: application/json

{
  "message": "How much should I save for a house down payment?"
}
```

#### Get Conversation History
```http
GET /api/conversations/{conversation_id}/messages?limit=50&offset=0
```

### Tool Response Formats

#### Calculation Results
```json
{
  "calculation_steps": [
    "Step 1: Calculate monthly payment",
    "Step 2: Apply extra payments",
    "Step 3: Track interest savings"
  ],
  "latex_formulas": [
    "\\text{Monthly Payment} = \\frac{P \\times r \\times (1+r)^n}{(1+r)^n - 1}",
    "\\text{Total Interest} = \\text{Total Payments} - \\text{Principal}"
  ],
  "scenario_type": "debt_optimization"
}
```

#### Chart Data
```json
{
  "chart_type": "bar",
  "title": "Monthly Spending by Category",
  "x_axis": "category",
  "y_axis": "amount",
  "data": [
    {"category": "Housing", "amount": 2500},
    {"category": "Food", "amount": 800},
    {"category": "Transportation", "amount": 400}
  ]
}
```

#### SQL Query Results
```json
{
  "query": "SELECT category, SUM(amount) as total FROM transactions WHERE customer_id = 'C001' GROUP BY category",
  "result_count": 5,
  "columns": ["category", "total"],
  "rows": [
    {"category": "Housing", "total": 2500.00},
    {"category": "Food", "total": 800.00}
  ],
  "execution_time": 0.15
}
```

---

## 🧪 Testing & Quality Assurance

### Running Tests
```bash
cd backend

# Run all tests
pytest

# Run specific test categories
pytest tests/test_conversation_flow.py
pytest tests/test_nl2sql_safety.py

# Run with coverage
pytest --cov=tools --cov=services
```

### Test Categories
- **Conversation Flow**: End-to-end chat functionality
- **Database Safety**: SQL injection prevention and data access controls
- **Tool Integration**: Calculator accuracy and tool orchestration
- **Security**: Scenario-based access controls and guardrails

---

## 🔧 Development

### Code Structure
```
growbe/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── tools/               # AI tools and calculators
│   ├── services/            # Business logic layer
│   ├── hooks/               # Event-driven features
│   ├── migrations/          # Database schema evolution
│   ├── prompts/             # AI system instructions
│   ├── tests/               # Quality assurance
│   └── data/                # SQLite databases
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # React components
│   │   └── lib/             # Utilities
│   └── public/              # Static assets
└── docs/                    # Documentation
```

### Development Workflow

1. **Setup Development Environment**
```bash
# Clone and setup as above
# Use development databases (auto-created)
```

2. **Run with Hot Reload**
```bash
# Backend
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm run dev
```

3. **Add New Features**
- Create tools in `backend/tools/`
- Add API routes in `backend/main.py`
- Build UI components in `frontend/src/components/`

4. **Database Changes**
```bash
# Create migration
cd backend/migrations
# Create new migration file: 005_add_new_feature.sql

# Apply migrations
python run_migrations.py
```

### Environment Variables

**Backend (`.env`)**:
```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
TAVILY_API_KEY=your_tavily_api_key_here
SQLITE_DB_PATH=./data/financial_data.db

# Development
DEBUG=true
LOG_LEVEL=INFO
```

**Frontend (`.env.local`)**:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=development
```

---

## 🐛 Troubleshooting

### Common Issues

#### "OpenAI API Key Missing"
**Solution:**
- Check that `OPENAI_API_KEY` is set in `backend/.env`
- Verify the API key is valid and has credits
- Ensure the `.env` file is in the correct location

#### "Database Connection Error"
**Solution:**
- Run `python db_setup.py` to create database
- Run `python populate_database.py` to add sample data
- Check `SQLITE_DB_PATH` in `.env` file

#### "Tool Not Found" Errors
**Solution:**
- Ensure all tool files are in `backend/tools/`
- Check tool imports and class definitions
- Verify tool registry auto-discovery

#### "Module Not Found" Errors
**Solution:**
- Install all requirements: `pip install -r requirements.txt`
- Activate virtual environment if using one
- Check Python path and package installations

### Debug Mode

Enable detailed logging:
```bash
# Backend
export DEBUG=true
export LOG_LEVEL=DEBUG
python main.py

# Frontend
npm run dev  # Already includes debug mode
```

### Performance Issues

- **Slow AI responses**: Check OpenAI API rate limits and billing
- **Memory usage**: Reduce conversation history limit
- **Database queries**: Check query execution plans

---

## 🔒 Security & Privacy

### Data Protection
- **Customer data isolation**: Strict per-customer data access
- **SQL injection prevention**: Parameterized queries only
- **API authentication**: Secure endpoint access
- **Data encryption**: Sensitive data encrypted at rest

### AI Safety
- **Financial guardrails**: Prevents harmful advice
- **Regulatory compliance**: Follows financial disclosure requirements
- **Source attribution**: All advice includes knowledge base citations
- **Conservative recommendations**: Prioritizes safety over high-risk strategies

### Access Controls
- **Scenario-based permissions**: Different access levels for new vs. existing users
- **Tool restrictions**: New users cannot access database tools
- **Rate limiting**: Prevents API abuse
- **Audit logging**: All conversations and tool usage logged

---

## 📊 Performance & Scaling

### Current Performance
- **Response Time**: 2-5 seconds for complex calculations
- **Concurrent Users**: Supports 50+ simultaneous conversations
- **Database**: SQLite handles 10K+ transactions efficiently
- **Memory Usage**: ~200MB for full application stack

### Optimization Opportunities
- **Database**: Migrate to PostgreSQL for higher concurrency
- **Caching**: Redis for frequently accessed data
- **CDN**: Static asset delivery optimization
- **Load Balancing**: Multiple backend instances

---

## 🤝 Contributing

We welcome contributions! Here's how to get involved:

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

### Contribution Guidelines
- Follow existing code style and patterns
- Add comprehensive tests for new features
- Update documentation for API changes
- Ensure all tests pass before submitting

### Areas for Contribution
- **New Financial Tools**: Calculators, analyzers, advisors
- **UI/UX Improvements**: Enhanced user experience
- **Performance Optimization**: Speed and efficiency improvements
- **Internationalization**: Multi-language support
- **Mobile Apps**: React Native implementations

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙋 Support & Community

### Getting Help
- **Documentation**: Check our [docs](docs/) folder
- **Issues**: Report bugs on [GitHub Issues](https://github.com/yourusername/growbe/issues)
- **Discussions**: Join community discussions

### Contact
- **Email**: p.kusha@gwu.edu

---

## 🗺️ Roadmap

### Q1 2026
- ✅ Core financial advisory features
- ✅ Debt optimization tools
- ✅ Conversation persistence
- 🔄 Mobile app development

### Q2 2026
- 🔄 Investment portfolio analysis
- 🔄 Retirement planning tools
- 🔄 Tax optimization features
- 🔄 Multi-language support

### Q3 2026
- 🔄 Voice interface integration
- 🔄 Advanced market analysis
- 🔄 Third-party integrations
- 🔄 Enterprise features

---

## 🏆 Acknowledgments

- **Strands Framework**: Powerful agent orchestration by AWS
- **OpenAI**: GPT-4 for natural language understanding
- **FastAPI**: Lightning-fast Python web framework
- **Next.js**: Modern React framework with app router
- **SQLite**: Reliable embedded database
- **Chart.js & Recharts**: Beautiful data visualizations

---

<p align="center">
  <strong>Built with ❤️ for financial empowerment</strong>
</p>

<p align="center">
  <a href="#growbe---ai-powered-financial-advisory-agent">Back to Top</a>
</p>

