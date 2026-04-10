"""
Helpers for extracting copy, cut, and paste signals from writing analytics
events.
"""

from __future__ import annotations

import datetime as dt

PASTE_WAIT_MS = 2500
MENU_FLAG_MS = 1500
DEDUP_MS = 750
BIG_PASTE_THRESHOLD = 200
MAX_RECENT_PASTE_TEXT_CHARS = 500
MAX_RECURSION_DEPTH = 50


class Actions:
    COPY = frozenset({"copy", "clipboard_copy", "gdocs_copy", "menu_copy", "edit_copy"})
    CUT = frozenset({"cut", "clipboard_cut", "gdocs_cut", "menu_cut", "edit_cut"})
    PASTE = frozenset({"paste", "clipboard_paste", "gdocs_paste", "insert_from_clipboard"})
    MENU_PASTE = frozenset({"menu_paste", "edit_paste", "contextmenu_paste"})
    GDOCS_SAVE = "google_docs_save"


def unwrap_event(event):
    if isinstance(event, dict) and isinstance(event.get("client"), dict):
        return event["client"]
    return event if isinstance(event, dict) else {}


def _get_event_time(event, client):
    """Resolve the timestamp once per event, with fallback."""
    server_time = (event.get("server") or {}).get("time")
    if server_time is not None:
        return server_time
    return client.get("timestamp") or (client.get("metadata") or {}).get("ts")


def event_action(client):
    action = client.get("action") or client.get("event") or client.get("type") or client.get("event_type") or ""
    if action:
        return str(action).lower()
    keystroke = client.get("keystroke", {}) if isinstance(client.get("keystroke"), dict) else {}
    return str(keystroke.get("action") or keystroke.get("type") or "").lower()


def keys_info(client):
    keystroke = client.get("keystroke", {}) if isinstance(client.get("keystroke"), dict) else {}
    key = keystroke.get("key") or client.get("key") or ""
    code = keystroke.get("code") or client.get("code") or ""
    event_type = keystroke.get("type") or client.get("type") or ""
    ctrl = bool(keystroke.get("ctrl") or client.get("ctrl") or keystroke.get("ctrlKey") or client.get("ctrlKey"))
    meta = bool(keystroke.get("metaKey") or client.get("metaKey"))
    key_code = keystroke.get("keyCode") or client.get("keyCode") or keystroke.get("which") or client.get("which")
    return {
        "key": str(key).lower() if key else "",
        "code": str(code),
        "event_type": str(event_type).lower(),
        "ctrl_or_meta": bool(ctrl or meta),
        "key_code": int(key_code) if isinstance(key_code, (int, float)) else None,
    }


def _is_key_combo(info, key_char, code_str, key_code_int):
    return info["event_type"] == "keydown" and info["ctrl_or_meta"] and (
        info["key"] == key_char or info["code"] == code_str or info["key_code"] == key_code_int
    )


def is_copy(client):
    action = event_action(client)
    if action in Actions.COPY:
        return True
    return _is_key_combo(keys_info(client), "c", "KeyC", 67)


def is_cut(client):
    action = event_action(client)
    if action in Actions.CUT:
        return True
    return _is_key_combo(keys_info(client), "x", "KeyX", 88)


def is_paste_keyboard(client):
    action = event_action(client)
    if action in Actions.PASTE:
        return True
    return _is_key_combo(keys_info(client), "v", "KeyV", 86)


def looks_like_menu_paste(client):
    action = event_action(client)
    if action in Actions.MENU_PASTE:
        return True
    if action == "contextmenu":
        return True
    # Catches both right-click → Paste and Edit menu → Paste
    if action == "mouseclick":
        mc = client.get("mouseclick") or {}
        inner_text = str(mc.get("target.innerText") or "").strip().lower()
        class_name = str(mc.get("target.className") or "")
        if inner_text == "paste" and "goog-menuitem-label" in class_name:
            return True
    return False


def timestamp_ms(event, client=None):
    client = client or unwrap_event(event)
    value = _get_event_time(event, client)
    if isinstance(value, (int, float)):
        return int(value * 1000) if value < 10**11 else int(value)
    return int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000)


def collect_inserted_text(command, output, _depth=0):
    if not isinstance(command, dict) or _depth > MAX_RECURSION_DEPTH:
        return

    if command.get("ty") == "is":
        string_value = command.get("s")
        if isinstance(string_value, str) and string_value:
            output.append(string_value)

    if isinstance(command.get("nmc"), dict):
        collect_inserted_text(command["nmc"], output, _depth + 1)

    for child in command.get("mts") or []:
        collect_inserted_text(child, output, _depth + 1)


def extract_insert_from_gdocs_save(client):
    parts = []
    for bundle in client.get("bundles") or []:
        for command in (bundle or {}).get("commands") or []:
            collect_inserted_text(command, parts)
    return "".join(parts)


def paste_length_bin(length):
    if length <= 0:
        return "none"
    if length <= 20:
        return "short_1_20"
    if length <= 200:
        return "medium_21_200"
    return "long_201_plus"


def append_recent(items, entry, limit=10):
    result = list(items or [])
    result.append(entry)
    return result[-limit:]


def clip_recent_paste_text(text, limit=MAX_RECENT_PASTE_TEXT_CHARS):
    if text is None:
        return None, False
    if len(text) <= limit:
        return text, False
    return text[:limit], True


def default_paste_state():
    return {
        "paste_count": 0,
        "pastes_with_length": 0,
        "total_paste_chars": 0,
        "max_paste_len": 0,
        "last_paste_len": 0,
        "big_pastes": 0,
        "length_bins": {
            "short_1_20": 0,
            "medium_21_200": 0,
            "long_201_plus": 0,
        },
        "last_right_click_ms": 0,
        "pending_paste_source": None,
        "recent_pastes": [],
        "awaiting_paste_until": 0,
        "maybe_menu_paste_until": 0,
        "last_paste_signal_ms": 0,
    }


def default_copy_cut_state():
    return {
        "copy_count": 0,
        "cut_count": 0,
        "last_copy_ts": 0,
        "last_cut_ts": 0,
        "recent_events": [],
    }


def update_paste_state(event, state):
    state = dict(default_paste_state() if state is None else state)
    state["length_bins"] = dict(state.get("length_bins", {}))
    state["recent_pastes"] = [dict(p) for p in state.get("recent_pastes", [])]

    client = unwrap_event(event)
    ts_ms = timestamp_ms(event, client)
    action = event_action(client)

    if action == "mouseclick": #Fixed
        mc = client.get("mouseclick") or {}
        if mc.get("button") == 2:
            state["last_right_click_ms"] = ts_ms
            return state  # not a paste itself, just record it

    if is_paste_keyboard(client):
        if ts_ms - state.get("last_paste_signal_ms", 0) <= DEDUP_MS:
            return False
        state["paste_count"] = state.get("paste_count", 0) + 1
        state["last_paste_signal_ms"] = ts_ms
        state["awaiting_paste_until"] = ts_ms + PASTE_WAIT_MS
        state["recent_pastes"] = append_recent(
            state["recent_pastes"],
            {
                "timestamp_ms": ts_ms,
                "length": None,
                "source": "keyboard",
                "text": None,
                "text_truncated": False,
                "resolved": False,
            },
        )
        return state

    if looks_like_menu_paste(client):                     # FIXED : now detects mouseclick Paste
        state["maybe_menu_paste_until"] = ts_ms + MENU_FLAG_MS
        # FIX 4: label right-click paste vs. menubar paste
        is_right_click = (ts_ms - state.get("last_right_click_ms", 0)) < MENU_FLAG_MS
        state["pending_paste_source"] = "right_click" if is_right_click else "menubar"
        return state

    if action != Actions.GDOCS_SAVE:
        return False

    inserted_text = extract_insert_from_gdocs_save(client)
    if not inserted_text:
        return False

    paste_length = len(inserted_text)
    awaiting_paste_until = state.get("awaiting_paste_until", 0)
    maybe_menu_paste_until = state.get("maybe_menu_paste_until", 0)
    counted_from_save = False

    if ts_ms <= maybe_menu_paste_until and ts_ms > awaiting_paste_until:
        if ts_ms - state.get("last_paste_signal_ms", 0) <= DEDUP_MS:
            return False
        state["paste_count"] = state.get("paste_count", 0) + 1
        state["last_paste_signal_ms"] = ts_ms
        counted_from_save = True

    if ts_ms > awaiting_paste_until and not counted_from_save:
        return False

    state["pastes_with_length"] = state.get("pastes_with_length", 0) + 1
    state["total_paste_chars"] = state.get("total_paste_chars", 0) + paste_length
    state["max_paste_len"] = max(state.get("max_paste_len", 0), paste_length)
    state["last_paste_len"] = paste_length
    if paste_length >= BIG_PASTE_THRESHOLD:
        state["big_pastes"] = state.get("big_pastes", 0) + 1

    bin_name = paste_length_bin(paste_length)
    if bin_name != "none":
        state["length_bins"][bin_name] = state["length_bins"].get(bin_name, 0) + 1

    clipped_text, was_truncated = clip_recent_paste_text(inserted_text)

    # --- Coalesce: find the pending keyboard entry and enrich it ---
    if not counted_from_save:
        resolved = False
        for entry in reversed(state["recent_pastes"]):
            if not entry.get("resolved") and entry.get("source") == "keyboard":
                entry["length"] = paste_length
                entry["text"] = clipped_text
                entry["text_truncated"] = was_truncated
                entry["resolved"] = True
                resolved = True
                break
        if not resolved:
            # Defensive fallback: no pending entry found, append standalone
            state["recent_pastes"] = append_recent(
                state["recent_pastes"],
                {
                    "timestamp_ms": ts_ms,
                    "length": paste_length,
                    "source": "keyboard",
                    "text": clipped_text,
                    "text_truncated": was_truncated,
                    "resolved": True,
                },
            )
    else:
        state["recent_pastes"] = append_recent(
            state["recent_pastes"],
            {
                "timestamp_ms": ts_ms,
                "length": paste_length,
                "source": "menu",
                "text": clipped_text,
                "text_truncated": was_truncated,
                "resolved": True,
            },
        )

    state["awaiting_paste_until"] = 0
    state["maybe_menu_paste_until"] = 0
    return state


def update_copy_cut_state(event, state):
    state = dict(default_copy_cut_state() if state is None else state)
    state["recent_events"] = list(state.get("recent_events", []))

    client = unwrap_event(event)
    ts_ms = timestamp_ms(event, client)
    event_type = None

    if is_copy(client):
        if ts_ms - state.get("last_copy_ts", 0) <= DEDUP_MS:
            return False
        state["copy_count"] = state.get("copy_count", 0) + 1
        state["last_copy_ts"] = ts_ms
        event_type = "copy"
    elif is_cut(client):
        if ts_ms - state.get("last_cut_ts", 0) <= DEDUP_MS:
            return False
        state["cut_count"] = state.get("cut_count", 0) + 1
        state["last_cut_ts"] = ts_ms
        event_type = "cut"

    if not event_type:
        return False

    state["recent_events"] = append_recent(
        state.get("recent_events"),
        {"timestamp_ms": ts_ms, "event_type": event_type},
    )
    return state
