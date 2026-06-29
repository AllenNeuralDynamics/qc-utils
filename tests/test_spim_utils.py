"""Tests for qc_utils.spim.spim_utils."""

import unittest
from pathlib import Path
from unittest.mock import patch

from aind_data_schema.core.quality_control import QualityControl, Stage, Status
from aind_data_schema_models.modalities import Modality

from qc_utils.spim.spim_utils import spim_qc

CHANNELS = ["CH_0", "CH_1"]
FIXED_METRIC_NAMES = [
    "Image and tissue quality",
    "Tissue perfusion",
    "Flatfield correction",
    "Image destriping",
    "Image stitching",
]
GOOD_SUFFICIENT_BAD_METRICS = [
    "Image and tissue quality",
    "Tissue perfusion",
    "Image destriping",
]
PASS_FAIL_METRICS = [
    "Flatfield correction",
    "Image stitching",
]


class TestSpimQc(unittest.TestCase):
    """Tests for spim_qc."""

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_returns_quality_control_instance(self, mock_write):
        """Return type is QualityControl."""
        result = spim_qc(Path("/output"), channels=CHANNELS)
        self.assertIsInstance(result, QualityControl)

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_metric_count(self, mock_write):
        """Metric count equals 5 fixed + 1 per channel."""
        qc = spim_qc(Path("/output"), channels=CHANNELS)
        self.assertEqual(len(qc.metrics), 5 + len(CHANNELS))

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_metric_count_no_channels(self, mock_write):
        """With no channels there are exactly 5 metrics."""
        qc = spim_qc(Path("/output"), channels=[])
        self.assertEqual(len(qc.metrics), 5)

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_fixed_metric_names_present(self, mock_write):
        """All fixed metric names are present."""
        qc = spim_qc(Path("/output"), channels=[])
        names = [m.name for m in qc.metrics]
        for name in FIXED_METRIC_NAMES:
            self.assertIn(name, names)

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_channel_brightness_metrics(self, mock_write):
        """One brightness metric per channel with correct name and tags."""
        qc = spim_qc(Path("/output"), channels=CHANNELS)
        for channel in CHANNELS:
            metric = next((m for m in qc.metrics if m.name == f"{channel} brightness"), None)
            self.assertIsNotNone(metric, f"Missing metric for channel {channel}")
            self.assertEqual(metric.tags, {"evaluation": "image quality", "channel": channel})

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_modality_and_stage(self, mock_write):
        """Every metric has SPIM modality; stage is RAW or PROCESSING depending on metric."""
        raw_metrics = {"Tissue perfusion"} | {f"{c} brightness" for c in CHANNELS}
        processing_metrics = {"Image and tissue quality", "Flatfield correction", "Image destriping", "Image stitching"}
        qc = spim_qc(Path("/output"), channels=CHANNELS)
        for metric in qc.metrics:
            self.assertEqual(metric.modality, Modality.SPIM)
            if metric.name in raw_metrics:
                self.assertEqual(metric.stage, Stage.RAW)
            elif metric.name in processing_metrics:
                self.assertEqual(metric.stage, Stage.PROCESSING)

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_status_history_pending(self, mock_write):
        """Every metric starts with a single PENDING automated status."""
        qc = spim_qc(Path("/output"), channels=CHANNELS)
        for metric in qc.metrics:
            self.assertEqual(len(metric.status_history), 1)
            self.assertEqual(metric.status_history[0].status, Status.PENDING)
            self.assertEqual(metric.status_history[0].evaluator, "automated")

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_good_sufficient_bad_dropdown_values(self, mock_write):
        """Good/Sufficient/Bad metrics have the correct dropdown options and status mapping."""
        from aind_qcportal_schema.metric_value import Status as DropdownStatus

        qc = spim_qc(Path("/output"), channels=CHANNELS)
        for name in GOOD_SUFFICIENT_BAD_METRICS:
            metric = next(m for m in qc.metrics if m.name == name)
            value = metric.value
            self.assertEqual(value["options"], ["Good", "Sufficient", "Bad"])
            self.assertEqual(
                value["status"],
                [DropdownStatus.PASS, DropdownStatus.PASS, DropdownStatus.FAIL],
            )
            self.assertEqual(value["type"], "dropdown")
            self.assertEqual(value["value"], "")

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_pass_fail_dropdown_values(self, mock_write):
        """Pass/Fail metrics have the correct dropdown options and status mapping."""
        from aind_qcportal_schema.metric_value import Status as DropdownStatus

        qc = spim_qc(Path("/output"), channels=CHANNELS)
        for name in PASS_FAIL_METRICS:
            metric = next(m for m in qc.metrics if m.name == name)
            value = metric.value
            self.assertEqual(value["options"], ["Pass", "Fail"])
            self.assertEqual(
                value["status"],
                [DropdownStatus.PASS, DropdownStatus.FAIL],
            )
            self.assertEqual(value["type"], "dropdown")
            self.assertEqual(value["value"], "")

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_reference_propagated(self, mock_write):
        """reference is set on every metric."""
        ref = "https://neuroglancer.example.com/link"
        qc = spim_qc(Path("/output"), channels=CHANNELS, reference=ref)
        for metric in qc.metrics:
            self.assertEqual(metric.reference, ref)

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_reference_defaults_to_none(self, mock_write):
        """Omitting reference leaves it as None on every metric."""
        qc = spim_qc(Path("/output"), channels=CHANNELS)
        for metric in qc.metrics:
            self.assertIsNone(metric.reference)

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_output_path_passed_to_write(self, mock_write):
        """write_standard_file is called with the correct output_path and suffix."""
        output = Path("/my/custom/output/dir")
        spim_qc(output, channels=CHANNELS)
        mock_write.assert_called_once_with(suffix="spim", output_directory=output)

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_write_called_exactly_once(self, mock_write):
        """write_standard_file is called exactly once."""
        spim_qc(Path("/output"), channels=CHANNELS)
        mock_write.assert_called_once()
