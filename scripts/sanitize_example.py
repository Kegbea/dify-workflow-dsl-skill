#!/usr/bin/env python3
"""Create a shareable Dify example from a private workspace export.

This is a structural sanitizer, not a substitute for human review. It removes
top-level dependencies, replaces model and dataset bindings, clears environment
variable values, and rejects likely credential literals through the validator.
"""
from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

import yaml

from validate_dsl import validate_path


MODEL_PROVIDER = "REPLACE_WITH_MODEL_PROVIDER"
MODEL_NAME = "REPLACE_WITH_MODEL_NAME"
DATASET_ID = "REPLACE_WITH_DATASET_ID"


def sanitize_document(document: dict[str, Any], name: str | None = None) -> dict[str, Any]:
    result = copy.deepcopy(document)
    result["dependencies"] = []
    app = result.get("app")
    if isinstance(app, dict):
        if name:
            app["name"] = name
        app["description"] = "Sanitized reference example. Replace workspace bindings before import."

    workflow = result.get("workflow")
    if not isinstance(workflow, dict):
        return result
    features = workflow.get("features")
    if isinstance(features, dict):
        if "opening_statement" in features:
            features["opening_statement"] = ""
        if "suggested_questions" in features:
            features["suggested_questions"] = []
    environment = workflow.get("environment_variables")
    if isinstance(environment, list):
        for item in environment:
            if isinstance(item, dict) and "value" in item:
                item["value"] = ""

    graph = workflow.get("graph")
    nodes = graph.get("nodes") if isinstance(graph, dict) else None
    if not isinstance(nodes, list):
        return result
    for node in nodes:
        data = node.get("data") if isinstance(node, dict) else None
        if not isinstance(data, dict):
            continue
        node_type = data.get("type")
        if node_type in {"llm", "question-classifier", "parameter-extractor"}:
            model = data.get("model")
            if isinstance(model, dict):
                model["provider"] = MODEL_PROVIDER
                model["name"] = MODEL_NAME
        if node_type == "knowledge-retrieval":
            data["dataset_ids"] = [DATASET_ID]
            replace_model_bindings(data)
        if node_type == "tool":
            for key in ("provider_id", "provider_name", "tool_name"):
                if data.get(key):
                    data[key] = f"REPLACE_WITH_{key.upper()}"
    return result


def replace_model_bindings(value: Any, parent_key: str = "") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if isinstance(item, str) and "provider" in lowered:
                value[key] = MODEL_PROVIDER
            elif isinstance(item, str) and "model" in lowered and lowered not in {"mode", "model_mode"}:
                value[key] = MODEL_NAME
            else:
                replace_model_bindings(item, lowered)
    elif isinstance(value, list):
        for item in value:
            replace_model_bindings(item, parent_key)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--name", help="Public example app name")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    document = yaml.safe_load(args.input.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise SystemExit("input must contain one Dify App DSL mapping")
    sanitized = sanitize_document(document, args.name)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(sanitized, allow_unicode=True, sort_keys=False), encoding="utf-8")
    diagnostics, mode = validate_path(args.output, target_version="0.7.0")
    errors = [item for item in diagnostics if item.severity == "error"]
    if errors:
        for item in errors:
            location = f" path={item.path}" if item.path else ""
            print(f"{item.severity}: {item.code}: {item.message}{location}")
        return 1
    print(f"sanitized: {args.output} mode={mode} errors=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
