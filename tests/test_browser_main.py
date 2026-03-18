from __future__ import annotations

import pytest

import minesweeper.__main__ as main_module


def test_parse_mode_accepts_browser_dom() -> None:
    assert main_module.parse_mode("browser-dom") == "browser-dom"


def test_main_routes_browser_dom_mode_to_browser_entrypoint(monkeypatch) -> None:
    recorded: dict[str, object] = {}

    class UnexpectedApp:
        def __init__(self, *_args, **_kwargs) -> None:
            raise AssertionError("local App should not be constructed in browser-dom mode")

    def stub_run_browser_dom(**kwargs):
        recorded.update(kwargs)
        recorded["browser_dom_ran"] = True
        return "no moves available"

    monkeypatch.setattr(main_module, "App", UnexpectedApp)
    monkeypatch.setattr(main_module, "_run_browser_dom", stub_run_browser_dom)

    exit_code = main_module.main(["--mode", "browser-dom", "--verbose"])

    assert exit_code == 0
    assert recorded["output"] is print
    assert recorded["browser_dom_ran"] is True


def test_run_browser_dom_starts_and_stops_http_bridge() -> None:
    events: list[object] = []
    captured_executor = None

    class FakeBridge:
        def register_session(self, session_id: str) -> None:
            events.append(("register", session_id))

        def queue_command(self, session_id: str, command: object) -> None:
            events.append(("queue", session_id, command))

    class FakeHttpServer:
        def __init__(self, bridge: object) -> None:
            events.append(("server_init", bridge))

        def start(self) -> None:
            events.append("start")

        def stop(self) -> None:
            events.append("stop")

    class FakeExecutor:
        def __init__(self, session_id: str, send) -> None:  # noqa: ANN001
            nonlocal captured_executor
            events.append(("executor_init", session_id, send))
            self._send = send
            captured_executor = self

        def execute_batch(self, moves) -> None:  # noqa: ANN001
            self._send(("moves", tuple(moves)))

    class FakeApp:
        def __init__(self, **kwargs) -> None:
            events.append(("app_init", kwargs))
            self._executor = kwargs["executor"]

        def run(self) -> str:
            events.append("run")
            self._executor.execute_batch(["sentinel"])
            return "no moves available"

    result = main_module._run_browser_dom(
        output=print,
        bridge_factory=FakeBridge,
        http_server_factory=FakeHttpServer,
        executor_factory=FakeExecutor,
        app_factory=FakeApp,
    )

    assert result == "no moves available"
    assert "start" in events
    assert "stop" in events
    assert events.index("start") < events.index("stop")
    assert ("register", "browser-dom") in events
    assert any(event == "run" for event in events)
    assert captured_executor is not None
    assert ("queue", "browser-dom", ("moves", ("sentinel",))) in events


def test_main_rejects_browser_dom_with_debug_captures(monkeypatch, capsys) -> None:
    class UnexpectedApp:
        def __init__(self, *_args, **_kwargs) -> None:
            raise AssertionError("local App should not be constructed in browser-dom mode")

    monkeypatch.setattr(main_module, "App", UnexpectedApp)
    monkeypatch.setattr(main_module, "_run_browser_dom", lambda **_kwargs: "no moves available")

    with pytest.raises(SystemExit) as excinfo:
        main_module.main(["--mode", "browser-dom", "--debug-captures", "debug"])

    assert excinfo.value.code == 2
    assert "--debug-captures is not supported with --mode browser-dom" in capsys.readouterr().err


def test_browser_dom_mode_surfaces_clear_startup_error_when_bridge_is_missing(
    monkeypatch, capsys
) -> None:
    class UnexpectedApp:
        def __init__(self, *_args, **_kwargs) -> None:
            raise AssertionError("local App should not be constructed in browser-dom mode")

    monkeypatch.setattr(main_module, "App", UnexpectedApp)
    monkeypatch.setattr(
        main_module,
        "_run_browser_dom",
        lambda **_kwargs: main_module.STOP_REASONS.board_refresh_failed_after_retry,
    )

    with pytest.raises(SystemExit) as excinfo:
        main_module.main(["--mode", "browser-dom"])

    assert excinfo.value.code == 2
    assert (
        "browser-dom mode requires a connected extension session"
        in capsys.readouterr().err
    )
