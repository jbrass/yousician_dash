import json
import os

import pandas as pd

DATA_ROOT = os.environ.get(
    "YUSICIAN_DATA_ROOT", "data/yousician"
)
EVENTS_ROOT = os.environ.get(
    "YUSICIAN_EVENTS_ROOT", "data/events"
)


def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_history():
    path = os.path.join(DATA_ROOT, "history.json")
    raw = _read_json(path)
    df = pd.DataFrame(raw)
    if not df.empty and "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True)
    return df


def load_stats():
    path = os.path.join(DATA_ROOT, "stats.json")
    raw = _read_json(path)
    rows = []
    for rec in raw:
        base = {k: rec.get(k) for k in ["instrument", "week"]}
        base["week"] = pd.to_datetime(base["week"], errors="coerce", utc=True)
        s = rec.get("stats", {}) or {}
        rows.append(
            {
                **base,
                "duration_sec": s.get("duration", 0),
                "stars": s.get("stars", 0),
                "notes": s.get("notes", 0),
                "chords": s.get("chords", 0),
            }
        )
    df = pd.DataFrame(rows)
    return df


def load_exercise_progress():
    path = os.path.join(DATA_ROOT, "exercise_progress.json")
    raw = _read_json(path)
    df = pd.DataFrame(raw)
    if not df.empty and "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True)
    return df


def load_song_time_summary():
    """Parse ysapi.jsonl to compute per-song duration by play_mode (play vs practice)."""
    jsonl_path = os.path.join(EVENTS_ROOT, "ysapi.jsonl")
    if not os.path.exists(jsonl_path):
        return pd.DataFrame(
            columns=["song_id", "title", "play_mode", "total_duration_sec", "sessions"]
        )
    # Build song_id -> title mapping from any event that carries a name
    id_to_title = {}
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                o = json.loads(line)
            except Exception:
                continue
            if "song_id" in o:
                title = o.get("song_name") or o.get("song_title") or o.get("title")
                if title and o["song_id"] not in id_to_title:
                    id_to_title[o["song_id"]] = title
    # Aggregate durations from 'song_played' events which include play_mode
    rows = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("_yap_event_name") == "song_played" and "song_id" in o:
                sid = o["song_id"]
                mode = o.get("play_mode") or "unknown"
                dur = o.get("duration", 0) or 0
                rows.append(
                    {
                        "song_id": sid,
                        "title": id_to_title.get(sid),
                        "play_mode": mode,
                        "duration_sec": dur,
                    }
                )
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(
            columns=["song_id", "title", "play_mode", "total_duration_sec", "sessions"]
        )
    df["duration_sec"] = (
        pd.to_numeric(df["duration_sec"], errors="coerce").fillna(0).astype(int)
    )
    summary = (
        df.groupby(["song_id", "title", "play_mode"], dropna=False)
        .agg(
            total_duration_sec=("duration_sec", "sum"),
            sessions=("duration_sec", "count"),
        )
        .reset_index()
    )
    return summary


def songs_by_instrument(history_df):
    df = history_df.copy()
    if "item_type" in df.columns:
        df = df[df["item_type"] == "song"]
    if "item_name" in df.columns:
        df = df[~df["item_name"].isna()]
    else:
        df["item_name"] = "Unknown"
    grp = (
        df.groupby(["instrument", "item_name"])
        .agg(
            plays=("time", "count"),
            first_play=("time", "min"),
            last_play=("time", "max"),
        )
        .reset_index()
        .sort_values(["instrument", "plays"], ascending=[True, False])
    )
    return grp


def practice_time_by_week(stats_df):
    df = stats_df.copy()
    if df.empty:
        return df
    df["duration_min"] = df["duration_sec"] / 60.0
    return df
