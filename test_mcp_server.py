#!/usr/bin/env python3
"""
Test script for MCP MySQL Server
This script tests the basic functionality of the MCP server
"""

import requests
import json
import time
import sys
from typing import Dict, Any

class MCPServerTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def wait_for_server(self, timeout: int = 30) -> bool:
        """Wait for the server to be ready"""
        print("Waiting for server to be ready...")
        for i in range(timeout):
            try:
                response = self.session.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    print("✓ Server is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
            print(f"Waiting... ({i+1}/{timeout})")
        
        print("✗ Server did not become ready in time")
        return False
    
    def test_health_check(self) -> bool:
        """Test the health check endpoint"""
        print("\nTesting health check...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Health check passed: {data}")
                return True
            else:
                print(f"✗ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Health check error: {e}")
            return False
    
    def test_get_schema(self) -> bool:
        """Test getting database schema"""
        print("\nTesting schema endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/schema")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Schema retrieved successfully")
                print(f"  Found {len(data)} tables")
                for table in data:
                    print(f"  - {table['name']}: {len(table['columns'])} columns")
                return True
            else:
                print(f"✗ Schema retrieval failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Schema error: {e}")
            return False
    
    def test_get_tables(self) -> bool:
        """Test getting all tables"""
        print("\nTesting tables endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/tables")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Tables retrieved successfully")
                print(f"  Tables: {data['tables']}")
                return True
            else:
                print(f"✗ Tables retrieval failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Tables error: {e}")
            return False
    
    def test_sql_query(self) -> bool:
        """Test executing a simple SQL query"""
        print("\nTesting SQL query execution...")
        try:
            payload = {
                "query": "SELECT 1 as test_column",
                "natural_language": False
            }
            response = self.session.post(f"{self.base_url}/query", json=payload)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ SQL query executed successfully")
                print(f"  Result: {data}")
                return True
            else:
                print(f"✗ SQL query failed: {response.status_code}")
                print(f"  Error: {response.text}")
                return False
        except Exception as e:
            print(f"✗ SQL query error: {e}")
            return False
    
    def test_natural_language_query(self) -> bool:
        """Test natural language to SQL conversion and execution"""
        print("\nTesting natural language query...")
        try:
            payload = {
                "query": "Show me the number 1 as test",
                "natural_language": True
            }
            response = self.session.post(f"{self.base_url}/query", json=payload)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Natural language query executed successfully")
                print(f"  Generated SQL: {data.get('sql_query', 'N/A')}")
                print(f"  Result: {data}")
                return True
            else:
                print(f"✗ Natural language query failed: {response.status_code}")
                print(f"  Error: {response.text}")
                return False
        except Exception as e:
            print(f"✗ Natural language query error: {e}")
            return False
    
    def test_table_info(self) -> bool:
        """Test getting table information"""
        print("\nTesting table info endpoint...")
        try:
            # First get tables to find one to test
            tables_response = self.session.get(f"{self.base_url}/tables")
            if tables_response.status_code != 200:
                print("✗ Could not get tables list")
                return False
            
            tables_data = tables_response.json()
            if not tables_data['tables']:
                print("✗ No tables found in database")
                return False
            
            # Test with the first table
            table_name = tables_data['tables'][0]
            response = self.session.get(f"{self.base_url}/table/{table_name}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Table info retrieved successfully for '{table_name}'")
                print(f"  Columns: {len(data['columns'])}")
                print(f"  Sample rows: {len(data['sample_data'])}")
                return True
            else:
                print(f"✗ Table info failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Table info error: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests and return overall success status"""
        print("🚀 Starting MCP Server Tests")
        print("=" * 50)
        
        # Wait for server to be ready
        if not self.wait_for_server():
            return False
        
        tests = [
            self.test_health_check,
            self.test_get_schema,
            self.test_get_tables,
            self.test_sql_query,
            self.test_natural_language_query,
            self.test_table_info
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! MCP Server is working correctly.")
            return True
        else:
            print("❌ Some tests failed. Please check the server configuration.")
            return False

def main():
    """Main function to run tests"""
    print("MCP MySQL Server Test Script")
    print("Make sure the server is running: python mcp_server.py")
    print()
    
    # Check if server URL is provided as argument
    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    tester = MCPServerTester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
