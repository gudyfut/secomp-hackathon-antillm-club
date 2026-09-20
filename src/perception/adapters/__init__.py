"""Adapters that isolate perception SDK objects from project contracts."""

from .ultralytics import ultralytics_result_to_frame

__all__ = ["ultralytics_result_to_frame"]
