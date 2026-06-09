#This give full deatils of each table which contains in database

from data_loader.adapter.ssms_adapter import SqlServerAdapter

adapter = SqlServerAdapter()
adapter.connect()

schema = adapter.get_schema()

for table_name, table_info in schema.items():
    print(f"\n{'='*60}")
    print(f"TABLE: {table_name}")
    print(f"{'='*60}")

    for col in table_info["columns"]:
        print(
            f"{col['column_name']:30} "
            f"{col['data_type']:15} "
            f"Nullable={col['nullable']}"
        )


#if you want query run first replce by this above code 
"""

from data_loader.adapter.ssms_adapter import SqlServerAdapter

adapter = SqlServerAdapter()
adapter.connect()

df = adapter.execute_query_to_dataframe(
    "
    SELECT TOP 10
        symbol,
         volume
     FROM dbo.live_quote
     ORDER BY volume DESC
     "
)

print(df)

"""



#above code give full details of each table which contain in database
# ==========================================================
# Example Queries for Stock Database
# ==========================================================


# 1. Check Specific Stock
"""
SELECT *
FROM dbo.live_quote
WHERE symbol = 'KPIL'
"""

# 2. Count Records
"""
SELECT COUNT(*) AS total_rows
FROM dbo.ZerodhaTicks
"""

# 3. Top Volume Stocks
"""
SELECT TOP 10
    symbol,
    volume
FROM dbo.bhavcopy_equity
ORDER BY volume DESC
"""

# 4. Latest Live Quotes
"""
SELECT TOP 20
    symbol,
    ltp,
    volume,
    trade_date
FROM dbo.live_quote
ORDER BY trade_date DESC
"""

# 5. Highest Price Stocks
"""
SELECT TOP 10
    symbol,
    high
FROM dbo.live_quote
ORDER BY high DESC
"""

# 6. Lowest Price Stocks
"""
SELECT TOP 10
    symbol,
    low
FROM dbo.live_quote
ORDER BY low ASC
"""

# 7. Stocks Above Specific Price
"""
SELECT
    symbol,
    ltp
FROM dbo.live_quote
WHERE ltp > 1000
"""

# 8. Most Active Stocks
"""
SELECT TOP 10
    symbol,
    volume
FROM dbo.bhavcopy_deliverable
ORDER BY volume DESC
"""

# 9. Get Available Tables
"""
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
"""

# 10. Get Table Schema
"""
SELECT
    COLUMN_NAME,
    DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'live_quote'
"""