# Graph patterns

## Linear pipeline

Use for a single deterministic path:

```text
Start → Normalize → Process → Validate → End/Answer
```

Separate normalization and validation when downstream contracts matter.

## Conditional routing

```text
Start → Route ─┬─ Case A → A result ─┐
               ├─ Case B → B result ─┤→ Aggregator → End/Answer
               └─ Default → Fallback ┘
```

Every declared case and the default handle must have an edge. Normalize branch outputs to the same type before aggregation.

## Parallel enrichment

```text
Start ─┬→ Source A ─┐
       └→ Source B ─┴→ deterministic merge → End/Answer
```

Confirm that the target Dify execution model supports the intended convergence. Prefer an explicit merge Code node when multiple results must all be present; a Variable Aggregator is mainly for mutually exclusive branches.

## RAG

```text
Query → Knowledge Retrieval → LLM with retrieval context → End/Answer
```

Bind the retrieval result through the LLM context selector. Dataset IDs, embedding, reranking, and metadata filtering are workspace-specific.

## File processing

```text
File input → presence/cardinality check → extractor/list/iteration → normalize → analyze
```

Never send an optional empty file list into a node that requires a file. For Workflow use explicit Start file inputs; for Chatflow route `sys.files`.

## Safe external side effect

```text
Validate input → build request → HTTP/Tool → check transport → check business result → output
```

Require idempotency for retries. Keep durable retry scheduling outside Dify when requests may outlive one execution.

## Large graph assembly

Create one intermediate representation containing all IDs, selectors, outputs, branch handles, dependencies, and container parents. Generate leaf payloads from it, then assemble centrally. Validate and repair the smallest failing component rather than regenerating the whole workflow.

