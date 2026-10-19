# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

from datetime import datetime, timedelta, timezone

from colab_cli import t4_usage


def _tracker(monkeypatch, tmp_path):
    path = tmp_path / "usage.json"
    monkeypatch.setattr(t4_usage, "t4_usage_path", lambda profile: str(path))
    return t4_usage.T4UsageTracker("account1")


def test_t4_usage_tracks_interval_and_remaining(monkeypatch, tmp_path):
    tracker = _tracker(monkeypatch, tmp_path)
    start = datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=90)

    tracker.start("endpoint-1", "render", when=start)
    tracker.stop("endpoint-1", when=end)
    snap = tracker.snapshot(when=end)

    assert snap["used_seconds"] == 90 * 60
    assert snap["remaining_seconds"] == t4_usage.DAILY_T4_ALLOWANCE_SECONDS - 90 * 60
    assert snap["active_t4_sessions"] == 0


def test_t4_usage_active_session_accrues_without_polling(monkeypatch, tmp_path):
    tracker = _tracker(monkeypatch, tmp_path)
    start = datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)
    now = start + timedelta(minutes=30)

    tracker.start("endpoint-1", "render", when=start)
    snap = tracker.snapshot(when=now)

    assert snap["used_seconds"] == 30 * 60
    assert snap["active_t4_sessions"] == 1


def test_t4_usage_splits_across_local_midnight(monkeypatch, tmp_path):
    tracker = _tracker(monkeypatch, tmp_path)
    tz = timezone(timedelta(hours=5, minutes=30))
    start = datetime(2026, 10, 18, 23, 30, tzinfo=tz)
    end = datetime(2026, 10, 19, 0, 30, tzinfo=tz)

    tracker.start("endpoint-1", "overnight", when=start)
    tracker.stop("endpoint-1", when=end)

    snap = tracker.snapshot(when=end)
    assert snap["used_seconds"] == 30 * 60


def test_t4_usage_remaining_never_goes_negative(monkeypatch, tmp_path):
    tracker = _tracker(monkeypatch, tmp_path)
    start = datetime(2026, 10, 19, 8, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=6)

    tracker.start("endpoint-1", "long", when=start)
    tracker.stop("endpoint-1", when=end)
    snap = tracker.snapshot(when=end)

    assert snap["remaining_seconds"] == 0
