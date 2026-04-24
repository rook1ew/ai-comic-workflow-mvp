from collections.abc import Iterable

from app.models.enums import AssetTaskStatus, ProjectStatus, ShotStatus

PROJECT_TRANSITIONS: dict[ProjectStatus, set[ProjectStatus]] = {
    ProjectStatus.DRAFT: {ProjectStatus.APPROVED, ProjectStatus.ARCHIVED},
    ProjectStatus.APPROVED: {ProjectStatus.SCRIPTING, ProjectStatus.ARCHIVED},
    ProjectStatus.SCRIPTING: {ProjectStatus.STORYBOARD, ProjectStatus.ARCHIVED},
    ProjectStatus.STORYBOARD: {ProjectStatus.PRODUCING, ProjectStatus.ARCHIVED},
    ProjectStatus.PRODUCING: {ProjectStatus.REVIEWING, ProjectStatus.ARCHIVED},
    ProjectStatus.REVIEWING: {ProjectStatus.READY_TO_PUBLISH, ProjectStatus.PRODUCING, ProjectStatus.ARCHIVED},
    ProjectStatus.READY_TO_PUBLISH: {ProjectStatus.PUBLISHED, ProjectStatus.ARCHIVED},
    ProjectStatus.PUBLISHED: {ProjectStatus.ARCHIVED},
    ProjectStatus.ARCHIVED: set(),
}

SHOT_TRANSITIONS: dict[ShotStatus, set[ShotStatus]] = {
    ShotStatus.PENDING: {ShotStatus.PROMPT_READY, ShotStatus.LOCKED},
    ShotStatus.PROMPT_READY: {ShotStatus.GENERATING, ShotStatus.LOCKED},
    ShotStatus.GENERATING: {ShotStatus.GENERATED, ShotStatus.REVIEW_FAILED, ShotStatus.LOCKED},
    ShotStatus.GENERATED: {ShotStatus.APPROVED, ShotStatus.REVIEW_FAILED, ShotStatus.LOCKED},
    ShotStatus.REVIEW_FAILED: {ShotStatus.PROMPT_READY, ShotStatus.GENERATING, ShotStatus.LOCKED},
    ShotStatus.APPROVED: {ShotStatus.LOCKED},
    ShotStatus.LOCKED: set(),
}

ASSET_TASK_TRANSITIONS: dict[AssetTaskStatus, set[AssetTaskStatus]] = {
    AssetTaskStatus.QUEUED: {AssetTaskStatus.RUNNING, AssetTaskStatus.CANCELLED},
    AssetTaskStatus.RUNNING: {
        AssetTaskStatus.SUCCEEDED,
        AssetTaskStatus.FAILED,
        AssetTaskStatus.NEEDS_RETRY,
        AssetTaskStatus.NEEDS_HUMAN_REVISION,
        AssetTaskStatus.CANCELLED,
    },
    AssetTaskStatus.SUCCEEDED: set(),
    AssetTaskStatus.FAILED: {AssetTaskStatus.NEEDS_RETRY, AssetTaskStatus.NEEDS_HUMAN_REVISION, AssetTaskStatus.CANCELLED},
    AssetTaskStatus.NEEDS_RETRY: {AssetTaskStatus.RUNNING, AssetTaskStatus.CANCELLED},
    AssetTaskStatus.CANCELLED: set(),
    AssetTaskStatus.NEEDS_HUMAN_REVISION: set(),
}


def ensure_transition(current: ProjectStatus | ShotStatus | AssetTaskStatus, new: ProjectStatus | ShotStatus | AssetTaskStatus, transitions: dict, label: str) -> None:
    if new not in transitions[current]:
        raise ValueError(f"Invalid {label} transition: {current.value} -> {new.value}")


def allowed_transitions(current: ProjectStatus | ShotStatus | AssetTaskStatus, transitions: dict) -> Iterable:
    return transitions[current]
