import logging
import pyodbc
import pandas as pd
from dotenv import load_dotenv
from typing import List, Dict, Optional
from data_loader.common.environment import EnvironmentConfig

load_dotenv()

logging.basicConfig(level = logging.INFO)

class SqlServerAdapter:

    def __init__(self):
        self.conn = None
        self.logger = logging.getLogger(self.__class__.__name__)

        # load config
        self.config = EnvironmentConfig()

    def connect(self):
        try:
            if not self.conn:
                self.conn = pyodbc.connect(
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={self.config.DB_SERVER};"
                    f"DATABASE={self.config.DB_DATABASE};"
                    f"UID={self.config.DB_USER};"
                    f"PWD={self.config.DB_PASSWORD};"
                )

                self.logger.info("Connected to database")
            return True

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            raise


    #Query Execution
    def query_execution_with_timeout(
            self,
            query: str,
            params: Optional[tuple] = None,
            timeout: Optional[int] = None,
            retry_count: int = 0) -> Dict[str,any]:
    


        """
           use - Get actual data from database
           Execute a SQL query and return results.

 

        Args:

            query (str): SQL query to execute

            params (tuple, optional): Query parameters for parameterized queries

            timeout (int, optional): Query timeout in seconds (not fully supported)

            retry_count (int, optional): Number of retries (not implemented)

 

        Returns:

            Dict[str, Any]: Dictionary with 'column_names' and 'rows' for SELECT,

        or 'rowcount
        """

        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()

        try:
            #execute query with or without params
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            if cursor.description:
                column_names = [desc[0] for desc in cursor.description]
                rows = [tuple(row) for row in cursor.fetchall()]
                return {"column_names":column_names, "rows": rows}
            
        except Exception as e:
            self.logger.error(f"[error] query execution failed {e}",exc_info = True)
            raise


        finally:
            cursor.close()


    # RESULT FORMATTING
    def format_results(self, 
                       results: Dict[str, any],
                       format_type: str = "json")->any:
    
        """

        Format query results into specified format.

 

        Args:

            results (Dict[str, Any]): Raw query results

            format_type (str): Output format ('json' or 'dataframe')

 

        Returns:

            Any: Formatted results

        """

        if format_type == "json":
            return {"results": results}
        
        elif format_type == "dataframe":
            if "column_names" in results and "rows" in results:
                return pd.DataFrame(results["rows"],
                 columns = results["column_names"]
                )

            return pd.DataFrame()
        
        return results
        

    # SCHEMA INFORMATION
    def get_schema(self, schema_name: str = "dbo")-> Dict[str, any]:
        """
         purpose - Find structure of database
        Retrieve schema information for all tables in the database.

 

        Args:

            schema_name (str): Schema name to query (default: 'dbo')

 

        Returns:

            Dict[str, Any]: Dictionary mapping table names to their column details

        """

        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()

        schema_dict:Dict[str, any] = {}
        
        try:
            #get all tables in the schema
            query = """

                SELECT TABLE_NAME

                FROM INFORMATION_SCHEMA.TABLES

                WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'BASE TABLE'

                ORDER BY TABLE_NAME

            """
            cursor.execute(query,(schema_name,))
            tables = [row[0] for row in cursor.fetchall()]

            #get columns for each table
            for table in tables:
                column_query =  """

                    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE

                    FROM INFORMATION_SCHEMA.COLUMNS

                    WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?

                    ORDER BY ORDINAL_POSITION

                """
                cursor.execute(column_query,(schema_name,table))

                columns = [
                    {"column_name": row[0],
                     "data_type": row[1],
                     "max_length": row[2],
                     "nullable": row[3] == "YES"}
                     for row in cursor.fetchall()
                ]

                schema_dict[table] = {"columns": columns}
            self.logger.info(f"[SUCCESS] Retrived schema for {len(tables)} tables")
            return schema_dict
        
        except Exception as e:
            self.logger.error(f"[ERROR] failed to retrived schema:{e}",
                              exc_info = True)
            raise

        finally:
            cursor.close()


        
    # DATA RETRIEVAL
    def get_data_retrival(self,
                          table_name: str,
                          schema: str = "dbo",
                          limit: Optional[int] = None,
                          where_clause: Optional[str] = None
                          )-> pd.DataFrame:

        """

        Retrieve data from a table as pandas DataFrame.

 

        Args:

            table_name (str): Table name

            schema (str): Schema name (default: 'dbo')

            limit (int, optional): Maximum number of rows to retrieve

            where_clause (str, optional): WHERE clause (without 'WHERE' keyword)

 

        Returns:

            pd.DataFrame: DataFrame containing table data

        """
        if not self.conn:
            self.connect()

        try:
            #build query with proper schema qualification
            if limit:
                query = f"SELECT TOP{limit} * FROM [{schema}].[{table_name}]"
            else:
                query = f"SELECT * FROM [{schema}].[{table_name}]"

            if where_clause:
                query += f"WHERE {where_clause}"

            self.logger.info(f"[FETCH] fetching data from [{schema}].[{table_name}]")       
        
            results = self.query_execution_with_timeout(query)
            df = self.format_results(results,"dataframe")

            self.logger.info(f"[SUCCESS] retrived {len(df)} rows from [{schema}].[{table_name}]")
        
        except Exception as e:
            self.logger.error(f"[ERROR] failed to retrieve table {table_name}:{e}",
                              exc_info=True)
            raise


    def execute_query_to_dataframe(self,
                                   query: str,
                                   params: Optional[tuple] = None
                                   )->pd.DataFrame:
        
        """

        Execute a custom SQL query and return results as DataFrame.

 

        Args:

            query (str): SQL query to execute

            params (tuple, optional): Query parameters

 

        Returns:

            pd.DataFrame: Query results as DataFrame

        """
        if not self.conn:
            self.connect()

        try:
            self.logger.info(f"[QUERY] executing from custom query")
            results = self.query_execution_with_timeout(query, params)
            df = self.format_results(results, "dataframe")

            self.logger.info(f"[SUCCESS] query returned {len(df)} rows")
            return df
        except Exception as e:
            self.logger.error(f"[ERROR] query execution failed:{e}",exc_info=True)
            raise


