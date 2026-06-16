"""Tests for qc_utils.spim.fib_utils."""

import json
from pathlib import Path
from unittest.mock import patch

from qc_utils.spim.fib_utils import fiber_implant_qc

PROCEDURES_WITH_FIBERS = Path(__file__).parent / "resources" / "procedures.json"

NO_FIBER_PROCEDURES_JSON = json.dumps(
    {
        "object_type": "Procedures",
        "describedBy": (
            "https://raw.githubusercontent.com/AllenNeuralDynamics/"
            "aind-data-schema/main/src/aind_data_schema/core/procedures.py"
        ),
        "schema_version": "2.2.1",
        "subject_id": "000000",
        "subject_procedures": [
            {
                "object_type": "Water restriction",
                "ethics_review_id": "unknown",
                "target_fraction_weight": 85,
                "target_fraction_weight_unit": "percent",
                "minimum_water_per_day": 1,
                "minimum_water_per_day_unit": "milliliter",
                "baseline_weight": 25.0,
                "weight_unit": "gram",
                "start_date": "2026-01-01",
                "end_date": None,
            }
        ],
        "specimen_procedures": [],
    }
)


class TestFiberImplantQc:
    """Tests for fiber_implant_qc."""

    @patch("aind_data_schema.core.quality_control.QualityControl" ".write_standard_file")
    def test_with_fiber_implants(self, mock_write):
        """Procedures with fiber implants produce one metric per fiber."""
        procedures_json = PROCEDURES_WITH_FIBERS.read_text()

        with patch("pathlib.Path.read_text", return_value=procedures_json):
            qc = fiber_implant_qc(
                Path("procedures.json"),
                Path("/output"),
            )

        # The test procedures.json has 4 fiber implants (Fiber 0-3)
        assert len(qc.metrics) == 4
        metric_names = [m.name for m in qc.metrics]
        assert "Fiber 0 CCF location" in metric_names
        assert "Fiber 1 CCF location" in metric_names
        assert "Fiber 2 CCF location" in metric_names
        assert "Fiber 3 CCF location" in metric_names

        mock_write.assert_called_once_with(output_directory=Path("/output"))

    @patch("aind_data_schema.core.quality_control.QualityControl" ".write_standard_file")
    def test_with_fiber_implants_metric_fields(self, mock_write):
        """Metrics have correct modality, stage, value, and status."""
        from aind_data_schema.core.quality_control import Stage, Status
        from aind_data_schema_models.modalities import Modality

        procedures_json = PROCEDURES_WITH_FIBERS.read_text()

        with patch("pathlib.Path.read_text", return_value=procedures_json):
            qc = fiber_implant_qc(
                Path("procedures.json"),
                Path("/output"),
            )

        metric = qc.metrics[0]
        assert metric.modality == Modality.FIB
        assert metric.stage == Stage.PROCESSING
        assert metric.value == {"AP": None, "DV": None, "LR": None}
        assert len(metric.status_history) == 1
        assert metric.status_history[0].status == Status.PENDING
        assert metric.status_history[0].evaluator == "automated"
        assert "Fiber" in metric.description

    @patch("aind_data_schema.core.quality_control.QualityControl" ".write_standard_file")
    def test_no_fiber_implants(self, mock_write):
        """Procedures with no fiber implants produce an empty metrics list."""
        with patch("pathlib.Path.read_text", return_value=NO_FIBER_PROCEDURES_JSON):
            qc = fiber_implant_qc(
                Path("procedures.json"),
                Path("/output"),
            )

        assert qc.metrics == []
        mock_write.assert_called_once_with(output_directory=Path("/output"))

    @patch("aind_data_schema.core.quality_control.QualityControl" ".write_standard_file")
    def test_returns_quality_control_instance(self, mock_write):
        """Return type is QualityControl."""
        from aind_data_schema.core.quality_control import QualityControl

        with patch("pathlib.Path.read_text", return_value=NO_FIBER_PROCEDURES_JSON):
            result = fiber_implant_qc(
                Path("procedures.json"),
                Path("/output"),
            )

        assert isinstance(result, QualityControl)

    @patch("aind_data_schema.core.quality_control.QualityControl" ".write_standard_file")
    def test_output_path_passed_to_write(self, mock_write):
        """write_standard_file receives the output_path argument."""
        output = Path("/my/custom/output/dir")

        with patch("pathlib.Path.read_text", return_value=NO_FIBER_PROCEDURES_JSON):
            fiber_implant_qc(Path("procedures.json"), output)

        mock_write.assert_called_once_with(output_directory=output)

    @patch("aind_data_schema.core.quality_control.QualityControl" ".write_standard_file")
    def test_reference_and_tags_propagated(self, mock_write):
        """reference and tags are set on every metric."""
        procedures_json = PROCEDURES_WITH_FIBERS.read_text()
        ref = "https://example.com/histology"
        tags = {"project": "myproject"}

        with patch("pathlib.Path.read_text", return_value=procedures_json):
            qc = fiber_implant_qc(
                Path("procedures.json"),
                Path("/output"),
                reference=ref,
                tags=tags,
            )

        for metric in qc.metrics:
            assert metric.reference == ref
            assert metric.tags == tags

    @patch("aind_data_schema.core.quality_control.QualityControl" ".write_standard_file")
    def test_reference_and_tags_defaults_to_none_and_empty(self, mock_write):
        """Omitting reference and tags leaves them as None and {}."""
        procedures_json = PROCEDURES_WITH_FIBERS.read_text()

        with patch("pathlib.Path.read_text", return_value=procedures_json):
            qc = fiber_implant_qc(
                Path("procedures.json"),
                Path("/output"),
            )

        for metric in qc.metrics:
            assert metric.reference is None
            assert metric.tags == {}
