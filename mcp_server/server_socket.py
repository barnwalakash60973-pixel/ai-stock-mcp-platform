import sys 
import os 
# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
import json
import traceback
from typing import Dict, Any, List, Union, Optional
from fastmcp import FastMCP
import pandas as pd
from data_loader.adapter.ssms_adapter import SqlServerAdapter
from data_loader.common.environment import EnvironmentConfig
from data_loader.common.logger_factory import LoggerFactory  



# Logging Setup 
LoggerFactory.setup_logging("logs/mcp_server_socket.log", stream=sys.stderr)
logger = LoggerFactory.get_logger(__name__)


# MCP Server
app = FastMCP(
    name="Stock Analysis & Trading Insights Server",
    version="1.0.0",
    #stateless_http=True
)

# Environment 
env = EnvironmentConfig()

_sql_adapter: Optional[SqlServerAdapter] = None


def get_sql_adapter() -> SqlServerAdapter:
    global _sql_adapter
    if _sql_adapter is None:
        logger.info("Initializing SQL Server adapter...")
        _sql_adapter = SqlServerAdapter()   
        logger.info("sqlserver adapter initialized successfully.")
    
    return _sql_adapter

@app.tool()
def execute_sqlserver_query(query: str)-> List[Dict[str,Any]]:
    """
    Execute sql_server SQL query and return JSON-serializable results.
    
    Args:
        query: SQL query to execute against Databricks Unity Catalog
        
    Returns:
        List of dictionaries containing query results or error information
    """
    
    logger.info("=" *80)
    logger.info(f"Tool Invoked: execute_sqlserver_query")
    logger.info(f"Incoming Query: {query}")
    try:
        adapter = get_sql_adapter()
        logger.info("connecting to sqlserver...")
    

        if not adapter.connect():
            logger.error("Sqlserver connection failed")
            return [{"error": "Connection failed"}]
        logger.info(" Connection established. Executing query...")
        
        # Execute query using the adapter's method
        result = adapter.query_execution_with_timeout(query=query, timeout=30)
        
        # Convert to list of dictionaries format
        if result and "column_names" in result and "rows" in result:
            column_names = result["column_names"]
            rows = result["rows"]
            
            # Transform to list of dictionaries
            formatted_results = [
                dict(zip(column_names, row)) for row in rows
            ]
            
            logger.info(f"Query executed successfully. Returned {len(formatted_results)} rows.")
            return formatted_results

        else:
            logger.warning("Query returned unexpected response format.")
            return [{"result": result}]

    except Exception as e:
        error_message = str(e)
        error_trace = traceback.format_exc()

    # Log the error details
        logger.error(f"Query execution failed: {error_message}")
        logger.error(error_trace)


        
        return [{
        "error": "Query execution failed",
        "message": error_message,
        "details": error_trace
    }]

# --------------------------- Main Entry Point --------------------------- #
if __name__ == "__main__":
    app.run(
        transport="http",
        host="0.0.0.0",
        port=8765,
        stateless_http=True   
    )      

