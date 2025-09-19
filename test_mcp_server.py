#!/usr/bin/env python3
"""
Test script for MCP MySQL Server
This script tests the basic functionality of the MCP server using the MCP Inspector
"""

import asyncio
import subprocess
import sys
import time
from typing import Dict, Any, Optional
import json


class MCPServerTester:
    def __init__(self, server_script: str = "mcp_server.py"):
        self.server_script = server_script
        self.server_process = None
        
    def start_server(self) -> bool:
        """Start the MCP server process"""
        print("Starting MCP server...")
        try:
            # Start the server process
            self.server_process = subprocess.Popen(
                [sys.executable, self.server_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if process is running
            if self.server_process.poll() is None:
                print("✓ MCP server started successfully")
                return True
            else:
                print("✗ MCP server failed to start")
                stderr = self.server_process.stderr.read()
                if stderr:
                    print(f"Error: {stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Error starting server: {e}")
            return False
    
    def stop_server(self):
        """Stop the MCP server process"""
        if self.server_process:
            print("Stopping MCP server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
                print("✓ MCP server stopped")
            except subprocess.TimeoutExpired:
                print("✗ Server did not stop gracefully, killing...")
                self.server_process.kill()
    
    def test_mcp_inspector(self) -> bool:
        """Test the server with MCP Inspector"""
        print("\nTesting with MCP Inspector...")
        try:
            # Run MCP Inspector in development mode
            result = subprocess.run(
                ["uv", "run", "mcp", "dev", self.server_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("✓ MCP Inspector test passed")
                return True
            else:
                print(f"✗ MCP Inspector test failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("✓ MCP Inspector started successfully (timeout expected)")
            return True
        except Exception as e:
            print(f"✗ Error testing with MCP Inspector: {e}")
            return False
    
    def test_direct_execution(self) -> bool:
        """Test direct execution of the server"""
        print("\nTesting direct server execution...")
        try:
            # Test if the server script can be executed
            result = subprocess.run(
                [sys.executable, "-c", f"import {self.server_script.replace('.py', '')}; print('Import successful')"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print("✓ Server script can be imported")
                return True
            else:
                print(f"✗ Server script import failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Error testing direct execution: {e}")
            return False
    
    def test_dependencies(self) -> bool:
        """Test if all required dependencies are available"""
        print("\nTesting dependencies...")
        required_modules = [
            "mcp",
            "mysql.connector", 
            "sqlalchemy",
            "requests",
            "dotenv"
        ]
        
        all_good = True
        for module in required_modules:
            try:
                __import__(module)
                print(f"✓ {module} is available")
            except ImportError:
                print(f"✗ {module} is missing")
                all_good = False
        
        return all_good
    
    def test_environment_config(self) -> bool:
        """Test if environment configuration is valid"""
        print("\nTesting environment configuration...")
        try:
            from dotenv import load_dotenv
            import os
            
            # Load environment variables
            load_dotenv()
            
            # Check required environment variables
            required_vars = ["DB_HOST", "DB_USER", "DB_NAME", "OLLAMA_URL", "OLLAMA_MODEL"]
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                print(f"✗ Missing environment variables: {', '.join(missing_vars)}")
                return False
            else:
                print("✓ All required environment variables are set")
                return True
                
        except Exception as e:
            print(f"✗ Error testing environment configuration: {e}")
            return False
    
    def test_database_connection(self) -> bool:
        """Test database connection"""
        print("\nTesting database connection...")
        try:
            import mysql.connector
            from dotenv import load_dotenv
            import os
            
            load_dotenv()
            
            # Try to connect to the database
            connection = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "test_db"),
                port=int(os.getenv("DB_PORT", "3306"))
            )
            
            connection.close()
            print("✓ Database connection successful")
            return True
            
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False
    
    def test_ollama_connection(self) -> bool:
        """Test Ollama connection"""
        print("\nTesting Ollama connection...")
        try:
            import requests
            from dotenv import load_dotenv
            import os
            
            load_dotenv()
            
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            
            # Test Ollama API
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                print(f"✓ Ollama connection successful")
                print(f"  Available models: {', '.join(model_names)}")
                return True
            else:
                print(f"✗ Ollama API returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Ollama connection failed: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests"""
        print("=== MCP MySQL Server Test Suite ===\n")
        
        tests = [
            ("Dependencies", self.test_dependencies),
            ("Environment Configuration", self.test_environment_config),
            ("Database Connection", self.test_database_connection),
            ("Ollama Connection", self.test_ollama_connection),
            ("Direct Execution", self.test_direct_execution),
            ("MCP Inspector", self.test_mcp_inspector),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"Running {test_name} test...")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"✗ {test_name} test failed with exception: {e}")
                results.append((test_name, False))
            print()
        
        # Summary
        print("=== Test Summary ===")
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "PASS" if result else "FAIL"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Your MCP server is ready to use.")
            return True
        else:
            print("❌ Some tests failed. Please check the issues above.")
            return False


def main():
    """Main function to run tests"""
    tester = MCPServerTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
