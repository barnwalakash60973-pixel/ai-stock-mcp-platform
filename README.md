# 🚀 AI Stock MCP Platform

## 📌 Overview

AI Stock MCP Platform is a backend system for stock market data retrieval and analysis built using **FastMCP**, **Python**, and **SQL Server**.

The platform exposes stock market data through MCP (Model Context Protocol) tools, allowing applications and AI agents to execute database queries and retrieve structured financial information. The architecture is modular, scalable, and designed for future integration with Large Language Models (LLMs) and AI-powered analytics.

---

## ✨ Features

* ⚡ FastMCP-based tool server
* 📊 SQL Server integration for stock market datasets
* 🔍 Dynamic query execution through MCP tools
* 🧱 Modular architecture using the Adapter pattern
* 📝 Structured logging and error handling
* 🔒 Environment-based configuration management
* 🚀 Ready for future AI/LLM integration
* 🔌 Easy integration with MCP-compatible clients

---

## 🏗️ System Architecture

```text
Client Application
        │
        ▼
FastMCP Server
        │
        ▼
execute_sqlserver_query Tool
        │
        ▼
SqlServerAdapter
        │
        ▼
SQL Server Database
```

## 📂 Project Structure

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
├── logs/
│
└── requirements.txt
```

## 🛠️ Technology Stack

* Python 3.11+
* FastMCP
* SQL Server
* PyODBC
* Pandas
* Uvicorn

## 🚀 Getting Started

### Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### Run the MCP Server

```bash
python backend/mcp_server/server_socket.py
```

### MCP Endpoint

```text
http://localhost:8765/mcp
```

## 🔮 Future Enhancements

* Natural Language to SQL using LLMs
* AI-powered stock insights
* Interactive visualizations
* Multi-database support
* Agent-based analytics workflows

## 📄 License

This project is licensed under the MIT License.
