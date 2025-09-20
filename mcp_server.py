#!/usr/bin/env python3
"""
MCP MySQL Server - A proper Model Context Protocol server for MySQL database operations
with natural language query support using Ollama/Llama 3.2
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
import mysql.connector
from mysql.connector import Error
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import sys

# Load environment variables from .env file
load_dotenv()

# Configure logging to stderr (important for MCP servers)
script_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(script_dir, "mcp.log")
logging.basicConfig(
    level=logging.DEBUG,
    # stream=sys.stderr,
    filename=log_file_path,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("MySQL Database Server")

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "test_db"),
    "port": int(os.getenv("DB_PORT", "3306")),
}

# Ollama configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Database connection pool
engine = None
SessionLocal = None


def get_db_connection():
    """Create a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        raise Exception(f"Database connection error: {e}")


def init_database():
    """Initialize database connection pool"""
    global engine, SessionLocal
    try:
        db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("Database connection pool initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def query_ollama(prompt: str) -> str:
    """Send a prompt to Ollama and get response"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        )
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            logger.error(f"Ollama API error: {response.status_code} - {response.text}")
            raise Exception("Ollama API error")
    except Exception as e:
        logger.error(f"Error querying Ollama: {e}")
        raise Exception(f"Ollama query error: {e}")


def natural_language_to_sql(natural_query: str, schema_info: str) -> str:
    """Convert natural language query to SQL using Ollama"""
    prompt = f"""You are a SQL expert. Convert the following natural language query to SQL.
    
        Database Schema:
        {schema_info}

        Natural Language Query: {natural_query}

        Return only the SQL query without any explanation or formatting:
    """
    return query_ollama(prompt)


def get_database_schema() -> str:
    """Get database schema information"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        schema_info = "Database Schema:\n\n"

        for table in tables:
            table_name = list(table.values())[0]
            schema_info += f"Table: {table_name}\n"

            # Get columns for this table
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()

            for column in columns:
                col_name = column["Field"]
                col_type = column["Type"]
                col_null = "NULL" if column["Null"] == "YES" else "NOT NULL"
                col_key = column["Key"]
                col_default = column["Default"]

                schema_info += f"  - {col_name}: {col_type} {col_null}"
                if col_key:
                    schema_info += f" {col_key}"
                if col_default:
                    schema_info += f" DEFAULT {col_default}"
                schema_info += "\n"

            schema_info += "\n"

        cursor.close()
        connection.close()
        return schema_info
    except Exception as e:
        logger.error(f"Error getting database schema: {e}")
        return f"Error getting schema: {e}"


# Initialize database on startup
try:
    init_database()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")


# === MCP TOOLS ===


@mcp.tool()
async def execute_sql_query(query: str) -> str:
    """Execute a SQL query and return the results.

    Args:
        query: The SQL query to execute (SELECT, INSERT, UPDATE, DELETE, etc.)
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Execute the query
        cursor.execute(query)

        # For SELECT queries, fetch the results
        if query.strip().upper().startswith("SELECT"):
            results = cursor.fetchall()

            if not results:
                cursor.close()
                connection.close()
                return "Query executed successfully. No results returned."

            # Format results as a readable string
            output = f"Query Results ({len(results)} rows):\n\n"

            # Add headers
            if results:
                headers = list(results[0].keys())
                output += "| " + " | ".join(headers) + " |\n"
                output += (
                    "|" + "|".join(["-" * len(header) for header in headers]) + "|\n"
                )

                # Add data rows
                for row in results:
                    output += (
                        "| "
                        + " | ".join(str(row[header]) for header in headers)
                        + " |\n"
                    )

            cursor.close()
            connection.close()
            return output

        else:
            # For non-SELECT queries, return affected rows
            affected_rows = cursor.rowcount
            connection.commit()
            cursor.close()
            connection.close()
            return f"Query executed successfully. {affected_rows} rows affected."

    except Exception as e:
        return f"Error executing query: {str(e)}"


@mcp.tool()
async def natural_language_query(natural_query: str) -> str:
    """Convert natural language to SQL and execute the query.

    Args:
        natural_query: A natural language description of the query you want to execute
    """
    try:
        # Get database schema
        schema_info = get_database_schema()

        # Convert natural language to SQL
        sql_query = natural_language_to_sql(natural_query, schema_info)

        # Execute the SQL query
        return await execute_sql_query(sql_query)

    except Exception as e:
        return f"Error processing natural language query: {str(e)}"


@mcp.tool()
async def list_tables() -> str:
    """List all tables in the database."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        cursor.close()
        connection.close()

        if not tables:
            return "No tables found in the database."

        output = "Tables in the database:\n\n"
        for i, table in enumerate(tables, 1):
            table_name = table[0]
            output += f"{i}. {table_name}\n"

        return output

    except Exception as e:
        return f"Error listing tables: {str(e)}"


@mcp.tool()
async def describe_table(table_name: str) -> str:
    """Get detailed information about a specific table.

    Args:
        table_name: The name of the table to describe
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Check if table exists
        cursor.execute("SHOW TABLES")
        tables = [list(table.values())[0] for table in cursor.fetchall()]

        if table_name not in tables:
            cursor.close()
            connection.close()
            return (
                f"Table '{table_name}' not found. Available tables: {', '.join(tables)}"
            )

        # Get table structure
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()

        # Get row count
        cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        row_count = cursor.fetchone()["count"]

        cursor.close()
        connection.close()

        output = f"Table: {table_name}\n"
        output += f"Rows: {row_count}\n\n"
        output += "Columns:\n\n"

        for col in columns:
            output += f"- {col['Field']}: {col['Type']}\n"
            output += f"  - Null: {'YES' if col['Null'] == 'YES' else 'NO'}\n"
            output += f"  - Key: {col['Key'] or 'None'}\n"
            output += f"  - Default: {col['Default'] or 'None'}\n"
            output += f"  - Extra: {col['Extra'] or 'None'}\n\n"

        return output

    except Exception as e:
        return f"Error describing table: {str(e)}"


@mcp.tool()
async def get_table_data(table_name: str, limit: int = 10) -> str:
    """Get sample data from a table.

    Args:
        table_name: The name of the table
        limit: Maximum number of rows to return (default: 10)
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Check if table exists
        cursor.execute("SHOW TABLES")
        tables = [list(table.values())[0] for table in cursor.fetchall()]

        if table_name not in tables:
            cursor.close()
            connection.close()
            return (
                f"Table '{table_name}' not found. Available tables: {', '.join(tables)}"
            )

        # Get sample data
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        cursor.execute(query)
        results = cursor.fetchall()

        cursor.close()
        connection.close()

        if not results:
            return f"No data found in table '{table_name}'."

        # Format results
        output = f"Sample data from {table_name} (showing {len(results)} rows):\n\n"

        # Add headers
        headers = list(results[0].keys())
        output += "| " + " | ".join(headers) + " |\n"
        output += "|" + "|".join(["-" * len(header) for header in headers]) + "|\n"

        # Add data rows
        for row in results:
            output += "| " + " | ".join(str(row[header]) for header in headers) + " |\n"

        return output

    except Exception as e:
        return f"Error getting table data: {str(e)}"


# === MCP RESOURCES ===


@mcp.resource("schema://database")
async def get_database_schema_resource() -> str:
    """Get the complete database schema as a resource."""
    return get_database_schema()


@mcp.resource("schema://tables/{table_name}")
async def get_table_schema_resource(table_name: str) -> str:
    """Get schema information for a specific table.

    Args:
        table_name: The name of the table
    """
    return await describe_table(table_name)


@mcp.resource("data://tables/{table_name}")
async def get_table_data_resource(table_name: str) -> str:
    """Get sample data from a table as a resource.

    Args:
        table_name: The name of the table
    """
    return await get_table_data(table_name, limit=5)


# === MCP PROMPTS ===


@mcp.prompt()
def sql_query_assistant(query_description: str) -> str:
    """Generate a prompt for helping with SQL query creation.

    Args:
        query_description: Description of what you want to query
    """
    return f"""I need help creating a SQL query for the following request:

        {query_description}

        Please help me by:
        1. Understanding what data I need to retrieve
        2. Suggesting the appropriate SQL query
        3. Explaining how the query works

        I have access to the database schema and can execute queries to test them.
    """


@mcp.prompt()
def database_analysis_task(analysis_goal: str) -> str:
    """Generate a prompt for database analysis tasks.

    Args:
        analysis_goal: What you want to analyze in the database
    """
    return f"""I need to perform a database analysis with the following goal:

        {analysis_goal}

        Please help me by:
        1. Understanding what tables and data are relevant
        2. Suggesting the queries needed to gather the required information
        3. Helping me interpret the results

        I can explore the database schema, execute queries, and analyze the data.
    """


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
