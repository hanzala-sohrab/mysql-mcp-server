import os
import json
import logging
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MCP MySQL Server",
    description="MCP server for MySQL database operations with Ollama/Llama 3.2 integration",
)

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


class QueryRequest(BaseModel):
    query: str
    natural_language: bool = False


class QueryResponse(BaseModel):
    success: bool
    data: Optional[List[Dict]] = None
    message: str
    sql_query: Optional[str] = None


class TableInfo(BaseModel):
    name: str
    columns: List[Dict]


def get_db_connection():
    """Create a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")


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
            raise HTTPException(status_code=500, detail="Ollama API error")
    except Exception as e:
        logger.error(f"Error querying Ollama: {e}")
        raise HTTPException(status_code=500, detail=f"Ollama query error: {e}")


def natural_language_to_sql(natural_query: str, schema_info: str) -> str:
    """Convert natural language query to SQL using Ollama"""
    prompt = f"""
    You are a SQL expert. Convert the following natural language query to SQL.
    
    Database Schema:
    {schema_info}
    
    Natural Language Query: {natural_query}
    
    Return only the SQL query without any explanation or formatting.
    """

    sql_query = query_ollama(prompt)
    # Clean up the response
    sql_query = sql_query.strip().replace("```sql", "").replace("```", "").strip()
    return sql_query


def get_database_schema() -> str:
    """Get database schema information"""
    schema_info = []
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        for table in tables:
            table_name = list(table.values())[0]
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()

            schema_info.append(f"Table: {table_name}")
            for col in columns:
                schema_info.append(f"  - {col['Field']} ({col['Type']})")

        cursor.close()
        connection.close()

        return "\n".join(schema_info)
    except Exception as e:
        logger.error(f"Error getting database schema: {e}")
        return ""


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "MCP MySQL Server is running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        connection = get_db_connection()
        connection.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@app.get("/schema", response_model=List[TableInfo])
async def get_schema():
    """Get database schema"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        tables_info = []

        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        for table in tables:
            table_name = list(table.values())[0]
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()

            table_info = TableInfo(name=table_name, columns=columns)
            tables_info.append(table_info)

        cursor.close()
        connection.close()

        return tables_info
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting schema: {e}")


@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Execute a SQL query or natural language query"""
    try:
        sql_query = request.query
        schema_info = ""

        # If natural language query, convert to SQL first
        if request.natural_language:
            schema_info = get_database_schema()
            sql_query = natural_language_to_sql(request.query, schema_info)

        # Execute the SQL query
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(sql_query)

        # Check if it's a SELECT query or other type
        if sql_query.strip().upper().startswith("SELECT"):
            results = cursor.fetchall()
            data = results
        else:
            # For INSERT, UPDATE, DELETE, etc.
            connection.commit()
            affected_rows = cursor.rowcount
            data = [{"affected_rows": affected_rows}]

        cursor.close()
        connection.close()

        return QueryResponse(
            success=True,
            data=data,
            message="Query executed successfully",
            sql_query=sql_query if request.natural_language else None,
        )

    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=400, detail=f"Database error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@app.get("/tables")
async def get_tables():
    """Get list of all tables in the database"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        cursor.close()
        connection.close()

        # Extract table names from the result
        table_names = [table[0] for table in tables]

        return {"tables": table_names}
    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting tables: {e}")


@app.get("/table/{table_name}")
async def get_table_info(table_name: str):
    """Get information about a specific table"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Get table structure
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()

        # Get first 10 rows as sample data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
        sample_data = cursor.fetchall()

        cursor.close()
        connection.close()

        return {
            "table_name": table_name,
            "columns": columns,
            "sample_data": sample_data,
        }
    except Exception as e:
        logger.error(f"Error getting table info: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting table info: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
