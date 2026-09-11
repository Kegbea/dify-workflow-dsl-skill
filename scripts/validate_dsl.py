#!/usr/bin/env python3
"""Deterministic static checks for generated Dify Workflow/Chatflow DSL."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment failure
    raise SystemExit("PyYAML is required: python -m pip install -r requirements.txt") from exc


NODE_ID_RE = re.compile(r"^[A-Za-z0-9_]{1,50}$")
TEMPLATE_RE = re.compile(r"\{\{#([^#]+)#\}\}")
BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+\-/=]{12,}", re.IGNORECASE)
API_KEY_RE = re.compile(r"\b(?:sk|rk|pk)-[A-Za-z0-9_-]{12,}\b")
SECRET_KEYS = {
    "api_key",
    "apikey",
    "password",
    "passwd",
    "secret",
    "secret_key",
    "token",
    "access_token",
    "refresh_token",
    "credential_id",
    "webhook_secret",
}
SELECTOR_KEYS = {
    "value_selector",
    "variable_selector",
    "query_variable_selector",
    "iterator_selector",
    "output_selector",
}
BUILTIN_SOURCES = {"sys", "env", "conversation"}
TRIGGER_TYPES = {"trigger-schedule", "trigger-webhook", "trigger-plugin"}
PLACEHOLDER_MARKERS = {
    "placeholder",
    "from_export",
    "from_workspace",
    "replace_me",
    "replace_with",
    "your_",
    "example",
}


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    code: str
    message: str
    path: str = ""


class DifyValidator:
    def __init__(self, document: Any, target_version: str | None = None):
        self.document = document
        self.target_version = target_version
        self.diagnostics: list[Diagnostic] = []
        self.node_map: dict[str, dict[str, Any]] = {}
        self.edges: list[dict[str, Any]] = []
        self.outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.adjacency: dict[str, list[str]] = defaultdict(list)
        self.mode = ""

    def error(self, code: str, message: str, path: str = "") -> None:
        self.diagnostics.append(Diagnostic("error", code, message, path))

    def warning(self, code: str, message: str, path: str = "") -> None:
        self.diagnostics.append(Diagnostic("warning", code, message, path))

    def validate(self) -> list[Diagnostic]:
        if not isinstance(self.document, dict):
            self.error("DIFY_ROOT_TYPE", "Root YAML value must be a mapping.")
            return self.diagnostics

        self._validate_top_level()
        workflow = self.document.get("workflow")
        graph = workflow.get("graph") if isinstance(workflow, dict) else None
        if not isinstance(workflow, dict):
            self.error("DIFY_WORKFLOW_REQUIRED", "Graph app requires a workflow mapping.", "workflow")
            return self.diagnostics
        if not isinstance(graph, dict):
            self.error("DIFY_GRAPH_REQUIRED", "workflow.graph must be a mapping.", "workflow.graph")
            return self.diagnostics

        nodes = graph.get("nodes")
        edges = graph.get("edges")
        if not isinstance(nodes, list) or not nodes:
            self.error("DIFY_NODES_REQUIRED", "workflow.graph.nodes must be a non-empty list.", "workflow.graph.nodes")
            return self.diagnostics
        if not isinstance(edges, list):
            self.error("DIFY_EDGES_REQUIRED", "workflow.graph.edges must be a list.", "workflow.graph.edges")
            edges = []

        self._index_nodes(nodes)
        self._index_edges(edges)
        self._validate_mode(workflow)
        self._validate_edges()
        self._validate_reachability()
        self._validate_terminals()
        self._validate_branches()
        self._validate_selectors_and_templates()
        self._validate_code_nodes()
        self._validate_containers()
        self._validate_dependencies()
        self._validate_secrets(self.document)
        return self.diagnostics

    def _validate_top_level(self) -> None:
        if self.document.get("kind") != "app":
            self.error("DIFY_KIND", "kind must be 'app'.", "kind")

        version = self.document.get("version")
        if not isinstance(version, str) or not version:
            self.error("DIFY_VERSION_TYPE", "version must be a quoted, non-empty string.", "version")
        elif self.target_version and version != self.target_version:
            self.error(
                "DIFY_VERSION_TARGET",
                f"DSL version {version!r} does not match requested target {self.target_version!r}.",
                "version",
            )

        app = self.document.get("app")
        if not isinstance(app, dict):
            self.error("DIFY_APP_REQUIRED", "app must be a mapping.", "app")
            return
        self.mode = str(app.get("mode") or "")
        if self.mode not in {"workflow", "advanced-chat"}:
            self.error(
                "DIFY_MODE_UNSUPPORTED",
                "This skill validates app.mode 'workflow' or 'advanced-chat'.",
                "app.mode",
            )
        if not str(app.get("name") or "").strip():
            self.error("DIFY_APP_NAME", "app.name must be non-empty.", "app.name")
        dependencies = self.document.get("dependencies")
        if not isinstance(dependencies, list):
            self.error("DIFY_DEPENDENCIES_TYPE", "dependencies must be a list.", "dependencies")

    def _index_nodes(self, nodes: list[Any]) -> None:
        for index, node in enumerate(nodes):
            path = f"workflow.graph.nodes[{index}]"
            if not isinstance(node, dict):
                self.error("DIFY_NODE_TYPE", "Node must be a mapping.", path)
                continue
            node_id = node.get("id")
            if not isinstance(node_id, str) or not node_id:
                self.error("DIFY_NODE_ID", "Every node must have a non-empty string ID.", f"{path}.id")
                continue
            if not NODE_ID_RE.fullmatch(node_id):
                self.error(
                    "DIFY_NODE_ID_FORMAT",
                    "Generated node ID must match [A-Za-z0-9_]{1,50}.",
                    f"{path}.id",
                )
            if node_id in self.node_map:
                self.error("DIFY_NODE_ID_DUPLICATE", f"Duplicate node ID {node_id!r}.", f"{path}.id")
                continue
            data = node.get("data")
            if not isinstance(data, dict):
                self.error("DIFY_NODE_DATA", f"Node {node_id!r} has no data mapping.", f"{path}.data")
                continue
            if node.get("type") != "custom" and node.get("type") != "custom-note":
                self.warning(
                    "DIFY_NODE_WRAPPER_TYPE",
                    f"Node {node_id!r} normally uses wrapper type 'custom'.",
                    f"{path}.type",
                )
            if node.get("type") != "custom-note" and not str(data.get("type") or ""):
                self.error("DIFY_NODE_RUNTIME_TYPE", f"Node {node_id!r} has no data.type.", f"{path}.data.type")
            self.node_map[node_id] = node

    def _index_edges(self, edges: list[Any]) -> None:
        seen_ids: set[str] = set()
        for index, edge in enumerate(edges):
            path = f"workflow.graph.edges[{index}]"
            if not isinstance(edge, dict):
                self.error("DIFY_EDGE_TYPE", "Edge must be a mapping.", path)
                continue
            edge_id = edge.get("id")
            if not isinstance(edge_id, str) or not edge_id:
                self.error("DIFY_EDGE_ID", "Every edge must have a non-empty string ID.", f"{path}.id")
            elif edge_id in seen_ids:
                self.error("DIFY_EDGE_ID_DUPLICATE", f"Duplicate edge ID {edge_id!r}.", f"{path}.id")
            else:
                seen_ids.add(edge_id)
            self.edges.append(edge)
            source = edge.get("source")
            target = edge.get("target")
            if isinstance(source, str):
                self.outgoing[source].append(edge)
                if isinstance(target, str):
                    self.adjacency[source].append(target)

    def _node_type(self, node_id: str) -> str:
        node = self.node_map.get(node_id) or {}
        data = node.get("data") or {}
        return str(data.get("type") or "")

    def _validate_mode(self, workflow: dict[str, Any]) -> None:
        types = [self._node_type(node_id) for node_id in self.node_map]
        starts = types.count("start")
        triggers = sum(node_type in TRIGGER_TYPES for node_type in types)
        if self.mode == "advanced-chat":
            if starts != 1:
                self.error("DIFY_CHAT_START", "advanced-chat requires exactly one Start node.")
            if triggers:
                self.error("DIFY_CHAT_TRIGGER", "advanced-chat must not use Workflow trigger entry nodes.")
            if "end" in types:
                self.error("DIFY_CHAT_END", "advanced-chat response paths must use Answer, not End.")
            if "answer" not in types:
                self.error("DIFY_CHAT_ANSWER", "advanced-chat requires at least one Answer node.")
            start_nodes = [node for node in self.node_map.values() if (node.get("data") or {}).get("type") == "start"]
            if start_nodes and (start_nodes[0].get("data") or {}).get("variables") not in ([], None):
                self.warning(
                    "DIFY_CHAT_START_VARIABLES",
                    "Pure Chatflow normally uses an empty Start variables list; verify this input form against a target export.",
                )
        elif self.mode == "workflow":
            if starts + triggers < 1:
                self.error("DIFY_WORKFLOW_ENTRY", "workflow requires a Start or supported trigger entry node.")
            if starts > 1:
                self.error("DIFY_WORKFLOW_START_COUNT", "workflow must not contain multiple Start nodes.")
            if "answer" in types:
                self.error("DIFY_WORKFLOW_ANSWER", "workflow must use End outputs, not Answer nodes.")
            conversation_variables = workflow.get("conversation_variables")
            if isinstance(conversation_variables, list) and conversation_variables:
                self.error(
                    "DIFY_WORKFLOW_CONVERSATION_STATE",
                    "workflow must not rely on Chatflow conversation variables.",
                    "workflow.conversation_variables",
                )

    def _validate_edges(self) -> None:
        for index, edge in enumerate(self.edges):
            path = f"workflow.graph.edges[{index}]"
            source = edge.get("source")
            target = edge.get("target")
            if source not in self.node_map:
                self.error("DIFY_EDGE_SOURCE", f"Unknown edge source {source!r}.", f"{path}.source")
            if target not in self.node_map:
                self.error("DIFY_EDGE_TARGET", f"Unknown edge target {target!r}.", f"{path}.target")
            if not isinstance(edge.get("sourceHandle"), str) or not edge.get("sourceHandle"):
                self.error("DIFY_EDGE_SOURCE_HANDLE", "Edge sourceHandle must be non-empty.", f"{path}.sourceHandle")
            if not isinstance(edge.get("targetHandle"), str) or not edge.get("targetHandle"):
                self.error("DIFY_EDGE_TARGET_HANDLE", "Edge targetHandle must be non-empty.", f"{path}.targetHandle")
            data = edge.get("data")
            if not isinstance(data, dict):
                self.error("DIFY_EDGE_DATA", "Edge data must be a mapping.", f"{path}.data")
                continue
            if source in self.node_map and data.get("sourceType") != self._node_type(str(source)):
                self.error(
                    "DIFY_EDGE_SOURCE_TYPE",
                    f"sourceType must match node {source!r} data.type {self._node_type(str(source))!r}.",
                    f"{path}.data.sourceType",
                )
            if target in self.node_map and data.get("targetType") != self._node_type(str(target)):
                self.error(
                    "DIFY_EDGE_TARGET_TYPE",
                    f"targetType must match node {target!r} data.type {self._node_type(str(target))!r}.",
                    f"{path}.data.targetType",
                )

    def _entry_ids(self) -> list[str]:
        return [
            node_id
            for node_id in self.node_map
            if self._node_type(node_id) == "start" or self._node_type(node_id) in TRIGGER_TYPES
        ]

    def _validate_reachability(self) -> None:
        queue = deque(self._entry_ids())
        reachable: set[str] = set()
        while queue:
            current = queue.popleft()
            if current in reachable or current not in self.node_map:
                continue
            reachable.add(current)
            queue.extend(self.adjacency.get(current, []))
        for node_id in sorted(set(self.node_map) - reachable):
            if self.node_map[node_id].get("type") != "custom-note":
                self.error("DIFY_NODE_UNREACHABLE", f"Node {node_id!r} is unreachable from an entry.")

        if not any(self._node_type(node_id) in {"loop", "loop-start", "loop-end"} for node_id in self.node_map):
            self._validate_cycles()

    def _validate_cycles(self) -> None:
        state: dict[str, int] = {}

        def visit(node_id: str) -> bool:
            state[node_id] = 1
            for target in self.adjacency.get(node_id, []):
                if target not in self.node_map:
                    continue
                if state.get(target) == 1:
                    return True
                if state.get(target, 0) == 0 and visit(target):
                    return True
            state[node_id] = 2
            return False

        for node_id in self.node_map:
            if state.get(node_id, 0) == 0 and visit(node_id):
                self.error("DIFY_GRAPH_CYCLE", "Graph contains a cycle outside an explicit Loop structure.")
                break

    def _validate_terminals(self) -> None:
        sinks = [node_id for node_id in self.node_map if not self.outgoing.get(node_id)]
        expected = "end" if self.mode == "workflow" else "answer"
        triggers_present = any(self._node_type(node_id) in TRIGGER_TYPES for node_id in self.node_map)
        for node_id in sinks:
            if self.node_map[node_id].get("type") == "custom-note":
                continue
            node_type = self._node_type(node_id)
            if node_type != expected:
                if self.mode == "workflow" and triggers_present:
                    self.warning(
                        "DIFY_TRIGGER_SIDE_EFFECT_SINK",
                        f"Triggered Workflow sink {node_id!r} is {node_type!r}, not End; verify intentional side-effect-only behavior.",
                    )
                else:
                    self.error(
                        "DIFY_TERMINAL_TYPE",
                        f"Terminal node {node_id!r} must be {expected!r} for mode {self.mode!r}.",
                    )

    def _validate_branches(self) -> None:
        for node_id, node in self.node_map.items():
            data = node.get("data") or {}
            node_type = data.get("type")
            actual = {str(edge.get("sourceHandle")) for edge in self.outgoing.get(node_id, [])}
            if node_type == "if-else":
                cases = data.get("cases")
                if not isinstance(cases, list) or not cases:
                    self.error("DIFY_IF_CASES", f"IF/ELSE node {node_id!r} requires cases.")
                    continue
                case_ids: list[str] = []
                for index, case in enumerate(cases):
                    if not isinstance(case, dict):
                        self.error("DIFY_IF_CASE_TYPE", f"IF/ELSE node {node_id!r} case {index} must be a mapping.")
                        continue
                    case_id = case.get("case_id")
                    if not isinstance(case_id, str) or not case_id:
                        self.error("DIFY_IF_CASE_ID", f"IF/ELSE node {node_id!r} case {index} lacks case_id.")
                        continue
                    if case.get("id") != case_id:
                        self.error("DIFY_IF_CASE_MATCH", f"IF/ELSE node {node_id!r} case id must equal case_id {case_id!r}.")
                    case_ids.append(case_id)
                    conditions = case.get("conditions")
                    if not isinstance(conditions, list) or not conditions:
                        self.error("DIFY_IF_CONDITIONS", f"IF/ELSE node {node_id!r} case {case_id!r} needs conditions.")
                required = set(case_ids) | {"false"}
                if actual != required:
                    self.error(
                        "DIFY_IF_HANDLES",
                        f"IF/ELSE node {node_id!r} handles mismatch; missing={sorted(required - actual)}, extra={sorted(actual - required)}.",
                    )
            elif node_type == "question-classifier":
                classes = data.get("classes")
                if not isinstance(classes, list) or not classes:
                    self.error("DIFY_CLASSIFIER_CLASSES", f"Question Classifier {node_id!r} requires classes.")
                    continue
                required = {
                    str(item.get("id"))
                    for item in classes
                    if isinstance(item, dict) and item.get("id") is not None
                }
                if actual != required:
                    self.error(
                        "DIFY_CLASSIFIER_HANDLES",
                        f"Question Classifier {node_id!r} handles mismatch; missing={sorted(required - actual)}, extra={sorted(actual - required)}.",
                    )

    def _known_outputs(self, node_id: str) -> set[str]:
        data = (self.node_map.get(node_id) or {}).get("data") or {}
        node_type = data.get("type")
        outputs: set[str] = set()
        raw_outputs = data.get("outputs")
        if isinstance(raw_outputs, dict):
            outputs.update(str(key) for key in raw_outputs)
        elif isinstance(raw_outputs, list):
            outputs.update(
                str(item.get("variable"))
                for item in raw_outputs
                if isinstance(item, dict) and item.get("variable")
            )
        if node_type == "start":
            outputs.update(
                str(item.get("variable"))
                for item in data.get("variables") or []
                if isinstance(item, dict) and item.get("variable")
            )
        outputs.update(
            {
                "llm": {"text", "files", "json"},
                "template-transform": {"output"},
                "variable-aggregator": {"output"},
                "document-extractor": {"text"},
                "http-request": {"body", "status_code", "headers", "files"},
                "knowledge-retrieval": {"result"},
            }.get(str(node_type), set())
        )
        if node_type == "parameter-extractor":
            outputs.update(
                str(item.get("name"))
                for item in data.get("parameters") or []
                if isinstance(item, dict) and item.get("name")
            )
        return outputs

    def _iter_selectors(self, value: Any, path: str = "") -> Iterable[tuple[str, list[Any]]]:
        if isinstance(value, dict):
            for key, item in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                if key in SELECTOR_KEYS and isinstance(item, list):
                    yield child_path, item
                elif key in {"query", "variable"} and isinstance(item, list) and len(item) >= 2:
                    yield child_path, item
                yield from self._iter_selectors(item, child_path)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                yield from self._iter_selectors(item, f"{path}[{index}]")

    def _validate_reference(self, source: Any, output: Any, path: str) -> None:
        if not isinstance(source, str) or not isinstance(output, str):
            self.error("DIFY_SELECTOR_TYPE", "Selector source and output must be strings.", path)
            return
        if source in BUILTIN_SOURCES:
            if self.mode == "workflow" and source in {"sys", "conversation"}:
                self.error(
                    "DIFY_WORKFLOW_CHAT_SELECTOR",
                    f"Workflow must not depend on Chatflow selector {source}.{output}.",
                    path,
                )
            return
        if source not in self.node_map:
            self.error("DIFY_SELECTOR_SOURCE", f"Selector references unknown node {source!r}.", path)
            return
        known = self._known_outputs(source)
        first_output = output.split(".", 1)[0]
        if known and first_output not in known:
            self.error("DIFY_SELECTOR_OUTPUT", f"Selector references unknown output {source}.{output}.", path)

    def _validate_selectors_and_templates(self) -> None:
        for path, selector in self._iter_selectors(self.document):
            if not selector:
                continue
            if len(selector) < 2:
                self.error("DIFY_SELECTOR_SHAPE", "Selector must contain at least source and output.", path)
                continue
            self._validate_reference(selector[0], selector[1], path)

        for path, text in _iter_strings(self.document):
            for match in TEMPLATE_RE.finditer(text):
                content = match.group(1)
                if "." not in content:
                    self.error("DIFY_TEMPLATE_SHAPE", f"Malformed template reference {match.group(0)!r}.", path)
                    continue
                source, output = content.split(".", 1)
                if source not in BUILTIN_SOURCES and not NODE_ID_RE.fullmatch(source):
                    self.error("DIFY_TEMPLATE_NODE_ID", f"Template node ID {source!r} is not runtime-safe.", path)
                self._validate_reference(source, output, path)
            if "{{#" in text and "#}}" not in text:
                self.error("DIFY_TEMPLATE_UNCLOSED", "Unclosed Dify template reference.", path)

    def _validate_code_nodes(self) -> None:
        for node_id, node in self.node_map.items():
            data = node.get("data") or {}
            if data.get("type") != "code":
                continue
            code = data.get("code")
            language = str(data.get("code_language") or "")
            if not isinstance(code, str) or not code.strip():
                self.error("DIFY_CODE_MISSING", f"Code node {node_id!r} has no code.")
                continue
            if language != "python3":
                self.warning("DIFY_CODE_LANGUAGE", f"Code node {node_id!r} language {language!r} is not statically compiled by this validator.")
                continue
            try:
                tree = ast.parse(code, filename=f"<{node_id}>")
                compile(tree, f"<{node_id}>", "exec")
            except SyntaxError as exc:
                self.error("DIFY_CODE_SYNTAX", f"Code node {node_id!r} does not compile: {exc.msg} at line {exc.lineno}.")
                continue
            mains = [item for item in tree.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "main"]
            if len(mains) != 1:
                self.error("DIFY_CODE_MAIN", f"Code node {node_id!r} must define exactly one main function.")
                continue
            main = mains[0]
            args = {arg.arg for arg in main.args.args}
            variables = data.get("variables") or []
            bound = {
                str(item.get("variable"))
                for item in variables
                if isinstance(item, dict) and item.get("variable")
            }
            if args != bound:
                self.error(
                    "DIFY_CODE_INPUTS",
                    f"Code node {node_id!r} main args {sorted(args)} do not match variables {sorted(bound)}.",
                )
            declared = set((data.get("outputs") or {}).keys()) if isinstance(data.get("outputs"), dict) else set()
            literal_keys: set[str] = set()
            for returned in [item for item in ast.walk(main) if isinstance(item, ast.Return)]:
                if isinstance(returned.value, ast.Dict):
                    for key in returned.value.keys:
                        if isinstance(key, ast.Constant) and isinstance(key.value, str):
                            literal_keys.add(key.value)
            if literal_keys and literal_keys != declared:
                self.error(
                    "DIFY_CODE_OUTPUTS",
                    f"Code node {node_id!r} literal return keys {sorted(literal_keys)} do not match outputs {sorted(declared)}.",
                )

    def _validate_containers(self) -> None:
        for node_id, node in self.node_map.items():
            data = node.get("data") or {}
            for field, expected in (("iteration_id", "iteration"), ("loop_id", "loop")):
                parent = data.get(field) or node.get(field)
                if parent is None:
                    continue
                if parent not in self.node_map:
                    self.error("DIFY_CONTAINER_PARENT", f"Node {node_id!r} references unknown {field} {parent!r}.")
                elif self._node_type(str(parent)) != expected:
                    self.error(
                        "DIFY_CONTAINER_PARENT_TYPE",
                        f"Node {node_id!r} {field} must reference a {expected!r} node.",
                    )

    def _validate_dependencies(self) -> None:
        dependencies = self.document.get("dependencies")
        if not isinstance(dependencies, list):
            return
        serialized = json.dumps(dependencies, ensure_ascii=False).lower()
        for node_id, node in self.node_map.items():
            data = node.get("data") or {}
            candidates: list[str] = []
            if data.get("type") in {"llm", "question-classifier", "parameter-extractor"}:
                model = data.get("model")
                if isinstance(model, dict) and isinstance(model.get("provider"), str):
                    candidates.append(model["provider"])
            if data.get("type") == "tool" and isinstance(data.get("provider_id"), str):
                candidates.append(data["provider_id"])
            for provider in candidates:
                lowered = provider.lower()
                if _is_placeholder(provider):
                    continue
                parts = lowered.split("/")
                identity = "/".join(parts[:2]) if len(parts) >= 2 else lowered
                if identity and identity not in serialized:
                    self.warning(
                        "DIFY_DEPENDENCY_MISSING",
                        f"Node {node_id!r} provider {provider!r} has no obvious matching top-level dependency.",
                    )

    def _validate_secrets(self, value: Any, path: str = "") -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                normalized = str(key).strip().lower().replace("-", "_")
                if normalized in SECRET_KEYS and isinstance(item, str) and item.strip():
                    if not _is_safe_secret_placeholder(item):
                        self.error("DIFY_PLAINTEXT_SECRET", f"Possible plaintext secret in {child_path!r}.", child_path)
                self._validate_secrets(item, child_path)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                self._validate_secrets(item, f"{path}[{index}]")
        elif isinstance(value, str):
            if API_KEY_RE.search(value):
                self.error("DIFY_API_KEY_LITERAL", "Possible API key literal found.", path)
            if BEARER_RE.search(value) and "{{#env." not in value:
                self.error("DIFY_BEARER_LITERAL", "Hard-coded Bearer credential found.", path)


def _iter_strings(value: Any, path: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield from _iter_strings(item, child_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _iter_strings(item, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


def _is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in PLACEHOLDER_MARKERS)


def _is_safe_secret_placeholder(value: str) -> bool:
    stripped = value.strip()
    return (
        not stripped
        or "{{#env." in stripped
        or _is_placeholder(stripped)
        or stripped.startswith("${")
        or stripped.startswith("<") and stripped.endswith(">")
    )


def validate_path(path: Path, target_version: str | None = None) -> tuple[list[Diagnostic], str | None]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return [Diagnostic("error", "DIFY_FILE_READ", str(exc), str(path))], None
    except yaml.YAMLError as exc:
        return [Diagnostic("error", "DIFY_YAML_PARSE", str(exc), str(path))], None
    diagnostics = DifyValidator(document, target_version=target_version).validate()
    mode = None
    if isinstance(document, dict) and isinstance(document.get("app"), dict):
        mode = document["app"].get("mode")
    return diagnostics, mode


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Dify Workflow and Chatflow App DSL YAML.")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--target-version", help="Require this exact quoted App DSL version, for example 0.7.0.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as validation failure.")
    parser.add_argument("--format", choices=("human", "json"), default="human")
    args = parser.parse_args()

    reports: list[dict[str, Any]] = []
    failed = False
    for path in args.files:
        diagnostics, mode = validate_path(path, target_version=args.target_version)
        errors = sum(item.severity == "error" for item in diagnostics)
        warnings = sum(item.severity == "warning" for item in diagnostics)
        file_failed = errors > 0 or (args.strict and warnings > 0)
        failed = failed or file_failed
        reports.append(
            {
                "file": str(path),
                "mode": mode,
                "valid": not file_failed,
                "errors": errors,
                "warnings": warnings,
                "diagnostics": [asdict(item) for item in diagnostics],
            }
        )

    if args.format == "json":
        print(json.dumps(reports, ensure_ascii=False, indent=2))
    else:
        for report in reports:
            status = "valid" if report["valid"] else "invalid"
            print(
                f"{status}: {report['file']} mode={report['mode']} "
                f"errors={report['errors']} warnings={report['warnings']}"
            )
            for item in report["diagnostics"]:
                location = f" [{item['path']}]" if item["path"] else ""
                print(f"  {item['severity'].upper()} {item['code']}{location}: {item['message']}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
