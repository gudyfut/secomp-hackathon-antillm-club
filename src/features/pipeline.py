"""Deterministic, bounded temporal feature extraction from perception contracts.

Initial engineering defaults below require calibration with recorded camera data. Image-space
normalization reduces, but does not remove, perspective effects. Bbox IoU is visual overlap, not
physical contact; normalized 2D distance is not physical distance. Pose confidence degrades under
occlusion, track IDs can switch, and local pose motion remains sensitive to detector noise.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from math import isfinite

from contracts import InteractionFeatures, PerceptionFrame, PersonFeatures, WorldState
from contracts.perception import BoundingBox, TrackedPerson

from .geometry import (
    Point,
    bounding_box_center,
    bounding_box_height,
    bounding_box_iou,
    euclidean_distance,
    safe_mean,
)

TORSO_KEYPOINTS = frozenset({"left_shoulder", "right_shoulder", "left_hip", "right_hip"})
ARM_KEYPOINTS = frozenset({"left_elbow", "right_elbow", "left_wrist", "right_wrist"})
BODY_KEYPOINTS = frozenset(
    {
        "left_shoulder",
        "right_shoulder",
        "left_elbow",
        "right_elbow",
        "left_wrist",
        "right_wrist",
        "left_hip",
        "right_hip",
        "left_knee",
        "right_knee",
        "left_ankle",
        "right_ankle",
    }
)
HEAD_KEYPOINTS = frozenset({"nose", "left_eye", "right_eye", "left_ear", "right_ear"})


@dataclass(frozen=True, slots=True)
class FeatureConfig:
    """Initial engineering defaults; temporal values are measured in seconds."""

    history_seconds: float = 5.0
    short_window_seconds: float = 0.5
    medium_window_seconds: float = 2.0
    long_window_seconds: float = 5.0
    max_history_samples: int = 2_048
    min_dt_seconds: float = 0.001
    max_dt_seconds: float = 1.0
    minimum_keypoint_confidence: float = 0.35
    speed_ema_alpha: float = 0.25
    arm_motion_ema_alpha: float = 0.25
    body_motion_ema_alpha: float = 0.25
    minimum_speed_for_direction: float = 0.10
    track_ttl_seconds: float = 2.0
    interaction_ttl_seconds: float = 2.0
    world_state_interval_seconds: float = 0.25
    minimum_track_age_seconds: float = 0.25


@dataclass(frozen=True, slots=True)
class _TrackSample:
    timestamp_ms: int
    center: Point | None
    height: float | None
    bbox: BoundingBox
    global_points: dict[str, Point]
    local_points: dict[str, Point]
    raw_speed: float | None
    smoothed_speed: float | None
    arm_motion: float | None
    smoothed_arm_motion: float | None
    body_motion: float | None
    smoothed_body_motion: float | None


@dataclass(frozen=True, slots=True)
class _PairSample:
    timestamp_ms: int
    distance: float | None


@dataclass(slots=True)
class _PairHistory:
    samples: deque[_PairSample]
    started_at_ms: int
    last_seen_ms: int


def _ema(current: float | None, previous: float | None, alpha: float) -> float | None:
    if current is None:
        return None
    return current if previous is None else alpha * current + (1.0 - alpha) * previous


def _valid_dt(current_ms: int, previous_ms: int, config: FeatureConfig) -> float | None:
    dt = (current_ms - previous_ms) / 1_000.0
    return dt if config.min_dt_seconds <= dt <= config.max_dt_seconds else None


def _normalized_motion(
    current: Point | None, previous: Point | None, scale: float | None, dt: float | None
) -> float | None:
    displacement = euclidean_distance(current, previous)
    if displacement is None or scale is None or scale <= 0.0 or dt is None:
        return None
    value = displacement / scale / dt
    return value if isfinite(value) else None


def _local_points(person: TrackedPerson, confidence: float) -> dict[str, Point]:
    points = _valid_points(person, confidence)
    torso = [point for name, point in points.items() if name in TORSO_KEYPOINTS]
    if len(torso) < 2:
        return {}
    torso_x = safe_mean(point[0] for point in torso)
    torso_y = safe_mean(point[1] for point in torso)
    if torso_x is None or torso_y is None:
        return {}
    return {name: (point[0] - torso_x, point[1] - torso_y) for name, point in points.items()}


def _valid_points(person: TrackedPerson, confidence: float) -> dict[str, Point]:
    return {
        point.name: (point.x, point.y)
        for point in person.pose.points
        if (point.confidence is None or point.confidence >= confidence)
        and isfinite(point.x)
        and isfinite(point.y)
    }


def _mean_local_motion(
    current: dict[str, Point],
    previous: dict[str, Point],
    names: frozenset[str],
    scale: float | None,
    dt: float | None,
) -> float | None:
    return safe_mean(
        _normalized_motion(current.get(name), previous.get(name), scale, dt) for name in names
    )


class TemporalFeaturePipeline:
    """Concrete `contracts.FeaturePipeline` implementation.

    Global motion uses bbox centers consistently. Speeds are body-heights/second; local wrist and
    body motion use torso-relative keypoints in body-heights/second. Pair distance has body-heights
    units, and bbox overlap is IoU in [0, 1].
    """

    def __init__(self, config: FeatureConfig | None = None) -> None:
        self.config = config or FeatureConfig()
        self._tracks: dict[int, deque[_TrackSample]] = {}
        self._track_first_seen_ms: dict[int, int] = {}
        self._track_last_seen_ms: dict[int, int] = {}
        self._pairs: dict[tuple[int, int], _PairHistory] = {}
        self._last_emitted_ms: int | None = None

    def update(self, frame: PerceptionFrame) -> WorldState | None:
        """Absorb one frame and emit an interval-limited temporal state when ready."""
        timestamp_ms = frame.timestamp_ms
        active = {person.track_id: person for person in frame.persons}
        self._expire(timestamp_ms)
        samples: dict[int, _TrackSample] = {}
        for track_id in sorted(active):
            sample = self._update_track(active[track_id], timestamp_ms)
            samples[track_id] = sample
        interactions = self._update_pairs(active, samples, timestamp_ms)
        if not self._ready_to_emit(timestamp_ms):
            return None
        people = tuple(
            self._person_features(track_id, samples[track_id], timestamp_ms)
            for track_id in sorted(samples)
        )
        window_start = max(0, timestamp_ms - int(self.config.long_window_seconds * 1_000))
        self._last_emitted_ms = timestamp_ms
        return WorldState(
            source_id=frame.source_id,
            observed_at_ms=timestamp_ms,
            window_start_ms=window_start,
            window_end_ms=timestamp_ms,
            people=people,
            interactions=tuple(interactions),
        )

    def _update_track(self, person: TrackedPerson, timestamp_ms: int) -> _TrackSample:
        track_id = person.track_id
        history = self._tracks.setdefault(track_id, deque(maxlen=self.config.max_history_samples))
        previous = history[-1] if history else None
        if previous is None or _valid_dt(timestamp_ms, previous.timestamp_ms, self.config) is None:
            history.clear()
            previous = None
            self._track_first_seen_ms[track_id] = timestamp_ms
        elif track_id not in self._track_first_seen_ms:
            self._track_first_seen_ms[track_id] = timestamp_ms
        center = bounding_box_center(person.bounding_box)
        height = bounding_box_height(person.bounding_box)
        dt = _valid_dt(timestamp_ms, previous.timestamp_ms, self.config) if previous else None
        scale = safe_mean((height, previous.height)) if previous else None
        raw_speed = _normalized_motion(center, previous.center if previous else None, scale, dt)
        smoothed_speed = _ema(
            raw_speed, previous.smoothed_speed if previous else None, self.config.speed_ema_alpha
        )
        local = _local_points(person, self.config.minimum_keypoint_confidence)
        arm_motion = _mean_local_motion(
            local, previous.local_points if previous else {}, ARM_KEYPOINTS, scale, dt
        )
        body_motion = _mean_local_motion(
            local, previous.local_points if previous else {}, BODY_KEYPOINTS, scale, dt
        )
        sample = _TrackSample(
            timestamp_ms=timestamp_ms,
            center=center,
            height=height,
            bbox=person.bounding_box,
            global_points=_valid_points(person, self.config.minimum_keypoint_confidence),
            local_points=local,
            raw_speed=raw_speed,
            smoothed_speed=smoothed_speed,
            arm_motion=arm_motion,
            smoothed_arm_motion=_ema(
                arm_motion,
                previous.smoothed_arm_motion if previous else None,
                self.config.arm_motion_ema_alpha,
            ),
            body_motion=body_motion,
            smoothed_body_motion=_ema(
                body_motion,
                previous.smoothed_body_motion if previous else None,
                self.config.body_motion_ema_alpha,
            ),
        )
        history.append(sample)
        self._track_last_seen_ms[track_id] = timestamp_ms
        self._prune_history(history, timestamp_ms)
        return sample

    def _person_features(
        self, track_id: int, sample: _TrackSample, timestamp_ms: int
    ) -> PersonFeatures:
        age_ms = timestamp_ms - self._track_first_seen_ms[track_id]
        if age_ms < self.config.minimum_track_age_seconds * 1_000:
            return PersonFeatures(track_id=track_id)
        previous = self._tracks[track_id][-2] if len(self._tracks[track_id]) > 1 else None
        dt = (
            _valid_dt(sample.timestamp_ms, previous.timestamp_ms, self.config) if previous else None
        )
        acceleration = (
            (sample.smoothed_arm_motion - previous.smoothed_arm_motion) / dt
            if dt is not None
            and sample.smoothed_arm_motion is not None
            and previous is not None
            and previous.smoothed_arm_motion is not None
            else None
        )
        return PersonFeatures(
            track_id=track_id,
            body_speed=sample.smoothed_speed,
            wrist_speed=sample.smoothed_arm_motion,
            wrist_acceleration=(
                acceleration if acceleration is None or isfinite(acceleration) else None
            ),
            motion_intensity=sample.smoothed_body_motion,
        )

    def _update_pairs(
        self, people: dict[int, TrackedPerson], samples: dict[int, _TrackSample], timestamp_ms: int
    ) -> list[InteractionFeatures]:
        track_ids = sorted(people)
        interactions: list[InteractionFeatures] = []
        for index, first_id in enumerate(track_ids):
            for second_id in track_ids[index + 1 :]:
                first, second = samples[first_id], samples[second_id]
                distance = _normalized_motion(
                    first.center, second.center, safe_mean((first.height, second.height)), 1.0
                )
                key = (first_id, second_id)
                pair = self._pairs.get(key)
                if pair is None or _valid_dt(timestamp_ms, pair.last_seen_ms, self.config) is None:
                    pair = _PairHistory(
                        deque(maxlen=self.config.max_history_samples), timestamp_ms, timestamp_ms
                    )
                    self._pairs[key] = pair
                pair.samples.append(_PairSample(timestamp_ms, distance))
                pair.last_seen_ms = timestamp_ms
                self._prune_pair_history(pair, timestamp_ms)
                interactions.append(
                    InteractionFeatures(
                        first_track_id=first_id,
                        second_track_id=second_id,
                        distance_between_people=distance,
                        wrist_to_head_distance=self._wrist_to_points(first, second, HEAD_KEYPOINTS),
                        wrist_to_torso_distance=self._wrist_to_points(
                            first, second, TORSO_KEYPOINTS
                        ),
                        bbox_overlap=bounding_box_iou(first.bbox, second.bbox),
                        interaction_duration_ms=timestamp_ms - pair.started_at_ms,
                    )
                )
        return interactions

    def _wrist_to_points(
        self, origin: _TrackSample, target: _TrackSample, target_names: frozenset[str]
    ) -> float | None:
        wrists = [
            point
            for name, point in origin.global_points.items()
            if name in {"left_wrist", "right_wrist"}
        ]
        targets = [point for name, point in target.global_points.items() if name in target_names]
        scale = safe_mean((origin.height, target.height))
        if not wrists or not targets or scale is None or scale <= 0.0:
            return None
        distances = [
            distance / scale
            for wrist in wrists
            for point in targets
            if (distance := euclidean_distance(wrist, point)) is not None
        ]
        return min(distances) if distances else None

    def _ready_to_emit(self, timestamp_ms: int) -> bool:
        if self._last_emitted_ms is None:
            return True
        return (
            timestamp_ms - self._last_emitted_ms
            >= self.config.world_state_interval_seconds * 1_000
        )

    def _expire(self, timestamp_ms: int) -> None:
        expired_tracks = [
            track_id
            for track_id, last_seen in self._track_last_seen_ms.items()
            if timestamp_ms - last_seen > self.config.track_ttl_seconds * 1_000
        ]
        for track_id in expired_tracks:
            self._tracks.pop(track_id, None)
            self._track_first_seen_ms.pop(track_id, None)
            self._track_last_seen_ms.pop(track_id, None)
        expired_pairs = [
            key
            for key, pair in self._pairs.items()
            if timestamp_ms - pair.last_seen_ms > self.config.interaction_ttl_seconds * 1_000
            or key[0] in expired_tracks
            or key[1] in expired_tracks
        ]
        for key in expired_pairs:
            self._pairs.pop(key, None)

    def _prune_history(self, history: deque[_TrackSample], timestamp_ms: int) -> None:
        cutoff = timestamp_ms - int(self.config.history_seconds * 1_000)
        while history and history[0].timestamp_ms < cutoff:
            history.popleft()

    def _prune_pair_history(self, pair: _PairHistory, timestamp_ms: int) -> None:
        cutoff = timestamp_ms - int(self.config.history_seconds * 1_000)
        while pair.samples and pair.samples[0].timestamp_ms < cutoff:
            pair.samples.popleft()
