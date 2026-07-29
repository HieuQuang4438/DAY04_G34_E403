"""Streamlit UI for the Day 04 research agent.

Reuses `run_model_tool_loop` and `write_transcript` from chat.py so the UI and the
CLI produce identical transcripts and identical routing behaviour.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    ARTIFACTS_DIR,
    ROOT,
    json_text,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

# run_model_tool_loop prints an emoji per tool call; keep a non-UTF8 console from
# killing the loop mid-turn on Windows.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

RUNS_DIR = ROOT / "runs"
TRANSCRIPTS_DIR = ROOT / "transcripts"
PROVIDERS = ["gemini", "openrouter", "openai", "anthropic"]
MAX_RESULT_CHARS = 4000

STATUS_LABELS = {
    "answered": ("✅", "answered"),
    "waiting_for_user": ("❓", "waiting for user"),
    "max_tool_rounds": ("⚠️", "stopped at max tool rounds"),
    "provider_error": ("🛑", "provider error"),
}


def artifact_choices(pattern: str, fallback: Path) -> list[Path]:
    """Prompt/tool snapshots so one scenario can be replayed across versions."""
    found = sorted(ARTIFACTS_DIR.glob(pattern))
    return found or [fallback]


def session_signature(config: dict[str, Any]) -> str:
    return "|".join(str(config[key]) for key in sorted(config))


def start_session(config: dict[str, Any]) -> dict[str, Any]:
    prompt_path = Path(config["prompt_path"])
    tools_path = Path(config["tools_path"])
    artifact = build_artifact_version(config["version"], prompt_path, tools_path)

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([
        safe_slug(config["version"]),
        safe_slug(config["provider"]),
        timestamp,
    ])
    transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact),
        "provider": config["provider"],
        "model": config["model"],
        "system_prompt": str(prompt_path),
        "tools": str(tools_path),
        "history_window": config["history_window"],
        "max_tool_rounds": config["max_tool_rounds"],
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "surface": "streamlit",
        "turns": [],
    }

    declarations = load_tool_declarations(tools_path)
    return {
        "signature": session_signature(config),
        "config": config,
        "artifact": artifact,
        "system_prompt": prompt_path.read_text(encoding="utf-8"),
        "declarations": declarations,
        "openai_tools": to_openai_tools(declarations),
        "transcript": transcript,
        "transcript_path": TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json",
        "history": [],
    }


def render_tool_event(event: dict[str, Any]) -> None:
    result = event.get("result", {})
    is_error = isinstance(result, dict) and "error" in result
    icon = "🛑" if is_error else "🔧"
    st.markdown(f"{icon} **`{event.get('tool')}`**")
    st.caption("args")
    st.code(json_text(event.get("args", {})), language="json")
    st.caption("error" if is_error else "result")
    st.code(json_text(result, max_chars=MAX_RESULT_CHARS), language="json")


def render_turn(turn: dict[str, Any]) -> None:
    with st.chat_message("user"):
        st.markdown(turn.get("user", ""))

    with st.chat_message("assistant"):
        status = turn.get("status", "unknown")
        icon, label = STATUS_LABELS.get(status, ("•", status))
        rounds = turn.get("rounds", [])
        tool_events = turn.get("tool_events", [])
        st.caption(f"{icon} {label} · {len(rounds)} round(s) · {len(tool_events)} tool call(s)")

        if status == "provider_error":
            st.error(turn.get("error", "provider error"))
        else:
            st.markdown(turn.get("assistant_text") or "_(empty response)_")

        for round_record in rounds:
            names = [call.get("name") for call in round_record.get("tool_calls", [])]
            title = f"Round {round_record.get('round')} — " + (", ".join(names) if names else "no tool call")
            with st.expander(title):
                if round_record.get("assistant_text"):
                    st.markdown(round_record["assistant_text"])
                for event in round_record.get("tool_results", []):
                    render_tool_event(event)
                    st.divider()

        with st.expander("Turn JSON (evidence)"):
            st.code(json_text(turn, max_chars=MAX_RESULT_CHARS), language="json")


def send_turn(session: dict[str, Any], user_text: str) -> None:
    config = session["config"]
    turn_record: dict[str, Any] = {
        "turn_index": len(session["transcript"]["turns"]) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    messages = [
        {"role": "system", "content": session["system_prompt"]},
        *trim_history(session["history"], config["history_window"]),
        {"role": "user", "content": user_text},
    ]

    try:
        provider = make_provider(config["provider"])
        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=session["openai_tools"],
            model=config["model"] or None,
            max_tool_rounds=config["max_tool_rounds"],
        )
        turn_record.update(result)
        session["history"].append({"role": "user", "content": user_text})
        session["history"].append({"role": "assistant", "content": result["assistant_text"]})
    except Exception as exc:
        turn_record.update({
            "status": "provider_error",
            "error": f"{type(exc).__name__}: {exc}",
        })

    turn_record["ended_at"] = now_iso()
    session["transcript"]["turns"].append(turn_record)
    write_transcript(session["transcript_path"], session["transcript"])


def load_run_summaries() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(RUNS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        summary = data.get("summary", {})
        measured = summary.get("measured_cases")
        total = summary.get("total_cases")
        errors = summary.get("provider_error_cases")
        rows.append({
            "run": path.name,
            "version": data.get("version"),
            "suite": data.get("suite"),
            "artifact_version": data.get("artifact_version"),
            "measured": f"{measured}/{total}",
            "provider_errors": errors,
            "case_accuracy": summary.get("case_accuracy"),
            "tool_routing": summary.get("tool_routing_accuracy"),
            "argument": summary.get("argument_accuracy"),
            "multiturn": summary.get("multiturn_accuracy"),
            # README: metrics only count when nothing errored and every case ran.
            "valid": errors == 0 and measured == total,
        })
    return rows


def chat_tab(session: dict[str, Any]) -> None:
    for turn in session["transcript"]["turns"]:
        render_turn(turn)

    user_text = st.chat_input("Ask the research agent…")
    if user_text:
        with st.spinner("Running tool loop…"):
            send_turn(session, user_text.strip())
        st.rerun()


def runs_tab() -> None:
    rows = load_run_summaries()
    if not rows:
        st.info("No run JSON in runs/ yet.")
        return

    st.caption("Metrics are only meaningful when `valid` is true (0 provider errors, every case measured).")
    st.dataframe(rows, width="stretch", hide_index=True)

    selected = st.selectbox("Inspect failures in run", [row["run"] for row in rows], index=len(rows) - 1)
    data = json.loads((RUNS_DIR / selected).read_text(encoding="utf-8"))
    failed = [item for item in data.get("results", []) if not item.get("result", {}).get("passed")]
    st.markdown(f"**{len(failed)} failed case(s)** in `{selected}`")
    for item in failed:
        result = item.get("result", {})
        with st.expander(f"{item.get('id')} — {result.get('observed_mismatch') or result.get('failure_type')}"):
            st.code(json_text(result, max_chars=MAX_RESULT_CHARS), language="json")


def transcripts_tab(session: dict[str, Any]) -> None:
    st.caption(f"Current session writes to `{session['transcript_path'].name}`")
    paths = sorted(TRANSCRIPTS_DIR.glob("*.transcript.json"), reverse=True)
    if not paths:
        st.info("No transcripts yet — send a chat turn first.")
        return

    selected = st.selectbox("Transcript", [path.name for path in paths])
    path = TRANSCRIPTS_DIR / selected
    data = json.loads(path.read_text(encoding="utf-8"))
    st.write({
        "artifact_version": data.get("artifact_version"),
        "provider": data.get("provider"),
        "model": data.get("model"),
        "turns": len(data.get("turns", [])),
    })
    st.download_button("Download transcript", path.read_bytes(), file_name=selected, mime="application/json")
    st.code(json_text(data, max_chars=20000), language="json")


def main() -> None:
    st.set_page_config(page_title="Research Agent — Day 04", page_icon="🔎", layout="wide")
    st.title("🔎 Research Agent")

    with st.sidebar:
        st.header("Artifact version")
        prompt_options = artifact_choices("system_prompt*.md", ARTIFACTS_DIR / "system_prompt.md")
        tools_options = artifact_choices("tools*.yaml", ARTIFACTS_DIR / "tools.yaml")
        config = {
            "provider": st.selectbox("Provider", PROVIDERS),
            "model": st.text_input("Model (blank = provider default)", value=""),
            "version": st.text_input("Version label", value="v3"),
            "prompt_path": str(st.selectbox("System prompt", prompt_options, format_func=lambda p: p.name)),
            "tools_path": str(st.selectbox("Tool declarations", tools_options, format_func=lambda p: p.name)),
            "history_window": st.number_input("History window", min_value=0, max_value=20, value=5),
            "max_tool_rounds": st.number_input("Max tool rounds", min_value=1, max_value=10, value=4),
        }

    session = st.session_state.get("session")
    # Any artifact change starts a new transcript: one transcript, one artifact_version.
    if session is None or session["signature"] != session_signature(config):
        session = start_session(config)
        st.session_state.session = session

    with st.sidebar:
        if st.button("Start new session", width="stretch"):
            st.session_state.session = start_session(config)
            st.rerun()
        artifact = session["artifact"]
        st.code(artifact.artifact_version, language="text")
        st.caption(f"prompt_hash `{artifact.prompt_hash[:12]}` · tools_hash `{artifact.tools_hash[:12]}`")
        st.caption(f"{len(session['declarations'])} tools declared: " + ", ".join(
            item["name"] for item in session["declarations"]
        ))
        st.caption(f"transcript `{session['transcript_path'].name}`")

    chat, runs, transcripts = st.tabs(["Chat", "Eval runs", "Transcripts"])
    with chat:
        chat_tab(session)
    with runs:
        runs_tab()
    with transcripts:
        transcripts_tab(session)


main()