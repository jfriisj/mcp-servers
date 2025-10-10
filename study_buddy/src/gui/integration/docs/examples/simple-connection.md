# Simple Connection Example

**Basic MCP connection with minimal setup - perfect for getting started.**

## 🎯 Overview

This example shows the simplest way to establish an MCP connection and perform basic operations. Use this as a starting point for more complex integrations.

## 📋 Prerequisites

- Study Buddy MCP server running
- Python 3.8+
- Basic async/await understanding

## 🚀 Minimal Connection

### Basic Setup

```python
import asyncio
from gui.integration import MCPClient, ConfigManager

async def simple_connection():
    """Minimal MCP connection example"""
    
    # 1. Create configuration
    config = ConfigManager({
        "server_path": "mcp-server/main.py",
        "timeout": 30
    })
    
    # 2. Create client
    client = MCPClient(config)
    
    # 3. Connect
    success = await client.connect()
    
    if success:
        print("✅ Connected to MCP server!")
        
        # 4. Test basic operation
        result = await client.list_documents()
        
        if result.success:
            docs = result.data.get("documents", [])
            print(f"📚 Found {len(docs)} documents")
        else:
            print(f"❌ Error: {result.error_message}")
        
        # 5. Disconnect
        await client.disconnect()
        print("🔌 Disconnected")
    
    else:
        print("❌ Failed to connect")

# Run the example
asyncio.run(simple_connection())
```

## 🔧 Configuration Options

### Default Configuration (STDIO)

```python
# Minimal - uses defaults
config = ConfigManager({
    "server_path": "mcp-server/main.py"
})

# Equivalent full configuration
config = ConfigManager({
    "connection_type": "stdio",
    "server_command": ["python", "mcp-server/main.py"],
    "server_working_dir": None,  # Uses current directory
    "timeout": 30,
    "retry_attempts": 3,
    "log_level": "INFO"
})
```

### HTTP Configuration

```python
# HTTP connection (if server supports it)
config = ConfigManager({
    "connection_type": "http",
    "server_host": "localhost",
    "server_port": 3000,
    "timeout": 30
})
```

### Development Configuration

```python
# Development setup with debug logging
config = ConfigManager({
    "server_path": "mcp-server/main.py",
    "timeout": 10,           # Shorter timeout for quick feedback
    "retry_attempts": 1,     # Fast failure for debugging
    "log_level": "DEBUG"     # Detailed logging
})
```

## 📤 Document Upload Example

```python
async def upload_example():
    """Simple document upload example"""
    
    config = ConfigManager({"server_path": "mcp-server/main.py"})
    client = MCPClient(config)
    
    try:
        # Connect
        await client.connect()
        
        # Upload a document
        result = await client.upload_document("/path/to/document.pdf")
        
        if result.success:
            doc_id = result.data["document_id"]
            title = result.data["title"]
            print(f"✅ Uploaded: {title} (ID: {doc_id})")
        else:
            print(f"❌ Upload failed: {result.error_message}")
    
    finally:
        # Always disconnect
        await client.disconnect()

asyncio.run(upload_example())
```

## 📋 Document Management Example

```python
async def document_management_example():
    """Example showing basic document operations"""
    
    config = ConfigManager({"server_path": "mcp-server/main.py"})
    client = MCPClient(config)
    
    await client.connect()
    
    try:
        # 1. Upload a document
        print("📤 Uploading document...")
        upload_result = await client.upload_document(
            file_path="/path/to/sample.pdf",
            title="Sample Document",
            tags=["example", "test"]
        )
        
        if not upload_result.success:
            print(f"❌ Upload failed: {upload_result.error_message}")
            return
        
        doc_id = upload_result.data["document_id"]
        print(f"✅ Document uploaded with ID: {doc_id}")
        
        # 2. List all documents
        print("\\n📋 Listing documents...")
        list_result = await client.list_documents()
        
        if list_result.success:
            documents = list_result.data["documents"]
            print(f"📚 Found {len(documents)} documents:")
            
            for doc in documents:
                print(f"  • {doc['title']} ({doc['file_type']}) - ID: {doc['id']}")
        
        # 3. Get specific document details
        print(f"\\n📄 Getting document {doc_id} details...")
        get_result = await client.get_document(doc_id)
        
        if get_result.success:
            doc = get_result.data
            print(f"Title: {doc['title']}")
            print(f"Type: {doc['file_type']}")
            print(f"Pages: {doc['total_pages']}")
            print(f"Words: {doc['total_words']}")
            print(f"Indexed: {'Yes' if doc['indexed'] else 'No'}")
        
        # 4. Search documents
        print("\\n🔍 Searching documents...")
        search_result = await client.search_documents("sample")
        
        if search_result.success:
            results = search_result.data["results"]
            print(f"🎯 Found {len(results)} matching documents")
        
        # 5. Clean up (delete the test document)
        print(f"\\n🗑️ Cleaning up test document...")
        delete_result = await client.delete_document(doc_id)
        
        if delete_result.success:
            print("✅ Document deleted successfully")
        else:
            print(f"❌ Delete failed: {delete_result.error_message}")
    
    finally:
        await client.disconnect()
        print("\\n🔌 Disconnected from server")

asyncio.run(document_management_example())
```

## 🔍 Health Check Example

```python
async def health_check_example():
    """Check MCP server health and connection status"""
    
    config = ConfigManager({"server_path": "mcp-server/main.py"})
    client = MCPClient(config)
    
    # Test connection
    print("🔌 Testing connection...")
    success = await client.connect()
    
    if not success:
        print("❌ Failed to connect to server")
        return
    
    # Get health status
    print("\\n📊 Checking server health...")
    health = await client.get_health_status()
    
    print(f"Connection: {'✅ Healthy' if health.is_connected else '❌ Unhealthy'}")
    print(f"State: {health.connection_state.value}")
    print(f"Uptime: {health.uptime_seconds:.1f} seconds")
    print(f"Total Operations: {health.total_operations}")
    print(f"Error Count: {health.error_count}")
    print(f"Error Rate: {health.error_rate:.1f}%")
    
    if health.round_trip_time_ms:
        print(f"Response Time: {health.round_trip_time_ms:.1f}ms")
    
    # Performance assessment
    if health.error_rate > 10:
        print("⚠️ High error rate - server may have issues")
    elif health.round_trip_time_ms and health.round_trip_time_ms > 1000:
        print("⚠️ High latency - check network connection")
    else:
        print("🚀 Server performance looks good!")
    
    await client.disconnect()

asyncio.run(health_check_example())
```

## 📊 Progress Tracking Example

```python
async def progress_tracking_example():
    """Example with progress tracking for long operations"""
    
    def progress_callback(progress):
        """Handle progress updates"""
        phase = progress.phase.name
        percent = progress.progress_percent
        step = progress.current_step
        
        # Simple progress bar
        bar_length = 20
        filled = int(percent / 100 * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        print(f"\\r[{bar}] {percent:5.1f}% - {phase}: {step}", end="", flush=True)
    
    config = ConfigManager({"server_path": "mcp-server/main.py"})
    client = MCPClient(config)
    
    await client.connect()
    
    try:
        print("📤 Uploading document with progress tracking...")
        
        # Upload with progress callback
        result = await client.upload_document(
            file_path="/path/to/large-document.pdf",
            progress_callback=progress_callback
        )
        
        print()  # New line after progress bar
        
        if result.success:
            doc_id = result.data["document_id"]
            print(f"✅ Upload completed! Document ID: {doc_id}")
            
            # Index with progress tracking
            print("\\n🔍 Indexing document with progress tracking...")
            
            index_result = await client.index_document(
                document_id=doc_id,
                strategy="auto",
                progress_callback=progress_callback
            )
            
            print()  # New line after progress bar
            
            if index_result.success:
                chunks = index_result.data["chunks_created"]
                print(f"✅ Indexing completed! Created {chunks} chunks")
            else:
                print(f"❌ Indexing failed: {index_result.error_message}")
        
        else:
            print(f"❌ Upload failed: {result.error_message}")
    
    finally:
        await client.disconnect()

# Note: Use a real large file path for this example
# asyncio.run(progress_tracking_example())
```

## 🎯 Error Handling Example

```python
from gui.integration import (
    MCPConnectionError, 
    MCPToolError, 
    TimeoutError
)

async def error_handling_example():
    """Example with comprehensive error handling"""
    
    config = ConfigManager({"server_path": "mcp-server/main.py"})
    client = MCPClient(config)
    
    try:
        # Attempt connection with error handling
        print("🔌 Connecting to server...")
        success = await client.connect()
        
        if not success:
            print("❌ Initial connection failed")
            return
        
        print("✅ Connected successfully")
        
        # Try uploading a non-existent file (will cause error)
        print("\\n📤 Testing error handling with invalid file...")
        
        try:
            result = await client.upload_document("/nonexistent/file.pdf")
            
            # Check result even if no exception
            if result.success:
                print("✅ Upload succeeded unexpectedly")
            else:
                print(f"📝 Tool-level error (expected): {result.error_message}")
        
        except MCPConnectionError as e:
            print(f"🔗 Connection error: {e}")
            # Could attempt reconnection here
            
        except TimeoutError as e:
            print(f"⏰ Operation timed out: {e}")
            # Could retry with longer timeout
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        # Try a valid operation
        print("\\n📋 Testing valid operation...")
        list_result = await client.list_documents()
        
        if list_result.success:
            docs = list_result.data["documents"]
            print(f"✅ Successfully retrieved {len(docs)} documents")
        else:
            print(f"❌ List operation failed: {list_result.error_message}")
    
    except MCPConnectionError as e:
        print(f"❌ Failed to establish initial connection: {e}")
        
    except Exception as e:
        print(f"❌ Unexpected initialization error: {e}")
    
    finally:
        # Always attempt cleanup
        try:
            await client.disconnect()
            print("\\n🔌 Disconnected successfully")
        except Exception as e:
            print(f"⚠️ Error during disconnect: {e}")

asyncio.run(error_handling_example())
```

## 🔄 Retry Logic Example

```python
async def retry_example():
    """Example with custom retry logic"""
    
    async def upload_with_retry(client, file_path, max_retries=3):
        """Upload document with custom retry logic"""
        
        for attempt in range(max_retries):
            try:
                print(f"📤 Upload attempt {attempt + 1}/{max_retries}...")
                
                result = await client.upload_document(file_path)
                
                if result.success:
                    print(f"✅ Upload successful on attempt {attempt + 1}")
                    return result
                else:
                    print(f"❌ Attempt {attempt + 1} failed: {result.error_message}")
                    
                    # Don't retry certain errors
                    if "not found" in result.error_message.lower():
                        print("🚫 File not found - not retrying")
                        break
            
            except MCPConnectionError as e:
                print(f"🔗 Connection error on attempt {attempt + 1}: {e}")
                
                # Try to reconnect
                if attempt < max_retries - 1:
                    print("🔄 Attempting to reconnect...")
                    await client.disconnect()
                    await asyncio.sleep(2)  # Wait before retry
                    
                    reconnect_success = await client.connect()
                    if not reconnect_success:
                        print("❌ Reconnection failed")
                        break
            
            except Exception as e:
                print(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
                
                # Wait before retry (exponential backoff)
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 1s, 2s, 4s...
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
        
        print(f"❌ All {max_retries} attempts failed")
        return None
    
    # Main retry example
    config = ConfigManager({"server_path": "mcp-server/main.py"})
    client = MCPClient(config)
    
    try:
        await client.connect()
        
        # Upload with retry logic
        result = await upload_with_retry(
            client, 
            "/path/to/document.pdf",  # Use a real file path
            max_retries=3
        )
        
        if result and result.success:
            print(f"🎉 Final result: Document uploaded with ID {result.data['document_id']}")
        else:
            print("😞 Upload ultimately failed after all retries")
    
    finally:
        await client.disconnect()

# Note: Use a real file path for this example
# asyncio.run(retry_example())
```

## 🧪 Testing Connection

```python
async def test_connection():
    """Test basic connection functionality"""
    
    config = ConfigManager({"server_path": "mcp-server/main.py"})
    client = MCPClient(config)
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Connection
    print("🧪 Test 1: Connection")
    try:
        success = await client.connect()
        if success:
            print("  ✅ Connection successful")
            tests_passed += 1
        else:
            print("  ❌ Connection failed")
    except Exception as e:
        print(f"  ❌ Connection exception: {e}")
    
    # Test 2: Health check
    print("\\n🧪 Test 2: Health check")
    try:
        if await client.is_healthy():
            print("  ✅ Health check passed")
            tests_passed += 1
        else:
            print("  ❌ Health check failed")
    except Exception as e:
        print(f"  ❌ Health check exception: {e}")
    
    # Test 3: List documents
    print("\\n🧪 Test 3: List documents")
    try:
        result = await client.list_documents()
        if result.success:
            docs = result.data.get("documents", [])
            print(f"  ✅ Retrieved {len(docs)} documents")
            tests_passed += 1
        else:
            print(f"  ❌ List failed: {result.error_message}")
    except Exception as e:
        print(f"  ❌ List exception: {e}")
    
    # Test 4: Disconnection
    print("\\n🧪 Test 4: Disconnection")
    try:
        await client.disconnect()
        print("  ✅ Disconnection successful")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ Disconnection exception: {e}")
    
    # Summary
    print(f"\\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! MCP integration is working correctly.")
    elif tests_passed >= total_tests // 2:
        print("⚠️ Some tests failed. Check server configuration.")
    else:
        print("❌ Most tests failed. Server may not be running or configured correctly.")
    
    return tests_passed == total_tests

# Run the connection test
asyncio.run(test_connection())
```

## 📝 Complete Minimal Example

Here's a complete, runnable example you can copy and use:

```python
#!/usr/bin/env python3
"""
Minimal MCP connection example for Study Buddy.
Copy this file and run it to test your MCP integration.
"""

import asyncio
import os
from pathlib import Path

# Adjust this import based on your setup
from gui.integration import MCPClient, ConfigManager

async def main():
    """Main example function"""
    
    print("🚀 Study Buddy MCP Connection Example\\n")
    
    # Configuration - adjust paths as needed
    config = ConfigManager({
        "server_path": "mcp-server/main.py",  # Adjust this path
        "timeout": 30,
        "log_level": "INFO"
    })
    
    # Create client
    client = MCPClient(config)
    
    try:
        # 1. Connect
        print("🔌 Connecting to MCP server...")
        success = await client.connect()
        
        if not success:
            print("❌ Failed to connect. Is the MCP server running?")
            return
        
        print("✅ Connected successfully!")
        
        # 2. Check health
        print("\\n📊 Checking server health...")
        health = await client.get_health_status()
        print(f"Status: {'Healthy' if health.is_connected else 'Unhealthy'}")
        print(f"Uptime: {health.uptime_seconds:.1f} seconds")
        
        # 3. List documents
        print("\\n📋 Listing documents...")
        result = await client.list_documents()
        
        if result.success:
            documents = result.data.get("documents", [])
            print(f"Found {len(documents)} documents:")
            
            for i, doc in enumerate(documents[:5]):  # Show first 5
                print(f"  {i+1}. {doc['title']} ({doc['file_type']})")
                
            if len(documents) > 5:
                print(f"  ... and {len(documents) - 5} more")
        else:
            print(f"Failed to list documents: {result.error_message}")
        
        # 4. Upload example (optional)
        sample_file = "sample.txt"
        if os.path.exists(sample_file):
            print(f"\\n📤 Uploading {sample_file}...")
            upload_result = await client.upload_document(sample_file)
            
            if upload_result.success:
                doc_id = upload_result.data["document_id"]
                print(f"✅ Uploaded successfully! Document ID: {doc_id}")
            else:
                print(f"❌ Upload failed: {upload_result.error_message}")
        else:
            print(f"\\n💡 Create a '{sample_file}' file to test upload functionality")
        
        print("\\n🎉 Example completed successfully!")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Always disconnect
        print("\\n🔌 Disconnecting...")
        await client.disconnect()
        print("✅ Disconnected successfully")

if __name__ == "__main__":
    # Create a sample file for testing
    with open("sample.txt", "w") as f:
        f.write("This is a sample document for testing MCP integration.\\n")
        f.write("It contains some example content to demonstrate upload functionality.\\n")
    
    # Run the example
    asyncio.run(main())
    
    # Clean up sample file
    try:
        os.remove("sample.txt")
    except:
        pass
```

## 🚀 Next Steps

Once you have the basic connection working:

1. **[Basic Integration Guide](../guides/basic-integration.md)** - Learn complete GUI integration
2. **[Tool Invocation Examples](tool-invocation.md)** - Explore all available MCP tools
3. **[Event Handling Examples](event-handling.md)** - Handle connection events and progress
4. **[Configuration Examples](configuration.md)** - Advanced configuration options

---

## 🆘 Troubleshooting

**Connection fails?**
- Check if MCP server is running
- Verify the `server_path` in configuration
- Try running the server manually first

**Import errors?**
- Ensure `gui.integration` module is in your Python path
- Check that all dependencies are installed

**Timeout errors?**
- Increase timeout in configuration
- Check server performance and resources

See the **[Troubleshooting Guide](../troubleshooting.md)** for detailed solutions.

---

**This example provides the foundation for all MCP integration. Build on it to create powerful document management applications!**