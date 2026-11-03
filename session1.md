# session 1

## 1. model context protocol (MCP)

MCP is a protocol that standardizes how AI applications communicate with external tools and data sources.

Instead of implementing a custom inegration for every tool, applications can use MCP to discover available capabilities and invoke them through a consistent interface.

MCP standardizes communication, but it does not decide which tools an AI agent should execute. This decision belongs to the agent's orchestration logic.

![agent->client -> server](assets/session1/img/agent-client-server.png)

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





## 10. having local LLM for decision making about which tools should be invoked

**Ollama**: A tool for running and managing language models locally. It exposes an HTTP API, allowing Python applications to interact with models without requiring a paid cloud API.


**Local inference**: Executing an AI model on your own computer rather than sending requests to a cloud provider. It offers greater control over data, but performance depends on your available hardware.


**Tool-calling model**: An LLM capable of generating structured requests for external tools. The model selects the operation, `while our Python application executes it`.



Installing Ollama
```bash
brew install --cask ollama # Installs the Ollama application and local model server on macOS.
open -a Ollama # Starts the Ollama application and server.
pip install -U ollama # Installs the Python client library, allowing Python code to communicate with the Ollama server.
ollama pull qwen3:4b # Downloads the Qwen3 4B model to your computer.
```

for verifying the model

```bash
ollama run qwen3:4b
```

We can have a chat with the model in terminal. For exiting, give it `\bye`.

then if we execute (session1-04)

```bash
python llm_agent.py
```

it will look like as follow:

```bash
$ python llm_agent.py
Ask the agent: need to get gpu utilization
Calling MCP tool: gpu_status({})

Agent: The GPU utilization information is not directly available in the current response. Here's what we do have from the system:

**GPU Status**:
- **Model**: A100
- **Memory**: 40 GB
- **Availability**: Active (available: `true`)

This response indicates the GPU is operational but does not include utilization metrics (e.g., usage percentage, load, etc.). If you need detailed utilization data, you may need to use a different tool or command that specifically tracks GPU usage (e.g., `nvidia-smi` for Linux systems). Let me know if you'd like guidance on that!
```

So, the process in the example was :

> LLM selects gpu_status → MCP executes → LLM responds

and if we ask sth that the LLM can answer without needing tool:

```bash
$ python llm_agent.py
Ask the agent: what is capital of sweden

Agent: The question about the capital of Sweden cannot be answered using the provided tools. The available tool (`gpu_status`) only provides GPU information and isunrelated to geographical data like country capitals. 

<answer>
The capital of Sweden is Stockholm. (Note: This answer is based on general knowledge, not the provided tools.)
</answer>
```

> We can replace Ollama with a cloud LLM. The orchestration architecture remains largeley the same. We replace the model client and adapt the tool schemas and message formats. MCP remains independent of the LLM provider.

## 11. Full agent decision loop

**An agent loop** is a repeated cycle in which an LLM decides what to do, the application executes the requested actions, and the results are returned to the LLM. The cycle continues until the model produces a final answer or a termination condition is reached.

**Termination condition** is a rule determining when an agent should stop. Common conditions include receiving a final response, reaching a maximum number of iterations, exceeding a time budget, or encountering an unrecoverable error.

**Guardrails** are controls enforced by the application to limit what an agent can do. Examples include tool allowlists, argument validation, execution limits, and approval requirements for sensitive operations. Prompt instructions alone are not sufficient security controls.

**Conversation history** is the sequence of user, assistant, and tool messages supplied to the LLM. It lets the model understand previous actions and their results.

![full agent decision loop](assets/session1/img/full_agent_decision_loop.png)


see the example in session1-05

> The allowlist prevents calls to undiscovered tools. For a production system, we'd also enforce argument schemas, permissions, and resource limits.


`Interview question`
> **Why do we need an orchestration loop instead of a single LLM call?**
> Because complex tasks may require several dependent actions. For example, an agent might first inspect available GPUs, then check their utilization, and finally select a device. Each decision can depend on the result of a previous tool call. The orchestration loop coordinates these interactions while enforcing termination and execution policies.

## 12. Multi-step mcp tool execution

**Parameterized tools** are tools that only accept structured input rather than performing a fixed operation. For example, a GPU suitability checker might accept available memory and required memory. MCP automatically generates their input schemas from Python type annotations.

**Tool chaining**. Using the output of one tool as input to another one. The agent can first retrieve information, then use that information to decide its next action.

**Dynamic planning**. An LLM can choose the next action based on previous observations rather than following a completely predetermined sequence. However, tool chaining alone does not guarantee sophisticated planning.

**Dependency management**. Some tool calls can execute independently, while others must execute sequentially because one needs another's output. This distinction becomes particularly important when we study agent parallelization.

see the following example:

![two tools](assets/session1/img/two_tools.png)


check example code in session1/06. then verify with 

```
python llm_agent.py
```

if sth like as follows goes on:

```
$ python llm_agent.py            
Ask the agent: I want to train a model requiring 24 GB of GPU memory. Check the current GPU and then evaluate whether the model fits.

Agent step 1
Selected tools: ['gpu_status']
Tool: gpu_status({})

Agent step 2
Selected tools: ['estimate_training_fit']
Tool: estimate_training_fit({'available_memory_gb': 40, 'required_memory_gb': 24})

Agent step 3
Selected tools: []

Agent: The current GPU is an NVIDIA A100 with **40.0 GB** of available memory. Your model requires **24 GB**, which **fits** in the available memory with **16.0 GB** remaining. ✅
```

>**What is the difference between sequential and parallel tool execution?**
>In sequential execution, one tool completes before another executes. This is necessary when the second operation depends on the first operation's result.
>In parallel execution, independent tool calls can run concurrently, potentially reducing total latency. However, parallel execution requires careful handling of dependencies, failures, and shared resources.

## 13. Parallel mcp tool execution

**Concurrency**. Multiple operations make progress during overlapping periods. In Python, `asyncio` supports concurrency for I/O-bound tasks without requiring multiple threads.

**Parallel tool calling**. An LLM can request multiple tool executions in one response. The orchesterator can then dispatch independent requests concurrently and collect their results.


`asyncio.gather()` is an asynchronous python function that runs multiple awaitable operations concurrently and returns their results in the same order as the inputs.

**Concurrency vs. parallelism**. Concurrency means operations overlap in time; parallelism means work executes simultaneously. asyncio primarily provides concurrency, which is particularly useful for network requests, API calls, and MCP communication.

see the following example
![parallel mcp tool](assets/session1/img/parallel_mcp_tool.png)


check code in session1/07

>**Fan-out/fan-in**: Fan-out dispatches independent operations concurrently. Fan-in collects their results before the next processing step.

Then the example when executing will be sth like:

```bash
$ python llm_agent.py 
Ask the agent: Check both my GPU utilization and temperature using their respective tools, and summarize the results.

Agent step 1
Selected tools: ['gpu_utilization', 'gpu_temperature']
Executed: gpu_utilization
Executed: gpu_temperature
Tool execution time: 2.02s

Agent step 2
Selected tools: []

Agent: Your GPU utilization is currently at **75%** and the temperature is **65°C**. Both metrics indicate healthy operation within normal ranges.
```


> Should all agent tool calls execute concurrently?
> No. Only independent operations should be executed concurrently. If one tool requires another tool's output, the orchestrator must preserve their dependency order. Parallel execution also requires handling timeouts, errors, rate limits, and shared resources.

## 14. Tool secutiry, validation, and retires

**input valication**. Checking tool arguments against expected types, formats, and contraints before execution. This prevents malformed requests from reaching a tool. We can validate arguments against the **JSON Schema** advertised by `MCP`.

**tool authorization**: Restricting which operations an agent may execute. An MCP server advertising a tool does not automatically mean the agent should be permitted to use it.

**Retry policy**: A strategy for repeating an operation after **a temporary failure**. Retries should be bounded, and generally restricted to safe or `idempotent` operations, *since retrying a state-changing operation could duplicate its effects*.

**Least privilege**: Granting an agent only the capabilities necessary for its task. For example, a GPU monitoring agent may need permission to read GPU metrics but not execute shell commands.

see the concepts in the following image

![tool secutiry, validation, retires](assets/session1/img/tool_secutiry_validation_retries.png)


**Declarative constraints** describe permitted inputs using schemas instead of relying on manual checks scattered throughout application code. `Pydantic's field` can generate these contraints for mcp tools. 

check code in session1/08 - check and compare old commented and new estimate_training_fit function.

for adding secutiry and retry, we need to install 

```bash
pip install jsonschema
```

**Defense in depth**: We validate inputs in our agent before sending them to MCP, even though the high-level MCP server also validates its own tool parameters. Multiple independent validation layers reduce risk.

see the code in session1/08/llm_agent.py

Examples would look like as follows:

```bash
$ python llm_agent.py
Ask the agent: Check whether a 24 GB model fits

Agent step 1
Selected tools: ['gpu_status']
Tool: gpu_status -> {"meta": null, "content": [{"type": "text", "text": "{\n  \"gpu\": \"NVIDIA A100\",\n  \"available_memory_gb\": 40.0,\n 
Tool execution time: 0.01s

Agent step 2
Selected tools: ['estimate_training_fit']
Tool: estimate_training_fit -> {"meta": null, "content": [{"type": "text", "text": "{\n  \"fits_in_memory\": true,\n  \"remaining_memory_gb\": 16.0\n}"
Tool execution time: 0.01s

Agent step 3
Selected tools: []

Agent: The 24 GB model **fits** in the available GPU memory.  
✅ **Remaining memory**: 16 GB (after deployment)  

This means your model can run without exceeding the GPU's capacity. Let me know if you need further adjustments!
```

```bash
$ python llm_agent.py
Ask the agent: Check whether a -5 GB model fits

Agent step 1
Selected tools: ['gpu_status']
Tool: gpu_status -> {"meta": null, "content": [{"type": "text", "text": "{\n  \"gpu\": \"NVIDIA A100\",\n  \"available_memory_gb\": 40.0,\n 
Tool execution time: 0.01s

Agent step 2
Selected tools: ['estimate_training_fit']
Tool: estimate_training_fit -> Invalid arguments: -5 is less than the minimum of 0
Tool execution time: 0.00s

Agent step 3
Selected tools: []

Agent: The required memory value of -5 GB is invalid (memory cannot be negative). This likely indicates a typo in your request. Could you confirm the intended memory size (e.g., "5 GB" instead of "-5 GB")? I'll help check feasibility with the correct value.
```

```bash
$ python llm_agent.py
Ask the agent: decrease GPU working frequency

Agent step 1
Selected tools: []

Agent: The user requested to "decrease GPU working frequency," but none of the provided tools (`gpu_status`, `estimate_training_fit`, `gpu_utilization`, `gpu_temperature`) are designed to modify GPU settings like working frequency. These tools only provide read-only GPU status information and memory feasibility checks. There is no function available to adjust GPU frequency or configuration parameters. 

<response>
No tool is available to decrease GPU working frequency. The provided functions only retrieve GPU status and memory information, not configuration settings.
</response>
```

>**Q: How do you secure an LLM agent that executes external tools?**
>I would implement security in the orchestration layer rather than relying only on prompts. This includes an explicit tool allowlist, schema-based argument validation, least-privilege permissions, timeouts, bounded retries, and audit logging. Sensitive operations should also require authorization or human approval.

## 15. refactoring the code we practiced till here ...

**Separation of concerns**: A software design principle where each component has a clearly defined responsibility. This makes applications easier to test, maintain, debug, and extend.

**Modularity**: Organizing software into independent components with well-defined interfaces. For example, we should be able to replace Ollama with another LLM provider without rewriting our MCP execution logic.

**Dependency injection**: Providing a component with the dependencies it needs instead of creating them internally. This makes it easier to substitute mock dependencies during testing.

**Orchestrator**: The component responsible for coordinating the overall agent workflow: sending requests to the LLM, executing selected tools, collecting observations, and determining when to terminate.

![agent architecture](assets/session1/img/agent_architecture.png)


We'll preserve all the capabilities we've implemented: dynamic tool discovery, LLM decisions, concurrent execution, input validation, authorization, retries, and bounded iterations.

We'll also use the current MCP Python SDK v2 Client interface instead of the older ClientSession boilerplate. The official SDK recommends this higher-level client.

we keep the mcp_server.py as it was and we organize the rest as follows inside session1/09. 

```
ai-agent
├── main.py
├── agent.py
├── llm.py
├── tool_executor.py
├── mcp_server.py
└── requirements.txt
```
### LLM component - `llm.py`
**Responsibility**: Communicate with the language model. Other components don't need to know which LLM provider is being used. See `llm.py` in session1/09

If we later switch providers, this is the main integration point to change.


### tool executor - `tool_executor.py`

**Responsibility**: Enforce permissions, validate arguments, execute MCP tools, and handle failures.

**Fail-closed security**: If a tool is unknown or validation fails, execution is denied by default. *The application should not assume that an LLM-generated request is safe.*

see tool_executor in 09.

This retains bounded retries for our four mock, read-only tools. In production, retry policy should be configured per tool and distinguish transient failures from permanent errors.


### agent orchestrator - `agent.py`

**Responsibility**: Manage the conversation, request LLM decisions, dispatch tools, and enforce termination.

**Dependency injection**: Instead of directly creating Ollama and MCP clients, the agent receives the LLM and tool executor as constructor arguments.

see `agent.py` 

Notice how small our orchestrator has become. It doesn't need to understand the MCP transport, Ollama HTTP API, or JSON Schema validation.

### Application entry point — `main.py`

**Responsibility**: Initialize dependencies and connect components. This is sometimes called the composition root.

Dependencies also go into requirements.txt

```bash
pip install -r requirements.txt
python main.py
```

>Q: Why separate the agent, LLM, and tool executor?
>Each component has one responsibility. The agent manages workflow, the LLM provides decisions, and the executor handles secure tool execution. This improves maintainability, testability, and extensibility.

>Q: How would you replace Ollama with Azure OpenAI?
>I would implement a new LLM adapter exposing the same chat() interface. The orchestration and MCP components could remain largely unchanged, while the adapter handles provider-specific request and response formats.

>Q: How would you unit-test this architecture?
>I would inject a fake LLM that returns predefined tool decisions and a fake MCP client that returns controlled tool results. This allows testing orchestration, authorization, retry limits, and termination without running a real model.

>Q: Is this production-ready?
>Not yet. It has the core building blocks, but still needs structured logging, configuration management, stronger error classification, controlled dependency scheduling, proper tests, and authentication for remote MCP servers.



## 16. Automated tests and observability





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
