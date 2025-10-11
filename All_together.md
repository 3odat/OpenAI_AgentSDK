Let’s break this entire script down step by step, **technically and logically**, so you fully understand **how the workflow executes** and what happens *at each layer of the Agent SDK runtime*.

---

# 🧩 OVERVIEW

This code builds a **mini-agentic system** with:

* 🧠 A **triage (supervisor) agent** that routes questions to the right expert (`Math Tutor`, `History Tutor`).
* 🔒 A **guardrail** that only allows **homework-related** questions to go through.
* 🧮 Two **specialist agents** (`Math Tutor` and `History Tutor`) that answer the question.
* ⚙️ A **Runner** that orchestrates everything.

---

## 🧱 1️⃣ Define the structured output for the guardrail

```python
class HomeworkOutput(BaseModel):
    is_homework: bool
    reasoning: str
```

* This is a **Pydantic schema** that defines the **expected structure** of the guardrail’s output.
* The guardrail agent must output:

  ```json
  {
    "is_homework": true or false,
    "reasoning": "Explanation text"
  }
  ```
* This ensures the model output is **machine-validated**, not free text.

🧠 Think of it as:

> "The guardrail agent must answer in this format."

---

## 🧩 2️⃣ Define the **guardrail agent**

```python
guardrail_agent = Agent(
    name="Guardrail check",
    instructions="Check if the user is asking about homework.",
    output_type=HomeworkOutput,
)
```

* This is a **small classification agent**.
* It reads a user question and answers whether it’s about homework.
* It uses the `HomeworkOutput` model — so it must respond with that structure.

🧠 Think of it as:

> “A security agent that analyzes the question before letting it through.”

---

## 🧠 3️⃣ Define the **specialist agents**

```python
math_tutor_agent = Agent(
    name="Math Tutor",
    handoff_description="Specialist agent for math questions",
    instructions="You provide help with math problems. Explain your reasoning at each step and include examples",
)

history_tutor_agent = Agent(
    name="History Tutor",
    handoff_description="Specialist agent for historical questions",
    instructions="You provide assistance with historical queries. Explain important events and context clearly.",
)
```

Each one:

* Has a **specific domain**.
* The `handoff_description` helps the **triage agent** decide when to use them.
* These agents are *workers* in your small organization.

🧠 Think of them like:

> “Math teacher” and “History teacher” ready to be assigned questions.

---

## 🧩 4️⃣ Define the **guardrail function**

```python
async def homework_guardrail(ctx, agent, input_data):
    result = await Runner.run(guardrail_agent, input_data, context=ctx.context)
    final_output = result.final_output_as(HomeworkOutput)
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_homework,
    )
```

Let’s explain this line-by-line:

| Line                                                    | What it does                                                                              |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `result = await Runner.run(...)`                        | Runs the **guardrail agent** on the input text.                                           |
| `final_output = result.final_output_as(HomeworkOutput)` | Parses and validates the agent’s output using Pydantic (`is_homework`, `reasoning`).      |
| `tripwire_triggered=not final_output.is_homework`       | If the result says “not homework,” it triggers the guardrail tripwire (blocks execution). |
| `GuardrailFunctionOutput(...)`                          | Returns the structured result and tripwire flag to the SDK.                               |

🧠 In short:

> This function **calls the guardrail agent**, gets a True/False result, and decides whether to block or allow the question.

---

## 🧠 5️⃣ Define the **triage agent** (the supervisor)

```python
triage_agent = Agent(
    name="Triage Agent",
    instructions="You determine which agent to use based on the user's homework question",
    handoffs=[history_tutor_agent, math_tutor_agent],
    input_guardrails=[InputGuardrail(guardrail_function=homework_guardrail)],
)
```

This is the **main entry agent** — it:

* Decides which tutor to hand off to.
* Has access to **both tutors** as `handoffs`.
* Has one **input guardrail** that must approve the question before running.

🧭 Here’s the logic:

1. When the user asks a question, the triage agent doesn’t run immediately.
2. The guardrail (`homework_guardrail`) runs first.
3. If the question is approved (`is_homework=True`):

   * The triage agent proceeds.
   * It decides whether to hand off to Math Tutor or History Tutor.
4. If the question is not approved (`is_homework=False`):

   * The SDK raises an exception → `InputGuardrailTripwireTriggered`.
   * The workflow stops.

✅ This ensures that **only homework-related questions** are handled.

---

## ⚙️ 6️⃣ Define the main runner function

```python
async def main():
    # Example 1: History question
    try:
        result = await Runner.run(triage_agent, "who was the first president of the united states?")
        print(result.final_output)
    except InputGuardrailTripwireTriggered as e:
        print("Guardrail blocked this input:", e)

    # Example 2: General/philosophical question
    try:
        result = await Runner.run(triage_agent, "What is the meaning of life?")
        print(result.final_output)
    except InputGuardrailTripwireTriggered as e:
        print("Guardrail blocked this input:", e)
```

### What happens when `main()` runs:

---

### 🧩 Example 1: “Who was the first president of the United States?”

**Flow:**

1. The `Runner` starts a run with the `triage_agent`.
2. Before anything else, the SDK runs its **input guardrail**:

   * Calls `homework_guardrail()`
   * That calls the **guardrail agent**
   * The guardrail agent’s LLM says:

     ```json
     {"is_homework": true, "reasoning": "The question is about history homework."}
     ```
   * Tripwire is **not triggered**.
3. The SDK allows the run to continue.
4. The **triage agent** receives the question:

   * It reads its `handoffs` list → `[history_tutor_agent, math_tutor_agent]`.
   * It decides this is a **history question**.
   * It “hands off” the input to `history_tutor_agent`.
5. The **history tutor agent** answers:

   > “The first president of the United States was George Washington.”
6. The **Runner** returns the final result:

   ```text
   The first president of the United States was George Washington.
   ```

✅ Printed output:

```
The first president of the United States was George Washington.
```

---

### 🧩 Example 2: “What is the meaning of life?”

**Flow:**

1. The **input guardrail** runs again.
2. The guardrail agent classifies the question:

   ```json
   {"is_homework": false, "reasoning": "This is a philosophical question, not homework."}
   ```
3. The guardrail function sees `is_homework=False`.
4. It sets `tripwire_triggered=True`.
5. The SDK **raises an exception**: `InputGuardrailTripwireTriggered`.
6. The `try/except` catches it and prints:

   ```
   Guardrail blocked this input: ...
   ```

✅ Printed output:

```
Guardrail blocked this input: ...
```

---

## 🧠 7️⃣ Visual Workflow

```
User Input
   ↓
[Input Guardrail Function]
   ↓
┌───────────────┐
│ Guardrail Agent│
│  (LLM decides) │
└─────┬─────────┘
      │
      ├─> if is_homework = False → 🚫 STOP (tripwire triggered)
      │
      └─> if is_homework = True → ✅ CONTINUE
             ↓
        Triage Agent
             ↓
     ┌──────────────┐
     │ Handoffs     │
     │ (Math / Hist)│
     └──────┬───────┘
            ↓
     Specialist Agent
            ↓
        Final Output
```

---

## 🧭 8️⃣ What’s happening under the hood (Runner)

When you call:

```python
await Runner.run(triage_agent, input)
```

`Runner` does this:

1. Builds a `RunContextWrapper` (context, session, memory).
2. Checks for input guardrails → runs them in sequence.
3. If any guardrail triggers → raises exception.
4. Otherwise, sends the message to the agent’s model.
5. If the model calls a handoff → calls `Runner.run()` again for that sub-agent.
6. Collects final result and returns `RunResult` with:

   * `.final_output` (text)
   * `.usage` (token stats)
   * `.new_items` (messages)

---

## ✅ 9️⃣ Why this example is powerful

It demonstrates:

* **Guardrail enforcement** ✅ (filters irrelevant input)
* **Agent collaboration** ✅ (Triage → specialist)
* **Automatic routing** ✅ (handoffs)
* **Structured validation** ✅ (Pydantic schema)
* **Safe error handling** ✅ (`InputGuardrailTripwireTriggered`)

---

## 🧩 TL;DR Summary Table

| Component                                  | Role                                  | Happens When                                    |
| ------------------------------------------ | ------------------------------------- | ----------------------------------------------- |
| `HomeworkOutput`                           | Defines structure of guardrail output | During validation                               |
| `guardrail_agent`                          | Checks if input is homework           | Called inside `homework_guardrail()`            |
| `homework_guardrail()`                     | Runs guardrail agent, sets tripwire   | Before triage agent runs                        |
| `InputGuardrail(...)`                      | Wraps guardrail function for SDK      | Passed into triage agent                        |
| `triage_agent`                             | Routes question to correct tutor      | After guardrail passes                          |
| `math_tutor_agent` / `history_tutor_agent` | Specialists                           | Receive the final question                      |
| `Runner.run()`                             | The orchestrator                      | Manages all steps, guardrails, handoffs, output |
| `InputGuardrailTripwireTriggered`          | Exception type                        | Raised when guardrail blocks input              |

---

Would you like me to show a **diagram or timeline view** (like a mission log) of what exactly happens in order (step 1–10) from the moment the `Runner.run()` is called until the final print?
