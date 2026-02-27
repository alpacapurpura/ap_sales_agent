I have diagnosed the issues based on the logs:

1.  **Critical Crash (`metadata` collision)**: The error `generate_prompt() got multiple values for keyword argument 'metadata'` is caused by passing `metadata` in `kwargs` to the LangChain `invoke` method. The `OpenAIService` was not removing this argument before calling the model, causing a conflict.
2.  **API Error (`max_tokens`)**: The error `max_tokens is too large: 5000` occurs because the `node_state_manager` requests 5000 output tokens, but the model (likely GPT-4 or similar) has a limit of 4096 output tokens.

I propose the following fixes:

### 1. Fix `src/core/llm/providers/openai.py`
-   Modify `generate_response` to extract and remove `metadata` from `kwargs` *before* invoking the LLM.
-   Ensure the extracted `metadata` is still available for the logging logic in the `finally` block.

### 2. Fix `src/core/nodes.py`
-   Reduce `max_output_tokens` in `node_state_manager` from `5000` to `4000` (or `2048`) to comply with model limits.

This will resolve the "lapsus mental" fallback response and the API errors.
