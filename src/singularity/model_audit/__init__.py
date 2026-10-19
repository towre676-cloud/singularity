"""Portable behavioral audit packages for resident language models.

``core`` (standard library) builds, verifies and checks packages; ``adapters``
(optional PyTorch / transformers) turns models into observations.
"""
from .core import (PACKAGE_SCHEMA, build_package, check_package, deviation, flags, load_package,
                   package_digest, save_package, tolerances_from_clean, verify_package)

__all__ = ["PACKAGE_SCHEMA", "build_package", "check_package", "deviation", "flags", "load_package",
           "package_digest", "save_package", "tolerances_from_clean", "verify_package", "settings_from_contract"]


def settings_from_contract(contract):
    """Adapter keyword settings that reproduce a package's declared pipeline."""
    return {"max_context": contract["max_context"], "truncate_to": contract["truncate_to"], "pad_id": contract["pad_id"],
            "normalization": contract["normalization"], "temperature": contract["temperature"],
            "pass_attention_mask": contract["attention_mask"],
            "position_correction": contract["position_ids"] == "offset by left padding",
            "use_cache": contract["use_cache"]}
