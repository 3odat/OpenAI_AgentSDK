## 🧱 File Overview

The file defines:

* Base helper dataclasses (`ToolsToFinalOutputResult`, `AgentBase`, etc.)
* The main class: **`Agent`**
* Internal methods: for tools, handoffs, guardrails, model settings, etc.

This is the **core object** of the entire OpenAI Agents SDK —
every “assistant” you create (like your `Math Tutor`, `Triage Agent`, etc.) is built from this class.

---

## ⚙️ Part 1: Supporting Structures

### 1️⃣ `ToolsToFinalOutputResult`

```python
@dataclass
class ToolsToFinalOutputResult:
    is_final_output: bool
    final_output: Any | None = None
```

🧠 Purpose:
When an agent uses tools (e.g., calculator, search, etc.), this class helps decide:

* Should the output from that tool be treated as the **final answer**,
  or should the agent **run the LLM again** using that result as context?

📖 Example:
If the agent used a weather tool, the SDK asks:

> “Is this tool result final, or should I ask the LLM to explain it?”

---

### 2️⃣ `ToolsToFinalOutputFunction`

A **callable type alias** (like a function signature):

```python
ToolsToFinalOutputFunction = Callable[[RunContextWrapper, list[FunctionToolResult]], MaybeAwaitable[ToolsToFinalOutputResult]]
```

🧠 Means: a function that takes tool results and tells the SDK what to do next.
It supports both normal and async (awaitable) behavior.

---

### 3️⃣ `StopAtTools` / `MCPConfig`

These define configuration rules:

* **`StopAtTools`** → stops running when a specific tool name appears.
  Useful for safety or limited actions.

* **`MCPConfig`** → configuration for **Model Context Protocol servers** (like external data APIs).
  Example: convert schemas to strict JSON for validation.

---

## 🧩 Part 2: `AgentBase`

This is the *parent class* for `Agent` and `RealtimeAgent`.

It defines common attributes shared by all agents.

```python
@dataclass
class AgentBase(Generic[TContext]):
```

| Attribute             | Meaning                                                  |
| --------------------- | -------------------------------------------------------- |
| `name`                | Unique name of the agent (e.g., “Math Tutor”)            |
| `handoff_description` | A summary of what this agent does — used for routing     |
| `tools`               | List of callable functions the agent can use             |
| `mcp_servers`         | Connected Model Context Protocol servers (external APIs) |
| `mcp_config`          | Config for MCP servers                                   |

---

### 🔧 Key methods:

#### `get_mcp_tools()`

Asynchronously fetches all available tools from connected servers.

#### `get_all_tools()`

Combines both:

* `tools` defined manually, and
* `mcp_tools` fetched dynamically.

🧠 This is how the SDK builds the “tool inventory” an agent can see during reasoning.

---

## 🤖 Part 3: The `Agent` Class

This is the *real thing* you create in your code:

```python
@dataclass
class Agent(AgentBase)
```

It **extends** `AgentBase` and adds everything specific to reasoning, guardrails, handoffs, and models.

Let’s break it down.

---

### 🧠 Core Attributes

| Attribute           | Purpose                                        | Example                                                  |
| ------------------- | ---------------------------------------------- | -------------------------------------------------------- |
| `instructions`      | The **system prompt** (defines agent behavior) | “You are a math tutor who explains every step.”          |
| `prompt`            | Optional object for dynamic prompt building    | Custom `Prompt` classes                                  |
| `handoffs`          | Other agents this one can delegate to          | `[math_tutor, history_tutor]`                            |
| `model`             | Which OpenAI model to use                      | `"gpt-4o-mini"`, `"gpt-5"`                               |
| `model_settings`    | Controls creativity, top_p, temperature, etc.  | `ModelSettings(temperature=0.7)`                         |
| `input_guardrails`  | Pre-filters or validators before reasoning     | “Reject unsafe input”                                    |
| `output_guardrails` | Post-filters for validating responses          | “Ensure JSON format is correct”                          |
| `output_type`       | Defines type of expected output                | `str`, `TypedDict`, `dataclass`                          |
| `hooks`             | Lifecycle callbacks (start, finish, tool_call) | Useful for tracing or logging                            |
| `tool_use_behavior` | How to handle tool outputs                     | `'run_llm_again'`, `'stop_on_first_tool'`, or a function |
| `reset_tool_choice` | Resets chosen tool after each use              | Prevents infinite loops                                  |

---

## 🧩 Internal Methods

### 1️⃣ `__post_init__()`

This runs **automatically after initialization**.

✅ It performs **type validation** for all fields — e.g.:

* Checks `name` is a string
* Ensures `tools` is a list
* Validates `model` type
* Adjusts defaults if model = GPT-5
* Ensures `tool_use_behavior` is valid

🧠 In human terms: this is like the “entry inspection” step when creating an agent — ensuring all its settings make sense before it starts working.

---

### 2️⃣ `clone()`

```python
def clone(self, **kwargs) -> Agent:
```

Creates a **shallow copy** of the agent with optional overrides.

Example:

```python
new_agent = math_tutor.clone(instructions="Focus on geometry only.")
```

🧠 Think of it as “duplicate this teacher, but slightly change their personality.”

---

### 3️⃣ `as_tool()`

Turns the **entire agent** into a **tool** that another agent can call.

Example:

```python
math_tool = math_tutor.as_tool("solve_math", "Solves math problems.")
```

Now the math tutor can be “called” like a calculator by another agent.

⚙️ Internally, this method wraps the `Runner.run()` inside an async tool function.

---

### 4️⃣ `get_system_prompt()`

If `instructions` is:

* a string → returns it directly,
* a function → calls it dynamically with `(context, self)`,
* invalid → logs an error.

🧠 This lets you **generate custom prompts on the fly** based on runtime context.

---

### 5️⃣ `get_prompt()`

Builds a complete **ResponsePromptParam** (what the OpenAI model actually sees).

Uses `PromptUtil.to_model_input()` to convert your prompt object to the model-ready structure.

---

## 🧭 Internal Interaction Flow

Here’s how all these parts connect during a real agent run:

```
User → Runner.run(agent, input)
         ↓
  Agent.get_system_prompt()     → builds base prompt
  Agent.get_all_tools()         → fetches tools (local + MCP)
  Model.run()                   → sends message to LLM
  Tool_use_behavior              → decides how to handle tools
  Guardrails                     → check input/output
  (optional) Handoff             → route to sub-agent
         ↓
Final Answer
```

---

## 🧠 Summary Table of Key Features

| Feature          | Purpose                       | When It’s Used                |
| ---------------- | ----------------------------- | ----------------------------- |
| `handoffs`       | Multi-agent collaboration     | During routing                |
| `tools`          | Give agent action abilities   | When LLM calls tool functions |
| `guardrails`     | Safety + validation           | Input/output checking         |
| `model_settings` | Model tuning                  | When calling OpenAI API       |
| `hooks`          | Logging lifecycle             | Before/after run              |
| `clone()`        | Duplicate agent               | To create variants            |
| `as_tool()`      | Turn agent into callable tool | For nested workflows          |

---

## 🧩 In simple analogy form

| Code Component | Real-Life Analogy                                       |
| -------------- | ------------------------------------------------------- |
| `AgentBase`    | Employee base info (name, ID, job title)                |
| `Agent`        | Actual employee with full skills and job description    |
| `handoffs`     | Co-workers this employee can refer you to               |
| `tools`        | Things the employee can *do* (calculator, search, etc.) |
| `guardrails`   | Company policies for what they can/can’t say            |
| `clone()`      | Hiring a twin with slightly different training          |
| `as_tool()`    | Turning an employee into a “service” another can call   |
| `Runner`       | The manager who gives them tasks and collects results   |

---

If you’d like, next I can create a **visual diagram** (arrows and boxes) showing how the `Agent` interacts with `Runner`, `handoffs`, and `tools` in runtime — would you like that?
