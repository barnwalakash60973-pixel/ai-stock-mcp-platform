# 🚀 Stock Data Analysis Backend (FastMCP + SQL Server)

## 📌 Overview
This project is a backend system for stock market data analysis built using **FastMCP** and **SQL Server**. It enables dynamic execution of SQL queries through MCP tools and provides structured data retrieval from large financial datasets.

The system is designed with a scalable architecture, making it ready for future integration with AI/LLM-based querying and interactive data visualization.

---

## 🧠 Key Features

- ⚡ Execute dynamic SQL queries via MCP tools  
- 📊 Retrieve structured stock market data from SQL Server  
- 🔌 Clean modular architecture (MCP + Adapter pattern)  
- 📝 Logging and error handling support  
- 🧱 Scalable and extensible backend design  
- 🔮 Ready for future AI/LLM integration  

---

## 🏗️ Architecture
Client (Postman / Python / UI)
↓
FastMCP Server
↓
MCP Tool (execute_sqlserver_query)
↓
SqlServerAdapter
↓
SQL Server Database


---

## 📂 Project Structure
backend/
│
├── mcp_server/
│ └── server_socket.py
│
├── data_loader/
│ ├── adapter/
│ │ └── ssms_adapter.py
│ │
│ ├── common/
│ │ ├── environment.py
│ │ └── logger_factory.py
│
├── logs/
├── .env
├── requirements.txt