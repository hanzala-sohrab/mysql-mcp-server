# MCP MySQL Server

A proper Model Context Protocol (MCP) server that enables natural language interaction with MySQL databases using Ollama and Llama 3.2.

## Features

- **MCP Protocol Compliance**: Implements the official Model Context Protocol specification
- **Natural Language to SQL**: Convert natural language queries to SQL using Llama 3.2
- **Direct SQL Execution**: Execute raw SQL queries safely
- **Database Schema Exploration**: Explore database structure and table information
- **MCP Tools**: Expose database operations as MCP tools
- **MCP Resources**: Provide database schema and data as MCP resources
- **MCP Prompts**: Offer helpful prompts for database analysis
- **Error Handling**: Comprehensive error handling and logging

## Prerequisites

- Python 3.10+
- MySQL Server
- Ollama running with Llama 3.2 model
- MCP-compatible client (Claude Desktop, Windsurf, etc.)

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

Edit `.env` with your MySQL database configuration:

```env
# MySQL Database Configuration
DB_HOST=localhost
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=your_database_name
DB_PORT=3306

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

## MCP Tools

The server exposes the following MCP tools:

### `execute_sql_query`
Execute a SQL query and return the results.
- **Parameters**: `query` (string) - The SQL query to execute
- **Returns**: Formatted query results

### `natural_language_query`
Convert natural language to SQL and execute the query.
- **Parameters**: `natural_query` (string) - Natural language description of the query
- **Returns**: Query results after converting to SQL

### `list_tables`
List all tables in the database.
- **Parameters**: None
- **Returns**: List of all tables

### `describe_table`
Get detailed information about a specific table.
- **Parameters**: `table_name` (string) - Name of the table to describe
- **Returns**: Table structure and row count

### `get_table_data`
Get sample data from a table.
- **Parameters**: 
  - `table_name` (string) - Name of the table
  - `limit` (integer, optional) - Maximum rows to return (default: 10)
- **Returns**: Sample data from the table

## MCP Resources

The server provides the following MCP resources:

### `schema://database`
Get the complete database schema as a resource.

### `schema://tables/{table_name}`
Get schema information for a specific table.

### `data://tables/{table_name}`
Get sample data from a table as a resource.

## MCP Prompts

The server offers the following MCP prompts:

### `sql_query_assistant`
Generate a prompt for helping with SQL query creation.
- **Parameters**: `query_description` (string) - Description of what you want to query

### `database_analysis_task`
Generate a prompt for database analysis tasks.
- **Parameters**: `analysis_goal` (string) - What you want to analyze in the database

## Running the Server

### Development Mode

Run the server in development mode with MCP Inspector:

```bash
uv run mcp dev mcp_server.py
```

### Production Mode

Run the server with stdio transport:

```bash
python mcp_server.py
```

## Integration with MCP Clients

### Claude Desktop

1. Open Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the server configuration:

```json
{
  "mcpServers": {
    "mysql": {
      "command": "python",
      "args": ["/path/to/your/project/mcp_server.py"],
      "env": {
        "DB_HOST": "localhost",
        "DB_USER": "your_mysql_user",
        "DB_PASSWORD": "your_mysql_password",
        "DB_NAME": "your_database_name"
      }
    }
  }
}
```

3. Restart Claude Desktop

### Windsurf Editor

1. Open MCP settings in Windsurf
2. Add a new MCP server with the following configuration:
   - **Name**: `mysql`
   - **Command**: `python`
   - **Args**: `/path/to/your/project/mcp_server.py`
   - **Environment variables**: Your database configuration

## Usage Examples

### Natural Language Queries

Once connected to an MCP client, you can use natural language:

```
"Show me all users from the users table"
"Find orders placed in the last 30 days"
"Count the number of products in each category"
```

### Direct SQL Queries

```
"Execute: SELECT * FROM users WHERE created_at > '2024-01-01'"
"Run: UPDATE products SET price = price * 1.1 WHERE category = 'electronics'"
```

### Database Exploration

```
"List all tables in the database"
"Describe the structure of the orders table"
"Show me sample data from the customers table"
```

## Testing

Use the provided test script to verify the server functionality:

```bash
python test_mcp_server.py
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify MySQL is running
   - Check database credentials in `.env`
   - Ensure the database exists

2. **Ollama Connection Issues**
   - Verify Ollama is running: `ollama serve`
   - Check if Llama 3.2 is pulled: `ollama list`
   - Verify Ollama URL is correct

3. **MCP Server Not Detected**
   - Check server configuration in client settings
   - Verify the server script path is correct
   - Check for syntax errors in the server code

### Debug Mode

Enable debug logging by setting the log level:

```env
LOG_LEVEL=DEBUG
```

## Security Considerations

- Never expose your `.env` file in production
- Use database users with limited privileges
- Consider using connection pooling for production
- Validate all SQL queries to prevent injection attacks
- Use HTTPS for Ollama connections in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section
- Review MCP documentation at https://modelcontextprotocol.io
- Open an issue in the project repository
