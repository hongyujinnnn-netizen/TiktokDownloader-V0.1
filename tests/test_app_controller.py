import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.controllers.app_controller import AppController


def test_analyze_url_detects_profile_video_and_invalid():
    controller = AppController()

    profile = controller.analyze_url("https://www.tiktok.com/@sample_user")
    video = controller.analyze_url("https://www.tiktok.com/@sample_user/video/123456789")
    invalid = controller.analyze_url("https://example.com/not-tiktok")

    assert profile.is_valid is True
    assert profile.is_profile is True
    assert profile.is_video is False

    assert video.is_valid is True
    assert video.is_profile is False
    assert video.is_video is True

    assert invalid.is_valid is False
    assert invalid.is_profile is False
    assert invalid.is_video is False


def test_parse_batch_lines_classifies_duplicates_and_invalid_links():
    controller = AppController()

    result = controller.parse_batch_lines(
        [
            "https://www.tiktok.com/@sample_user/video/111",
            "https://www.tiktok.com/@sample_user/video/111",
            "https://www.tiktok.com/@another_user",
            "not-a-link",
        ]
    )

    assert [task.task_type for task in result.tasks] == ["video", "profile"]
    assert result.duplicate_links == ["https://www.tiktok.com/@sample_user/video/111"]
    assert result.ignored_links == ["not-a-link"]


def test_prepare_pending_batch_applies_per_profile_limit():
    controller = AppController()

    batch = controller.parse_batch_lines(
        [
            "https://www.tiktok.com/@sample_user/video/111",
            "https://www.tiktok.com/@sample_user/video/222",
            "https://www.tiktok.com/@sample_user/video/333",
            "https://www.tiktok.com/@another_user/video/444",
            "https://www.tiktok.com/@profile_owner",
        ]
    )
    controller.set_pending_batch(batch)
    controller.mark_batch_requested()

    prepared = controller.prepare_pending_batch(limit=2)

    assert [task.url for task in prepared.tasks] == [
        "https://www.tiktok.com/@sample_user/video/111",
        "https://www.tiktok.com/@sample_user/video/222",
        "https://www.tiktok.com/@another_user/video/444",
        "https://www.tiktok.com/@profile_owner",
    ]
    assert [task.url for task in prepared.skipped_due_to_limit] == [
        "https://www.tiktok.com/@sample_user/video/333",
    ]
    assert controller.has_pending_batch() is False
