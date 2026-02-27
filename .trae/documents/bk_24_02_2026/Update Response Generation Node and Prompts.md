I will update the `handle_objection_node` (specifically `node_response_generation` in `src/core/nodes.py`) and the `sales_system.j2` prompt to meet your requirements.

### **Plan of Action**

1.  **Modify `src/core/nodes.py` (`node_response_generation`)**:
    *   **Safety Handling**: Implement an immediate return for `router_outcome="handled_safety"` with `objection_type="safety_violation"`. It will return a polite refusal message without calling the LLM.
    *   **Unified RAG Pipeline**: Route *all* other non-safety interactions (including FAQs and Objections) through the RAG + LLM pipeline to ensure coherence and tone consistency.
    *   **Enhanced RAG Filtering**: Update the `rag_filters` logic to map user queries and intents to the new categories:
        *   `protocol_boundary` (Rules, camera, etc.)
        *   `sales_persuasion` (Objections, psychology)
        *   `financial_legal` (Pricing, contracts)
        *   `product_logic` (Logistics, dates)
        *   `avatar_psychology` (Pain points, desires)
        *   `brand_authority` (Philosophy, founders)
    *   **Downsell**: Add a comment/TODO block to handle downsell items later, as requested.

2.  **Modify `src/core/prompts/templates/sales_system.j2`**:
    *   **Integrate Reasoning**: Add `{{ latest_reasoning }}` (from the Manager node) to the prompt context so the LLM understands *why* it's in the current stage.
    *   **Closed Questions**: Add explicit instructions to ask closed, alternative-based questions (e.g., "A or B?") derived from the RAG context.
    *   **Off-topic/Aggression**: Add instructions to ignore off-topic tangents and aggressive behavior, steering the conversation back to the program.

3.  **Refine Logic**:
    *   Ensure the LLM uses the `current_state` logic combined with the retrieved RAG info to generate the final response.

### **Verification**
*   I will verify the code changes by inspecting the file content.
*   (If possible within the environment) I would simulate a flow, but primarily I will rely on code correctness and adherence to the prompt engineering requirements.
