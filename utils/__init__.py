# utils/__init__.py
"""
Utility package for the Fabric Defect Detection System.

This package contains utility modules for logging setup and other
shared functionality.
"""

from .logging_setup import setup_logging

__all__ = ['setup_logging']
