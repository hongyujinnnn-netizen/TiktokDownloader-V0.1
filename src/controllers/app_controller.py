"""
Application controller for UI-to-service coordination.
"""

from pathlib import Path

from src.core.app_models import (
    BatchImportResult,
    BatchPreparationResult,
    BatchTask,
    UrlAnalysis,
)
from src.core.downloader import TikTokDownloader
from src.core.profile_scraper import ProfileScraper
from src.utils.config_manager import ConfigManager
from src.utils.logger import get_logger
from src.utils.validators import is_valid_profile_url, is_valid_tiktok_url, is_valid_video_url


class AppController:
    """Coordinates non-UI application flow for the main window."""

    def __init__(self, config=None, downloader=None, profile_scraper=None):
        self.config = config or ConfigManager()
        self.downloader = downloader or TikTokDownloader()
        self.profile_scraper = profile_scraper or ProfileScraper()
        self.logger = get_logger("AppController")

        self.pending_batch_result = BatchImportResult()
        self.batch_user_requested = False

    def analyze_url(self, url: str | None) -> UrlAnalysis:
        """Classify a URL for UI behavior and download routing."""
        normalized_url = (url or "").strip()
        if not normalized_url:
            return UrlAnalysis(url="", is_valid=False)

        is_video = is_valid_video_url(normalized_url)
        is_profile = is_valid_profile_url(normalized_url) and not is_video
        is_valid = is_profile or is_video or is_valid_tiktok_url(normalized_url)
        return UrlAnalysis(
            url=normalized_url,
            is_valid=is_valid,
            is_profile=is_profile,
            is_video=is_video,
        )

    def load_batch_file(self, file_path: str) -> BatchImportResult:
        """Load and parse batch download links from a text file."""
        path = Path(file_path)
        with path.open("r", encoding="utf-8") as file_handle:
            lines = [line.strip() for line in file_handle if line.strip()]
        return self.parse_batch_lines(lines)

    def parse_batch_lines(self, lines: list[str]) -> BatchImportResult:
        """Parse raw lines into classified batch tasks."""
        tasks: list[BatchTask] = []
        ignored_links: list[str] = []
        duplicate_links: list[str] = []
        seen: set[str] = set()

        for line in lines:
            normalized = line.strip()
            if not normalized:
                continue

            dedupe_key = normalized.lower()
            if dedupe_key in seen:
                duplicate_links.append(normalized)
                continue
            seen.add(dedupe_key)

            analysis = self.analyze_url(normalized)
            if analysis.is_video:
                tasks.append(BatchTask(url=normalized, task_type="video"))
            elif analysis.is_profile:
                tasks.append(BatchTask(url=normalized, task_type="profile"))
            elif analysis.is_valid:
                tasks.append(BatchTask(url=normalized, task_type="video"))
            else:
                ignored_links.append(normalized)

        return BatchImportResult(
            tasks=tasks,
            ignored_links=ignored_links,
            duplicate_links=duplicate_links,
        )

    def set_pending_batch(self, batch_result: BatchImportResult) -> None:
        """Replace the pending batch state with a new result."""
        self.pending_batch_result = batch_result
        self.batch_user_requested = False

    def clear_pending_batch(self) -> None:
        """Clear pending batch state."""
        self.pending_batch_result = BatchImportResult()
        self.batch_user_requested = False

    def has_pending_batch(self) -> bool:
        """Return True when there are queued batch tasks."""
        return bool(self.pending_batch_result.tasks)

    def mark_batch_requested(self) -> None:
        """Mark that the user explicitly requested the queued batch to start."""
        self.batch_user_requested = True

    def prepare_pending_batch(self, limit: int) -> BatchPreparationResult:
        """Consume pending batch items and apply per-profile limits."""
        if not self.pending_batch_result.tasks or not self.batch_user_requested:
            return BatchPreparationResult()

        tasks = list(self.pending_batch_result.tasks)
        ignored_links = list(self.pending_batch_result.ignored_links)
        duplicate_links = list(self.pending_batch_result.duplicate_links)
        self.clear_pending_batch()

        skipped_due_to_limit: list[BatchTask] = []
        if limit > 0:
            tasks, skipped_due_to_limit = self.apply_profile_limit(tasks, limit)

        return BatchPreparationResult(
            tasks=tasks,
            ignored_links=ignored_links,
            duplicate_links=duplicate_links,
            skipped_due_to_limit=skipped_due_to_limit,
        )

    def apply_profile_limit(
        self,
        tasks: list[BatchTask],
        limit: int,
    ) -> tuple[list[BatchTask], list[BatchTask]]:
        """Apply per-profile limits to video tasks while preserving order."""
        counts: dict[str, int] = {}
        kept: list[BatchTask] = []
        skipped: list[BatchTask] = []

        for task in tasks:
            if task.task_type != "video":
                kept.append(task)
                continue

            profile_handle = self._extract_profile_handle(task.url) or "__unknown__"
            current_count = counts.get(profile_handle, 0)
            if current_count >= limit:
                skipped.append(task)
                continue

            counts[profile_handle] = current_count + 1
            kept.append(task)

        return kept, skipped

    def safe_int(self, value, default: int = 0) -> int:
        """Convert a value to int without raising."""
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _extract_profile_handle(self, url: str | None) -> str | None:
        """Extract a TikTok handle from a URL."""
        analysis = self.analyze_url(url)
        if not analysis.url or "@" not in analysis.url:
            return None

        handle = analysis.url.split("@", maxsplit=1)[1]
        for separator in ("/", "?", "#"):
            handle = handle.split(separator, maxsplit=1)[0]

        handle = handle.strip().lower()
        return handle or None
