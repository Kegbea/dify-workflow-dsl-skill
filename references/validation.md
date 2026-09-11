# Validation and delivery

Run validation after every generated or modified YAML:

```bash
python scripts/validate_dsl.py --strict --target-version 0.7.0 path/to/app.yml
```

## Static validation coverage

The bundled validator checks:

- parseable YAML and required top-level mappings;
- supported graph app mode and optional target version;
- node/edge IDs and endpoint existence;
- graph reachability and unintended cycles;
- mode-specific Start, End, and Answer rules;
- edge `sourceType`/`targetType` consistency;
- IF/ELSE and Question Classifier branch handles;
- common selectors and template references;
- Code syntax and declared return keys where statically discoverable;
- likely plaintext secrets and unsafe hard-coded authorization;
- basic dependency/provider coverage warnings;
- selected container-parent references.

Warnings fail under `--strict`. A warning may be intentionally waived only when the handoff explains why and what runtime check replaces it.

## Required runtime checks

Static validation cannot prove model credentials, plugin installation, dynamic tool fields, knowledge-base permissions, remote HTTP behavior, Human Input delivery, trigger subscriptions, or UI re-save behavior.

For a serious delivery:

1. Import into the target Dify version.
2. Resolve every import warning and workspace binding.
3. Save and re-export; inspect structural changes.
4. Preview the normal path.
5. Exercise empty input, each branch, and integration failures.
6. For Chatflow, run at least two turns and a separate fresh conversation.
7. For side effects, use a sandbox endpoint and verify idempotency.

## Handoff format

Report:

- selected mode;
- target Dify and App DSL versions;
- generated file path;
- validation command and result;
- assumptions and placeholders;
- runtime scenarios still required.

Do not claim “ready for production” based only on generated YAML or static validation.

