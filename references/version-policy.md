# Version and compatibility policy

## Default baseline

For new generation, default to Dify 1.17.x and App DSL `"0.7.0"` unless the user names another target. Treat this as a maintained baseline, not a promise that every future 1.17 patch or hosted workspace uses identical dynamic plugin schemas.

Before authoring for another version:

1. Check the target workspace version.
2. Prefer a fresh minimal export from that workspace.
3. Check the tagged Dify source for the App DSL version constant, app import service, workflow node models, and frontend node defaults.
4. Preserve an existing supported DSL version during repair unless migration was requested.
5. Do not migrate by editing only the top-level `version`; node payloads, app modes, variables, Agent structures, and dependencies may also differ.

## Evidence priority

Use schema evidence in this order:

1. A minimal export from the user's target Dify workspace.
2. Tagged official Dify source matching that workspace.
3. An official example for the same tagged version.
4. A maintained fixture bundled with this skill.
5. Marketplace or provider documentation.
6. Community examples only as provisional evidence.

When exact dynamic fields remain unknown, generate a structurally valid draft with conspicuous placeholders and state what the user must reconnect after import.

## Compatibility claims

Use precise claims:

- `static validation passed`: the bundled validator accepted the file.
- `source-model validation passed`: matching Dify source models accepted the file.
- `import tested`: a matching Dify workspace imported it.
- `runtime tested`: specified smoke-test paths executed successfully.

Never collapse these into a single claim such as “production ready.”

