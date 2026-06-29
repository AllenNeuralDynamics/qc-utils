"""SPIM QC utilities."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from aind_data_schema.core.quality_control import (
    QCMetric,
    QCStatus,
    QualityControl,
    Stage,
    Status,
)
from aind_data_schema_models.modalities import Modality
from aind_qcportal_schema.metric_value import DropdownMetric
from aind_qcportal_schema.metric_value import Status as DropdownStatus


def spim_qc(
    output_path: Path,
    channels: list[str],
    reference: Optional[str] = None,
) -> QualityControl:
    """Create a QualityControl object with standard SPIM processing metrics.

    Writes quality_control.json to output_path.

    Parameters
    ----------
    output_path : Path
        Directory where quality_control.json will be written.
    channels : list[str]
        List of channel names (e.g. ``["CH_0", "CH_1"]``).
    reference : str, optional
        Neuroglancer reference URL to attach to each metric.

    Returns
    -------
    QualityControl
        The constructed QualityControl object.
    """
    sp = QCStatus(
        evaluator="automated",
        status=Status.PENDING,
        timestamp=datetime.now(tz=timezone.utc),
    )

    good_sufficient_bad = DropdownMetric(
        options=["Good", "Sufficient", "Bad"],
        status=[DropdownStatus.PASS, DropdownStatus.PASS, DropdownStatus.FAIL],
    )

    pass_fail = DropdownMetric(
        options=["Pass", "Fail"],
        status=[DropdownStatus.PASS, DropdownStatus.FAIL],
    )

    metrics = [
        QCMetric(
            name="Image and tissue quality",
            modality=Modality.SPIM,
            stage=Stage.PROCESSING,
            description=(
                "Pass when image is of sufficient quality to meet experimental needs; "
                "i.e. tissue is well-cleared and image is in focus. Good images will have "
                "consistent clearing throughout the brain enabling sharp, crisp images of deep "
                "as well as superficial structures. Sufficient images may have clearing "
                "inhomogeneities or bubbles obstructing the imaging light path in some portions "
                "of the tissue, but remain suitable meeting some or all experimental needs. Bad "
                "images will be blurry, either due to poor tissue clearing or poor image focus."
            ),
            value=good_sufficient_bad.model_dump(),
            reference=reference,
            status_history=[sp],
            tags={"evaluation": "image quality"},
        ),
    ]

    for channel in channels:
        metrics.append(
            QCMetric(
                name=f"{channel} brightness",
                modality=Modality.SPIM,
                stage=Stage.RAW,
                description=(
                    "Pass when image channel is of sufficient brightness to meet experimental "
                    "needs; i.e. signal is neither under nor oversaturated. Good channel "
                    "brightness will have dynamic range for signal throughout the imaged volume. "
                    "Sufficient channel brightness meets experimental needs but may have some "
                    "regions of under or oversaturation, e.g. if good dynamic range at the "
                    "experimental region of interest oversaturates an injection site. Bad channel "
                    "brightness will be inappropriate for experimental needs, e.g. an "
                    "autofluorescent channel that is too dim for atlas alignment."
                ),
                value=good_sufficient_bad.model_dump(),
                reference=reference,
                status_history=[sp],
                tags={"evaluation": "image quality", "channel": channel},
            )
        )

    metrics += [
        QCMetric(
            name="Tissue perfusion",
            modality=Modality.SPIM,
            stage=Stage.RAW,
            description=(
                "Pass when tissue is sufficiently well-perfused and extracted to meet "
                "experimental needs. Good tissue perfusion will preserve gross anatomical "
                "structures without cracks in tissue, and will be free of perfusion-related "
                "artifacts. Sufficient tissue perfusion will meet experimental needs, but may "
                "have some tissue damage or broad-spectrum autofluorescent artifacts (e.g. "
                "bright, visible vasculature). Fail when tissue damage or artifacts render the "
                "sample unsuitable for meeting experimental needs."
            ),
            value=good_sufficient_bad.model_dump(),
            reference=reference,
            status_history=[sp],
            tags={"evaluation": "image quality"},
        ),
        QCMetric(
            name="Flatfield correction",
            modality=Modality.SPIM,
            stage=Stage.PROCESSING,
            description=(
                "Pass when image tiles appear evenly illuminated. "
                "Fail when image tiles are non-uniform or show vignetting."
            ),
            value=pass_fail.model_dump(),
            reference=reference,
            status_history=[sp],
            tags={"evaluation": "processing"},
        ),
        QCMetric(
            name="Image destriping",
            modality=Modality.SPIM,
            stage=Stage.PROCESSING,
            description=(
                "Pass when image stripes have been sufficiently mitigated to meet experimental "
                "needs. Good image destriping will have few to no visible striping artifacts. "
                "Sufficient image destriping will meet experimental needs, but may have stripes "
                "in some regions. Bad image destriping will have wide-spread striping artifacts "
                "that obstruct experimental analyses."
            ),
            value=good_sufficient_bad.model_dump(),
            reference=reference,
            status_history=[sp],
            tags={"evaluation": "processing"},
        ),
        QCMetric(
            name="Image stitching",
            modality=Modality.SPIM,
            stage=Stage.PROCESSING,
            description=(
                "Pass when there are no visible stitching artifacts at tile boundaries. "
                "Fail when stitching artifacts are present, e.g. visible misalignments, "
                "discontinuities, or doublings of landmarks."
            ),
            value=pass_fail.model_dump(),
            reference=reference,
            status_history=[sp],
            tags={"evaluation": "processing"},
        ),
    ]

    qc = QualityControl(metrics=metrics, default_grouping=["evaluation", "channel"])
    qc.write_standard_file(suffix="spim", output_directory=Path(output_path))
    return qc
