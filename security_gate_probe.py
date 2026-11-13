"""Temporary, non-executed probe for the S6 CodeQL security-gate test."""

import subprocess

from flask import request


def security_gate_probe() -> None:
    """Intentionally unsafe test probe. Never executed by the application."""
    command = request.args.get("command", "")
    subprocess.run(command, shell=True, check=False)
