# MCP MySQL Server with Ollama + Llama 3.2

A Model Context Protocol (MCP) server that enables natural language interaction with MySQL databases using Ollama and Llama 3.2.

## Features

- **Natural Language to SQL**: Convert natural language queries to SQL using Llama 3.2
- **Direct SQL Execution**: Execute raw SQL queries
- **Database Schema Exploration**: Explore database structure and table information
- **RESTful API**: FastAPI-based REST endpoints for all operations
- **Health Monitoring**: Built-in health checks for database connectivity
- **Error Handling**: Comprehensive error handling and logging

## Prerequisites

- Python 3.8+
- MySQL Server
- Ollama running with Llama 3.2 model

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Ollama

Make sure Ollama is installed and running:

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Pull Llama 3.2 model
ollama pull llama3.2
```

### 3. Configure Environment

Copy the environment template and configure your database settings:

```bash
cp .env.example .env
```

Edit `.env` file with your MySQL database credentials:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=your_database_name
DB_PORT=3306
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### 4. Run the Server

```bash
python mcp_server.py
```

The server will start on `http://localhost:8000`

## API Endpoints

### Health Check
```bash
GET /health
```

### Get Database Schema
```bash
GET /schema
```

### Get All Tables
```bash
GET /tables
```

### Get Table Information
```bash
GET /table/{table_name}
```

### Execute Query
```bash
POST /query
```

## Usage Examples

### 1. Health Check

```bash
curl http://localhost:8000/health
```

### 2. Get Database Schema

```bash
curl http://localhost:8000/schema
```

### 3. Get All Tables

```bash
curl http://localhost:8000/tables
```

### 4. Get Table Information

```bash
curl http://localhost:8000/table/users
```

### 5. Execute SQL Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM users LIMIT 5",
    "natural_language": false
  }'
```

### 6. Natural Language Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all users from the users table",
    "natural_language": true
  }'
```

### 7. More Natural Language Examples

```bash
# Get count of records
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many users are there in the database?",
    "natural_language": true
  }'

# Get specific columns
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me the names and emails of all users",
    "natural_language": true
  }'

# Filter data
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find all users who joined after January 2024",
    "natural_language": true
  }'
```

## Python Client Example

```python
import requests
import json

class MCPMySQLClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def health_check(self):
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def get_schema(self):
        response = requests.get(f"{self.base_url}/schema")
        return response.json()
    
    def get_tables(self):
        response = requests.get(f"{self.base_url}/tables")
        return response.json()
    
    def get_table_info(self, table_name):
        response = requests.get(f"{self.base_url}/table/{table_name}")
        return response.json()
    
    def execute_sql(self, query):
        payload = {
            "query": query,
            "natural_language": False
        }
        response = requests.post(f"{self.base_url}/query", json=payload)
        return response.json()
    
    def execute_natural_language(self, query):
        payload = {
            "query": query,
            "natural_language": True
        }
        response = requests.post(f"{self.base_url}/query", json=payload)
        return response.json()

# Usage example
client = MCPMySQLClient()

# Check health
print("Health Check:", client.health_check())

# Get tables
print("Tables:", client.get_tables())

# Natural language query
result = client.execute_natural_language("Show me all users")
print("Query Result:", result)

# SQL query
result = client.execute_sql("SELECT COUNT(*) as total FROM users")
print("User Count:", result)
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- `200`: Success
- `400`: Bad Request (invalid SQL, etc.)
- `500`: Internal Server Error (database connection issues, etc.)

## Security Considerations

- Never expose your `.env` file in production
- Use strong database passwords
- Consider adding authentication for production use
- Validate and sanitize all user inputs
- Use HTTPS in production

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check MySQL server is running
   - Verify database credentials in `.env`
   - Ensure database exists

2. **Ollama Connection Failed**
   - Check Ollama service is running: `ollama serve`
   - Verify Llama 3.2 model is pulled: `ollama pull llama3.2`
   - Check Ollama URL and port

3. **SQL Syntax Errors**
   - Review generated SQL queries
   - Check database schema matches expectations
   - Use the `/schema` endpoint to verify table structure

### Debug Mode

Enable debug logging by setting `LOG_LEVEL=DEBUG` in your `.env` file.

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is open source and available under the MIT License.
