from __future__ import annotations

import copy
import hashlib
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from package_release import build as build_release  # noqa: E402
from sanitize_example import sanitize_document  # noqa: E402
from validate_dsl import DifyValidator  # noqa: E402


def load_template(name: str):
    return yaml.safe_load((SKILL_ROOT / "assets" / "templates" / name).read_text(encoding="utf-8"))


def load_example(name: str):
    return yaml.safe_load((SKILL_ROOT / "examples" / name).read_text(encoding="utf-8"))


def codes(document):
    return {item.code for item in DifyValidator(document, target_version="0.7.0").validate()}


class ValidatorTests(unittest.TestCase):
    def test_empty_disabled_selector_is_allowed(self):
        document = load_template('workflow-minimal.yml')
        document['workflow']['graph']['nodes'][1]['data']['context'] = {
            'enabled': False,
            'variable_selector': [],
        }
        self.assertNotIn('DIFY_SELECTOR_SHAPE', codes(document))

    def test_minimal_workflow_is_strictly_valid(self):
        self.assertEqual(codes(load_template("workflow-minimal.yml")), set())

    def test_minimal_chatflow_is_strictly_valid(self):
        self.assertEqual(codes(load_template("chatflow-minimal.yml")), set())

    def test_mode_pollution_is_rejected(self):
        document = load_template("workflow-minimal.yml")
        document["app"]["mode"] = "advanced-chat"
        result = codes(document)
        self.assertIn("DIFY_CHAT_END", result)
        self.assertIn("DIFY_CHAT_ANSWER", result)

    def test_unknown_selector_source_is_rejected(self):
        document = load_template("workflow-minimal.yml")
        document["workflow"]["graph"]["nodes"][1]["data"]["variables"][0]["value_selector"] = [
            "missing_node",
            "result",
        ]
        self.assertIn("DIFY_SELECTOR_SOURCE", codes(document))

    def test_code_output_mismatch_is_rejected(self):
        document = load_template("workflow-minimal.yml")
        document["workflow"]["graph"]["nodes"][1]["data"]["outputs"] = {
            "wrong": {"type": "string", "children": None}
        }
        self.assertIn("DIFY_CODE_OUTPUTS", codes(document))

    def test_plaintext_secret_is_rejected(self):
        document = copy.deepcopy(load_template("workflow-minimal.yml"))
        document["workflow"]["environment_variables"] = [
            {"name": "PASSWORD", "password": "definitely-not-a-secret-test-value"}
        ]
        result = codes(document)
        self.assertIn("DIFY_PLAINTEXT_SECRET", result)

    def test_version_target_is_enforced(self):
        document = load_template("workflow-minimal.yml")
        diagnostics = DifyValidator(document, target_version="0.6.0").validate()
        self.assertIn("DIFY_VERSION_TARGET", {item.code for item in diagnostics})

    def test_sanitized_complex_examples_are_strictly_valid(self):
        for name in ("customer-service-chatflow.example.yml", "user-profile-workflow.example.yml"):
            document = load_example(name)
            self.assertEqual(set(), codes(document), name)
            serialized = yaml.safe_dump(document, allow_unicode=True)
            self.assertIn("REPLACE_WITH_MODEL_PROVIDER", serialized)
            self.assertNotIn("marketplace_plugin_unique_identifier", serialized)
            self.assertNotIn("木子", serialized)

    def test_sanitizer_removes_workspace_bindings(self):
        document = load_template("chatflow-minimal.yml")
        document["dependencies"] = [{"value": {"marketplace_plugin_unique_identifier": "private-binding"}}]
        document["workflow"]["features"]["opening_statement"] = "Private company greeting"
        sanitized = sanitize_document(document, "Public Example")
        self.assertEqual([], sanitized["dependencies"])
        self.assertEqual("", sanitized["workflow"]["features"]["opening_statement"])
        self.assertEqual("Public Example", sanitized["app"]["name"])

    def test_release_archive_is_deterministic_and_scoped(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.zip"
            second = Path(temporary) / "second.zip"
            build_release(first)
            build_release(second)
            self.assertEqual(hashlib.sha256(first.read_bytes()).digest(), hashlib.sha256(second.read_bytes()).digest())
            with zipfile.ZipFile(first) as archive:
                names = set(archive.namelist())
            self.assertIn("dify-workflow-dsl/SKILL.md", names)
            self.assertIn("dify-workflow-dsl/README.md", names)
            self.assertFalse(any("/__pycache__/" in name or "/dist/" in name for name in names))


if __name__ == "__main__":
    unittest.main()
