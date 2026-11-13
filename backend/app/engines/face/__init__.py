# Face verification engine package
from .verifier import (
    extract_document_portrait,
    evaluate_face_quality,
    compute_face_similarity,
    verify_document_vs_live
)

__all__ = [
    "extract_document_portrait",
    "evaluate_face_quality",
    "compute_face_similarity",
    "verify_document_vs_live"
]

