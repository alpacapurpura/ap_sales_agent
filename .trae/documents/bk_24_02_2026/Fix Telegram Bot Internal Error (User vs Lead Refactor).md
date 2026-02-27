I have identified the root cause of the error:
The `ChatOrchestrator` is attempting to look up and create users in the `users` table using `telegram_id`, but the system has been refactored to store chatbot contacts in the `leads` table. The `User` model no longer has channel-specific IDs (Telegram/WhatsApp), while the `Lead` model does.

### Plan:

1.  **Create `LeadRepository`**:
    -   Create a new file `backend/src/services/db/repositories/lead.py`.
    -   Implement `get_by_channel_id` to find leads by Telegram/WhatsApp ID.
    -   Implement `create_lead` to register new contacts from these channels.
    -   Implement `get_by_id` and `update_profile` for the `Lead` model.

2.  **Refactor `ChatOrchestrator`**:
    -   Modify `backend/src/services/chat_orchestrator.py` to use `LeadRepository` instead of `UserRepository`.
    -   Replace all references to `user_repo` with `lead_repo` in the chat flow logic.
    -   Ensure the `user` object (now a `Lead`) is correctly passed to the agent state and audit logs.

3.  **Verification**:
    -   Restart the backend service.
    -   Send a test message via Telegram ("hola amiga, como estas").
    -   Verify that the bot responds correctly without the "internal error" message.
