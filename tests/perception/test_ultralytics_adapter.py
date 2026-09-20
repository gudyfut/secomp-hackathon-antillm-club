from types import SimpleNamespace

from perception.adapters import ultralytics_result_to_frame


def test_ultralytics_adapter_copies_tracked_pose_scalars_to_contract() -> None:
    result = SimpleNamespace(
        boxes=SimpleNamespace(
            id=[7], xyxy=[[10.0, 20.0, 110.0, 220.0]], conf=[0.95]
        ),
        keypoints=SimpleNamespace(data=[[[float(index), float(index + 1), 0.8] for index in range(17)]]),
    )

    frame = ultralytics_result_to_frame(
        result,
        source_id="0",
        frame_index=3,
        timestamp_ms=125,
        image_width=640,
        image_height=480,
    )

    assert frame.source_id == "0"
    assert frame.frame_index == 3
    assert frame.persons[0].track_id == 7
    assert frame.persons[0].bounding_box.x_max == 110.0
    assert frame.persons[0].pose.points[9].name == "left_wrist"
    assert frame.persons[0].pose.points[9].confidence == 0.8


def test_ultralytics_adapter_ignores_untracked_detections() -> None:
    result = SimpleNamespace(boxes=SimpleNamespace(id=None))

    frame = ultralytics_result_to_frame(
        result,
        source_id="0",
        frame_index=0,
        timestamp_ms=0,
        image_width=640,
        image_height=480,
    )

    assert frame.persons == ()
