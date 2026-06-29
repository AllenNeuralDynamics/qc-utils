"""Fiber photometry QC utilities for SPIM/fiber implant assets."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from aind_data_schema.components.devices import FiberProbe
from aind_data_schema.components.surgery_procedures import ProbeImplant
from aind_data_schema.core.procedures import Procedures, Surgery
from aind_data_schema.core.quality_control import (
    QCMetric,
    QCStatus,
    QualityControl,
    Stage,
    Status,
)
from aind_data_schema_models.modalities import Modality


def fiber_implant_qc(
    input_path: Path,
    output_path: Path,
    reference: Optional[str] = None,
    tags: Optional[dict] = None,
) -> QualityControl:
    """Load a procedures.json file and create a QualityControl object with
    one pending 'CCF location' metric per fiber implant found.

    Writes quality_control.json to output_path.

    Parameters
    ----------
    input_path : Path
        Path to the procedures.json file.
    output_path : Path
        Directory where quality_control.json will be written.
    reference : str, optional
        Reference URL to attach to each metric.
    tags : dict, optional
        Tags to attach to each metric.

    Returns
    -------
    QualityControl
        The constructed QualityControl object.
    """
    procedures = Procedures.model_validate_json(Path(input_path).read_text())

    metrics = []
    for subject_procedure in procedures.subject_procedures:
        if not isinstance(subject_procedure, Surgery):
            continue
        for proc in subject_procedure.procedures:
            if isinstance(proc, ProbeImplant) and isinstance(proc.implanted_device, FiberProbe):
                fiber_name = proc.implanted_device.name
                metrics.append(
                    QCMetric(
                        name=f"{fiber_name} CCF location",
                        modality=Modality.FIB,
                        stage=Stage.RAW,
                        value={"AP": None, "DV": None, "LR": None},
                        description=(
                            f"CCF (25um) location for fiber implant {fiber_name}."
                            " Coordinate system is A->+P, D->+V, L->+R"
                        ),
                        reference=reference,
                        tags=tags or {"evaluation": "procedures"},
                        status_history=[
                            QCStatus(
                                evaluator="automated",
                                status=Status.PENDING,
                                timestamp=datetime.now(tz=timezone.utc),
                            )
                        ],
                    )
                )

    qc = QualityControl(metrics=metrics, default_grouping=["evaluation"])
    qc.write_standard_file(suffix="fib", output_directory=Path(output_path))
    return qc
