"""
Shared application models for controller and UI coordination.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class UrlAnalysis:
    """Represents the detected type of a TikTok URL."""

    url: str
    is_valid: bool
    is_profile: bool = False
    is_video: bool = False


@dataclass(frozen=True)
class BatchTask:
    """Single batch download item."""

    url: str
    task_type: str


@dataclass
class BatchImportResult:
    """Outcome of parsing a batch input source."""

    tasks: list[BatchTask] = field(default_factory=list)
    ignored_links: list[str] = field(default_factory=list)
    duplicate_links: list[str] = field(default_factory=list)

    @property
    def video_count(self) -> int:
        return sum(1 for task in self.tasks if task.task_type == "video")

    @property
    def profile_count(self) -> int:
        return sum(1 for task in self.tasks if task.task_type == "profile")


@dataclass
class BatchPreparationResult:
    """Batch items ready to start after controller-level rules are applied."""

    tasks: list[BatchTask] = field(default_factory=list)
    ignored_links: list[str] = field(default_factory=list)
    duplicate_links: list[str] = field(default_factory=list)
    skipped_due_to_limit: list[BatchTask] = field(default_factory=list)
