import unittest
from decimal import Decimal

from edi_framework.core import EDITransformEngine, MappingPipeline
from edi_framework.core.pipeline import TransformError


class EDITransformEngineCase(unittest.TestCase):
    def setUp(self):
        self.engine = EDITransformEngine()

    def test_supported_transforms(self):
        self.assertEqual(self.engine.apply("7", [{"type": "cast", "target": "int"}]), 7)
        self.assertEqual(
            self.engine.apply("abcdef", [{"type": "substring", "start": 1, "end": 4}]),
            "bcd",
        )
        self.assertEqual(
            self.engine.apply("A-B-C", [{"type": "split", "separator": "-", "index": 1}]),
            "B",
        )
        self.assertEqual(self.engine.apply("45", [{"type": "zfill", "width": 5}]), "00045")
        self.assertEqual(
            self.engine.apply("12.50", [{"type": "multiply", "factor": "2"}]),
            Decimal("25.00"),
        )
        self.assertEqual(
            self.engine.apply("25.00", [{"type": "divide", "factor": "2"}]),
            Decimal("12.50"),
        )
        self.assertEqual(
            self.engine.apply(
                "2026-04-18",
                [
                    {
                        "type": "date_format",
                        "source_format": "%Y-%m-%d",
                        "target_format": "%d/%m/%Y",
                    }
                ],
            ),
            "18/04/2026",
        )
        self.assertEqual(
            self.engine.apply(
                "draft",
                [{"type": "value_map", "mapping": {"draft": "pending", "done": "success"}}],
            ),
            "pending",
        )
        self.assertEqual(self.engine.apply("abcdef", [{"type": "left", "length": 2}]), "ab")
        self.assertEqual(self.engine.apply("abcdef", [{"type": "right", "length": 2}]), "ef")
        self.assertEqual(self.engine.apply("  abc  ", [{"type": "strip"}]), "abc")
        self.assertEqual(self.engine.apply("abc", [{"type": "upper"}]), "ABC")
        self.assertEqual(self.engine.apply("ABC", [{"type": "lower"}]), "abc")
        self.assertEqual(self.engine.apply("A-123.B", [{"type": "remove_non_digits"}]), "123")
        self.assertEqual(self.engine.apply("abcdef", [{"type": "truncate", "length": 3}]), "abc")
        self.assertEqual(
            self.engine.apply("123", [{"type": "concat", "prefix": "N-", "suffix": "-BR"}]),
            "N-123-BR",
        )
        self.assertEqual(
            self.engine.apply("Pedido 456", [{"type": "regex_extract", "pattern": r"(\d+)"}]),
            "456",
        )
        self.assertTrue(self.engine.apply("sim", [{"type": "cast_bool"}]))
        self.assertEqual(self.engine.apply("7", [{"type": "safe_eval", "expression": "int(value) + 1"}]), 8)

    def test_invalid_transform_raises(self):
        with self.assertRaises(TransformError):
            self.engine.apply("value", [{"type": "unknown"}])


class MappingPipelineCase(unittest.TestCase):
    def test_pipeline_maps_dataset_with_transforms_and_defaults(self):
        pipeline = MappingPipeline()
        dataset = [
            {
                "document_number": "42",
                "amount": "15.75",
                "status": "draft",
                "issued_on": "2026-04-18",
            }
        ]
        mapping_spec = [
            {
                "source": "document_number",
                "target": "doc_number",
                "transforms": [{"type": "zfill", "width": 6}],
            },
            {
                "source": "amount",
                "target": "amount_cents",
                "transforms": [{"type": "multiply", "factor": "100"}],
            },
            {
                "source": "status",
                "target": "transaction_state",
                "transforms": [
                    {
                        "type": "value_map",
                        "mapping": {"draft": "pending", "done": "success"},
                        "default": "unknown",
                    }
                ],
            },
            {
                "source": "issued_on",
                "target": "issued_label",
                "transforms": [
                    {
                        "type": "date_format",
                        "source_format": "%Y-%m-%d",
                        "target_format": "%d/%m/%Y",
                    }
                ],
            },
            {
                "source": "missing_field",
                "target": "fallback_value",
                "default": "N/A",
            },
        ]

        result = pipeline.run(dataset, mapping_spec)

        self.assertEqual(
            result,
            [
                {
                    "doc_number": "000042",
                    "amount_cents": Decimal("1575.00"),
                    "transaction_state": "pending",
                    "issued_label": "18/04/2026",
                    "fallback_value": "N/A",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
