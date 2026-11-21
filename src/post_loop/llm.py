"""Model callers (D-9).

- `RecordedCaller` answers from `fixtures/recorded.json`, keyed `<agent>:<case>:<pass>`. No network, no key, zero usage.
  The file is hand-written in each agent's output shape; it is not a recording of a live model.
- `AgentSdkCaller` runs one agent turn in a Claude Agent SDK session (`claude_agent_sdk.query`): its own system
  prompt, no built-in tools, structured output, a budget cap. Implemented, **never run in this build**; it refuses to
  construct without `ANTHROPIC_API_KEY`.
- `RecordingCaller` wraps a live caller and writes what it got in the recorded file's shape, so a first live run can
  replace the hand-made responses.
"""

from __future__ import annotations

import json
import os
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from post_loop.fixtures import RECORDED_FILE
from post_loop.prompts import AgentSpec


class ModelCallError(RuntimeError):
    """The caller could not produce a response for this agent turn."""


class NoRecording(ModelCallError):
    """The recorded file has no response for this key."""


class LiveCallRefused(RuntimeError):
    """A live model call was asked for without a key (D-9)."""


@dataclass
class CallResult:
    agent: str
    model: str
    raw: str | dict[str, Any]  # the Critic's raw output is validated by the loop, never trusted here
    input_tokens: int = 0
    output_tokens: int = 0
    sdk_cost_usd: float | None = None
    duration_ms: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class ModelCaller(Protocol):
    name: str
    measured: bool
    calls: Counter[str]

    async def call(self, spec: AgentSpec, user_text: str, key: str) -> CallResult: ...


class RecordedCaller:
    name = "recorded"
    measured = False

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or RECORDED_FILE
        self.responses: dict[str, Any] = json.loads(self.path.read_text(encoding="utf-8"))["responses"]
        self.calls: Counter[str] = Counter()

    def has(self, key: str) -> bool:
        return key in self.responses

    async def call(self, spec: AgentSpec, user_text: str, key: str) -> CallResult:
        if key not in self.responses:
            raise NoRecording(f"no recording for {key!r} in {self.path.name}; live mode needs a key (D-9)")
        self.calls[spec.name] += 1
        return CallResult(agent=spec.name, model=spec.model, raw=self.responses[key], extra={"recorded_key": key})


class AgentSdkCaller:
    name = "claude-agent-sdk"
    measured = True

    def __init__(self, max_budget_usd: float = 10.0) -> None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise LiveCallRefused("ANTHROPIC_API_KEY is not set; this build runs on the recorded path only (D-9).")
        self.max_budget_usd = max_budget_usd
        self.calls: Counter[str] = Counter()

    async def call(self, spec: AgentSpec, user_text: str, key: str) -> CallResult:  # pragma: no cover - never run here
        from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query

        options = ClaudeAgentOptions(
            model=spec.model,
            system_prompt=spec.system_prompt(),
            tools=[],
            allowed_tools=[],
            permission_mode="dontAsk",
            setting_sources=[],
            max_turns=spec.max_turns,
            output_format={"type": "json_schema", "schema": spec.schema},
            max_budget_usd=self.max_budget_usd,
        )
        started = time.monotonic()
        text_parts: list[str] = []
        result: Any = None
        async for message in query(prompt=user_text, options=options):
            if isinstance(message, AssistantMessage):
                text_parts.extend(b.text for b in message.content if isinstance(b, TextBlock))
            elif isinstance(message, ResultMessage):
                result = message
        if result is None or result.is_error:
            raise ModelCallError(f"{spec.name}: the SDK returned no usable result")
        self.calls[spec.name] += 1
        usage = result.usage or {}
        raw: str | dict[str, Any] = result.structured_output if isinstance(result.structured_output, dict) else (
            text_parts[-1] if text_parts else (result.result or ""))
        return CallResult(agent=spec.name, model=spec.model, raw=raw,
                          input_tokens=int(usage.get("input_tokens", 0)) + int(usage.get("cache_read_input_tokens", 0))
                          + int(usage.get("cache_creation_input_tokens", 0)),
                          output_tokens=int(usage.get("output_tokens", 0)), sdk_cost_usd=result.total_cost_usd,
                          duration_ms=int((time.monotonic() - started) * 1000))


class RecordingCaller:  # pragma: no cover - only meaningful with a live caller
    """Wraps a live caller and saves each response under its key, in the recorded file's shape."""

    def __init__(self, inner: ModelCaller, path: Path) -> None:
        self.inner, self.path = inner, path
        self.name, self.measured = f"recording({inner.name})", inner.measured
        self.calls = inner.calls
        self.saved: dict[str, Any] = {}

    async def call(self, spec: AgentSpec, user_text: str, key: str) -> CallResult:
        r = await self.inner.call(spec, user_text, key)
        self.saved[key] = r.raw
        doc = {"_about": "Recorded from a live run (RecordingCaller).", "responses": self.saved}
        self.path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return r
