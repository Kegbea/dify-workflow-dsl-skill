# Dify Workflow DSL Skill

[![CI](https://github.com/Kegbea/dify-workflow-dsl-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/Kegbea/dify-workflow-dsl-skill/actions/workflows/ci.yml)

[简体中文](README.zh-CN.md)

A portable Agent Skill for creating, modifying, repairing, reviewing, and validating Dify `workflow` and `advanced-chat` App DSL YAML from natural-language requirements.

## Capabilities

- Selects stateless Workflow or multi-turn Chatflow from the requested behavior.
- Plans node inputs, outputs, branches, failure paths, and dependencies before emitting YAML.
- Uses version-aware, mode-specific, and node-specific references.
- Validates graph structure, selectors, branch handles, Code nodes, dependencies, and likely secrets.
- Includes portable minimal templates and sanitized complex examples for both modes.

## Compatibility

| Component | Baseline |
|---|---|
| Skill | `0.1.0` |
| Dify | `1.17.x` |
| App DSL | `0.7.0` |
| Python | `3.9+` |
| Runtime dependency | `PyYAML 6.x` |

The bundled baseline is a generation target, not a promise that every dynamic node is portable. Model providers, marketplace plugins, tools, knowledge bases, Human Input, triggers, and Agent nodes can contain workspace-specific fields. A recent export from the target Dify workspace remains authoritative.

## Install

Clone the repository and copy or link the complete directory into the skills directory supported by your agent. For Codex, the personal location is normally:

```bash
git clone https://github.com/Kegbea/dify-workflow-dsl-skill.git
cp -R dify-workflow-dsl-skill ~/.codex/skills/dify-workflow-dsl
```

On Windows PowerShell:

```powershell
git clone https://github.com/Kegbea/dify-workflow-dsl-skill.git
Copy-Item -Recurse -Force dify-workflow-dsl-skill "$HOME/.codex/skills/dify-workflow-dsl"
```

Keep the directory intact: `SKILL.md` relies on the bundled `references/`, `assets/`, and `scripts/` files. Restart or reload the agent so it can discover the Skill.

Other coding agents can use the Skill when they support `SKILL.md`-style skills and can read local files and execute Python. Otherwise, explicitly ask the agent to read `SKILL.md`; automatic discovery is agent-specific.

## Use

```text
Use $dify-workflow-dsl to create a Dify workflow that accepts an order ID,
queries an HTTP API, classifies the order risk, and returns strict JSON.
```

```text
Use $dify-workflow-dsl to create a multi-turn customer-service Chatflow with
conversation memory, knowledge retrieval, file uploads, and fallback answers.
```

Agents that support implicit Skill selection may activate it automatically when the request clearly asks for Dify Workflow or Chatflow DSL.

## Examples

See [`examples/`](examples/README.md) for complex, sanitized Workflow and Chatflow exports. Values beginning with `REPLACE_WITH_` are deliberate workspace-binding placeholders and must be replaced before import.

## Validate

```bash
python -m pip install -r requirements.txt
python scripts/validate_dsl.py --strict --target-version 0.7.0 path/to/app.yml
python -m unittest discover -s tests -p "test_*.py" -v
```

Static validation does not replace Dify import, preview, and channel smoke tests.

## Release package

```bash
python scripts/package_release.py
```

The archive is written to `dist/` and contains a top-level `dify-workflow-dsl/` directory. Generated archives are intentionally ignored by Git.

## Scope and limitations

This Skill improves generation consistency and catches many static defects. It cannot guarantee that an arbitrarily complex graph will run in every Dify workspace. Runtime success still depends on installed plugins, credentials, model capabilities, dataset bindings, external APIs, Dify version behavior, and representative smoke tests.

Never publish real API keys, tokens, private endpoints, customer data, or private dataset identifiers in an example. Use environment variables or explicit placeholders.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow and [SECURITY.md](SECURITY.md) for private vulnerability reporting guidance. Changes are recorded in [CHANGELOG.md](CHANGELOG.md).

## License

MIT. See [LICENSE](LICENSE). See [ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md) for project acknowledgements.
