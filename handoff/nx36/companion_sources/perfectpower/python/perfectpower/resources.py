"""Locate runtime assets in a source checkout or an installed wheel."""
from pathlib import Path


def runtime_root():
    module=Path(__file__).resolve().parent
    checkout=module.parents[1]
    if (checkout/'pyproject.toml').is_file() and (checkout/'PerfectPower').is_dir():
        return checkout
    packaged=module/'_assets'
    if packaged.is_dir():return packaged
    raise FileNotFoundError('PerfectPower runtime assets missing; reinstall the complete wheel')
