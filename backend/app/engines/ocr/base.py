from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ExtractedFieldDTO(BaseModel):
    field_name: str
    value: Optional[str] = None
    confidence: Optional[float] = None
    bounding_box: Optional[Dict[str, int]] = None  # {"x": int, "y": int, "w": int, "h": int}
    validation_status: str = "MISSING"
    notes: Optional[str] = None


class OCRResultDTO(BaseModel):
    engine_name: str
    fields: List[ExtractedFieldDTO]
    raw_mrz_lines: List[str]
    full_text: str
    execution_time_ms: int
    status: str = "SUCCESS"  # SUCCESS, ENGINE_UNAVAILABLE, EXTRACTION_FAILED
    error_message: Optional[str] = None
    fallback_used: bool = False
    primary_engine: Optional[str] = None


class OCREngine(ABC):
    @abstractmethod
    def extract(self, image_path: str) -> OCRResultDTO:
        """Execute text detection, layout analysis, and field extraction on image."""
        pass
