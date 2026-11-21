"""Load the test data (D-14): `fixtures/cases.json` and `fixtures/recorded.json`."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from post_loop.models import FIXTURES_DIR, Case, CriticVerdict, Source

CASES_FILE = FIXTURES_DIR / "cases.json"
RECORDED_FILE = FIXTURES_DIR / "recorded.json"


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


@dataclass
class Cases:
    notes: dict[str, dict[str, str]]
    cases: list[Case]
    recorded_file: Path

    def by_id(self, case_id: str) -> Case:
        for c in self.cases:
            if c.id == case_id:
                return c
        raise KeyError(f"no case '{case_id}'. Known: {[c.id for c in self.cases]}")

    def by_topic(self, topic: str) -> Case | None:
        want = topic.strip().lower()
        return next((c for c in self.cases if c.topic and c.topic.strip().lower() == want), None)

    def note(self, note_id: str) -> Source:
        n = self.notes[note_id]
        return Source(id=note_id, title=n["title"], text=n["text"])

    def source_for(self, case: Case) -> Source:
        if case.note:
            return self.note(case.note)
        assert case.topic is not None
        return Source(id=slug(case.topic), title=case.topic, text=case.topic)

    def recorded(self, key: str) -> Any:
        return json.loads(self.recorded_file.read_text(encoding="utf-8"))["responses"][key]

    @staticmethod
    def critic_ok() -> CriticVerdict:
        return CriticVerdict.model_validate({"pass": True, "scores": {"claims": 5, "brand": 5, "hook": 5}, "fixes": []})


def load_cases(path: Path | None = None, recorded_file: Path | None = None) -> Cases:
    doc = json.loads((path or CASES_FILE).read_text(encoding="utf-8"))
    return Cases(notes=doc["notes"], cases=[Case.model_validate(c) for c in doc["cases"]], recorded_file=recorded_file or RECORDED_FILE)
