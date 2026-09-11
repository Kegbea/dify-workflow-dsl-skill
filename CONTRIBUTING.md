# Contributing

Contributions that improve Dify version coverage, graph correctness, portability, documentation, or validation are welcome.

## Development setup

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p "test_*.py" -v
```

Validate every changed example or template:

```bash
python scripts/validate_dsl.py --strict --target-version 0.7.0 path/to/file.yml
```

## Pull requests

1. Keep `SKILL.md` focused on decisions every invocation needs. Put mode-specific and node-specific detail in `references/`.
2. Add or update a meaningful test for validator behavior changes.
3. Use stable ASCII node IDs matching `[A-Za-z0-9_]{1,50}`.
4. Do not add real credentials, private endpoints, customer data, workspace dataset IDs, or copied proprietary exports.
5. State the tested Dify and App DSL versions.
6. Confirm templates and examples pass strict validation.

Dynamic Dify schemas change between versions. When adding model, tool, plugin, knowledge-base, Human Input, trigger, or Agent fields, include the source Dify version and prefer a sanitized target-workspace export over an invented schema.

## Commit style

Use concise, imperative commit messages such as `Add loop container validation` or `Document Dify 1.18 changes`.
