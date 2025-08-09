
import json, os, pandas as pd, numpy as np
from datetime import datetime

DATA_ROOT = os.environ.get("YUSICIAN_DATA_ROOT", "/Users/jbrass/Development/yousician_dash/data/yousician")

def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_history():
    path = os.path.join(DATA_ROOT, "history.json")
    raw = _read_json(path)
    df = pd.DataFrame(raw)
    if not df.empty and 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'], errors='coerce', utc=True)
    return df

def load_stats():
    path = os.path.join(DATA_ROOT, "stats.json")
    raw = _read_json(path)
    rows = []
    for rec in raw:
        base = {k: rec.get(k) for k in ['instrument', 'week']}
        base['week'] = pd.to_datetime(base['week'], errors='coerce', utc=True)
        s = rec.get('stats', {}) or {}
        rows.append({
            **base,
            'duration_sec': s.get('duration', 0),
            'stars': s.get('stars', 0),
            'notes': s.get('notes', 0),
            'chords': s.get('chords', 0),
        })
    df = pd.DataFrame(rows)
    return df

def load_exercise_progress():
    path = os.path.join(DATA_ROOT, "exercise_progress.json")
    raw = _read_json(path)
    df = pd.DataFrame(raw)
    if not df.empty and 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'], errors='coerce', utc=True)
    return df

def songs_by_instrument(history_df):
    df = history_df.copy()
    if 'item_type' in df.columns:
        df = df[df['item_type'] == 'song']
    if 'item_name' in df.columns:
        df = df[~df['item_name'].isna()]
    else:
        df['item_name'] = 'Unknown'
    grp = df.groupby(['instrument', 'item_name']).agg(
        plays=('time', 'count'),
        first_play=('time', 'min'),
        last_play=('time', 'max'),
    ).reset_index().sort_values(['instrument', 'plays'], ascending=[True, False])
    return grp

def practice_time_by_week(stats_df):
    df = stats_df.copy()
    if df.empty:
        return df
    df['duration_min'] = df['duration_sec'] / 60.0
    return df
