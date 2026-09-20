"""Small finite-safe geometry helpers for image-coordinate feature extraction."""

from __future__ import annotations

from collections.abc import Iterable
from math import hypot, isfinite

from contracts import BoundingBox

Point = tuple[float, float]
Vector = tuple[float, float]


def _finite(value: float) -> bool:
    return isfinite(value)


def euclidean_distance(first: Point | None, second: Point | None) -> float | None:
    """Return image-pixel distance, or None when either point is non-finite."""
    if first is None or second is None or not all(map(_finite, (*first, *second))):
        return None
    return hypot(first[0] - second[0], first[1] - second[1])


def bounding_box_center(box: BoundingBox) -> Point | None:
    """Return bbox center in image pixels, or None for invalid coordinates."""
    if not all(map(_finite, (box.x_min, box.y_min, box.x_max, box.y_max))):
        return None
    return ((box.x_min + box.x_max) / 2.0, (box.y_min + box.y_max) / 2.0)


def bounding_box_width(box: BoundingBox) -> float | None:
    """Return positive bbox width in image pixels, or None for a degenerate bbox."""
    width = box.x_max - box.x_min
    return width if _finite(width) and width > 0.0 else None


def bounding_box_height(box: BoundingBox) -> float | None:
    """Return positive bbox height in image pixels, or None for a degenerate bbox."""
    height = box.y_max - box.y_min
    return height if _finite(height) and height > 0.0 else None


def bounding_box_area(box: BoundingBox) -> float | None:
    """Return positive bbox area in square pixels, or None for a degenerate bbox."""
    width = bounding_box_width(box)
    height = bounding_box_height(box)
    return width * height if width is not None and height is not None else None


def bounding_box_iou(first: BoundingBox, second: BoundingBox) -> float | None:
    """Return visual bbox IoU in [0, 1], or None when either bbox is degenerate."""
    first_area = bounding_box_area(first)
    second_area = bounding_box_area(second)
    if first_area is None or second_area is None:
        return None
    overlap_width = max(0.0, min(first.x_max, second.x_max) - max(first.x_min, second.x_min))
    overlap_height = max(0.0, min(first.y_max, second.y_max) - max(first.y_min, second.y_min))
    union = first_area + second_area - overlap_width * overlap_height
    return overlap_width * overlap_height / union if union > 0.0 and _finite(union) else None


def vector_magnitude(vector: Vector | None) -> float | None:
    """Return finite vector magnitude, or None for invalid input."""
    if vector is None or not all(map(_finite, vector)):
        return None
    return hypot(*vector)


def vector_normalization(vector: Vector | None) -> Vector | None:
    """Return unit vector, or None for a zero or invalid vector."""
    magnitude = vector_magnitude(vector)
    if vector is None or magnitude is None or magnitude == 0.0:
        return None
    return (vector[0] / magnitude, vector[1] / magnitude)


def dot_product(first: Vector | None, second: Vector | None) -> float | None:
    """Return finite vector dot product, or None for invalid input."""
    if first is None or second is None or not all(map(_finite, (*first, *second))):
        return None
    return first[0] * second[0] + first[1] * second[1]


def cosine_similarity(first: Vector | None, second: Vector | None) -> float | None:
    """Return cosine similarity in [-1, 1], or None for a zero or invalid vector."""
    first_unit = vector_normalization(first)
    second_unit = vector_normalization(second)
    similarity = dot_product(first_unit, second_unit)
    if similarity is None:
        return None
    return max(-1.0, min(1.0, similarity))


def safe_mean(values: Iterable[float | None]) -> float | None:
    """Return mean of finite values, or None when no finite value exists."""
    finite_values = [value for value in values if value is not None and _finite(value)]
    return sum(finite_values) / len(finite_values) if finite_values else None
