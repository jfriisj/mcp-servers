# Troubleshooting Guide

**Common issues and solutions for the Study Buddy GUI Integration Layer.**

## 🎯 Quick Diagnosis

### Health Check Command

First, check the overall health of your integration:

```python
async def health_check():
    """Comprehensive health check"""
    
    # 1. Check MCP client status
    if not mcp_manager.is_ready():
        print("❌ MCP Manager not initialized")
        return False
    
    # 2. Check connection health
    health = await mcp_manager.get_connection_health()
    print(f"Connection: {'✅' if health['healthy'] else '❌'}")
    print(f"State: {health['state']}")
    print(f"Error Rate: {health.get('error_rate', 0):.1f}%")
    print(f"Round Trip: {health.get('round_trip_time', 'N/A')}ms")
    
    # 3. Test basic operation
    try:
        result = await mcp_manager.get_documents()
        print(f"API Test: {'✅' if result['success'] else '❌'}")
        if not result['success']:
            print(f"API Error: {result['error']}")
    except Exception as e:
        print(f"API Test: ❌ - {e}")
    
    return health['healthy']

# Run health check
asyncio.run(health_check())
```

---

## 🔌 Connection Issues

### Problem: "Failed to connect to MCP server"

#### Symptoms
- Initial connection fails
- `ConnectionError` exceptions
- Status shows "Disconnected ❌"

#### Diagnosis
```python
# Check if server is running
import subprocess
import psutil

def check_server_process():
    """Check if MCP server process is running"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'])
                if 'mcp-server' in cmdline or 'main.py' in cmdline:
                    print(f"✅ Server process found: PID {proc.info['pid']}")
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    print("❌ No MCP server process found")
    return False

check_server_process()
```

#### Solutions

**Solution 1: Start the MCP Server**
```bash
# Navigate to server directory
cd mcp-server

# Start server manually
python main.py

# Or use the configured command
python -m mcp_server.main
```

**Solution 2: Fix Server Configuration**
```python
# Check server configuration
config = ConfigManager({
    "connection_type": "stdio",
    "server_command": ["python", "main.py"],  # Verify this path
    "server_working_dir": "mcp-server/",      # Verify this directory exists
    "timeout": 30
})

# Test server command manually
import os
os.chdir("mcp-server")
result = subprocess.run(["python", "main.py", "--test"], capture_output=True, text=True)
print(f"Server test: {result.returncode}")
print(f"Output: {result.stdout}")
print(f"Error: {result.stderr}")
```

**Solution 3: Try Different Connection Type**
```python
# If STDIO fails, try HTTP
config = ConfigManager({
    "connection_type": "http",
    "http_host": "localhost",
    "http_port": 3000,
    "timeout": 30
})
```

### Problem: "Connection drops frequently"

#### Symptoms
- Initial connection succeeds but drops after short time
- `ConnectionLost` exceptions
- Status alternates between connected/disconnected

#### Diagnosis
```python
async def connection_stability_test():
    """Test connection stability over time"""
    
    stable_connections = 0
    failed_connections = 0
    
    for i in range(10):
        try:
            # Test connection
            health = await mcp_manager.get_connection_health()
            
            if health['healthy']:
                stable_connections += 1
                print(f"Test {i+1}: ✅ Stable")
            else:
                failed_connections += 1
                print(f"Test {i+1}: ❌ Unstable - {health.get('error', 'Unknown')}")
            
            # Wait between tests
            await asyncio.sleep(5)
            
        except Exception as e:
            failed_connections += 1
            print(f"Test {i+1}: ❌ Exception - {e}")
    
    print(f"\\nStability: {stable_connections}/10 successful")
    print(f"Failure Rate: {(failed_connections/10)*100:.1f}%")
    
    return stable_connections >= 8  # 80% success rate

asyncio.run(connection_stability_test())
```

#### Solutions

**Solution 1: Increase Timeouts**
```python
config = ConfigManager({
    "timeout": 120,                    # Increase from 30 to 120 seconds
    "keepalive_interval_seconds": 15,  # More frequent keepalives
    "retry_attempts": 5,               # More retry attempts
    "max_retry_delay_seconds": 60      # Longer max retry delay
})
```

**Solution 2: Enable Connection Pooling**
```python
config = ConfigManager({
    "min_connections": 3,              # Always keep 3 connections
    "max_connections": 10,             # Scale up to 10
    "connection_idle_timeout": 300,    # Keep idle connections for 5 minutes
    "health_check_interval": 30        # Check health every 30 seconds
})
```

**Solution 3: Check Server Resources**
```python
def check_server_resources():
    """Check if server has sufficient resources"""
    import psutil
    
    # Check memory usage
    memory = psutil.virtual_memory()
    print(f"Memory: {memory.percent:.1f}% used")
    
    # Check CPU usage
    cpu = psutil.cpu_percent(interval=1)
    print(f"CPU: {cpu:.1f}% used")
    
    # Check disk space
    disk = psutil.disk_usage('/')
    print(f"Disk: {disk.percent:.1f}% used")
    
    # Recommendations
    if memory.percent > 90:
        print("⚠️ High memory usage - server may be struggling")
    if cpu > 80:
        print("⚠️ High CPU usage - server may be overloaded")
    if disk.percent > 95:
        print("⚠️ Low disk space - server may fail")

check_server_resources()
```

### Problem: "Connection timeout errors"

#### Symptoms
- `TimeoutError` exceptions
- Operations take too long to complete
- Progress bars stuck at intermediate values

#### Solutions

**Solution 1: Adjust Timeout Configuration**
```python
# Different timeouts for different operations
config = ConfigManager({
    "connection_timeout": 30,          # Connection establishment
    "operation_timeout": 180,          # Tool operations (3 minutes)
    "upload_timeout": 600,             # Large file uploads (10 minutes)
    "health_check_timeout": 5          # Health checks (fast)
})
```

**Solution 2: Implement Operation-Specific Timeouts**
```python
async def upload_with_custom_timeout(file_path: str):
    """Upload with custom timeout based on file size"""
    
    import os
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    
    # Calculate timeout: 30 seconds per MB, minimum 60 seconds
    timeout = max(60, file_size_mb * 30)
    
    print(f"File size: {file_size_mb:.1f}MB, Timeout: {timeout}s")
    
    # Set temporary timeout
    original_timeout = mcp_manager.client.config.timeout
    mcp_manager.client.config.timeout = timeout
    
    try:
        result = await mcp_manager.upload_document(file_path)
        return result
    finally:
        # Restore original timeout
        mcp_manager.client.config.timeout = original_timeout
```

---

## 🛠️ Tool Invocation Issues

### Problem: "Tool not found" errors

#### Symptoms
- `ToolNotFoundError` exceptions
- "Unknown tool" error messages

#### Diagnosis
```python
async def check_available_tools():
    """Check what tools are actually available"""
    
    try:
        # Get available tools from server
        response = await mcp_manager.client.get_available_tools()
        
        if response.success:
            tools = response.data
            print(f"Available tools ({len(tools)}):")
            for tool in tools:
                print(f"  • {tool}")
        else:
            print(f"Failed to get tools: {response.error_message}")
            
    except Exception as e:
        print(f"Error checking tools: {e}")

asyncio.run(check_available_tools())
```

#### Solutions

**Solution 1: Verify Server Implementation**
```bash
# Check server has all required tools
cd mcp-server
python -c "
from src.handlers.mcp_handler import MCPHandler
handler = MCPHandler()
tools = handler.list_tools()
for tool in tools:
    print(f'Tool: {tool.name}')
"
```

**Solution 2: Check Tool Names**
```python
# Common tool name mismatches
TOOL_NAME_MAPPING = {
    "upload": "upload_document",           # Use full name
    "list": "list_documents",             # Use full name  
    "search": "search_documents",         # Use full name
    "get_doc": "get_document",           # Use correct name
    "delete_doc": "delete_document"       # Use correct name
}

async def invoke_tool_safe(tool_name: str, params: dict):
    """Invoke tool with name mapping"""
    
    # Map common abbreviations
    actual_tool_name = TOOL_NAME_MAPPING.get(tool_name, tool_name)
    
    try:
        return await mcp_manager.client.invoke_tool(actual_tool_name, params)
    except ToolNotFoundError:
        # Get available tools for suggestions
        available = await mcp_manager.client.get_available_tools()
        if available.success:
            similar = [t for t in available.data if tool_name.lower() in t.lower()]
            if similar:
                raise ToolNotFoundError(f"Tool '{tool_name}' not found. Did you mean: {', '.join(similar)}?")
        raise
```

### Problem: "Parameter validation failed"

#### Symptoms
- `ValidationError` exceptions  
- "Invalid parameter" error messages
- Parameters rejected by server

#### Diagnosis
```python
async def check_tool_schema(tool_name: str):
    """Check parameter schema for a tool"""
    
    try:
        response = await mcp_manager.client.get_tool_schema(tool_name)
        
        if response.success:
            schema = response.data
            print(f"Schema for '{tool_name}':")
            print(f"Required parameters: {schema.get('required', [])}")
            print(f"Optional parameters: {schema.get('optional', [])}")
            
            # Show parameter details
            props = schema.get('properties', {})
            for param, details in props.items():
                print(f"  • {param}: {details.get('type', 'unknown')} - {details.get('description', 'No description')}")
        else:
            print(f"Failed to get schema: {response.error_message}")
            
    except Exception as e:
        print(f"Error checking schema: {e}")

# Check schemas for common tools
asyncio.run(check_tool_schema("upload_document"))
asyncio.run(check_tool_schema("list_documents"))
```

#### Solutions

**Solution 1: Parameter Validation Helper**
```python
async def validate_parameters(tool_name: str, params: dict) -> dict:
    """Validate and fix common parameter issues"""
    
    # Get tool schema
    schema_response = await mcp_manager.client.get_tool_schema(tool_name)
    if not schema_response.success:
        return params  # Can't validate without schema
    
    schema = schema_response.data
    validated_params = {}
    
    # Check required parameters
    required = schema.get('required', [])
    for param in required:
        if param not in params:
            raise ValidationError(f"Missing required parameter: {param}")
        validated_params[param] = params[param]
    
    # Add optional parameters
    optional = schema.get('optional', [])
    for param in optional:
        if param in params:
            validated_params[param] = params[param]
    
    # Type conversion for common issues
    properties = schema.get('properties', {})
    for param, value in validated_params.items():
        if param in properties:
            expected_type = properties[param].get('type')
            
            # Convert strings to integers
            if expected_type == 'integer' and isinstance(value, str):
                try:
                    validated_params[param] = int(value)
                except ValueError:
                    raise ValidationError(f"Parameter '{param}' must be an integer, got '{value}'")
            
            # Convert strings to lists
            elif expected_type == 'array' and isinstance(value, str):
                validated_params[param] = [value]  # Single item to list
    
    return validated_params

# Usage
params = await validate_parameters("upload_document", {
    "file_path": "/path/to/doc.pdf",
    "tags": "research"  # Will be converted to ["research"]
})
```

**Solution 2: Common Parameter Fixes**
```python
def fix_common_parameter_issues(tool_name: str, params: dict) -> dict:
    """Fix common parameter issues"""
    
    fixed_params = params.copy()
    
    if tool_name == "upload_document":
        # Ensure file_path is absolute
        if 'file_path' in fixed_params:
            file_path = fixed_params['file_path']
            if not os.path.isabs(file_path):
                fixed_params['file_path'] = os.path.abspath(file_path)
        
        # Ensure tags is a list
        if 'tags' in fixed_params and isinstance(fixed_params['tags'], str):
            fixed_params['tags'] = [fixed_params['tags']]
    
    elif tool_name == "list_documents":
        # Ensure limit is integer
        if 'limit' in fixed_params and isinstance(fixed_params['limit'], str):
            fixed_params['limit'] = int(fixed_params['limit'])
        
        # Ensure offset is integer  
        if 'offset' in fixed_params and isinstance(fixed_params['offset'], str):
            fixed_params['offset'] = int(fixed_params['offset'])
    
    elif tool_name == "get_document":
        # Ensure document_id is integer
        if 'document_id' in fixed_params and isinstance(fixed_params['document_id'], str):
            fixed_params['document_id'] = int(fixed_params['document_id'])
    
    return fixed_params
```

---

## ⚡ Performance Issues

### Problem: "Slow operation responses"

#### Symptoms
- Operations take longer than expected
- GUI becomes unresponsive
- High CPU/memory usage

#### Diagnosis
```python
import time
import psutil

async def performance_benchmark():
    """Benchmark common operations"""
    
    operations = [
        ("list_documents", lambda: mcp_manager.get_documents()),
        ("get_health", lambda: mcp_manager.get_connection_health()),
        ("search_documents", lambda: mcp_manager.search_documents("test"))
    ]
    
    for op_name, op_func in operations:
        print(f"\\nBenchmarking {op_name}...")
        
        # Measure multiple runs
        times = []
        for i in range(5):
            start_time = time.time()
            
            try:
                result = await op_func()
                end_time = time.time()
                
                if result.get("success", False):
                    times.append(end_time - start_time)
                    print(f"  Run {i+1}: {times[-1]:.2f}s ✅")
                else:
                    print(f"  Run {i+1}: Failed ❌ - {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"  Run {i+1}: Exception ❌ - {e}")
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"  Average: {avg_time:.2f}s")
            print(f"  Range: {min_time:.2f}s - {max_time:.2f}s")
            
            # Performance assessment
            if avg_time > 10:
                print("  ⚠️ Very slow - investigate server performance")
            elif avg_time > 5:
                print("  ⚠️ Slow - consider optimization")
            elif avg_time > 2:
                print("  ✅ Acceptable performance")
            else:
                print("  🚀 Fast performance")

asyncio.run(performance_benchmark())
```

#### Solutions

**Solution 1: Enable Connection Pooling**
```python
# High-performance configuration
config = ConfigManager({
    "min_connections": 5,              # Keep 5 warm connections
    "max_connections": 20,             # Scale up under load
    "connection_idle_timeout": 600,    # Keep connections for 10 minutes
    "operation_timeout": 120,          # 2-minute operation timeout
    "health_check_interval": 30        # More frequent health checks
})
```

**Solution 2: Implement Caching**
```python
import asyncio
from datetime import datetime, timedelta

class CachedMCPManager:
    """MCP manager with response caching"""
    
    def __init__(self, mcp_manager):
        self.mcp_manager = mcp_manager
        self.cache = {}
        self.cache_ttl = timedelta(minutes=5)  # Cache for 5 minutes
    
    def _get_cache_key(self, operation: str, params: dict) -> str:
        """Generate cache key for operation"""
        import hashlib
        key_data = f"{operation}:{sorted(params.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: dict) -> bool:
        """Check if cache entry is still valid"""
        return datetime.now() - cache_entry['timestamp'] < self.cache_ttl
    
    async def get_documents_cached(self, filters: dict = None) -> dict:
        """Get documents with caching"""
        cache_key = self._get_cache_key("list_documents", filters or {})
        
        # Check cache first
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if self._is_cache_valid(entry):
                print(f"📋 Cache hit for list_documents")
                return entry['result']
        
        # Cache miss - fetch from server
        print(f"🌐 Cache miss for list_documents - fetching from server")
        result = await self.mcp_manager.get_documents(filters)
        
        # Cache successful results
        if result.get("success"):
            self.cache[cache_key] = {
                'result': result,
                'timestamp': datetime.now()
            }
        
        return result
    
    def clear_cache(self):
        """Clear all cached results"""
        self.cache.clear()
        print("🗑️ Cache cleared")

# Usage
cached_manager = CachedMCPManager(mcp_manager)
documents = await cached_manager.get_documents_cached()
```

**Solution 3: Background Preloading**
```python
class PreloadingMCPManager:
    """MCP manager with background preloading"""
    
    def __init__(self, mcp_manager):
        self.mcp_manager = mcp_manager
        self.preloaded_data = {}
        self.preloading_task = None
    
    async def start_preloading(self):
        """Start background preloading of common data"""
        self.preloading_task = asyncio.create_task(self._preload_loop())
    
    async def stop_preloading(self):
        """Stop background preloading"""
        if self.preloading_task:
            self.preloading_task.cancel()
            try:
                await self.preloading_task
            except asyncio.CancelledError:
                pass
    
    async def _preload_loop(self):
        """Background loop to preload common data"""
        while True:
            try:
                # Preload document list
                print("🔄 Preloading document list...")
                documents = await self.mcp_manager.get_documents()
                if documents.get("success"):
                    self.preloaded_data['documents'] = documents
                    print(f"✅ Preloaded {len(documents.get('documents', []))} documents")
                
                # Preload connection health
                health = await self.mcp_manager.get_connection_health()
                self.preloaded_data['health'] = health
                
                # Wait before next preload
                await asyncio.sleep(30)  # Preload every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Preloading error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def get_documents_fast(self) -> dict:
        """Get documents with preloaded data fallback"""
        
        # Try to get fresh data
        try:
            return await asyncio.wait_for(
                self.mcp_manager.get_documents(), 
                timeout=2.0  # 2-second timeout
            )
        except asyncio.TimeoutError:
            # Fallback to preloaded data
            print("⚡ Using preloaded documents (fresh data timeout)")
            return self.preloaded_data.get('documents', {
                "success": False, 
                "error": "No preloaded data available"
            })

# Usage
preloading_manager = PreloadingMCPManager(mcp_manager)
await preloading_manager.start_preloading()
```

### Problem: "Memory leaks"

#### Symptoms
- Memory usage increases over time
- Application becomes slow after extended use
- System runs out of memory

#### Diagnosis
```python
import gc
import psutil
import weakref

class MemoryMonitor:
    """Monitor memory usage and detect leaks"""
    
    def __init__(self):
        self.initial_memory = None
        self.object_counts = {}
    
    def start_monitoring(self):
        """Start memory monitoring"""
        process = psutil.Process()
        self.initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Count objects by type
        for obj in gc.get_objects():
            obj_type = type(obj).__name__
            self.object_counts[obj_type] = self.object_counts.get(obj_type, 0) + 1
        
        print(f"📊 Initial memory: {self.initial_memory:.1f}MB")
        print(f"📊 Initial objects: {len(gc.get_objects())}")
    
    def check_memory(self):
        """Check current memory usage"""
        process = psutil.Process()
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = current_memory - self.initial_memory
        
        # Count current objects
        current_objects = {}
        for obj in gc.get_objects():
            obj_type = type(obj).__name__
            current_objects[obj_type] = current_objects.get(obj_type, 0) + 1
        
        print(f"\\n📊 Memory Check:")
        print(f"  Current: {current_memory:.1f}MB")
        print(f"  Growth: {memory_growth:+.1f}MB")
        print(f"  Objects: {len(gc.get_objects())}")
        
        # Show objects with significant growth
        print(f"\\n📈 Object Growth:")
        for obj_type, current_count in current_objects.items():
            initial_count = self.object_counts.get(obj_type, 0)
            growth = current_count - initial_count
            if growth > 100:  # Show types with >100 new objects
                print(f"  {obj_type}: +{growth} objects")
        
        # Memory warnings
        if memory_growth > 100:  # >100MB growth
            print("⚠️ Significant memory growth detected")
        if len(gc.get_objects()) > 100000:  # >100k objects
            print("⚠️ High object count - potential leak")
    
    def force_cleanup(self):
        """Force garbage collection"""
        print("🗑️ Forcing garbage collection...")
        collected = gc.collect()
        print(f"🗑️ Collected {collected} objects")

# Usage
monitor = MemoryMonitor()
monitor.start_monitoring()

# ... run operations ...

monitor.check_memory()
monitor.force_cleanup()
```

#### Solutions

**Solution 1: Proper Resource Cleanup**
```python
class ResourceManager:
    """Manage MCP resources with proper cleanup"""
    
    def __init__(self):
        self.active_connections = []
        self.active_callbacks = []
        self.cleanup_tasks = []
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup resources"""
        await self.cleanup_all()
    
    def register_connection(self, connection):
        """Register connection for cleanup"""
        self.active_connections.append(weakref.ref(connection))
    
    def register_callback(self, callback):
        """Register callback for cleanup"""
        self.active_callbacks.append(callback)
    
    async def cleanup_all(self):
        """Clean up all managed resources"""
        print("🧹 Starting resource cleanup...")
        
        # Cleanup connections
        for conn_ref in self.active_connections:
            conn = conn_ref()
            if conn:
                try:
                    await conn.disconnect()
                except Exception as e:
                    print(f"Error cleaning up connection: {e}")
        
        # Remove callbacks
        for callback in self.active_callbacks:
            try:
                mcp_manager.remove_connection_listener(callback)
                mcp_manager.remove_progress_listener(callback)
                mcp_manager.remove_error_listener(callback)
            except Exception as e:
                print(f"Error removing callback: {e}")
        
        # Clear lists
        self.active_connections.clear()
        self.active_callbacks.clear()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        print("✅ Resource cleanup complete")

# Usage
async def main():
    async with ResourceManager() as resource_mgr:
        # Your MCP operations here
        # Resources automatically cleaned up on exit
        pass
```

**Solution 2: Connection Lifecycle Management**
```python
class ConnectionLifecycleManager:
    """Manage connection lifecycle to prevent leaks"""
    
    def __init__(self, max_connection_age=3600):  # 1 hour max age
        self.connections = {}
        self.max_connection_age = max_connection_age
        self.cleanup_task = None
    
    async def start_cleanup_task(self):
        """Start periodic connection cleanup"""
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup_task(self):
        """Stop periodic connection cleanup"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
    
    async def _cleanup_loop(self):
        """Periodic cleanup of old connections"""
        while True:
            try:
                await self._cleanup_old_connections()
                await asyncio.sleep(300)  # Check every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Connection cleanup error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_old_connections(self):
        """Remove connections that are too old"""
        import time
        current_time = time.time()
        
        old_connections = []
        for conn_id, conn_info in self.connections.items():
            age = current_time - conn_info['created_at']
            if age > self.max_connection_age:
                old_connections.append(conn_id)
        
        for conn_id in old_connections:
            conn_info = self.connections.pop(conn_id)
            try:
                await conn_info['connection'].disconnect()
                print(f"🗑️ Cleaned up old connection: {conn_id}")
            except Exception as e:
                print(f"Error cleaning up connection {conn_id}: {e}")
```

---

## 🔍 Debugging Tools

### Debug Mode Configuration

```python
def create_debug_config():
    """Create configuration with extensive debugging"""
    
    return ConfigManager({
        "log_level": "DEBUG",
        "debug_mode": True,
        "trace_operations": True,
        "connection_logging": True,
        "performance_monitoring": True,
        
        # Reduced timeouts for faster debugging
        "timeout": 10,
        "retry_attempts": 1,
        
        # Single connection for easier debugging
        "min_connections": 1,
        "max_connections": 1
    })
```

### Operation Tracer

```python
import functools
import time

def trace_operation(func):
    """Decorator to trace MCP operations"""
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        operation_name = func.__name__
        start_time = time.time()
        
        print(f"🔍 Starting {operation_name}")
        print(f"   Args: {args}")
        print(f"   Kwargs: {kwargs}")
        
        try:
            result = await func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"✅ {operation_name} completed in {duration:.2f}s")
            print(f"   Result: {result}")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"❌ {operation_name} failed after {duration:.2f}s")
            print(f"   Error: {e}")
            print(f"   Type: {type(e).__name__}")
            
            raise
    
    return wrapper

# Usage: Apply to MCP operations
@trace_operation
async def upload_document_traced(file_path: str):
    return await mcp_manager.upload_document(file_path)
```

### Network Debugging

```python
import asyncio
import aiohttp

async def debug_network_connectivity():
    """Debug network connectivity to MCP server"""
    
    config = mcp_manager.config
    
    if config.connection_type == "http":
        # Test HTTP connectivity
        url = f"http://{config.http_host}:{config.http_port}/health"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    print(f"✅ HTTP connectivity: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text[:100]}...")
        except Exception as e:
            print(f"❌ HTTP connectivity failed: {e}")
    
    elif config.connection_type == "stdio":
        # Test STDIO command
        cmd = config.server_command
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=10
            )
            
            print(f"✅ STDIO command executed: {process.returncode}")
            print(f"   Stdout: {stdout.decode()[:100]}...")
            print(f"   Stderr: {stderr.decode()[:100]}...")
            
        except Exception as e:
            print(f"❌ STDIO command failed: {e}")

asyncio.run(debug_network_connectivity())
```

---

## 📞 Getting Help

### Collect Diagnostic Information

```python
async def collect_diagnostics():
    """Collect comprehensive diagnostic information"""
    
    print("=== STUDY BUDDY MCP DIAGNOSTICS ===\\n")
    
    # System information
    import platform
    import sys
    print("SYSTEM INFO:")
    print(f"  OS: {platform.system()} {platform.release()}")
    print(f"  Python: {sys.version}")
    print(f"  Working Dir: {os.getcwd()}")
    
    # MCP configuration
    print(f"\\nMCP CONFIGURATION:")
    config = mcp_manager.config
    print(f"  Connection Type: {config.connection_type}")
    print(f"  Timeout: {config.timeout}s")
    print(f"  Retry Attempts: {config.retry_attempts}")
    
    # Connection health
    print(f"\\nCONNECTION HEALTH:")
    try:
        health = await mcp_manager.get_connection_health()
        print(f"  Healthy: {health['healthy']}")
        print(f"  State: {health['state']}")
        print(f"  Error Rate: {health.get('error_rate', 'N/A')}%")
        print(f"  Round Trip: {health.get('round_trip_time', 'N/A')}ms")
    except Exception as e:
        print(f"  Error getting health: {e}")
    
    # Available tools
    print(f"\\nAVAILABLE TOOLS:")
    try:
        tools_response = await mcp_manager.client.get_available_tools()
        if tools_response.success:
            tools = tools_response.data
            print(f"  Count: {len(tools)}")
            for tool in tools[:5]:  # Show first 5
                print(f"    • {tool}")
            if len(tools) > 5:
                print(f"    ... and {len(tools) - 5} more")
        else:
            print(f"  Error: {tools_response.error_message}")
    except Exception as e:
        print(f"  Error getting tools: {e}")
    
    # Recent errors
    print(f"\\nRECENT ERRORS:")
    # This would require error logging system
    print("  (Error logging not implemented)")
    
    print(f"\\n=== END DIAGNOSTICS ===")

# Run diagnostics and save to file
async def save_diagnostics():
    import io
    import sys
    from contextlib import redirect_stdout
    
    # Capture output
    output = io.StringIO()
    with redirect_stdout(output):
        await collect_diagnostics()
    
    # Save to file
    with open("mcp_diagnostics.txt", "w") as f:
        f.write(output.getvalue())
    
    print("📋 Diagnostics saved to mcp_diagnostics.txt")

asyncio.run(save_diagnostics())
```

### When to Contact Support

Contact support when you have:

1. **Collected diagnostics** using the script above
2. **Tried common solutions** from this guide  
3. **Specific error messages** with full stack traces
4. **Reproducible steps** to trigger the issue
5. **System information** (OS, Python version, etc.)

Include:
- The `mcp_diagnostics.txt` file
- Your configuration settings
- Recent error logs
- Steps to reproduce the issue

---

## 📚 Additional Resources

- **[Basic Integration Guide](basic-integration.md)** - Step-by-step integration
- **[API Reference](../api-reference/)** - Complete API documentation  
- **[Performance Guide](performance.md)** - Performance optimization
- **[Testing Guide](testing-integration.md)** - Testing your integration

---

**Most issues can be resolved by following this guide. For persistent problems, collect diagnostics and contact support with specific details.**