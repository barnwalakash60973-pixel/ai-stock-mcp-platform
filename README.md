# 🚀 AI Stock MCP Platform

## 📌 Overview

AI Stock MCP Platform is a backend system built using **FastMCP** and **SQL Server** that enables AI agents and LLMs to access, analyze, and visualize stock market data through MCP (Model Context Protocol).

The platform provides database connectivity, schema discovery, SQL query execution, and is designed for future integration with:

* 🤖 Large Language Models (OpenAI, Claude, Gemini, etc.)
* 📊 Plotly Interactive Dashboards
* 📈 Matplotlib Visualizations
* 📉 Seaborn Statistical Analysis
* 🔍 Automated Stock Insights
* 💹 Technical & Fundamental Analysis

---

## 🏗️ Project Architecture

```text
backend/
│
├── data_loader/
│   ├── adapter/
│   │   └── ssms_adapter.py
│   │
│   └── common/
│       ├── environment.py
│       └── logger_factory.py
│
├── mcp_server/
│   └── server_socket.py
│
├── main.py
│
├── requirements.txt
│
|── Screenshots
|
└── README.md
```

---

## ⚙️ Features

### Database Features

* SQL Server Integration
* Secure Environment Variable Management
* Automatic Connection Handling
* Query Timeout Support
* DataFrame Conversion Support
* Schema Discovery

### MCP Features

* Execute Custom SQL Queries
* Retrieve Database Schema
* Fetch Table Metadata
* Health Check Endpoint
* MCP Tool Registration

### Analytics Features (Planned)

* Data Profiling
* Trend Analysis
* Volume Analysis
* Price Movement Analysis
* Sector-wise Analysis

### Visualization Features (Planned)

* Plotly Interactive Charts
* Matplotlib Visualizations
* Seaborn Statistical Plots
* Candlestick Charts
* Volume Charts
* Correlation Heatmaps

### AI Features (Planned)

* Natural Language to SQL
* AI-Powered Stock Analysis
* Automated Insights Generation
* Financial Question Answering
* Portfolio Analysis
* Market Trend Explanation

---

## 🗄️ Database Tables

Example tables available in the platform:

* bhavcopy_asm
* bhavcopy_delivery
* bhavcopy_equity
* bhavcopy_live
* DailyAnalysis
* intraday
* live_quote
* PreDefineSymbol
* Sectors
* securities
* StrongStart
* ZerodhaCandle
* ZerodhaHistorical
* ZerodhaTicks

### Database Schema Discovery

The platform can automatically discover table structures, column names, data types, and nullable fields using the `get_schema()` method.

![Database Schema](screenshots/get_schema_screenshot.png)

---

## 🔧 Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd ai-stock-mcp-platform
```

### 2. Create Virtual Environment

```bash
python -m venv .venu
```

### 3. Activate Environment

Windows:

```bash
.venu\Scripts\activate
```

Linux / Mac:

```bash
source .venu/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file:

```env
DB_SERVER=YOUR_SERVER
DB_DATABASE=YOUR_DATABASE
DB_USER=YOUR_USERNAME
DB_PASSWORD=YOUR_PASSWORD
```

---

## ▶️ Run MCP Server

```bash
python backend/main.py
```

Server starts at:

![Schema](screenshots/mcp_server_running.png)

---

## 🧪 Example SQL Queries

### Check Specific Stock

![Query Result](screenshots/query_execution_screenshot.png)

```sql
SELECT *
FROM dbo.live_quote
WHERE symbol = 'KPIL'
```

### Count Records

```sql
SELECT COUNT(*) AS total_rows
FROM dbo.live_quote
```

### Top Volume Stocks

```sql
SELECT TOP 10
    symbol,
    volume
FROM dbo.live_quote
ORDER BY volume DESC
```

### Latest Live Quotes

```sql
SELECT TOP 20
    symbol,
    ltp,
    volume,
    trade_date
FROM dbo.live_quote
ORDER BY trade_date DESC
```

---

## 🔌 MCP Tools

### execute_sqlserver_query()

Execute SQL queries against SQL Server.

### get_schema()

Retrieve database schema information.

### get_data_retrival()

Retrieve table data as a pandas DataFrame.

### execute_query_to_dataframe()

Execute custom SQL and return DataFrame output.

---

## 📊 Future Roadmap

### Phase 1

* SQL Server Integration ✅
* FastMCP Integration ✅
* Schema Discovery ✅

### Phase 2

* Plotly Visualizations
* Matplotlib Support
* Seaborn Analysis

### Phase 3

* OpenAI Integration
* Natural Language SQL Generation
* Automated Insights

### Phase 4

* Technical Indicators
* Portfolio Analytics
* Real-time Market Monitoring

---

## 🛠️ Technology Stack

### Backend

* Python
* FastMCP
* SQL Server
* PyODBC

### Data Analysis

* Pandas
* NumPy

### Visualization

* Plotly
* Matplotlib
* Seaborn

### AI/LLM

* OpenAI
* Claude
* Gemini
* MCP Protocol

---

## 👨‍💻 Author

Akash Kumar

AI | Machine Learning | Data Science | Stock Market Analytics
