import sys
import os
import json
import asyncio
import logging
import traceback
from fastmcp import Client
from dotenv import load_dotenv
from pathlib import Path
from typing import TypedDict, Literal, List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langsmith import traceable

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────
env_path = Path(__file__).parent / "data_loader" / "common" / ".env"
load_dotenv(env_path)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LLM client
client = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

# ─────────────────────────────────────────────────────────────
# MCP SERVER CONFIG
# FastMCP exposes tools at /mcp by default
# ─────────────────────────────────────────────────────────────
MCP_SERVER_URL = "http://localhost:8765/mcp"


# Fetch Schema from database
@traceable(name="Fetch Schema From MCP")
async def load_schema_from_mcp():
    async with Client(MCP_SERVER_URL) as mcp:

        result = await mcp.call_tool("get_schema", {})

        raw_text = "".join(
            block.text
            for block in result.content
            if hasattr(block, "text")
        )

        return json.loads(raw_text)
    
DB_SCHEMA = asyncio.run(load_schema_from_mcp())
logger.info(f"[STARTUP] Schema loaded. Tables found: {list(DB_SCHEMA.keys())}")


# ─────────────────────────────────────────────────────────────
# SYSTEM PROMPT — LLM DECISION MAKER
# ─────────────────────────────────────────────────────────────
DECISION_PROMPT = """
You are a financial assistant router.
Your ONLY job is to classify the user request into one of two types.

RULES:
- Return valid JSON only
- No SQL, no markdown, no explanation
- Never add extra fields

TYPE 1 — answer
Use when:
- General/educational questions (definitions, concepts, how things work)
- Greetings or small talk (hi, hello, thanks, bye)
- Questions you can answer without database data
Return:
{"type": "answer", "response": "your plain English answer here"}

TYPE 2 — query_required
Use when:
- User asks for specific data (prices, rankings, volumes, history)
- User asks for company-specific information that requires database data
- User asks for trends, reports, or analytics
Return:
{"type": "query_required", "topic": "brief description of the user's data request"}

FALLBACK — if request is completely unclear:
{"type": "answer", "response": "I'm not sure what you're asking. Could you please clarify?"}

EXAMPLES:
User: What is a stock?
{"type": "answer", "response": "A stock represents ownership in a company."}

User: hi
{"type": "answer", "response": "Hello! How can I help you with financial information today?"}

User: Show top stocks by volume
{"type": "query_required", "topic": "top stocks by volume"}

User: Reliance current price
{"type": "query_required", "topic": "Reliance current price"}

User: thanks
{"type": "answer", "response": "You're welcome! Let me know if you need anything else."}
"""


# ─────────────────────────────────────────────────────────────
# STATE — Shared bag passed between every LangGraph node
# ─────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    user_question: str                                        
    decision_type: Literal["answer", "query_required", ""]   
    direct_answer: str                                        
    sql: str                                                  
    db_results: list                                          
    final_response: str                                       

# ─────────────────────────────────────────────────────────────
# MCP HELPER — async call to execute_sqlserver_query tool
# Connects to FastMCP server, calls the tool, unwraps CallToolResult.
# CallToolResult has a .content list of TextContent blocks — not directly iterable.
# Returns: List[Dict] rows or [{"error": ...}]
# ─────────────────────────────────────────────────────────────
@traceable(name="Execute MCP Query")
async def _call_mcp_tool(sql: str) -> List[Dict[str, Any]]:
    try:
        async with Client(MCP_SERVER_URL) as mcp:
            logger.info(f"[MCP] Connected to {MCP_SERVER_URL}")

            # result is a CallToolResult object — access .content, not result itself
            call_result = await mcp.call_tool("execute_sqlserver_query", {"query": sql})

            
            raw_text = "".join(
                block.text
                for block in call_result.content          
                if hasattr(block, "text")
            )
            logger.info(f"[MCP] Raw response: {raw_text[:300]}")

            parsed = json.loads(raw_text)

            # Server returns list of dicts directly
            if isinstance(parsed, list):
                return parsed

            return [{"result": parsed}]

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"[MCP] Tool call failed: {e}")
        logger.error(error_trace)
        return [{"error": str(e), "details": error_trace}]


# ─────────────────────────────────────────────────────────────
# NODE 1: decide_intent
# Calls LLM with DECISION_PROMPT to classify question as answer or query.
# Returns: decision_type, direct_answer
# ─────────────────────────────────────────────────────────────
@traceable(name="Decision Node")
def decide_intent(state: AgentState) -> AgentState:
    question = state["user_question"]
    logger.info(f"\n{'='*55}")
    logger.info(f"[USER] {question}")

    response = client.invoke(
        f"""
        {DECISION_PROMPT}

        User Question:
        {question}
        """
    )

    raw = response.content.strip()
    logger.info(f"[DECISION] {raw}")

    try:
        decision = json.loads(raw)
    except json.JSONDecodeError:
        # Unparseable response → treat as a direct answer
        return {**state, "decision_type": "answer", "direct_answer": raw}

    return {
        **state,
        "decision_type": decision.get("type", ""),
        "direct_answer": decision.get("response", ""),
    }


# ─────────────────────────────────────────────────────────────
# NODE 2: answer_directly
# For general/educational questions — copies LLM answer to final_response.
# Returns: final_response
# ─────────────────────────────────────────────────────────────
@traceable(name="Answer Directly")
def answer_directly(state: AgentState) -> AgentState:
    logger.info("[FLOW] → Direct answer")
    answer = state.get("direct_answer") or "I could not process your question."
    return {**state, "final_response": answer}


# ─────────────────────────────────────────────────────────────
# NODE 3: generate_sql
# Sends user question + real DB schema to LLM → gets back a T-SQL SELECT.
# Returns: sql
# ─────────────────────────────────────────────────────────────
@traceable(name="Generate SQL")
def generate_sql(state: AgentState) -> AgentState:
    logger.info("[FLOW] → Data required — generating SQL")

    if not DB_SCHEMA:
        return {
            **state,
            "sql": "",
            "final_response": "Could not retrieve database schema. Please check your database connection.",
        }

    question = state["user_question"]

    prompt_template = """
You are a SQL Server query generator.

User Request: {question}

Database Schema: {schema}

RULES:
- Use ONLY tables and columns from the schema
- Never invent tables, columns, or relationships
- Generate SQL Server T-SQL only
- If a column name is a SQL Server reserved keyword
  (e.g. Open, Close, Order, User, Group, Timestamp),
  wrap it in square brackets
- Use TOP N, never LIMIT — default TOP 50 if user does not specify
- Generate SELECT statements only — never INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, MERGE, EXEC
- Never use SELECT * — select only required columns
- Use TOP 1 + ORDER BY DESC/ASC for highest/lowest records
- Use TRY_CAST(column AS DECIMAL(18,2)) for VARCHAR numeric comparisons:
  CORRECT: ORDER BY TRY_CAST(price AS DECIMAL(18,2)) DESC
  WRONG:   ORDER BY price DESC
- For latest/current data use:
  WHERE TradeDate = (SELECT MAX(TradeDate) FROM table_name)
- Use IS NULL / IS NOT NULL — never = NULL
- If user explicitly mentions a table, prioritize that table
- If request cannot be answered from schema, return exactly: NO_RELEVANT_TABLE

Return ONLY raw SQL. No markdown. No explanation. No comments.
"""
    prompt = prompt_template.format(
    question=question,
    schema=json.dumps(DB_SCHEMA, indent=2)
)
    response = client.invoke(prompt)
    sql = response.content.strip()
    logger.info(f"[SQL GENERATED] {sql}")

    return {**state, "sql": sql}


# ─────────────────────────────────────────────────────────────
# NODE 4: execute_query
# Validates SQL, then calls FastMCP tool execute_sqlserver_query via HTTP.
# Returns: db_results  (or sets final_response on guard-rail exit)
# ─────────────────────────────────────────────────────────────
@traceable(name="Execute Query Node")
def execute_query(state: AgentState) -> AgentState:
    sql = state.get("sql", "")

    # Guard: LLM found no matching table
    if sql.strip() == "NO_RELEVANT_TABLE":
        logger.info("[FLOW] → No relevant table in schema")
        return {
            **state,
            "db_results": [],
            "final_response": (
                "I don't have information related to this request "
                "in the available database."
            ),
        }

    # Guard: block non-SELECT statements
    sql_upper = sql.upper().strip()

    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        logger.warning(f"[BLOCKED SQL] {sql}")
        return {**state, "db_results": [],"final_response": "Only SELECT queries are allowed."}
    
    logger.info(f"[MCP] Sending query to MCP tool: {sql}")

    # Call MCP tool synchronously (LangGraph nodes are sync)
    results = asyncio.run(_call_mcp_tool(sql))

    logger.info(f"[MCP] Returned {len(results)} rows")
    return {**state, "db_results": results}


# ─────────────────────────────────────────────────────────────
# NODE 5: summarize_results
# Asks LLM to turn raw DB rows into a friendly plain-English answer.
# Returns: final_response
# ─────────────────────────────────────────────────────────────
@traceable(name="Summarize Results")
def summarize_results(state: AgentState) -> AgentState:
    results = state.get("db_results", [])
    question = state["user_question"]

    # Surface DB / MCP errors clearly
    if results and isinstance(results, list) and "error" in results[0]:
        return {**state, "final_response": f"Database error: {results[0].get('error')}"}

    # Empty result set
    if not results:
        return {**state, "final_response": "No data available for the requested information."}

    prompt = f"""
The user asked:

{question}

The database returned:

{json.dumps(results, indent=2, default=str)}

Summarize this clearly for the user.

Rules:
- No SQL terminology
- No database terminology
- Present the information in a friendly way
- If no records exist, say:
  "No data available for the requested information."
"""

    response = client.invoke(prompt)
    summary = response.content.strip()
    return {**state, "final_response": summary}


# ─────────────────────────────────────────────────────────────
# ROUTER 1 — after decide_intent
# Routes to answer_directly (general Q) or generate_sql (data Q).
# ─────────────────────────────────────────────────────────────
def route_after_decision(state: AgentState) -> str:
    """Return next node name based on decision_type."""
    if state.get("decision_type") == "answer":
        return "answer_directly"
    if state.get("decision_type") == "query_required":
        return "generate_sql"
    return "answer_directly"  # fallback


# ─────────────────────────────────────────────────────────────
# ROUTER 2 — after execute_query
# Skips summarize if a guard-rail already set final_response.
# ─────────────────────────────────────────────────────────────
def route_after_execute(state: AgentState) -> str:
    """Jump to END early if execute_query set final_response (guard-rail hit)."""
    if state.get("final_response"):
        return END
    return "summarize_results"


# ─────────────────────────────────────────────────────────────
# BUILD GRAPH — wires all nodes + routers into a compiled app
# ─────────────────────────────────────────────────────────────
def build_graph() -> StateGraph:
    """Register nodes, set entry point, wire edges; return compiled graph."""
    graph = StateGraph(AgentState)

    graph.add_node("decide_intent",    decide_intent)
    graph.add_node("answer_directly",  answer_directly)
    graph.add_node("generate_sql",     generate_sql)
    graph.add_node("execute_query",    execute_query)
    graph.add_node("summarize_results", summarize_results)

    graph.set_entry_point("decide_intent")

    graph.add_conditional_edges(
        "decide_intent",
        route_after_decision,
        {
            "answer_directly": "answer_directly",
            "generate_sql":    "generate_sql",
        },
    )

    graph.add_edge("answer_directly", END)
    graph.add_edge("generate_sql",    "execute_query")

    graph.add_conditional_edges(
        "execute_query",
        route_after_execute,
        {
            "summarize_results": "summarize_results",
            END: END,
        },
    )

    graph.add_edge("summarize_results", END)

    return graph.compile()


# ─────────────────────────────────────────────────────────────
# APP — compiled graph (built once at import time)
# ─────────────────────────────────────────────────────────────
app = build_graph()


# ─────────────────────────────────────────────────────────────
# HANDLE — public entry point, same signature as original
# Seeds initial state, runs graph, returns final_response string.
# ─────────────────────────────────────────────────────────────
@traceable(name="Stock Assistant Workflow")
def handle(user_question: str) -> str:
    """Run the full LangGraph pipeline and return the assistant's answer."""
    initial_state: AgentState = {
        "user_question":  user_question,
        "decision_type":  "",
        "direct_answer":  "",
        "sql":            "",
        "db_results":     [],
        "final_response": "",
    }

    result = app.invoke(initial_state)
    return result.get("final_response", "Sorry, I could not understand your request.")


# ─────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n💼 Financial Assistant Ready!")
    print("   Ask about stocks, prices, rankings, or financial concepts.")
    print("   Type 'exit' to quit.\n")
    print("─" * 55)

    while True:
        try:
            question = input("\nYou: ").strip()
            if not question:
                continue
            if question.lower() in ("exit", "quit"):
                print("Goodbye!")
                break

            answer = handle(question)
            print(f"\nAssistant: {answer}")
            print("─" * 55)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break