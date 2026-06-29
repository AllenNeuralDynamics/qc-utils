"""Tests for qc_utils.utils."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aind_data_schema.core.quality_control import QualityControl

from qc_utils.utils import merge_quality_control_files

# Minimal valid QualityControl JSON produced by QualityControl(metrics=[], default_grouping=[])
_EMPTY_QC_JSON = QualityControl(metrics=[], default_grouping=[]).model_dump_json()


def _write_qc(directory: Path, filename: str, content: str = _EMPTY_QC_JSON) -> Path:
    """Write a QC JSON file into directory and return its path."""
    path = directory / filename
    path.write_text(content)
    return path


class TestMergeQualityControlFiles(unittest.TestCase):
    """Tests for merge_quality_control_files."""

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_single_file_returns_qc_instance(self, mock_write):
        """A single valid file is returned as a QualityControl instance."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_qc(Path(tmp), "quality_control.json")
            result = merge_quality_control_files([Path(tmp)], Path(tmp))
        self.assertIsInstance(result, QualityControl)

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_multiple_files_metrics_merged(self, mock_write):
        """Metrics from all valid files are combined in the merged result."""
        from datetime import datetime, timezone

        from aind_data_schema.core.quality_control import QCMetric, QCStatus, Stage, Status
        from aind_data_schema_models.modalities import Modality

        def _make_qc_json(metric_name: str) -> str:
            """Create a QC JSON with a single metric named `metric_name`."""
            qc = QualityControl(
                metrics=[
                    QCMetric(
                        name=metric_name,
                        modality=Modality.SPIM,
                        stage=Stage.PROCESSING,
                        value={"key": "val"},
                        status_history=[
                            QCStatus(
                                evaluator="automated",
                                status=Status.PENDING,
                                timestamp=datetime.now(tz=timezone.utc),
                            )
                        ],
                    )
                ],
                default_grouping=[],
            )
            return qc.model_dump_json()

        with tempfile.TemporaryDirectory() as tmp:
            _write_qc(Path(tmp), "quality_control_a.json", _make_qc_json("Metric A"))
            _write_qc(Path(tmp), "quality_control_b.json", _make_qc_json("Metric B"))
            result = merge_quality_control_files([Path(tmp)], Path(tmp))

        names = [m.name for m in result.metrics]
        self.assertIn("Metric A", names)
        self.assertIn("Metric B", names)
        self.assertEqual(len(result.metrics), 2)

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_invalid_files_skipped(self, mock_write):
        """Files that are not valid QualityControl JSON are silently skipped."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_qc(Path(tmp), "quality_control_valid.json")
            _write_qc(Path(tmp), "quality_control_bad.json", "not json at all")
            result = merge_quality_control_files([Path(tmp)], Path(tmp))
        self.assertIsInstance(result, QualityControl)

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_no_valid_files_raises(self, mock_write):
        """ValueError is raised when no valid files are found."""
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                merge_quality_control_files([Path(tmp)], Path(tmp))

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_no_valid_files_only_invalid_raises(self, mock_write):
        """ValueError is raised when only invalid files are present."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_qc(Path(tmp), "quality_control_bad.json", "{}")
            with self.assertRaises(ValueError):
                merge_quality_control_files([Path(tmp)], Path(tmp))

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_output_path_passed_to_write(self, mock_write):
        """write_standard_file is called with the specified output_path."""
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out"
            _write_qc(Path(tmp), "quality_control.json")
            merge_quality_control_files([Path(tmp)], output)
        mock_write.assert_called_once_with(output_directory=output)

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_non_matching_filenames_ignored(self, mock_write):
        """Files not matching *quality_control*.json are not loaded."""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "other.json").write_text(_EMPTY_QC_JSON)
            with self.assertRaises(ValueError):
                merge_quality_control_files([Path(tmp)], Path(tmp))

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_searches_recursively(self, mock_write):
        """Files in subdirectories are found."""
        with tempfile.TemporaryDirectory() as tmp:
            subdir = Path(tmp) / "subdir"
            subdir.mkdir()
            _write_qc(subdir, "quality_control.json")
            result = merge_quality_control_files([Path(tmp)], Path(tmp))
        self.assertIsInstance(result, QualityControl)

    @patch("aind_data_schema.core.quality_control.QualityControl.write_standard_file")
    def test_multiple_search_paths(self, mock_write):
        """Files from multiple search paths are all collected and merged."""
        with tempfile.TemporaryDirectory() as tmp_a, tempfile.TemporaryDirectory() as tmp_b:
            _write_qc(Path(tmp_a), "quality_control.json")
            _write_qc(Path(tmp_b), "quality_control.json")
            result = merge_quality_control_files([Path(tmp_a), Path(tmp_b)], Path(tmp_a))
        self.assertIsInstance(result, QualityControl)
