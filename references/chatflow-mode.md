# Chatflow mode

Use `app.mode: advanced-chat` when the user needs multi-turn dialogue, conversation-scoped state, chat uploads, or streamed user-visible responses.

## Input and response contract

- User text normally comes from `sys.query`.
- Chat uploads normally come from `sys.files` or the target export's system selector form.
- Start node `variables` is normally empty for a pure Chatflow; preserve explicit user input forms only when supported by the target export and requirement.
- Each response path reaches an `answer` node. Multiple branches may use separate Answer nodes when each produces a valid response.
- Keep machine-readable metadata separate from the human-facing answer when an external channel consumes both.

Minimal shape:

```text
Start → LLM or processing nodes → Answer
```

## State and memory

Treat model memory and business state as different mechanisms:

- LLM memory supplies conversational context; keep its window bounded.
- Conversation variables store explicit structured state such as stage, confirmed fields, current asset, or last action.
- Update structured state through an Assigner/Variable Assigner using the exact schema exported by the target Dify version.
- Each turn should read the previous state and produce a complete, deterministic new state where business correctness matters.
- The caller must isolate `conversation_id` by end user. Never share a conversation across unrelated users.
- Durable records, permissions, audit, payment/order state, and background task status belong in external storage.

## Files and multimodal input

- Route on file presence before passing `sys.files` into a node that requires non-empty files.
- Provide a text-only path and a file path, then normalize or aggregate their outputs before downstream use.
- Use a vision-enabled LLM only when the selected model and provider support it, with a selector matching the chat file input.
- Image-edit and text-to-image HTTP requests often require different body encodings; model them as separate paths.

## Response safety

- Ensure template variables are actually resolved rather than printed literally.
- Strip internal reasoning and sensitive metadata from visible answers.
- Unknown intents and integration failures still need a user-visible fallback Answer.
- Do not let asynchronous model polling block a Chatflow for long periods; return task metadata and let an external worker notify or update the user.

## Delivery tests

At minimum test two consecutive turns, a fresh conversation, each routing intent, file present/absent, unresolved variables, memory/state updates, integration failure, and every Answer path.

