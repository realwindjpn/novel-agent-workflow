import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "bus_manifest_adapter.py"
SPEC = importlib.util.spec_from_file_location("bus_manifest_adapter", SCRIPT)
adapter = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(adapter)


class BusManifestAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.card_md = self.root / "card.md"
        self.body = self.root / "body.txt"
        self.card_md.write_text("# Card\n\n## Body Extract\n" + "技术数据 " * 80, encoding="utf-8")
        self.body.write_text("芯片算力与制造约束。" * 100, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def record(self, material_id="m-1", title="芯片算力工程约束", url="https://example.test/a", **kwargs):
        return {
            "id": material_id,
            "candidate_id": "candidate-" + material_id,
            "source_run": "/old/sensenova/run-001",
            "card_md": str(self.card_md),
            "body_path": str(self.body),
            "url": url,
            "title": title,
            "body_status": "fetched",
            "verification_status": "official_verified",
            "source": "domestic",
            "platform": "official",
            "domain": "ai",
            **kwargs,
        }

    def manifest(self, *ids):
        return {"schema": "kewu_disposition_manifest_v1", "entries": [
            {"id": i, "disposition": "MIROFISH_CANDIDATE", "reason": "selected"} for i in ids
        ]}

    def test_selects_exact_twenty_manifest_ids_not_first_twenty_cards(self):
        ids = [f"m-{i}" for i in range(20)]
        entries = adapter.select_manifest_entries(self.manifest(*ids), limit=20)
        self.assertEqual(ids, [e["id"] for e in entries])
        records = [self.record(i, title=f"芯片算力工程约束-{i}", url=f"https://example.test/{i}") for i in ids]
        records.append(self.record("not-selected", title="未选卡", url="https://example.test/not-selected"))
        package = adapter.build_package(self.manifest(*ids), records, limit=20)
        self.assertEqual(ids, [x["material_id"] for x in package["accepted"]])

    def test_missing_card_is_rejected_per_card(self):
        package = adapter.build_package(self.manifest("m-1", "missing"), [self.record()], limit=20)
        rejected = {x["material_id"]: x["reasons"] for x in package["rejected"]}
        self.assertIn("missing_card", rejected["missing"])

    def test_duplicate_card_id_is_rejected(self):
        package = adapter.build_package(self.manifest("m-1"), [self.record(), self.record()], limit=20)
        self.assertEqual([], package["accepted"])
        self.assertIn("duplicate_card_id", package["rejected"][0]["reasons"])

    def test_missing_body_is_rejected(self):
        rec = self.record(body_path=str(self.root / "gone.txt"))
        package = adapter.build_package(self.manifest("m-1"), [rec], limit=20)
        self.assertIn("body_path_missing_or_empty", package["rejected"][0]["reasons"])

    def test_old_run_is_provenance_only_and_cannot_impersonate_run_dir(self):
        package = adapter.build_package(self.manifest("m-1"), [self.record()], limit=20)
        mapping = package["accepted"][0]
        self.assertEqual("/old/sensenova/run-001", mapping["source_run"])
        self.assertEqual("material_bus_manifest", package["bridge_input_mode"])
        self.assertNotIn("run_dir", mapping)
        self.assertNotIn("run_dir", package)

    def test_mapping_sha_is_stable_and_records_file_hashes(self):
        rec = self.record()
        package = adapter.build_package(self.manifest("m-1"), [rec], limit=20)
        mapping = package["accepted"][0]
        raw_sha = hashlib.sha256(adapter.canonical_json(rec).encode()).hexdigest()
        self.assertEqual(raw_sha, mapping["source_sha256"])
        self.assertEqual(hashlib.sha256(self.body.read_bytes()).hexdigest(), mapping["body_sha256"])
        self.assertEqual(hashlib.sha256(self.card_md.read_bytes()).hexdigest(), mapping["card_sha256"])

    def test_embedded_json_title_is_unwrapped_for_bridge_decision(self):
        rec = self.record(title='{"url":"https://example.test/a","title":"Embedded source title"}')
        package = adapter.build_package(self.manifest("m-1"), [rec], limit=20)
        self.assertEqual("Embedded source title", package["decision_cards"][0]["title"])

    def test_truncated_embedded_json_title_is_unwrapped_for_bridge_decision(self):
        rec = self.record(title='{"url":"https://example.test/a","title":"Truncated source title"')
        package = adapter.build_package(self.manifest("m-1"), [rec], limit=20)
        self.assertEqual("Truncated source title", package["decision_cards"][0]["title"])

    def test_escaped_embedded_json_title_is_unwrapped_for_bridge_decision(self):
        rec = self.record(title=r'{\"url\":\"https://example.test/a\",\"title\":\"Escaped envelope title\"')
        package = adapter.build_package(self.manifest("m-1"), [rec], limit=20)
        self.assertEqual("Escaped envelope title", package["decision_cards"][0]["title"])

    def test_manifest_material_id_alias_is_selected(self):
        manifest = {"schema": "kewu_disposition_manifest_v1", "entries": [
            {"material_id": "m-1", "disposition": "MIROFISH_CANDIDATE", "reason": "selected"}
        ]}
        package = adapter.build_package(manifest, [self.record()], limit=20)
        self.assertEqual(["m-1"], [x["material_id"] for x in package["accepted"]])

    def test_invalid_body_status_is_rejected_per_card(self):
        package = adapter.build_package(
            self.manifest("m-1"), [self.record(body_status="pending")], limit=20
        )
        self.assertIn("body_status_not_fetched", package["rejected"][0]["reasons"])

    def test_write_outputs_only_creates_dry_run_artifacts(self):
        package = adapter.build_package(self.manifest("m-1"), [self.record()], limit=20)
        out = self.root / "out"
        adapter.write_outputs(package, out)
        self.assertTrue((out / "adapter_package.json").is_file())
        self.assertTrue((out / "decision_cards.json").is_file())
        self.assertTrue((out / "card_conversion_tasks.json").is_file())
        written = json.loads((out / "adapter_package.json").read_text())
        self.assertTrue(written["dry_run"])
        self.assertFalse(written["formal_cards_written"])
        self.assertFalse(written["production_files_modified"])

    def test_duplicate_signature_rejects_second_mapping(self):
        first = self.record("m-1", title="同一事件", url="https://example.test/same")
        second = self.record("m-2", title="同一事件", url="https://example.test/same")
        package = adapter.build_package(self.manifest("m-1", "m-2"), [first, second], limit=20)
        self.assertEqual(["m-1"], [x["material_id"] for x in package["accepted"]])
        self.assertIn("duplicate_signature", package["rejected"][0]["reasons"])


if __name__ == "__main__":
    unittest.main()
