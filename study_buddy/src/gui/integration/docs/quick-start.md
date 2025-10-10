# Quick Start Guide

**Get up and running with the Study Buddy GUI Integration Layer in 5 minutes.**

## 🎯 What You'll Learn

- How to establish a basic MCP connection
- How to invoke MCP tools from your GUI
- How to handle responses and errors
- Best practices for integration

## 📋 Prerequisites

- Python 3.8+
- Study Buddy MCP Server running
- Basic understanding of async/await patterns

## 🚀 Step 1: Basic Setup

### Import the Integration Layer

```python
import asyncio
from gui.integration import MCPClient, ConfigManager, MCPConnectionError

# Create configuration
config = ConfigManager({
    "server_path": "mcp-server/main.py",
    "server_args": [],
    "timeout": 30,
    "retry_attempts": 3,
    "log_level": "INFO"
})

# Create client instance
client = MCPClient(config)
```

## 🔌 Step 2: Connect to MCP Server

### Establish Connection

```python
async def connect_to_server():
    try:
        # Connect to the MCP server
        await client.connect()
        print("✅ Connected to MCP server successfully!")
        
        # Verify connection
        if client.is_connected():
            print("🔗 Connection established and verified")
        
    except MCPConnectionError as e:
        print(f"❌ Connection failed: {e}")
        # Handle connection failure
```

### Connection with Error Handling

```python
async def robust_connect():
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            await client.connect()
            print("✅ Connected successfully!")
            break
            
        except MCPConnectionError as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                print("🔄 Retrying in 2 seconds...")
                await asyncio.sleep(2)
            else:
                print("❌ All connection attempts failed")
                raise
```

## 🛠️ Step 3: Invoke MCP Tools

### Simple Tool Invocation

```python
async def upload_document():
    try:
        # Invoke the upload_document tool
        result = await client.invoke_tool("upload_document", {
            "file_path": "/path/to/document.pdf",
            "tags": ["angular", "programming"]
        })
        
        if result.get("success"):
            doc_id = result.get("document_id")
            print(f"✅ Document uploaded successfully! ID: {doc_id}")
            return doc_id
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"❌ Upload failed: {error_msg}")
            
    except Exception as e:
        print(f"❌ Tool invocation failed: {e}")
        return None
```

### Tool Invocation with Progress Tracking

```python
async def upload_with_progress():
    # Set up progress callback
    def progress_callback(status):
        print(f"📊 Progress: {status}")
    
    # Register progress handler
    client.on_event("tool_progress", progress_callback)
    
    try:
        result = await client.invoke_tool("upload_document", {
            "file_path": "/path/to/large_document.pdf"
        })
        
        return result
        
    finally:
        # Clean up event handler
        client.off_event("tool_progress", progress_callback)
```

## 📋 Step 4: List and Manage Documents

### List Documents

```python
async def list_documents():
    try:
        result = await client.invoke_tool("list_documents", {
            "filters": {
                "file_type": "pdf",
                "indexed": True
            },
            "limit": 10
        })
        
        if result.get("success"):
            documents = result.get("documents", [])
            print(f"📚 Found {len(documents)} documents:")
            
            for doc in documents:
                print(f"  • {doc['title']} (ID: {doc['id']})")
                
            return documents
        else:
            print(f"❌ Failed to list documents: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error listing documents: {e}")
        return []
```

### Get Document Details

```python
async def get_document_details(doc_id):
    try:
        result = await client.invoke_tool("get_document", {
            "document_id": doc_id
        })
        
        if result.get("success"):
            doc = result.get("document")
            print(f"📄 Document: {doc['title']}")
            print(f"   Type: {doc['file_type']}")
            print(f"   Pages: {doc['total_pages']}")
            print(f"   Words: {doc['total_words']}")
            print(f"   Indexed: {'✅' if doc['indexed'] else '❌'}")
            
            return doc
        else:
            print(f"❌ Document not found: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error getting document: {e}")
        return None
```

## 🎯 Step 5: Complete Example

Here's a complete working example that demonstrates the core functionality:

```python
import asyncio
from gui.integration import MCPClient, ConfigManager, MCPConnectionError

async def main():
    """Complete example showing MCP integration workflow"""
    
    # 1. Setup
    config = ConfigManager({
        "server_path": "mcp-server/main.py",
        "timeout": 30,
        "retry_attempts": 3
    })
    
    client = MCPClient(config)
    
    try:
        # 2. Connect
        print("🔌 Connecting to MCP server...")
        await client.connect()
        print("✅ Connected successfully!")
        
        # 3. Upload a document
        print("\n📤 Uploading document...")
        upload_result = await client.invoke_tool("upload_document", {
            "file_path": "/path/to/sample.pdf",
            "tags": ["sample", "test"]
        })
        
        if upload_result.get("success"):
            doc_id = upload_result["document_id"]
            print(f"✅ Document uploaded! ID: {doc_id}")
            
            # 4. Get document details
            print(f"\n📄 Retrieving document details...")
            doc_result = await client.invoke_tool("get_document", {
                "document_id": doc_id
            })
            
            if doc_result.get("success"):
                doc = doc_result["document"]
                print(f"📚 Title: {doc['title']}")
                print(f"📊 Pages: {doc['total_pages']}")
                print(f"💬 Words: {doc['total_words']}")
            
            # 5. List all documents
            print(f"\n📋 Listing all documents...")
            list_result = await client.invoke_tool("list_documents")
            
            if list_result.get("success"):
                docs = list_result["documents"]
                print(f"📚 Found {len(docs)} total documents")
        
    except MCPConnectionError as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        # 6. Cleanup
        print("\n🔌 Disconnecting...")
        await client.disconnect()
        print("✅ Disconnected successfully!")

# Run the example
if __name__ == "__main__":
    asyncio.run(main())
```

## ⚡ Performance Tips

### 1. Connection Reuse
```python
# GOOD: Reuse connections
client = MCPClient(config)
await client.connect()

# Multiple tool calls using same connection
result1 = await client.invoke_tool("tool1", params1)
result2 = await client.invoke_tool("tool2", params2)

# BAD: Don't reconnect for each tool
# await client.connect()
# result1 = await client.invoke_tool("tool1", params1)
# await client.disconnect()
# await client.connect()  # Unnecessary reconnection
```

### 2. Batch Operations
```python
# GOOD: Batch multiple operations
documents = await client.invoke_tool("list_documents")
doc_ids = [doc["id"] for doc in documents["documents"]]

# Process in batches
for batch in chunks(doc_ids, 5):
    batch_results = await asyncio.gather(*[
        client.invoke_tool("get_document", {"document_id": doc_id})
        for doc_id in batch
    ])
```

### 3. Error Recovery
```python
async def resilient_tool_call(tool_name, params, max_retries=3):
    """Resilient tool call with automatic retry"""
    
    for attempt in range(max_retries):
        try:
            return await client.invoke_tool(tool_name, params)
            
        except MCPConnectionError:
            if attempt < max_retries - 1:
                print(f"🔄 Reconnecting... (attempt {attempt + 1})")
                await client.reconnect()
            else:
                raise
```

## 🚨 Common Pitfalls

### ❌ Don't Do This
```python
# DON'T: Forget to handle connection errors
result = await client.invoke_tool("tool_name", params)  # Can fail!

# DON'T: Forget to disconnect
client = MCPClient(config)
await client.connect()
# ... use client ...
# Missing: await client.disconnect()

# DON'T: Ignore error responses
result = await client.invoke_tool("tool_name", params)
doc_id = result["document_id"]  # Might not exist if tool failed!
```

### ✅ Do This Instead
```python
# DO: Always handle errors
try:
    result = await client.invoke_tool("tool_name", params)
    if result.get("success"):
        doc_id = result["document_id"]
        # Process success
    else:
        error_msg = result.get("error", "Unknown error")
        # Handle error
except MCPConnectionError as e:
    # Handle connection issues
    
# DO: Use context managers for cleanup
async with MCPClient(config) as client:
    result = await client.invoke_tool("tool_name", params)
    # Client automatically disconnected
```

## 📚 Next Steps

Now that you have basic integration working:

1. **[Basic Integration Guide](guides/basic-integration.md)** - Learn more integration patterns
2. **[API Reference](api-reference/)** - Explore all available methods and options
3. **[Error Handling Guide](guides/error-handling.md)** - Implement robust error handling
4. **[Examples](examples/)** - See more practical code examples

## 🆘 Need Help?

- **Connection Issues**: Check the [Troubleshooting Guide](troubleshooting.md)
- **Tool Errors**: See [Error Handling Guide](guides/error-handling.md)
- **Performance**: Review [Advanced Patterns](guides/advanced-patterns.md)
- **Testing**: Check [Testing Integration Guide](guides/testing-integration.md)

---

**Congratulations!** 🎉 You now have a working MCP integration. The integration layer handles all the complexity of MCP communication, so you can focus on building great GUI experiences.