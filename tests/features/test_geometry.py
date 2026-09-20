from contracts import BoundingBox
from features.geometry import (
    bounding_box_area,
    bounding_box_center,
    bounding_box_height,
    bounding_box_iou,
    bounding_box_width,
    cosine_similarity,
    dot_product,
    euclidean_distance,
    safe_mean,
    vector_magnitude,
    vector_normalization,
)


def test_geometry_helpers_handle_values_and_degenerate_boxes() -> None:
    box = BoundingBox(0.0, 0.0, 10.0, 20.0)
    assert bounding_box_center(box) == (5.0, 10.0)
    assert bounding_box_width(box) == 10.0
    assert bounding_box_height(box) == 20.0
    assert bounding_box_area(box) == 200.0
    assert euclidean_distance((0.0, 0.0), (3.0, 4.0)) == 5.0
    assert bounding_box_area(BoundingBox(2.0, 0.0, 2.0, 3.0)) is None
    assert bounding_box_iou(box, BoundingBox(5.0, 0.0, 15.0, 20.0)) == 1 / 3
    assert bounding_box_iou(box, BoundingBox(20.0, 20.0, 30.0, 30.0)) == 0.0


def test_vector_helpers_never_convert_missing_or_zero_to_measurements() -> None:
    assert vector_magnitude((3.0, 4.0)) == 5.0
    assert vector_normalization((3.0, 4.0)) == (0.6, 0.8)
    assert vector_normalization((0.0, 0.0)) is None
    assert dot_product((1.0, 2.0), (3.0, 4.0)) == 11.0
    assert cosine_similarity((1.0, 0.0), (1.0, 0.0)) == 1.0
    assert cosine_similarity((1.0, 0.0), (-1.0, 0.0)) == -1.0
    assert cosine_similarity((0.0, 0.0), (1.0, 0.0)) is None
    assert safe_mean([None, 2.0, float("nan"), 4.0]) == 3.0
