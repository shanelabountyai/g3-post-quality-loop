from __future__ import annotations

import pytest

from post_loop.layer import Layer


@pytest.fixture()
def layer(tmp_path):
    lay = Layer(db_path=str(tmp_path / "layer.sqlite"))
    yield lay
    lay.close()


@pytest.fixture(autouse=True)
def _no_key(monkeypatch, tmp_path):
    # No test may reach a live model or the owner's real layer file.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("G0_DB_PATH", str(tmp_path / "default-layer.sqlite"))
