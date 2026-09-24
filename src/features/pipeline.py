"""Deterministic, bounded temporal feature extraction from perception contracts.

Initial engineering defaults below require calibration with recorded camera data. Skeleton-scale
normalization reduces, but does not remove, perspective effects. Bbox IoU is visual overlap, not
physical contact; normalized 2D distance is not physical distance. Pose confidence degrades under
occlusion, track IDs can switch, and local pose motion remains sensitive to detector noise.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from itertools import pairwise
from math import isfinite
from statistics import median

from contracts import InteractionFeatures, PerceptionFrame, PersonFeatures, WorldState
from contracts.perception import BoundingBox, TrackedPerson

from .geometry import (
    Point,
    bounding_box_height,
    bounding_box_iou,
    bounding_box_width,
    euclidean_distance,
    safe_mean,
)

TORSO_KEYPOINTS = frozenset({"left_shoulder", "right_shoulder", "left_hip", "right_hip"})
ARM_KEYPOINTS = frozenset({"left_elbow", "right_elbow", "left_wrist", "right_wrist"})
WRIST_KEYPOINTS = frozenset({"left_wrist", "right_wrist"})
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
SKELETON_BODY_SCALE_FACTORS = {
    # Approximate each visible segment as a fraction of standing body height. The median of all
    # available estimates makes the scale usable when legs or the lower bounding box are cropped.
    "torso_length": 2.5,
    "shoulder_width": 10.0 / 3.0,
    "hip_width": 5.0,
    "left_upper_arm": 4.472135955,
    "right_upper_arm": 4.472135955,
    "left_forearm": 4.8507125,
    "right_forearm": 4.8507125,
}


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
    minimum_interaction_track_age_seconds: float = 0.50
    minimum_pair_observation_seconds: float = 0.15
    interaction_window_seconds: float = 2.0
    rapid_approach_window_seconds: float = 0.75
    rapid_approach_speed_threshold: float = 0.50
    interaction_proximity_threshold: float = 1.50
    head_contact_distance_threshold: float = 0.28
    torso_contact_distance_threshold: float = 0.22
    aggressive_arm_speed_threshold: float = 1.50
    torso_arm_speed_threshold: float = 2.10
    contact_approach_speed_threshold: float = 0.80
    torso_approach_speed_threshold: float = 1.10
    interaction_scale_ratio_threshold: float = 0.70
    repeated_motion_min_peaks: int = 2
    fallen_bbox_aspect_ratio: float = 0.90


@dataclass(frozen=True, slots=True)
class _TrackSample:
    timestamp_ms: int
    center: Point | None
    height: float | None
    body_scale: float | None
    bbox: BoundingBox
    global_points: dict[str, Point]
    local_points: dict[str, Point]
    raw_speed: float | None
    smoothed_speed: float | None
    arm_motion: float | None
    wrist_motion: dict[str, float]
    pose_scales: dict[str, float]
    smoothed_arm_motion: float | None
    body_motion: float | None
    smoothed_body_motion: float | None


@dataclass(frozen=True, slots=True)
class _WristTargetSample:
    name: str
    motion: float | None
    head_distance: float | None
    torso_distance: float | None


@dataclass(frozen=True, slots=True)
class _PairSample:
    timestamp_ms: int
    distance: float | None
    first_to_second: tuple[_WristTargetSample, ...]
    second_to_first: tuple[_WristTargetSample, ...]
    bbox_overlap: float | None
    scale_compatible: bool | None


@dataclass(frozen=True, slots=True)
class _ContactEvidence:
    first_head: bool | None
    first_torso: bool | None
    second_head: bool | None
    second_torso: bool | None


@dataclass(slots=True)
class _PairHistory:
    samples: deque[_PairSample]
    started_at_ms: int
    last_seen_ms: int
    close_started_at_ms: int | None = None


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


def _midpoint(first: Point | None, second: Point | None) -> Point | None:
    if first is None or second is None:
        return None
    return ((first[0] + second[0]) / 2.0, (first[1] + second[1]) / 2.0)


def _pose_scales(points: dict[str, Point]) -> dict[str, float]:
    """Return comparable body segments, retaining useful scale for partially visible people."""

    shoulders = _midpoint(points.get("left_shoulder"), points.get("right_shoulder"))
    hips = _midpoint(points.get("left_hip"), points.get("right_hip"))
    candidates = {
        "torso_length": euclidean_distance(shoulders, hips),
        "shoulder_width": euclidean_distance(
            points.get("left_shoulder"), points.get("right_shoulder")
        ),
        "hip_width": euclidean_distance(points.get("left_hip"), points.get("right_hip")),
        "left_upper_arm": euclidean_distance(
            points.get("left_shoulder"), points.get("left_elbow")
        ),
        "right_upper_arm": euclidean_distance(
            points.get("right_shoulder"), points.get("right_elbow")
        ),
        "left_forearm": euclidean_distance(points.get("left_elbow"), points.get("left_wrist")),
        "right_forearm": euclidean_distance(
            points.get("right_elbow"), points.get("right_wrist")
        ),
    }
    return {
        name: value
        for name, value in candidates.items()
        if value is not None and value > 0.0 and isfinite(value)
    }


def _skeleton_center(points: dict[str, Point]) -> Point | None:
    """Return a crop-resistant body center from torso anchors or other visible body points."""

    torso = [point for name, point in points.items() if name in TORSO_KEYPOINTS]
    candidates = torso if len(torso) >= 2 else list(points.values())
    center_x = safe_mean(point[0] for point in candidates)
    center_y = safe_mean(point[1] for point in candidates)
    if center_x is None or center_y is None:
        return None
    return (center_x, center_y)


def _estimated_body_scale(scales: dict[str, float]) -> float | None:
    """Estimate full-body image scale from whichever reliable skeleton segments are visible."""

    estimates = [
        value * SKELETON_BODY_SCALE_FACTORS[name]
        for name, value in scales.items()
        if name in SKELETON_BODY_SCALE_FACTORS
    ]
    return float(median(estimates)) if estimates else None


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


def _finite_min(values: list[float | None]) -> float | None:
    available = [value for value in values if value is not None and isfinite(value)]
    return min(available) if available else None


def _finite_max(values: list[float | None]) -> float | None:
    available = [value for value in values if value is not None and isfinite(value)]
    return max(available) if available else None


class TemporalFeaturePipeline:
    """Concrete `contracts.FeaturePipeline` implementation.

    Global motion uses skeleton centers and skeleton-derived scale. Speeds are estimated
    body-scales per second; local wrist and body motion use torso-relative keypoints in the same
    units. Pair distance is skeleton-scale normalized, and bbox overlap is IoU in [0, 1].
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
        height = bounding_box_height(person.bounding_box)
        global_points = _valid_points(person, self.config.minimum_keypoint_confidence)
        center = _skeleton_center(global_points)
        pose_scales = _pose_scales(global_points)
        body_scale = _estimated_body_scale(pose_scales)
        dt = _valid_dt(timestamp_ms, previous.timestamp_ms, self.config) if previous else None
        scale = safe_mean((body_scale, previous.body_scale)) if previous else None
        raw_speed = _normalized_motion(center, previous.center if previous else None, scale, dt)
        smoothed_speed = _ema(
            raw_speed, previous.smoothed_speed if previous else None, self.config.speed_ema_alpha
        )
        local = _local_points(person, self.config.minimum_keypoint_confidence)
        arm_motion = _mean_local_motion(
            local, previous.local_points if previous else {}, ARM_KEYPOINTS, scale, dt
        )
        wrist_motion = {
            name: motion
            for name in WRIST_KEYPOINTS
            if (
                motion := _normalized_motion(
                    local.get(name),
                    previous.local_points.get(name) if previous else None,
                    scale,
                    dt,
                )
            )
            is not None
        }
        body_motion = _mean_local_motion(
            local, previous.local_points if previous else {}, BODY_KEYPOINTS, scale, dt
        )
        sample = _TrackSample(
            timestamp_ms=timestamp_ms,
            center=center,
            height=height,
            body_scale=body_scale,
            bbox=person.bounding_box,
            global_points=global_points,
            local_points=local,
            raw_speed=raw_speed,
            smoothed_speed=smoothed_speed,
            arm_motion=arm_motion,
            wrist_motion=wrist_motion,
            pose_scales=pose_scales,
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
        cutoff = timestamp_ms - int(self.config.interaction_window_seconds * 1_000)
        recent = [item for item in self._tracks[track_id] if item.timestamp_ms >= cutoff]
        accelerations: list[float | None] = []
        for previous, current in pairwise(recent):
            dt = _valid_dt(current.timestamp_ms, previous.timestamp_ms, self.config)
            if dt is None or current.arm_motion is None or previous.arm_motion is None:
                accelerations.append(None)
            else:
                accelerations.append(abs(current.arm_motion - previous.arm_motion) / dt)
        return PersonFeatures(
            track_id=track_id,
            body_speed=_finite_max([item.smoothed_speed for item in recent]),
            wrist_speed=_finite_max([item.arm_motion for item in recent]),
            wrist_acceleration=_finite_max(accelerations),
            motion_intensity=_finite_max([item.body_motion for item in recent]),
            person_fallen=self._person_fallen(sample),
        )

    def _person_fallen(self, sample: _TrackSample) -> bool | None:
        shoulders = [
            sample.global_points.get(name) for name in ("left_shoulder", "right_shoulder")
        ]
        hips = [sample.global_points.get(name) for name in ("left_hip", "right_hip")]
        if any(point is None for point in (*shoulders, *hips)):
            return None
        shoulder_x = safe_mean(point[0] for point in shoulders if point is not None)
        shoulder_y = safe_mean(point[1] for point in shoulders if point is not None)
        hip_x = safe_mean(point[0] for point in hips if point is not None)
        hip_y = safe_mean(point[1] for point in hips if point is not None)
        width = bounding_box_width(sample.bbox)
        height = bounding_box_height(sample.bbox)
        if None in {shoulder_x, shoulder_y, hip_x, hip_y, width, height}:
            return None
        assert shoulder_x is not None and shoulder_y is not None
        assert hip_x is not None and hip_y is not None and width is not None and height is not None
        torso_is_horizontal = abs(shoulder_x - hip_x) > abs(shoulder_y - hip_y)
        box_is_horizontal = width / height >= self.config.fallen_bbox_aspect_ratio
        return torso_is_horizontal and box_is_horizontal

    def _update_pairs(
        self, people: dict[int, TrackedPerson], samples: dict[int, _TrackSample], timestamp_ms: int
    ) -> list[InteractionFeatures]:
        track_ids = sorted(people)
        interactions: list[InteractionFeatures] = []
        for index, first_id in enumerate(track_ids):
            for second_id in track_ids[index + 1 :]:
                key = (first_id, second_id)
                minimum_age_ms = self.config.minimum_interaction_track_age_seconds * 1_000
                if (
                    timestamp_ms - self._track_first_seen_ms[first_id] < minimum_age_ms
                    or timestamp_ms - self._track_first_seen_ms[second_id] < minimum_age_ms
                ):
                    self._pairs.pop(key, None)
                    continue
                first, second = samples[first_id], samples[second_id]
                scale_compatible = self._scale_compatible(first, second)
                if scale_compatible is not True:
                    self._pairs.pop(key, None)
                    continue
                distance = _normalized_motion(
                    first.center,
                    second.center,
                    safe_mean((first.body_scale, second.body_scale)),
                    1.0,
                )
                first_to_second = self._wrist_target_samples(first, second)
                second_to_first = self._wrist_target_samples(second, first)
                overlap = bounding_box_iou(first.bbox, second.bbox)
                pair = self._pairs.get(key)
                if pair is None or _valid_dt(timestamp_ms, pair.last_seen_ms, self.config) is None:
                    pair = _PairHistory(
                        deque(maxlen=self.config.max_history_samples), timestamp_ms, timestamp_ms
                    )
                    self._pairs[key] = pair
                if distance is not None and distance <= self.config.interaction_proximity_threshold:
                    if pair.close_started_at_ms is None:
                        pair.close_started_at_ms = timestamp_ms
                else:
                    pair.close_started_at_ms = None
                pair.samples.append(
                    _PairSample(
                        timestamp_ms,
                        distance,
                        first_to_second,
                        second_to_first,
                        overlap,
                        scale_compatible,
                    )
                )
                pair.last_seen_ms = timestamp_ms
                self._prune_pair_history(pair, timestamp_ms)
                if (
                    timestamp_ms - pair.started_at_ms
                    < self.config.minimum_pair_observation_seconds * 1_000
                ):
                    continue
                recent = self._recent_pair_samples(pair, timestamp_ms)
                interactions.append(
                    InteractionFeatures(
                        first_track_id=first_id,
                        second_track_id=second_id,
                        distance_between_people=distance,
                        rapid_approach=self._rapid_approach(pair, timestamp_ms),
                        wrist_to_head_distance=_finite_min(
                            [
                                distance
                                for item in recent
                                for direction in (item.first_to_second, item.second_to_first)
                                for wrist in direction
                                for distance in (wrist.head_distance,)
                            ]
                        ),
                        wrist_to_torso_distance=_finite_min(
                            [
                                distance
                                for item in recent
                                for direction in (item.first_to_second, item.second_to_first)
                                for wrist in direction
                                for distance in (wrist.torso_distance,)
                            ]
                        ),
                        bbox_overlap=_finite_max([item.bbox_overlap for item in recent]),
                        possible_contact=self._possible_contact(recent),
                        interaction_duration_ms=(
                            timestamp_ms - pair.close_started_at_ms
                            if pair.close_started_at_ms is not None
                            else None
                        ),
                        repeated_aggressive_motion=self._repeated_aggressive_motion(recent),
                    )
                )
        return interactions

    def _recent_pair_samples(
        self, pair: _PairHistory, timestamp_ms: int
    ) -> list[_PairSample]:
        cutoff = timestamp_ms - int(self.config.interaction_window_seconds * 1_000)
        return [sample for sample in pair.samples if sample.timestamp_ms >= cutoff]

    def _rapid_approach(self, pair: _PairHistory, timestamp_ms: int) -> bool | None:
        cutoff = timestamp_ms - int(self.config.rapid_approach_window_seconds * 1_000)
        samples = [
            sample
            for sample in pair.samples
            if sample.timestamp_ms >= cutoff
            and sample.distance is not None
            and sample.scale_compatible is True
        ]
        if len(samples) < 2:
            return None
        elapsed = (samples[-1].timestamp_ms - samples[0].timestamp_ms) / 1_000.0
        if elapsed <= 0.0:
            return None
        assert samples[0].distance is not None and samples[-1].distance is not None
        approach_speed = (samples[0].distance - samples[-1].distance) / elapsed
        return (
            approach_speed >= self.config.rapid_approach_speed_threshold
            and samples[-1].distance <= self.config.interaction_proximity_threshold
        )

    def _possible_contact(self, samples: list[_PairSample]) -> bool | None:
        evidence = [
            self._contact_evidence(previous, current) for previous, current in pairwise(samples)
        ]
        if any(item.first_head is True or item.second_head is True for item in evidence):
            return True
        torso_peaks = 0
        torso_was_high = False
        for item in evidence:
            torso_is_high = item.first_torso is True or item.second_torso is True
            if torso_is_high and not torso_was_high:
                torso_peaks += 1
            torso_was_high = torso_is_high
        # One smooth torso reach is too ambiguous: hugs and greetings routinely produce it.
        # Repeated forceful entries remain contact evidence even without a head-directed motion.
        if torso_peaks >= self.config.repeated_motion_min_peaks:
            return True
        measured = any(
            value is not None
            for item in evidence
            for value in (
                item.first_head,
                item.first_torso,
                item.second_head,
                item.second_torso,
            )
        )
        return False if measured else None

    def _contact_evidence(
        self, previous: _PairSample, current: _PairSample
    ) -> _ContactEvidence:
        """Correlate each wrist with its own direction and target region across two frames."""

        dt = _valid_dt(current.timestamp_ms, previous.timestamp_ms, self.config)
        if dt is None or previous.scale_compatible is not True or current.scale_compatible is not True:
            return _ContactEvidence(None, None, None, None)
        results: list[tuple[bool | None, bool | None]] = []
        for previous_direction, current_direction in (
            (previous.first_to_second, current.first_to_second),
            (previous.second_to_first, current.second_to_first),
        ):
            previous_by_name = {wrist.name: wrist for wrist in previous_direction}
            head_measured = False
            torso_measured = False
            head_contact = False
            torso_contact = False
            for wrist in current_direction:
                previous_wrist = previous_by_name.get(wrist.name)
                if previous_wrist is None or wrist.motion is None:
                    continue
                if previous_wrist.head_distance is not None and wrist.head_distance is not None:
                    head_measured = True
                    head_approach = (previous_wrist.head_distance - wrist.head_distance) / dt
                    head_contact = head_contact or (
                        wrist.motion >= self.config.aggressive_arm_speed_threshold
                        and wrist.head_distance <= self.config.head_contact_distance_threshold
                        and head_approach >= self.config.contact_approach_speed_threshold
                    )
                if previous_wrist.torso_distance is not None and wrist.torso_distance is not None:
                    torso_measured = True
                    torso_approach = (
                        previous_wrist.torso_distance - wrist.torso_distance
                    ) / dt
                    torso_contact = torso_contact or (
                        wrist.motion >= self.config.torso_arm_speed_threshold
                        and wrist.torso_distance <= self.config.torso_contact_distance_threshold
                        and torso_approach >= self.config.torso_approach_speed_threshold
                    )
            results.append(
                (
                    head_contact if head_measured else None,
                    torso_contact if torso_measured else None,
                )
            )
        while len(results) < 2:
            results.append((None, None))
        return _ContactEvidence(
            first_head=results[0][0],
            first_torso=results[0][1],
            second_head=results[1][0],
            second_torso=results[1][1],
        )

    def _repeated_aggressive_motion(self, samples: list[_PairSample]) -> bool | None:
        evidence = [
            self._contact_evidence(previous, current)
            for previous, current in pairwise(samples)
        ]
        contacts = [
            any(value is True for value in (item.first_head, item.first_torso, item.second_head, item.second_torso))
            for item in evidence
            if any(
                value is not None
                for value in (
                    item.first_head,
                    item.first_torso,
                    item.second_head,
                    item.second_torso,
                )
            )
        ]
        if len(contacts) < 2:
            return None
        peaks = 0
        was_high = False
        for is_high in contacts:
            if is_high is None:
                continue
            if is_high and not was_high:
                peaks += 1
            was_high = is_high
        return peaks >= self.config.repeated_motion_min_peaks

    def _wrist_target_samples(
        self, origin: _TrackSample, target: _TrackSample
    ) -> tuple[_WristTargetSample, ...]:
        scale = safe_mean((origin.body_scale, target.body_scale))
        if scale is None or scale <= 0.0:
            return ()
        heads = [point for name, point in target.global_points.items() if name in HEAD_KEYPOINTS]
        torso = [point for name, point in target.global_points.items() if name in TORSO_KEYPOINTS]
        return tuple(
            _WristTargetSample(
                name=name,
                motion=origin.wrist_motion.get(name),
                head_distance=self._point_to_targets(point, heads, scale),
                torso_distance=self._point_to_targets(point, torso, scale),
            )
            for name, point in origin.global_points.items()
            if name in WRIST_KEYPOINTS
        )

    def _scale_compatible(
        self, first: _TrackSample, second: _TrackSample
    ) -> bool | None:
        """Compare only homologous skeleton segments, never cropped bounding-box height."""

        ratios = {
            name: min(first_value, second.pose_scales[name])
            / max(first_value, second.pose_scales[name])
            for name, first_value in first.pose_scales.items()
            if name in second.pose_scales
        }
        if not ratios:
            return None
        threshold = self.config.interaction_scale_ratio_threshold
        # Torso and shoulder measurements remain useful when legs or half the box are cropped.
        if any(ratios.get(name, 0.0) >= threshold for name in ("shoulder_width", "torso_length")):
            return True
        limb_ratios = [
            value
            for name, value in ratios.items()
            if name not in {"shoulder_width", "torso_length", "hip_width"}
        ]
        if len(limb_ratios) >= 2:
            return median(limb_ratios) >= threshold
        if "hip_width" in ratios:
            return ratios["hip_width"] >= threshold
        return None

    @staticmethod
    def _point_to_targets(point: Point, targets: list[Point], scale: float) -> float | None:
        distances = [
            distance / scale
            for target in targets
            if (distance := euclidean_distance(point, target)) is not None
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
