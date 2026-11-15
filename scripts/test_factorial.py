"""Focused integration tests for the optional runner; no full-data training.

The only training test uses 16 synthetic edges, two epochs, and temporary
outputs. It verifies that resuming an epoch checkpoint preserves the result.
"""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import torch

import factorial
import train


def record(cell, seed, value=20.0):
    groups = {"all": {"n": 20, "positive": 4, "f1": value},
              "first": {"n": 10, "positive": 3, "f1": value},
              "repeat": {"n": 10, "positive": 1, "f1": value},
              "repeat_free": {"n": 3, "positive": 1, "f1": value}}
    return dict(**factorial.expected_metadata(cell, seed), selected_epoch=1,
                val_f1=.2, ap=25., groups=groups)


def tiny_graph():
    pairs = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (0, 2), (2, 4),
             (1, 3), (3, 5), (5, 1), (0, 1), (6, 7), (2, 3), (1, 4), (0, 2)]
    seen, first = set(), []
    for pair in pairs:
        first.append(pair not in seen)
        seen.add(pair)
    index = torch.arange(len(pairs), dtype=torch.float64)
    return dict(edge_index=torch.tensor(pairs).T, n_nodes=8,
                y=torch.tensor([0, 1] * 8), split=torch.tensor([0] * 8 + [1] * 4 + [2] * 4),
                first_contact=torch.tensor(first),
                base=torch.stack((index, index % 7 + 1, index % 2, index % 3), dim=1))


class OptionalRunnerTests(unittest.TestCase):
    def setUp(self):
        fingerprints = patch.object(factorial, "INPUT_FINGERPRINTS",
                                    {"graph_sha256": "a" * 64,
                                     "model_sha256": factorial.PINNED_MODEL_SHA256})
        fingerprints.start()
        self.addCleanup(fingerprints.stop)

    def test_sampled_seed_order_with_missing_edges(self):
        loader = SimpleNamespace(course_seed_ids=torch.tensor([2, 5, 7]),
                                 data=SimpleNamespace(edge_attr=torch.arange(8)[:, None].float()))

        def batch(edge_ids):
            edge_ids = torch.tensor(edge_ids, dtype=torch.long)
            return SimpleNamespace(input_id=torch.tensor([2, 0, 1]), e_id=edge_ids,
                edge_index=torch.zeros(2, len(edge_ids), dtype=torch.long),
                edge_attr=loader.data.edge_attr[edge_ids], x=torch.zeros(2, 1),
                edge_label_index=torch.tensor([[0, 1, 0], [1, 0, 1]]),
                edge_label=torch.tensor([1, 0, 1]))

        def echo_edge_ids(x, edge_index, edge_attr):
            return torch.cat((edge_attr, -edge_attr), dim=1)

        logits, labels = factorial.sampled_logits(echo_edge_ids, loader, batch([2, 7]), False)
        self.assertEqual(logits[:, 0].tolist(), [7, 2])
        self.assertEqual(labels.tolist(), [1, 0])
        for present in ([2, 7], []):
            current = batch(present)
            logits, labels = factorial.sampled_logits(echo_edge_ids, loader, current, True)
            self.assertEqual(logits[:, 0].tolist(), [7, 2, 5])
            self.assertEqual(labels.tolist(), [1, 0, 1])
            self.assertEqual(current.edge_attr.size(0), 3)

    def test_as_of_subset_does_not_reclassify_earlier_edges(self):
        graph = dict(edge_index=torch.tensor([[0, 2, 0, 0], [1, 3, 1, 2]]), n_nodes=4,
                     first_contact=torch.tensor([True, True, False, True]),
                     split=torch.tensor([2, 2, 2, 2]))
        groups = factorial.groups(graph)
        self.assertEqual(groups["repeat_free"].tolist(), [True, True, False, False])
        self.assertEqual(groups["repeat"].tolist(), [False, False, True, False])

    def test_missing_report_is_explicit_and_does_not_train(self):
        with TemporaryDirectory() as directory, patch.object(factorial, "RESULTS", Path(directory)):
            with self.assertRaisesRegex(ValueError, "0/20.*src/analyze.py"):
                factorial.report()
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_existing_result_metadata_is_checked_before_skipping(self):
        with TemporaryDirectory() as directory, patch.object(factorial, "RESULTS", Path(directory)):
            path = Path(directory) / "base_s0.json"
            for key, value in [("epochs", 5), ("protocol_id", "legacy"), ("seed", 1),
                               ("hp", {"lr": 99})]:
                result = record("base", 0)
                result[key] = value
                original = json.dumps(result)
                path.write_text(original)
                with self.assertRaisesRegex(ValueError, "Incompatible optional-run metadata"):
                    factorial.run({}, "base", 0, {})
                self.assertEqual(path.read_text(), original)

    def test_legacy_checkpoint_is_rejected_before_loading_graph(self):
        with TemporaryDirectory() as directory, patch.object(factorial, "RESULTS", Path(directory)):
            path = Path(directory) / "base_s0.pt"
            torch.save({"next": 1}, path)
            with self.assertRaisesRegex(ValueError, "Incompatible optional-run metadata"):
                factorial.run({}, "base", 0, {})
            self.assertTrue(path.exists())

    def test_report_arithmetic_and_cross_run_support(self):
        baseline = np.array([10, 11, 9, 10, 10], dtype=float)
        gains = np.array([4, 5, 6, 5, 5], dtype=float)
        residuals = np.array([2, 3, 4, 3, 3], dtype=float)
        counts = baseline + np.array([1, 0, 2, 1, 1])
        values = {"base": baseline, "ports": baseline + gains,
                  "counts": counts, "counts+ports": counts + residuals}
        with TemporaryDirectory() as directory, patch.object(factorial, "RESULTS", Path(directory)):
            for cell in factorial.CELLS:
                for seed in factorial.SEEDS:
                    (Path(directory) / f"{cell}_s{seed}.json").write_text(
                        json.dumps(record(cell, seed, float(values[cell][seed]))))
            factorial.report()
            text = (Path(directory) / "REPORT.md").read_text()
            self.assertIn("Ports − Base in F1 points: +5.00", text)
            self.assertIn("Share of the gain explained by counts: 40.0%", text)
            self.assertIn(factorial.PROTOCOL_ID, text)
            path = Path(directory) / "ports_s2.json"
            changed = json.loads(path.read_text())
            changed["groups"]["all"]["n"] = 22
            changed["groups"]["first"]["n"] = 11
            changed["groups"]["repeat"]["n"] = 11
            path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, "Stratum support differs"):
                factorial.report()
            changed = record("ports", 2, float(values["ports"][2]))
            changed["graph_sha256"] = "b" * 64
            path.write_text(json.dumps(changed))
            with patch.object(factorial, "INPUT_FINGERPRINTS", {}):
                with self.assertRaisesRegex(ValueError, "Input fingerprints differ"):
                    factorial.report()

    def test_fieller_preserves_unidentified_confidence_set(self):
        text = factorial.explained_share(np.array([-2, -1, 0, 1, 2]), np.ones(5))
        self.assertIn("Not identified", text)
        self.assertIn("∪", text)

    def test_two_epoch_resume_matches_uninterrupted_tiny_run(self):
        self.assertTrue((ROOT / "data/reference/models.py").is_file(), "Run setup.sh first")
        graph = tiny_graph()
        masks = factorial.groups(graph)
        hp = {**train.HP, "n_hidden": 8, "n_gnn_layers": 1, "batch_size": 4,
              "num_neighbors": [2], "lr": .005, "final_dropout": .1}

        class Interrupted(Exception):
            pass

        saved = {}
        original_save = torch.save

        def capture_save(state, path):
            if "next" in state:
                saved[(Path(path).parent.name, state["next"])] = {
                    key: value.detach().clone() for key, value in state["model"].items()}
            original_save(state, path)

        with TemporaryDirectory() as directory, patch.object(factorial, "EPOCHS", 2), \
             patch.object(train, "HP", hp), patch.object(torch, "save", side_effect=capture_save), \
             redirect_stdout(io.StringIO()):
            full, resumed = Path(directory) / "full", Path(directory) / "resumed"
            full.mkdir(); resumed.mkdir()
            graph_path = Path(directory) / "tiny.pt"
            torch.save(graph, graph_path)
            factorial.configure_inputs(graph_path)
            with patch.object(factorial, "RESULTS", full):
                factorial.run(graph, "base", 0, masks)
            expected = json.loads((full / "base_s0.json").read_text())
            self.assertEqual(expected["epochs"], 2)
            with patch.object(factorial, "RESULTS", resumed):
                with patch.object(factorial, "print", side_effect=Interrupted(), create=True):
                    with self.assertRaises(Interrupted):
                        factorial.run(graph, "base", 0, masks)
                checkpoint = torch.load(resumed / "base_s0.pt", weights_only=True)
                self.assertEqual(checkpoint["next"], 1)
                self.assertEqual(checkpoint["metadata"]["epochs"], 2)
                factorial.run(graph, "base", 0, masks)
                actual = json.loads((resumed / "base_s0.json").read_text())
                self.assertEqual(actual, expected)
                self.assertFalse((resumed / "base_s0.pt").exists())
            for key, value in saved[("full", 2)].items():
                torch.testing.assert_close(value, saved[("resumed", 2)][key], rtol=0, atol=0)
            self.assertTrue(any(not torch.equal(value, saved[("full", 1)][key])
                                for key, value in saved[("full", 2)].items()))
        # Tiny-test artifacts must not satisfy the real fixed-budget contract.
        with self.assertRaisesRegex(ValueError, "Incompatible optional-run metadata"):
            factorial.validate_result(expected, factorial.expected_metadata("base", 0), "tiny run")


if __name__ == "__main__":
    torch.set_num_threads(1)
    unittest.main(verbosity=2)
