"""
Model-Form Error Authority (v7.0.0)
Deterministic forward-checks + closure-consistent cross-validation.
© 2026 Afshin Arjhangmehr
"""

from .schema import ModelFormConfig, CVSplit, ForwardCheckRow, ModelFormScorecard
from .splits import generate_cv_splits
from .forward import run_forward_checks
from .mfe import run_model_form_audit
from .pack import build_consistency_triangle_pack

__all__ = [
    "ModelFormConfig",
    "CVSplit",
    "ForwardCheckRow",
    "ModelFormScorecard",
    "generate_cv_splits",
    "run_forward_checks",
    "run_model_form_audit",
    "build_consistency_triangle_pack",
]
