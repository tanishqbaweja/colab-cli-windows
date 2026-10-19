# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""Local T4 allocation-time accounting.

This is intentionally local accounting, not a claim about the service's actual
quota. Each profile gets a fixed 4h30m daily budget for display purposes.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any

import filelock

from colab_cli.profiles import t4_usage_path

DAILY_T4_ALLOWANCE_SECONDS = 4 * 60 * 60 + 30 * 60


def _now() -> datetime:
    return datetime.now().astimezone()


def _parse(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        return dt.astimezone()
    return dt


def _midnight(day, tz) -> datetime:
    return datetime.combine(day, time.min, tzinfo=tz)


class T4UsageTracker:
    def __init__(self, profile: str):
        self.profile = profile
        self.path = Path(t4_usage_path(profile))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = filelock.FileLock(str(self.path) + ".lock")

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "daily_seconds": {}, "active": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            data.setdefault("version", 1)
            data.setdefault("daily_seconds", {})
            data.setdefault("active", {})
            return data
        except Exception:
            return {"version": 1, "daily_seconds": {}, "active": {}}

    def _save(self, data: dict[str, Any]) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.path)

    @staticmethod
    def _record_interval(data: dict[str, Any], start: datetime, end: datetime) -> None:
        if end <= start:
            return
        cursor = start
        tz = start.tzinfo or _now().tzinfo
        while cursor.date() < end.astimezone(tz).date():
            boundary = _midnight(cursor.date() + timedelta(days=1), tz)
            seconds = max(0.0, (boundary - cursor).total_seconds())
            key = cursor.date().isoformat()
            data["daily_seconds"][key] = float(data["daily_seconds"].get(key, 0.0)) + seconds
            cursor = boundary
        seconds = max(0.0, (end.astimezone(tz) - cursor).total_seconds())
        key = cursor.date().isoformat()
        data["daily_seconds"][key] = float(data["daily_seconds"].get(key, 0.0)) + seconds

    def start(self, endpoint: str, session_name: str | None = None, when: datetime | None = None) -> None:
        when = when or _now()
        with self.lock:
            data = self._load()
            if endpoint not in data["active"]:
                data["active"][endpoint] = {
                    "started_at": when.isoformat(),
                    "session_name": session_name,
                    "accelerator": "T4",
                }
                self._save(data)

    def stop(self, endpoint: str, when: datetime | None = None) -> bool:
        when = when or _now()
        with self.lock:
            data = self._load()
            item = data["active"].pop(endpoint, None)
            if not item:
                return False
            self._record_interval(data, _parse(item["started_at"]), when)
            self._save(data)
            return True

    def reconcile(self, assignments) -> None:
        now = _now()
        live_t4 = {
            a.endpoint: getattr(getattr(a, "accelerator", None), "value", None)
            for a in assignments
            if getattr(getattr(a, "accelerator", None), "value", None) == "T4"
        }
        with self.lock:
            data = self._load()
            changed = False
            for endpoint in list(data["active"]):
                if endpoint not in live_t4:
                    item = data["active"].pop(endpoint)
                    self._record_interval(data, _parse(item["started_at"]), now)
                    changed = True
            for endpoint in live_t4:
                if endpoint not in data["active"]:
                    data["active"][endpoint] = {
                        "started_at": now.isoformat(),
                        "session_name": None,
                        "accelerator": "T4",
                    }
                    changed = True
            if changed:
                self._save(data)

    def snapshot(self, when: datetime | None = None) -> dict[str, Any]:
        when = when or _now()
        day = when.date().isoformat()
        with self.lock:
            data = self._load()
            used = float(data["daily_seconds"].get(day, 0.0))
            active_count = 0
            for item in data["active"].values():
                start = _parse(item["started_at"]).astimezone(when.tzinfo)
                if start.date() < when.date():
                    start = _midnight(when.date(), when.tzinfo)
                if start <= when:
                    used += (when - start).total_seconds()
                    active_count += 1
            used = max(0.0, used)
            return {
                "profile": self.profile,
                "date": day,
                "used_seconds": used,
                "remaining_seconds": max(0.0, DAILY_T4_ALLOWANCE_SECONDS - used),
                "allowance_seconds": DAILY_T4_ALLOWANCE_SECONDS,
                "active_t4_sessions": active_count,
            }


def format_duration(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if secs:
        return f"{hours}h {minutes:02d}m {secs:02d}s"
    return f"{hours}h {minutes:02d}m"
