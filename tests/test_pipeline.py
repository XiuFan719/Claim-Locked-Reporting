import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claim_locked.model import Claim  # noqa: E402
from claim_locked.pipeline import run_pipeline  # noqa: E402


class PipelineTests(unittest.TestCase):
    def test_policy_is_monotone(self):
        claim = Claim("c", "result", "text", "source",
                      allowed_strength="descriptive")
        claim.downgrade("fact", "must not strengthen")
        self.assertEqual(claim.allowed_strength, "descriptive")
        claim.downgrade("hypothesis", "post-selection")
        self.assertEqual(claim.allowed_strength, "hypothesis")

    def test_demo_writes_observable_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            outputs = run_pipeline(
                ROOT / "examples" / "evidence.json",
                ROOT / "examples" / "connective_prose.json",
                tmp,
            )
            self.assertTrue(all(path.exists() for path in outputs.values()))
            final_ledger = json.loads(
                outputs["claim_ledger.final.json"].read_text())
            claims = {c["claim_id"]: c for c in final_ledger["claims"]}
            self.assertEqual(
                claims["selected_subgroup"]["allowed_strength"],
                "hypothesis",
            )

    def test_connective_prose_cannot_add_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            prose_path = Path(tmp) / "prose.json"
            prose_path.write_text(json.dumps({"opening": "There were 99 cases."}))
            with self.assertRaises(ValueError):
                run_pipeline(ROOT / "examples" / "evidence.json",
                             prose_path, Path(tmp) / "out")


if __name__ == "__main__":
    unittest.main()
