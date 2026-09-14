"""
app/processing/result_mapper.py

Maps raw extraction/processing output into the canonical
ProcessingContext representation.

Architecture:

    Processing Stage / Extraction Engine
                |
                v
        raw processing result
                |
                v
          ResultMapper
                |
                v
        ProcessingContext
                |
                v
        ProcessingResult

Responsibilities
----------------

ResultMapper:

    - normalize raw extraction results
    - normalize extracted fields
    - normalize confidence values
    - normalize provider/stage output
    - update ProcessingContext through its public API
    - remain stateless and deterministic

ResultMapper does NOT:

    - execute processing
    - access the database
    - manage ProcessingJob state
    - call external services
    - resolve stages
    - access StageRegistry
    - create ORM/database models
    - own ProcessingContext
    - mutate pipeline execution state

The mapper intentionally uses plain dictionaries because the
processing layer should remain independent from persistence models.

Canonical structured output is stored in:

    ProcessingContext.extracted_data

Canonical text output is stored in:

    ProcessingContext.raw_text
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from app.processing.pipeline.context import ProcessingContext


class ResultMapper:
    """
    Stateless mapper for raw processing/extraction results.

    The mapper converts loosely structured extraction-engine or
    provider output into the canonical ProcessingContext representation.
    """

    # ======================================================================
    # FIELD MAPPING
    # ======================================================================

    @staticmethod
    def map_fields(
        raw_fields: Any,
    ) -> list[dict[str, Any]]:
        """
        Normalize extracted fields.

        Supported examples:

            [
                {
                    "field": "invoice_number",
                    "value": "INV-1001",
                    "confidence": 0.98,
                }
            ]

        or:

            [
                {
                    "name": "invoice_number",
                    "value": "INV-1001",
                    "confidence": "98%",
                }
            ]

        Also supports a single mapping as a convenience:

            {
                "invoice_number": "INV-1001"
            }

        Invalid individual field entries are skipped.
        """

        if raw_fields is None:
            return []

        # --------------------------------------------------------------
        # Mapping-style fields
        # --------------------------------------------------------------

        if isinstance(raw_fields, Mapping):
            normalized_fields: list[dict[str, Any]] = []

            for field_name, field_value in raw_fields.items():
                if field_name is None:
                    continue

                name = str(field_name).strip()

                if not name:
                    continue

                # Nested canonical field representation.
                if isinstance(field_value, Mapping):
                    item = dict(field_value)

                    item.setdefault(
                        "field",
                        name,
                    )

                    normalized_fields.extend(
                        ResultMapper.map_fields([item])
                    )
                    continue

                normalized_fields.append(
                    {
                        "field": name,
                        "value": field_value,
                        "confidence": 0.0,
                    }
                )

            return normalized_fields

        if isinstance(raw_fields, (str, bytes)):
            raise TypeError(
                "raw_fields must be a sequence or mapping, "
                "not a string."
            )

        if not isinstance(raw_fields, Sequence):
            raise TypeError(
                "raw_fields must be a sequence or mapping."
            )

        fields: list[dict[str, Any]] = []

        for item in raw_fields:

            if not isinstance(item, Mapping):
                continue

            # ----------------------------------------------------------
            # Resolve field name
            # ----------------------------------------------------------

            field_name = item.get("field")

            if field_name is None:
                field_name = item.get("name")

            if field_name is None:
                field_name = item.get("key")

            if field_name is None:
                continue

            field_name = str(field_name).strip()

            if not field_name:
                continue

            # ----------------------------------------------------------
            # Resolve value
            # ----------------------------------------------------------

            field_value = item.get("value")

            if field_value is None and "text" in item:
                field_value = item.get("text")

            # ----------------------------------------------------------
            # Resolve confidence
            # ----------------------------------------------------------

            confidence = ResultMapper._normalize_confidence(
                item.get(
                    "confidence",
                    0.0,
                )
            )

            normalized_field: dict[str, Any] = {
                "field": field_name,
                "value": field_value,
                "confidence": confidence,
            }

            # ----------------------------------------------------------
            # Preserve useful provider-independent metadata
            # ----------------------------------------------------------

            for key in (
                "source",
                "page",
                "page_number",
                "bbox",
                "bounding_box",
                "line",
                "start",
                "end",
                "label",
                "type",
            ):
                if key in item:
                    normalized_field[key] = item[key]

            # Canonicalize common aliases.
            if "page_number" in normalized_field and "page" not in normalized_field:
                normalized_field["page"] = normalized_field["page_number"]

            if (
                "bounding_box" in normalized_field
                and "bbox" not in normalized_field
            ):
                normalized_field["bbox"] = normalized_field["bounding_box"]

            fields.append(normalized_field)

        return fields

    # ======================================================================
    # EXTRACTION MAPPING
    # ======================================================================

    @staticmethod
    def map_extraction(
        raw_result: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """
        Normalize a raw extraction-engine result.

        Supported values include:

            fields
            text
            raw_text
            metadata
            tables
            entities
            sections
            pages
            layout
            document_type
            document_subtype
            classification_confidence
        """

        if raw_result is None:
            raw_result = {}

        if not isinstance(raw_result, Mapping):
            raise TypeError(
                "raw_result must be a mapping."
            )

        # ------------------------------------------------------------------
        # Fields
        # ------------------------------------------------------------------

        raw_fields = raw_result.get(
            "fields",
            [],
        )

        fields = ResultMapper.map_fields(
            raw_fields
        )

        # ------------------------------------------------------------------
        # Raw text
        # ------------------------------------------------------------------

        raw_text = raw_result.get(
            "text"
        )

        if raw_text is None:
            raw_text = raw_result.get(
                "raw_text",
                "",
            )

        if raw_text is None:
            raw_text = ""

        if not isinstance(raw_text, str):
            raw_text = str(raw_text)

        # ------------------------------------------------------------------
        # Metadata
        # ------------------------------------------------------------------

        metadata = raw_result.get(
            "metadata",
            {},
        )

        if metadata is None:
            metadata = {}

        if not isinstance(metadata, Mapping):
            raise TypeError(
                "Extraction result 'metadata' must be a mapping."
            )

        normalized: dict[str, Any] = {
            "fields": fields,
            "text": raw_text,
            "metadata": dict(metadata),
        }

        # ------------------------------------------------------------------
        # Preserve structured extraction artifacts
        # ------------------------------------------------------------------

        optional_keys = (
            "tables",
            "entities",
            "sections",
            "pages",
            "layout",
            "key_values",
            "forms",
            "coordinates",
        )

        for key in optional_keys:
            if key in raw_result:
                normalized[key] = raw_result[key]

        # ------------------------------------------------------------------
        # Classification information
        # ------------------------------------------------------------------

        for key in (
            "document_type",
            "document_subtype",
        ):
            if key in raw_result:
                value = raw_result[key]

                if value is not None:
                    normalized[key] = str(value).strip()

        if "classification_confidence" in raw_result:
            normalized[
                "classification_confidence"
            ] = ResultMapper._normalize_confidence(
                raw_result["classification_confidence"]
            )

        return normalized

    # ======================================================================
    # APPLY EXTRACTION
    # ======================================================================

    @staticmethod
    def apply_extraction(
        context: ProcessingContext,
        raw_result: Mapping[str, Any] | None,
    ) -> ProcessingContext:
        """
        Normalize extraction output and apply it to ProcessingContext.
        """

        ResultMapper._validate_context(context)

        normalized = ResultMapper.map_extraction(
            raw_result
        )

        # ------------------------------------------------------------------
        # Raw text
        # ------------------------------------------------------------------

        context.set_raw_text(
            normalized["text"]
        )

        # ------------------------------------------------------------------
        # Fields
        # ------------------------------------------------------------------

        context.set_extracted_data(
            "fields",
            normalized["fields"],
        )

        # ------------------------------------------------------------------
        # Extraction metadata
        # ------------------------------------------------------------------

        metadata = normalized["metadata"]

        if metadata:
            context.update_metadata(
                metadata
            )

        # ------------------------------------------------------------------
        # Structured artifacts
        # ------------------------------------------------------------------

        for key in (
            "tables",
            "entities",
            "sections",
            "pages",
            "layout",
            "key_values",
            "forms",
            "coordinates",
        ):
            if key in normalized:
                context.set_extracted_data(
                    key,
                    normalized[key],
                )

        return context

    # ======================================================================
    # APPLY RESULT
    # ======================================================================

    @staticmethod
    def apply_result(
        context: ProcessingContext,
        raw_result: Mapping[str, Any] | None,
    ) -> ProcessingContext:
        """
        Apply a complete raw processing result to ProcessingContext.

        This method handles extraction, classification and common
        document-processing artifacts.
        """

        ResultMapper._validate_context(context)

        if raw_result is None:
            raw_result = {}

        if not isinstance(raw_result, Mapping):
            raise TypeError(
                "raw_result must be a mapping."
            )

        ResultMapper.apply_extraction(
            context,
            raw_result,
        )

        # ------------------------------------------------------------------
        # Classification
        # ------------------------------------------------------------------

        if "document_type" in raw_result:
            value = raw_result["document_type"]

            if value is not None:
                normalized = str(value).strip()

                if normalized:
                    context.document_type = normalized

        if "document_subtype" in raw_result:
            value = raw_result["document_subtype"]

            if value is not None:
                normalized = str(value).strip()

                if normalized:
                    context.document_subtype = normalized

        if "classification_confidence" in raw_result:
            context.classification_confidence = (
                ResultMapper._normalize_confidence(
                    raw_result[
                        "classification_confidence"
                    ]
                )
            )

        # ------------------------------------------------------------------
        # Optional document information
        # ------------------------------------------------------------------

        if "mime_type" in raw_result:
            value = raw_result["mime_type"]

            if value is not None:
                context.mime_type = str(value).strip()

        if "file_name" in raw_result:
            value = raw_result["file_name"]

            if value is not None:
                context.file_name = str(value).strip()

        if "file_path" in raw_result:
            value = raw_result["file_path"]

            if value is not None:
                context.file_path = str(value)

        if "checksum" in raw_result:
            value = raw_result["checksum"]

            if value is not None:
                context.checksum = str(value).strip()

        if "file_size" in raw_result:
            value = raw_result["file_size"]

            if value is not None:
                if not isinstance(value, int):
                    raise TypeError(
                        "file_size must be an integer."
                    )

                if value < 0:
                    raise ValueError(
                        "file_size cannot be negative."
                    )

                context.file_size = value

        # ------------------------------------------------------------------
        # Cleaned text
        # ------------------------------------------------------------------

        if "cleaned_text" in raw_result:
            value = raw_result["cleaned_text"]

            if value is None:
                context.set_cleaned_text(None)
            elif isinstance(value, str):
                context.set_cleaned_text(value)
            else:
                context.set_cleaned_text(str(value))

        # ------------------------------------------------------------------
        # Generic result metadata
        # ------------------------------------------------------------------

        if "stage_result" in raw_result:
            context.set_extracted_data(
                "stage_result",
                raw_result["stage_result"],
            )

        return context

    # ======================================================================
    # APPLY STAGE RESULT
    # ======================================================================

    @staticmethod
    def apply_stage_result(
        context: ProcessingContext,
        stage: str,
        raw_result: Any,
    ) -> ProcessingContext:
        """
        Map a stage result into ProcessingContext.

        This is intentionally conservative.

        Mapping rules:

            mapping result
                -> extraction/classification fields when present

            other result
                -> context.stage_results

        The mapper does not attempt to understand provider-specific
        objects.
        """

        ResultMapper._validate_context(context)

        normalized_stage = context.normalize_stage(
            stage
        )

        if isinstance(raw_result, Mapping):
            ResultMapper.apply_result(
                context,
                raw_result,
            )

            context.set_stage_result(
                normalized_stage,
                dict(raw_result),
            )

            return context

        context.set_stage_result(
            normalized_stage,
            raw_result,
        )

        return context

    # ======================================================================
    # CONFIDENCE NORMALIZATION
    # ======================================================================

    @staticmethod
    def _normalize_confidence(
        value: Any,
    ) -> float:
        """
        Normalize confidence to [0.0, 1.0].

        Supported:

            0.95
            "0.95"
            95
            "95%"
            "confidence: 95%"

        Invalid values become 0.0.

        NaN and infinity are rejected.
        """

        if value is None:
            return 0.0

        if isinstance(value, bool):
            return 0.0

        try:
            if isinstance(value, str):
                text = value.strip()

                if not text:
                    return 0.0

                # Handle common provider strings such as:
                # "95%"
                # "0.95"
                # "confidence: 95%"
                lowered = text.lower()

                if ":" in lowered:
                    text = text.split(
                        ":",
                        1,
                    )[1].strip()

                is_percentage = text.endswith("%")

                if is_percentage:
                    text = text[:-1].strip()

                number = float(text)

                if not math.isfinite(number):
                    return 0.0

                if is_percentage:
                    number /= 100.0

            else:
                number = float(value)

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return 0.0

        if not math.isfinite(number):
            return 0.0

        # Numeric values greater than one are treated as percentages.
        if number > 1.0:
            number /= 100.0

        return max(
            0.0,
            min(
                number,
                1.0,
            ),
        )

    # ======================================================================
    # HELPERS
    # ======================================================================

    @staticmethod
    def _validate_context(
        context: ProcessingContext,
    ) -> None:
        if not isinstance(
            context,
            ProcessingContext,
        ):
            raise TypeError(
                "context must be a ProcessingContext."
            )


__all__ = [
    "ResultMapper",
]