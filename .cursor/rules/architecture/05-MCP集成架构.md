# MCP 集成架构

> 本档详细说明 Lynxe 项目中 Model Context Protocol (MCP) 的集成架构。

## 📋 目录

- [MCP 概述](#mcp-概述)
- [MCP 架构设计](#mcp-架构设计)
- [连接管理](#连接管理)
- [工具注册与发现](#工具注册与发现)
- [工具调用流程](#工具调用流程)
- [缓存策略](#缓存策略)
- [错误处理](#错误处理)

---

## MCP 概述

### 什么是 MCP

Model Context Protocol (MCP) 是一个开放协议，用于 AI 应用与外部数据源和工具之间的连接。Lynxe 原生支持 MCP，可以动态加载和使用 MCP 服务提供的工具。

### MCP 在 Lynxe 中的作用

```
┌─────────────────────────────────────────────────────────────┐
│                    Lynxe 系统                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Agent                                                 │  │
│  │  - 决策和规划                                          │  │
│  │  - 需要使用工具                                        │  │
│  └───────────────────┬───────────────────────────────────┘  │
│                      │ 使用工具                              │
│  ┌───────────────────▼───────────────────────────────────┐  │
│  │  ToolRegistry                                          │  │
│  │  - 统一的工具注册表                                    │  │
│  │  - 管理内置工具和 MCP 工具                             │  │
│  └───────────────────┬───────────────────────────────────┘  │
│                      │                                      │
│         ┌────────────┴────────────┐                        │
│         │                         │                        │
│  ┌──────▼──────┐          ┌──────▼────────┐               │
│  │ 内置工具     │          │ MCP 工具       │               │
│  │ (文件、DB等) │          │ (外部服务)     │               │
│  └─────────────┘          └──────┬────────┘               │
│                                   │                        │
│                          ┌────────▼────────┐              │
│                          │  MCP 客户端      │              │
│                          │  - 连接管理      │              │
│                          │  - 通信协议      │              │
│                          └────────┬────────┘              │
│                                   │                        │
│                          ┌────────▼────────┐              │
│                          │  MCP 服务器      │              │
│                          │  (外部进程)      │              │
│                          └─────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

---

## MCP 架构设计

### 核心组件

#### 1. McpService
**位置**: `mcp/service/McpService.java`

**职责**:
- MCP 服务器配置管理
- MCP 客户端生命周期管理
- 工具注册和发现

**接口定义**:
```java
public interface IMcpService {

    // 保存 MCP 服务器配置
    void saveMcpServers(List<McpServerConfig> servers);

    // 获取所有 MCP 服务器
    List<McpServerConfig> getMcpServers();

    // 删除 MCP 服务器
    void removeMcpServer(String serverName);

    // 获取 MCP 提供的工具
    List<Tool> getMcpTools(String serverName);

    // 验证 MCP 配置
    boolean validateMcpConfig(McpServerConfig config);

    // 重新连接服务器
    void reconnectServer(String serverName);
}
```

#### 2. McpClient
**位置**: `mcp/client/McpClient.java`

**职责**:
- 建立 MCP 连接
- 实现 MCP 协议
- 处理工具调用

**核心方法**:
```java
public interface McpClient {

    // 初始化连接
    void initialize();

    // 关闭连接
    void close();

    // 检查连接状态
    boolean isConnected();

    // 列出可用工具
    List<Tool> listTools();

    // 调用工具
    ToolResult callTool(String toolName, Map<String, Object> arguments);

    // 获取服务器信息
    McpServerInfo getServerInfo();
}
```

#### 3. McpToolRegistry
**位置**: `mcp/service/McpToolRegistry.java`

**职责**:
- 管理 MCP 工具注册
- 工具名称解析
- 工具查找

**实现**:
```java
@Component
public class McpToolRegistry {

    private final Map<String, McpToolWrapper> toolRegistry = new ConcurrentHashMap<>();

    /**
     * 注册 MCP 工具
     * 工具名称格式: mcp:{serverName}:{toolName}
     */
    public void registerTool(String serverName, Tool tool) {
        String registryName = buildToolName(serverName, tool.getName());
        McpToolWrapper wrapper = new McpToolWrapper(serverName, tool);
        toolRegistry.put(registryName, wrapper);
        toolRegistry.put(tool.getName(), wrapper); // 同时支持短名称
    }

    /**
     * 获取工具
     */
    public Tool getTool(String toolName) {
        McpToolWrapper wrapper = toolRegistry.get(toolName);
        return wrapper != null ? wrapper.getTool() : null;
    }

    /**
     * 获取服务器名称
     */
    public String getServerName(String toolName) {
        McpToolWrapper wrapper = toolRegistry.get(toolName);
        return wrapper != null ? wrapper.getServerName() : null;
    }

    private String buildToolName(String serverName, String toolName) {
        return "mcp:" + serverName + ":" + toolName;
    }
}
```

### 连接类型支持

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP 连接类型                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Process 连接                                          │  │
│  │  - 启动子进程                                          │  │
│  │  - 通过 stdin/stdt 通信                                 │  │
│  │  - 适用于 Node.js、Python 等                            │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  HTTP 连接                                             │  │
│  │  - 通过 HTTP 协议通信                                   │  │
│  │  - 支持 Headers 和超时配置                              │  │
│  │  - 适用于远程服务器                                     │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 连接管理

### 1. Process 连接

**配置示例**:
```json
{
  "serverName": "filesystem-server",
  "connectionType": "process",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp/mount"],
  "env": {
    "NODE_ENV": "production"
  }
}
```

**实现**:
```java
// mcp/client/ProcessMcpClient.java
public class ProcessMcpClient implements McpClient {

    private Process process;
    private InputStream stdout;
    private OutputStream stdin;

    @Override
    public void initialize() {
        try {
            // 1. 构建进程命令
            ProcessBuilder builder = new ProcessBuilder(config.getCommand());
            builder.command().addAll(config.getArgs());

            // 2. 设置环境变量
            if (config.getEnv() != null) {
                Map<String, String> env = builder.environment();
                env.putAll(config.getEnv());
            }

            // 3. 启动进程
            process = builder.start();
            stdout = process.getInputStream();
            stdin = process.getOutputStream();

            // 4. 初始化 MCP 会话
            initializeSession();

        } catch (IOException e) {
            throw new McpConnectionException(config.getServerName(),
                "Failed to start process", e);
        }
    }

    private void initializeSession() {
        // 1. 发送 initialize 请求
        McpRequest request = new McpRequest();
        request.setJsonrpc("2.0");
        request.setId("1");
        request.setMethod("initialize");
        request.setParams(Map.of(
            "protocolVersion", "2024-11-05",
            "capabilities", Map.of(),
            "clientInfo", Map.of(
                "name", "lynxe",
                "version", "1.0.0"
            )
        ));

        sendRequest(request);

        // 2. 等待响应
        McpResponse response = readResponse();

        // 3. 发送 initialized 通知
        sendNotification("notifications/initialized");
    }

    @Override
    public void close() {
        if (process != null && process.isAlive()) {
            process.destroy();
        }
    }
}
```

### 2. HTTP 连接

**配置示例**:
```json
{
  "serverName": "remote-server",
  "connectionType": "http",
  "url": "http://localhost:8080/mcp",
  "headers": {
    "Authorization": "Bearer token123",
    "Content-Type": "application/json"
  },
  "timeout": 30000
}
```

**实现**:
```java
// mcp/client/HttpMcpClient.java
public class HttpMcpClient implements McpClient {

    private final HttpClient httpClient;
    private final String baseUrl;

    @Override
    public void initialize() {
        // HTTP 连接不需要显式初始化
        // 验证连接
        try {
            McpRequest request = new McpRequest();
            request.setMethod("initialize");
            sendRequest(request);
        } catch (Exception e) {
            throw new McpConnectionException(config.getServerName(),
                "Failed to connect to HTTP server", e);
        }
    }

    @Override
    public ToolResult callTool(String toolName, Map<String, Object> arguments) {
        McpRequest request = new McpRequest();
        request.setMethod("tools/call");
        request.setParams(Map.of(
            "name", toolName,
            "arguments", arguments
        ));

        McpResponse response = sendRequest(request);
        return parseToolResult(response);
    }

    private McpResponse sendRequest(McpRequest request) {
        try {
            HttpRequest httpRequest = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl))
                .header("Content-Type", "application/json")
                .headers(config.getHeaders())
                .timeout(Duration.ofMillis(config.getTimeout()))
                .POST(BodyPublishers.ofString(objectMapper.writeValueAsString(request)))
                .build();

            HttpResponse<String> httpResponse = httpClient.send(httpRequest,
                HttpResponse.BodyHandlers.ofString());

            return objectMapper.readValue(httpResponse.body(), McpResponse.class);

        } catch (Exception e) {
            throw new McpException("HTTP request failed", e);
        }
    }
}
```

---

## 工具注册与发现

### 1. 工具发现流程

```
┌─────────────────────────────────────────────────────────────┐
│              1. MCP 客户端初始化                             │
│  - 建立连接                                                 │
│  - 发送 initialize 请求                                      │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│              2. 请求工具列表                                │
│  - 调用 tools/list                                          │
│  - 解析工具 Schema                                          │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│              3. 构建工具定义                                │
│  - 创建 Tool 对象                                           │
│  - 设置工具名称、描述、参数                                  │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│              4. 注册到 ToolRegistry                         │
│  - McpToolRegistry.registerTool()                           │
│  - 支持短名称和完整名称                                      │
└─────────────────────────────────────────────────────────────┘
```

### 2. 工具 Schema 解析

```java
// mcp/service/McpToolRegistry.java
private Tool createToolFromSchema(String serverName, Map<String, Object> toolSchema) {
    String toolName = (String) toolSchema.get("name");
    String description = (String) toolSchema.get("description");

    // 解析输入 Schema
    Map<String, Object> inputSchema = (Map<String, Object>) toolSchema.get("inputSchema");

    // 构建参数定义
    List<ParameterDefinition> parameters = parseInputSchema(inputSchema);

    // 创建 Tool 对象
    return new Tool() {
        @Override
        public String getName() {
            return toolName;
        }

        @Override
        public String getDescription() {
            return description;
        }

        @Override
        public ToolSchema getSchema() {
            return new ToolSchema(parameters);
        }

        @Override
        public ToolResult execute(ToolInput input) {
            // 委托给 MCP 客户端执行
            return mcpClient.callTool(toolName, input.getParameters());
        }
    };
}
```

---

## 工具调用流程

### 1. Agent 调用 MCP 工具

```
┌─────────────────────────────────────────────────────────────┐
│              1. Agent 需要使用工具                           │
│  toolCall {                                                 │
│    name: "mcp:filesystem-server:read_file",                 │
│    arguments: {"path": "/tmp/file.txt"}                     │
│  }                                                         │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│              2. ToolRegistry 查找工具                       │
│  - 解析工具名称                                              │
│  - 提取 serverName: "filesystem-server"                      │
│  - 提取 toolName: "read_file"                                │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│              3. 获取 MCP 客户端                              │
│  - mcpService.getClient("filesystem-server")                 │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│              4. 调用 MCP 工具                               │
│  - 构建 JSON-RPC 请求                                        │
│  - 发送 tools/call                                           │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│              5. 等待响应                                    │
│  - 解析 JSON-RPC 响应                                        │
│  - 提取工具结果                                              │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│              6. 返回结果                                    │
│  - 转换为统一的 ToolResult 格式                              │
│  - 返回给 Agent                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2. 工具调用实现

```java
// mcp/service/McpService.java
public ToolResult executeMcpTool(String fullToolName, Map<String, Object> arguments) {
    // 1. 解析工具名称
    String[] parts = fullToolName.split(":");
    if (parts.length < 3 || !parts[0].equals("mcp")) {
        throw new IllegalArgumentException("Invalid MCP tool name: " + fullToolName);
    }

    String serverName = parts[1];
    String toolName = parts[2];

    // 2. 获取客户端
    McpClient client = getClient(serverName);
    if (client == null || !client.isConnected()) {
        throw new McpConnectionException(serverName, "Client not connected");
    }

    // 3. 调用工具
    try {
        return client.callTool(toolName, arguments);
    } catch (Exception e) {
        logger.error("MCP tool execution failed: server={}, tool={}",
            serverName, toolName, e);
        return ToolResult.failure("Tool execution failed: " + e.getMessage());
    }
}
```

---

## 缓存策略

### 1. 连接缓存

```java
// mcp/service/McpCacheManager.java
@Component
public class McpCacheManager {

    private final Map<String, McpClient> clientCache = new ConcurrentHashMap<>();
    private final ScheduledExecutorService scheduler;

    @PostConstruct
    public void init() {
        // 定期清理过期连接
        scheduler.scheduleAtFixedRate(this::cleanupExpiredConnections,
            5, 5, TimeUnit.MINUTES);
    }

    public McpClient getClient(String serverName) {
        return clientCache.get(serverName);
    }

    public void putClient(String serverName, McpClient client) {
        clientCache.put(serverName, client);
    }

    public void removeClient(String serverName) {
        McpClient client = clientCache.remove(serverName);
        if (client != null) {
            client.close();
        }
    }

    private void cleanupExpiredConnections() {
        clientCache.forEach((serverName, client) -> {
            if (!client.isConnected()) {
                logger.warn("Removing disconnected MCP client: {}", serverName);
                removeClient(serverName);
            }
        });
    }
}
```

### 2. 工具列表缓存

```java
// mcp/service/McpService.java
private final Map<String, List<Tool>> toolListCache = new ConcurrentHashMap<>();

public List<Tool> getMcpTools(String serverName) {
    // 1. 检查缓存
    List<Tool> cached = toolListCache.get(serverName);
    if (cached != null) {
        return cached;
    }

    // 2. 从服务器获取
    McpClient client = getClient(serverName);
    List<Tool> tools = client.listTools();

    // 3. 缓存结果
    toolListCache.put(serverName, tools);

    return tools;
}

public void refreshToolList(String serverName) {
    // 清除缓存，强制重新获取
    toolListCache.remove(serverName);
    getMcpTools(serverName);
}
```

---

## 错误处理

### 1. 连接错误处理

```java
// mcp/service/McpService.java
public McpClient getClient(String serverName) {
    McpClient client = cacheManager.getClient(serverName);

    if (client == null) {
        throw new McpConnectionException(serverName, "Client not found");
    }

    if (!client.isConnected()) {
        logger.warn("MCP client disconnected, attempting reconnect: {}", serverName);
        try {
            reconnectServer(serverName);
            client = cacheManager.getClient(serverName);
        } catch (Exception e) {
            throw new McpConnectionException(serverName,
                "Failed to reconnect", e);
        }
    }

    return client;
}
```

### 2. 工具调用错误处理

```java
// mcp/client/McpClient.java
public ToolResult callTool(String toolName, Map<String, Object> arguments) {
    try {
        // 1. 发送请求
        McpRequest request = buildToolCallRequest(toolName, arguments);
        McpResponse response = sendRequest(request);

        // 2. 检查错误
        if (response.getError() != null) {
            return ToolResult.failure(response.getError().getMessage());
        }

        // 3. 解析结果
        return parseToolResult(response);

    } catch (TimeoutException e) {
        logger.error("MCP tool call timeout: tool={}", toolName);
        return ToolResult.failure("Tool call timeout");

    } catch (IOException e) {
        logger.error("MCP tool call failed: tool={}", toolName, e);
        // 连接可能已断开
        close();
        return ToolResult.failure("Tool call failed: " + e.getMessage());
    }
}
```

### 3. 配置验证

```java
// mcp/service/McpConfigValidator.java
@Component
public class McpConfigValidator {

    public ValidationResult validate(McpServerConfig config) {
        ValidationResult result = new ValidationResult();

        // 1. 验证服务器名称
        if (config.getServerName() == null || config.getServerName().isEmpty()) {
            result.addError("serverName", "Server name is required");
        }

        // 2. 验证连接类型
        if (config.getConnectionType() == null) {
            result.addError("connectionType", "Connection type is required");
        }

        // 3. 根据连接类型验证配置
        switch (config.getConnectionType()) {
            case PROCESS:
                validateProcessConfig(config, result);
                break;
            case HTTP:
                validateHttpConfig(config, result);
                break;
        }

        return result;
    }

    private void validateProcessConfig(McpServerConfig config, ValidationResult result) {
        if (config.getCommand() == null || config.getCommand().isEmpty()) {
            result.addError("command", "Command is required for process connection");
        }
    }

    private void validateHttpConfig(McpServerConfig config, ValidationResult result) {
        if (config.getUrl() == null || config.getUrl().isEmpty()) {
            result.addError("url", "URL is required for HTTP connection");
        }

        try {
            new URL(config.getUrl());
        } catch (MalformedURLException e) {
            result.addError("url", "Invalid URL format");
        }
    }
}
```

---

## MCP 配置示例

### Filesystem MCP Server

```json
{
  "serverName": "filesystem-server",
  "connectionType": "process",
  "command": "npx",
  "args": [
    "-y",
    "@modelcontextprotocol/server-filesystem",
    "/Users/lynxe/workspace"
  ],
  "enabled": true
}
```

### GitHub MCP Server

```json
{
  "serverName": "github-server",
  "connectionType": "http",
  "url": "http://localhost:3000/mcp/github",
  "headers": {
    "Authorization": "Bearer ghp_xxx"
  },
  "timeout": 30000,
  "enabled": true
}
```

### Database MCP Server

```json
{
  "serverName": "database-server",
  "connectionType": "process",
  "command": "python",
  "args": [
    "-m",
    "mcp_server_db",
    "--connection-string",
    "postgresql://user:password@localhost:5432/db"
  ],
  "env": {
    "PYTHONPATH": "/path/to/mcp/server"
  },
  "enabled": true
}
```

---

## MCP 集成速查表

| 组件 | 职责 | 位置 |
|------|------|------|
| IMcpService | MCP 服务接口 | mcp/service/ |
| McpService | MCP 服务实现 | mcp/service/ |
| McpClient | MCP 客户端接口 | mcp/client/ |
| ProcessMcpClient | Process 连接实现 | mcp/client/ |
| HttpMcpClient | HTTP 连接实现 | mcp/client/ |
| McpToolRegistry | 工具注册表 | mcp/service/ |
| McpCacheManager | 缓存管理 | mcp/service/ |
| McpConfigValidator | 配置验证 | mcp/service/ |

| 连接类型 | 适用场景 | 配置字段 |
|----------|----------|----------|
| Process | 本地进程 | command, args, env |
| HTTP | 远程服务器 | url, headers, timeout |

| 工具名称格式 | 示例 |
|-------------|------|
| 短名称 | read_file |
| 完整名称 | mcp:filesystem-server:read_file |
