"""Temporary, non-executed probe for the S6 CodeQL security-gate test."""

import subprocess


def security_gate_probe(user_value: str) -> None:
    """Intentionally unsafe pattern; this function is never called."""
    subprocess.run(user_value, shell=True, check=False)
