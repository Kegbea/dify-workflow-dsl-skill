# Security Policy

## Supported versions

Security fixes are applied to the latest released version.

## Reporting a vulnerability

Do not open a public issue for a vulnerability that could expose credentials, private data, or unsafe generated behavior. Use GitHub private vulnerability reporting when enabled, or contact the repository owner through the private address listed in the repository profile.

Include the affected version, reproduction steps, impact, and a minimal sanitized sample. Do not include active credentials or customer data.

## Scope

Relevant reports include:

- validator bypasses that allow plaintext secrets;
- unsafe path handling in bundled scripts;
- generated DSL that silently embeds credentials or private data;
- dependency or archive behavior that adds unintended files.

The validator is a static safeguard, not a sandbox. Import and run untrusted Dify DSL only in an isolated test workspace.
