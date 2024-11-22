Okay, here's the LangChain Expression Language (LCEL) cheatsheet reformatted into a document format, along with a concise cheatsheet at the beginning.

**Document Title:** LangChain Expression Language (LCEL) Reference Guide

**Version:** 0.3

**Introduction:**

This document provides a comprehensive reference for the LangChain Expression Language (LCEL) primitives. It covers basic usage, composition, advanced features, and configuration options. For more in-depth explanations and examples, refer to the LCEL how-to guides and the full API reference.

**Cheat Sheet:**

| Operation                     | Syntax                                    | Description                                                                                                              |
| ----------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Invoke                        | `runnable.invoke(input)`                 | Execute a runnable with a single input.                                                                                   |
| Async Invoke                  | `await runnable.ainvoke(input)`           | Execute a runnable asynchronously.                                                                                      |
| Batch                         | `runnable.batch([input1, input2, ...])`   | Execute a runnable with multiple inputs.                                                                                   |
| Async Batch                   | `await runnable.abatch([input1, input2,...])`| Execute a runnable asynchronously with multiple inputs.                                                                                    |
| Stream                        | `runnable.stream(input)`                 | Execute a runnable and stream its output.                                                                                |
| Async Stream                  | `await runnable.astream(input)`           | Execute a runnable asynchronously and stream its output.                                                                                |
| Compose (Pipe)                | `runnable1 \| runnable2`                 | Chain two runnables together sequentially.                                                                               |
| Parallel                      | `RunnableParallel(a=runnable1, b=runnable2)`| Execute multiple runnables in parallel.                                                                                    |
| Lambda (Function to Runnable) | `RunnableLambda(func)`                   | Convert a Python function into a runnable.                                                                               |
| Assign                        | `RunnablePassthrough.assign(key=runnable)`| Merge the output of a runnable into the input dictionary.                                                                 |
| Pass Through                  | `RunnablePassthrough()`                  | Pass the input directly to the output, optionally merging other outputs.                                                    |
| Bind                          | `runnable.bind(arg=value)`               | Partially apply arguments to a runnable.                                                                                |
| Fallback                      | `runnable.with_fallbacks([fallback_runnable])`| Use a fallback runnable if the primary runnable fails.                                                                   |
| Retry                         | `runnable.with_retry(stop_after_attempt=n)` | Retry a runnable multiple times on failure.                                                                                |
| Config                        | `runnable.invoke(input, config={...})`     | Configure runnable execution (e.g., concurrency).                                                                          |
| Add Config                     | `runnable.with_config(...)` | Add default config to a runnable.                                                                          |
| Configurable Fields           | `runnable.configurable_fields(...)`       | Make runnable attributes configurable at runtime.                                                                        |
| Configurable Alternatives      | `runnable.configurable_alternatives(...)`   | Make chain components configurable at runtime.                                                                        |
| Dynamic Chains               | `RunnableLambda(lambda x: runnable1 if condition else runnable2)` | Create chains dynamically based on input.                                                                   |
| Stream Events                 | `runnable.astream_events()`              | Get a stream of events during runnable execution.                                                                       |
| Batch as Completed            | `runnable.batch_as_completed(...)`         | Yield results from a batch as they complete.                                                                           |
| Pick                          | `runnable.pick(["key1", "key2"])`          | Select specific keys from the output dictionary.                                                                        |
| Map                           | `runnable.map()`                         | Declaratively create a batched version of a runnable.                                                                    |
| Graph                         | `runnable.get_graph()`                   | Get a graph representation of the runnable's structure.                                                                  |
| Prompts                       | `runnable.get_prompts()`                 | Get all prompts contained within a chain.                                                                                 |
| Listeners                     | `runnable.with_listeners(on_start, on_end)` | Add lifecycle listeners to a runnable.                                                                                  |

---

**Table of Contents**

1. [Basic Operations](#basic-operations)
    *   [Invoking a Runnable](#invoking-a-runnable)
    *   [Batching a Runnable](#batching-a-runnable)
    *   [Streaming a Runnable](#streaming-a-runnable)
2. [Composition and Chaining](#composition-and-chaining)
    *   [Composing Runnables with the Pipe Operator](#composing-runnables-with-the-pipe-operator)
    *   [Invoking Runnables in Parallel](#invoking-runnables-in-parallel)
3. [Creating Runnables](#creating-runnables)
    *   [Turning Any Function into a Runnable](#turning-any-function-into-a-runnable)
    *   [Merging Input and Output Dictionaries](#merging-input-and-output-dictionaries)
    *   [Including Input Dictionary in Output Dictionary](#including-input-dictionary-in-output-dictionary)
4. [Modifying Runnables](#modifying-runnables)
    *   [Adding Default Invocation Arguments](#adding-default-invocation-arguments)
    *   [Adding Fallbacks](#adding-fallbacks)
    *   [Adding Retries](#adding-retries)
5. [Configuring Runnables](#configuring-runnables)
    *   [Configuring Runnable Execution](#configuring-runnable-execution)
    *   [Adding Default Configuration to a Runnable](#adding-default-configuration-to-a-runnable)
    *   [Making Runnable Attributes Configurable](#making-runnable-attributes-configurable)
    *   [Making Chain Components Configurable](#making-chain-components-configurable)
6. [Advanced Usage](#advanced-usage)
    *   [Building a Chain Dynamically Based on Input](#building-a-chain-dynamically-based-on-input)
    *   [Generating a Stream of Events](#generating-a-stream-of-events)
    *   [Yielding Batched Outputs as They Complete](#yielding-batched-outputs-as-they-complete)
    *   [Returning a Subset of the Output Dictionary](#returning-a-subset-of-the-output-dictionary)
    *   [Declaratively Making a Batched Version of a Runnable](#declaratively-making-a-batched-version-of-a-runnable)
    *   [Getting a Graph Representation of a Runnable](#getting-a-graph-representation-of-a-runnable)
    *   [Getting All Prompts in a Chain](#getting-all-prompts-in-a-chain)
    *   [Adding Lifecycle Listeners](#adding-lifecycle-listeners)

---

**1. Basic Operations**

**1.1 Invoking a Runnable**

*   **`Runnable.invoke(input)` / `Runnable.ainvoke(input)`**: Executes a runnable with a single input.

    ```python
    from langchain_core.runnables import RunnableLambda

    runnable = RunnableLambda(lambda x: str(x))
    result = runnable.invoke(5)  # Synchronous invocation
    # Async variant:
    # result = await runnable.ainvoke(5) # Asynchronous invocation
    print(result)  # Output: '5'
    ```

    *   **API Reference:** [`RunnableLambda`](https://api.python.langchain.com/en/latest/runnables/langchain_core.runnables.RunnableLambda.html)

**1.2 Batching a Runnable**

*   **`Runnable.batch([input1, input2, ...])` / `Runnable.abatch([input1, input2, ...])`**: Executes a runnable with multiple inputs.

    ```python
    from langchain_core.runnables import RunnableLambda

    runnable = RunnableLambda(lambda x: str(x))
    results = runnable.batch([7, 8, 9])  # Synchronous batch processing
    # Async variant:
    # results = await runnable.abatch([7, 8, 9]) # Asynchronous batch processing
    print(results)  # Output: ['7', '8', '9']
    ```

    *   **API Reference:** [`RunnableLambda`](https://api.python.langchain.com/en/latest/runnables/langchain_core.runnables.RunnableLambda.html)

**1.3 Streaming a Runnable**

*   **`Runnable.stream(input)` /  `Runnable.astream(input)`**: Executes a runnable and streams its output.

    ```python
    from langchain_core.runnables import RunnableLambda

    def func(x):
        for y in x:
            yield str(y)

    runnable = RunnableLambda(func)

    