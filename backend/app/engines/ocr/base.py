from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ExtractedFieldDTO(BaseModel):
    field_name: str
    value: str
    confidence: float
    bounding_box: Dict[str, int]  # {"x": int, "y": int, "w": int, "h": int}
    validation_status: str = "VALID"
    notes: Optional[str] = None


class OCRResultDTO(BaseModel):
    engine_name: str
    fields: List[ExtractedFieldDTO]
    raw_mrz_lines: List[str]
    full_text: str
    execution_time_ms: int


class OCREngine(ABC):
    @abstractmethod
    def extract(self, image_path: str) -> OCRResultDTO:
        """Execute text detection, layout analysis, and field extraction on image."""
        pass
