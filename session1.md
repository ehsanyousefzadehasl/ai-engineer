# session 1

## 1. model context protocol (MCP)

MCP is a protocol that standardizes how AI applications communicate with external tools and data sources.

Instead of implementing a custom inegration for every tool, applications can use MCP to discover available capabilities and invoke them through a consistent interface.

MCP standardizes communication, but it does not decide which tools an AI agent should execute. This decision belongs to the agent's orchestration logic.



## 2. mcp server

An mcp server is a program that exposes capabilities to MCP clients, primarily:

- **Tools**: Executable operations, such as querying GPU utilization
- **Resources**: Data that clients can retrieve, such as files or documentations
- **Prompts**: reusable prompt templates


## 3. mcp client

An mcp client is the component that establishes a connetion with an mcp server and communicates using the mcp protocol.

It can initialize communication, discover available tools, and execute them with structured arguments.

In our example, `mcp_client.py` connects to the GPU monitoring server and invokes `gpu_status`.

## 4. mcp transport (stdio)

A transport defines how messages travel between the client and server.

MCP commonly supports:
- **stdio**: communication through standard input/output, suitable for local processes.
- **streamable http**: communication over http, suitable for remote services

both carry mcp messages based on JSON-PRC 2.0.

## 5. mcp session

A session represents an established communication context between an MCP client and server.

It handles protocol initialization, message exchange, and request/response correlation.

In Python, `ClientSession` provides methods such as `initialize()`, `list_tools()`, and `call_tool()`.

>**How does an AI agent use an MCP server?**
>The agent decides when a tool is needed. The MCP client communicates with the MCP server, which executes the requeted operation and returns the result. The agent can then use that result to continue its reasoning or produce an answer.

## 6. agent decision loop

The control cycle that allows an AI agent to evaluate a request, decide whether an action is necessary, execute it, observe the result, and continue until the task is completed.

## 7. tool discovery

An mcp client queries a server to discover its available tools, including their names, desciptions, and input schemas. This allows the application to integrate tools without hardcoding their implementation.

## 8. tool routing

The process of deciding which available tool should handle a request. Routing can be rule-based or performed by an LLM. An LLM-based router can use the user's request and tool descriptions to choose a suitable tool.

> user request
> ↓
> agent decision logic (choose whether to call a tool)
> ↓
> MCP client → MCP server → tool
> ↓
> tool → MCP server → MCP client
> ↓
> tool result → agent → response

**Caution**: 02 example is not an AI agent. We've implemented the tool execution portion of an agent architecture, but our decision logic is hardcoded. An LLM-powered agent would dynamically decide whether to call a tool, which tool to call, and what arguments to provide, based on the request and available tool schema.




## 9. LLM tool calling + mcp

LLM tool or function calling is a mechanism allowing an LLM to request an external function instead of directly answering. The model generate a tool name and structured arguments, while application code validates and executes the operation.

Tool schema is a machine readable description of a tool's name, purpose, and accepted arguments, usually expressed using JSON schedma. The LLM uses this information to select tools and construct valid requests.

Agent orchestration: the application logic that coordinates decisions, tool execution, results, and subsequent model calls. The LLM decides what to request, but the orchestration layer controls what is actually executed.

> An LLM does not execute MCP tools itself. Our application bridges the LLM's function calls to an MCP client.

what happens actually is shown below:
>User Request
> ↓
>LLM
> ↓
>Decides whether to call a tool and with what arguments
> ↓
>Python Orchestrator → MCP Client → MCP Server
> ↓
>Tool Result → LLM → Final Answer



**API client** is a python library that communicates with a hosted LLM through an API. For example we can install and use OpenAI SDK,

```
pip install openai
```

Then we need to set an environment variable for API key like as follows:

```
export OPENAI_API_KEY="your-api-key"
```

An OpenAI API key requires API access and may incur usage charges; a ChatGPT subscription does not automatically include API credits. Do not commit the key to GitHub.


> What is the difference between function calling and MCP?
> Function calling defines how an LLM requests operations using **tool schemas**. MCP standardizes how applications discover and communicate with tools exposed by external servers. They are **complementary**: our orchestration layer translates LLM function calls into MCP requests.

pay attention that two calls happen in code 03, the following figure shows why:

![two times llm call](assets/session1/img/two_llm_calls.png)

## command to execute

```
mcp dev mcp_server.py
```

```
python mcp_client.py
```

# to install

```
 brew install uv

 pip install -U "mcp[cli]"


```

# env to make with mini-conda

```
conda create --name ai-engineer

conda install python

pip install -U "mcp[cli]"
```
