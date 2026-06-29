"""General QC utilities."""

from functools import reduce
from pathlib import Path

from aind_data_schema.core.quality_control import QualityControl


def merge_quality_control_files(
    search_path: Path,
    output_path: Path,
) -> QualityControl:
    """Find all *quality_control*.json files under search_path, merge them,
    and write the result to output_path.

    Files that cannot be parsed as a valid QualityControl are silently skipped.

    Parameters
    ----------
    search_path : Path
        Directory to search recursively for ``*quality_control*.json`` files.
    output_path : Path
        Directory where the merged ``quality_control.json`` will be written.

    Returns
    -------
    QualityControl
        The merged QualityControl object.

    Raises
    ------
    ValueError
        If no valid ``*quality_control*.json`` files are found under
        ``search_path``.
    """
    qc_objects = []
    for f in sorted(Path(search_path).rglob("*quality_control*.json")):
        try:
            qc_objects.append(QualityControl.model_validate_json(f.read_text()))
        except Exception:
            pass

    if not qc_objects:
        raise ValueError(
            f"No valid *quality_control*.json files found under {search_path}"
        )

    merged = reduce(lambda a, b: a + b, qc_objects)
    merged.write_standard_file(output_directory=Path(output_path))
    return merged
