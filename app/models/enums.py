import enum


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    SCRIPTING = "scripting"
    STORYBOARD = "storyboard"
    PRODUCING = "producing"
    REVIEWING = "reviewing"
    READY_TO_PUBLISH = "ready_to_publish"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ShotStatus(str, enum.Enum):
    PENDING = "pending"
    PROMPT_READY = "prompt_ready"
    GENERATING = "generating"
    GENERATED = "generated"
    REVIEW_FAILED = "review_failed"
    APPROVED = "approved"
    LOCKED = "locked"


class AssetTaskStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    NEEDS_RETRY = "needs_retry"
    CANCELLED = "cancelled"
    NEEDS_HUMAN_REVISION = "needs_human_revision"


class AssetModality(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    VOICE = "voice"
    BGM = "bgm"


class ReviewTargetType(str, enum.Enum):
    PROJECT = "project"
    SHOT = "shot"
    ASSET = "asset"


class ReviewConclusion(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
