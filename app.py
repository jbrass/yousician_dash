import os
import pandas as pd
from dash import Dash, html, dcc, dash_table, callback, Input, Output
import plotly.graph_objects as go
import plotly.express as px

from data_loader import (
    load_history,
    load_stats,
    load_exercise_progress,
    songs_by_instrument,
    practice_time_by_week,
)

DATA_ROOT = os.environ.get(
    "YUSICIAN_DATA_ROOT", "/Users/jbrass/Development/yousician_dash/data"
)

history_df = load_history()
stats_df = load_stats()
exercise_df = load_exercise_progress()

songs_df = (
    songs_by_instrument(history_df)
    if not history_df.empty
    else pd.DataFrame(
        columns=["instrument", "item_name", "plays", "first_play", "last_play"]
    )
)
time_df = (
    practice_time_by_week(stats_df)
    if not stats_df.empty
    else pd.DataFrame(columns=["instrument", "week", "duration_min"])
)

instruments = sorted(
    set(
        (
            history_df["instrument"].dropna().unique().tolist()
            if "instrument" in history_df.columns
            else []
        )
        + (
            stats_df["instrument"].dropna().unique().tolist()
            if "instrument" in stats_df.columns
            else []
        )
    )
)

app = Dash(__name__)
app.title = "Yousician Analytics"

app.layout = html.Div(
    [
        html.Div(
            [
                html.H1("Yousician Analytics"),
                html.P("Explore your Yousician gameplay history and progress."),
                html.Div(
                    [
                        html.Label("Instrument"),
                        dcc.Dropdown(
                            id="instrument-filter",
                            options=[
                                {"label": i.title(), "value": i} for i in instruments
                            ],
                            value=None,
                            multi=True,
                            placeholder="All instruments",
                        ),
                    ],
                    style={"width": "300px"},
                ),
                html.Hr(),
            ],
            style={"padding": "16px"},
        ),
        dcc.Tabs(
            id="tabs",
            value="tab-songs",
            children=[
                dcc.Tab(
                    label="Songs",
                    value="tab-songs",
                    children=[
                        html.Br(),
                        html.Div(
                            [
                                html.H3("Songs Played"),
                                html.P(
                                    "Counts of plays per song (duration per song is not provided by the export)."
                                ),
                                dash_table.DataTable(
                                    id="songs-table",
                                    columns=[
                                        {"name": "Instrument", "id": "instrument"},
                                        {"name": "Song", "id": "item_name"},
                                        {"name": "Plays", "id": "plays"},
                                        {"name": "First Play", "id": "first_play"},
                                        {"name": "Last Play", "id": "last_play"},
                                    ],
                                    data=songs_df.to_dict("records"),
                                    page_size=15,
                                    sort_action="native",
                                    filter_action="native",
                                    style_table={"overflowX": "auto"},
                                ),
                                html.Br(),
                                dcc.Graph(id="songs-bar"),
                            ],
                            style={"padding": "16px"},
                        ),
                    ],
                ),
                dcc.Tab(
                    label="Practice Time",
                    value="tab-time",
                    children=[
                        html.Br(),
                        html.Div(
                            [
                                html.H3("Practice Time by Week and Instrument"),
                                html.P(
                                    "From stats.json weekly rollups (duration in minutes)."
                                ),
                                dcc.Graph(id="practice-time"),
                            ],
                            style={"padding": "16px"},
                        ),
                    ],
                ),
                dcc.Tab(
                    label="Exercise Heatmap",
                    value="tab-heatmap",
                    children=[
                        html.Br(),
                        html.Div(
                            [
                                html.H3("Exercise Section Heatmap"),
                                html.P(
                                    "Shows per-exercise section completion (progress) and success_ratio. Select an exercise to view."
                                ),
                                html.Div(
                                    [
                                        html.Label("Exercise ID"),
                                        dcc.Dropdown(
                                            id="exercise-id",
                                            options=[
                                                {"label": e, "value": e}
                                                for e in (
                                                    exercise_df["exercise_id"]
                                                    .dropna()
                                                    .unique()
                                                    if not exercise_df.empty
                                                    else []
                                                )
                                            ],
                                            value=(
                                                exercise_df["exercise_id"]
                                                .dropna()
                                                .unique()[0]
                                                if not exercise_df.empty
                                                else None
                                            ),
                                            placeholder="Choose an exercise",
                                        ),
                                    ],
                                    style={"width": "500px"},
                                ),
                                dcc.Graph(id="exercise-heatmap"),
                                html.Div(
                                    id="exercise-meta",
                                    style={"marginTop": "8px", "fontStyle": "italic"},
                                ),
                            ],
                            style={"padding": "16px"},
                        ),
                    ],
                ),
            ],
        ),
    ]
)


@callback(
    Output("songs-table", "data"),
    Output("songs-bar", "figure"),
    Input("instrument-filter", "value"),
)
def update_songs_table(instruments_selected):
    df = songs_df.copy()
    if instruments_selected:
        df = df[df["instrument"].isin(instruments_selected)]
    top = df.sort_values("plays", ascending=False).head(20)
    fig = px.bar(top, x="item_name", y="plays", color="instrument")
    fig.update_layout(
        xaxis_title="Song",
        yaxis_title="Plays",
        xaxis_tickangle=45,
        margin=dict(t=30, b=120),
    )
    return df.to_dict("records"), fig


@callback(Output("practice-time", "figure"), Input("instrument-filter", "value"))
def update_practice_time(instruments_selected):
    df = time_df.copy()
    if instruments_selected:
        df = df[df["instrument"].isin(instruments_selected)]
    fig = go.Figure()
    if not df.empty:
        for inst, g in df.groupby("instrument"):
            g = g.sort_values("week")
            fig.add_trace(
                go.Scatter(
                    x=g["week"],
                    y=g["duration_min"],
                    name=inst.title(),
                    stackgroup="one",
                    mode="lines",
                )
            )
    fig.update_layout(xaxis_title="Week", yaxis_title="Minutes")
    return fig


@callback(
    Output("exercise-heatmap", "figure"),
    Output("exercise-meta", "children"),
    Input("exercise-id", "value"),
)
def update_heatmap(exercise_id):
    if not exercise_id:
        return go.Figure(), "No exercise selected."
    recs = exercise_df[exercise_df["exercise_id"] == exercise_id].sort_values("time")
    if recs.empty:
        return go.Figure(), f"No records found for {exercise_id}."
    latest = recs.iloc[-1]
    progress = latest.get("progress", {}) or {}
    if not progress:
        return go.Figure(), f"No section progress found for {exercise_id}."
    sections = sorted([int(k) for k in progress.keys()])
    values = [progress[str(k)] for k in sections]
    z = [values]
    fig = go.Figure(
        data=go.Heatmap(
            z=z, x=[f"Sec {k}" for k in sections], y=["Progress"], zmin=0, zmax=1
        )
    )
    fig.update_layout(
        xaxis_title="Section", yaxis_title="", height=300, margin=dict(t=30, b=80)
    )
    meta = f"Instrument: {latest.get('instrument', 'n/a')} • Success ratio: {latest.get('success_ratio', 'n/a')} • Last updated: {latest.get('time')}"
    return fig, meta


if __name__ == "__main__":
    app.run_server(debug=False, host="0.0.0.0", port=8050)
