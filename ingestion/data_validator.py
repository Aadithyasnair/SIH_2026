"""
Data Validator Module for SIH26146 Data Ingestion
Validates incoming raw records against Pydantic schemas.
Quarantines (logs + skips, doesn't crash) malformed records.
"""

import logging
from typing import Any, Dict, List, Tuple, Type
from pydantic import BaseModel, ValidationError

from shared.schemas.records import NetworkEvent, BlockchainTxn

logger = logging.getLogger("ingestion.data_validator")


class DataValidator:
    """
    Validates data records against target Pydantic schemas.
    Quarantines malformed records instead of crashing the pipeline.
    """

    def __init__(self):
        self.quarantined_records: List[Dict[str, Any]] = []

    def validate_record(
        self, record: Dict[str, Any], model_cls: Type[BaseModel]
    ) -> BaseModel | None:
        """
        Validates a single dictionary record against model_cls.
        Returns model instance if valid, or None if quarantined.
        """
        if not isinstance(record, dict):
            msg = f"Record is not a dictionary: {type(record)}"
            logger.warning(msg)
            self.quarantined_records.append({"raw_record": str(record), "error": msg})
            return None

        try:
            return model_cls(**record)
        except (ValidationError, TypeError, ValueError) as e:
            logger.warning("Record validation failed (%s): %s | Raw record: %s", model_cls.__name__, e, record)
            self.quarantined_records.append({"raw_record": record, "error": str(e)})
            return None

    def validate_batch(
        self, records: List[Dict[str, Any]], model_cls: Type[BaseModel]
    ) -> Tuple[List[BaseModel], List[Dict[str, Any]]]:
        """
        Validates a list of records against model_cls.
        Returns (valid_models, newly_quarantined_records).
        """
        valid_models: List[BaseModel] = []
        batch_quarantined: List[Dict[str, Any]] = []

        for idx, rec in enumerate(records):
            validated = self.validate_record(rec, model_cls)
            if validated is not None:
                valid_models.append(validated)
            else:
                batch_quarantined.append(self.quarantined_records[-1])

        return valid_models, batch_quarantined

    def get_quarantine_stats(self) -> Dict[str, int]:
        """Returns stats on total quarantined records."""
        return {"total_quarantined": len(self.quarantined_records)}
