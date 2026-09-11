# Dynamic integrations and portability

## Models

Model providers are plugins. Preserve the exact `provider`, model `name`, mode, completion parameters, and top-level dependency from a target export. If the user does not choose a model, use placeholders and tell them to select an installed provider after import.

## Tools and plugins

Plugin nodes are dynamic. Establish their schema using:

1. a minimal target-workspace export;
2. plugin source or package metadata;
3. marketplace documentation.

Do not infer exact provider identifiers, parameter schemas, output names, or dependency hashes from a display name.

## Knowledge bases

Dataset IDs, permissions, embedding providers, retrieval modes, rerankers, and metadata filters are workspace-specific. Public templates should use placeholders. A private generated workflow may preserve IDs only when the user provided them and authorized their use.

## HTTP APIs

Capture the contract before building the node:

- method and URL;
- authentication mechanism;
- headers, query, and body encoding;
- timeout and safe retry policy;
- response status and body schema;
- pagination or asynchronous task behavior;
- idempotency and side effects.

Never place credentials in URL query parameters or exported header literals. Prefer Dify authorization settings or Secret environment-variable references.

Separate these concepts:

- transport success: request reached the service and returned a status;
- protocol success: status and body were parseable;
- business success: response satisfies the task contract.

Branch on the correct level. A `200` response containing a failed task is not business success.

## Secrets and identifiers

Public DSL must not contain real API keys, tokens, passwords, credential IDs, webhook secrets, private dataset IDs, personal information, or internal-only URLs. Use unmistakable placeholders such as `PROVIDER_FROM_EXPORT`, `MODEL_FROM_EXPORT`, and `DATASET_ID_FROM_WORKSPACE`.

## Delivery disclosure

List every workspace-bound action remaining after import: install plugin, select model, bind credentials, choose dataset, configure contact/delivery channel, restore webhook/schedule, or confirm environment variables.

