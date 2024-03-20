from dash import html, dcc
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from enum import Enum
import numpy as np
from numpy.typing import NDArray


class ProjectionType(Enum):
    MERCATOR = "mercator"
    ROBINSON = "robinson"
    ORTHOGRAPHIC = "orthographic"


class PointColor(Enum):
    SILVER = "silver"
    RED = "red"
    GREEN = "green"


def create_layout(station_map: go.Figure, station_data: go.Figure) -> html.Div:
    # station_checklist = create_station_checklist()

    projection_radio = _create_projection_radio()

    size_map = 5
    size_data = 7
    layout = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Button("Загрузить", className="me-1"),
                            dbc.Button(
                                "Открыть",
                                className="me-1",
                                style={"margin-left": "20px"},
                            ),
                            dbc.Button(
                                "Настройки",
                                className="me-1",
                                style={"margin-left": "20px"},
                            ),
                        ]
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(id="graph-station-map", figure=station_map),
                        width={"size": size_map},
                    ),
                    # dbc.Col(station_checklist, width={"size": 2}),
                    dbc.Col(
                        dcc.Graph(id="graph-station-data", figure=station_data),
                        width={"size": size_data},
                    ),
                ],
                style={"margin-top": "30px"},
            ),
            dbc.Row(
                dbc.Col(
                    projection_radio,
                    width={"size": size_map},
                ),
                style={"margin-top": "30px", "text-align": "center"},
            ),
        ],
        style={
            "margin-top": "30px",
            "margin-left": "50px",
            "margin-right": "50px",
        },
    )
    return layout


def create_station_map(
    site_names: NDArray, latitudes_array: NDArray, longitudes_array: NDArray
) -> go.Figure:
    colors = np.array([PointColor.SILVER.value] * site_names.shape[0])
    station_map = go.Scattergeo(
        lat=latitudes_array,
        lon=longitudes_array,
        text=[site.upper() for site in site_names],
        mode="markers+text",
        marker=dict(size=8, color=colors, line=dict(color="gray", width=1)),
        hoverlabel=dict(bgcolor="white"),
        textposition="top center",
        hoverinfo="lat+lon",
    )

    figure = go.Figure(station_map)
    figure.update_layout(
        title="Карта",
        title_font=dict(size=28, color="black"),
        margin=dict(l=0, t=60, r=0, b=0),
    )
    figure.update_geos(
        landcolor="white",
        # landcolor="LightGreen",
        # showocean=True,
        # oceancolor="LightBlue",
        # showcountries=True,
        # countrycolor="Black",
    )

    return figure


def _create_projection_radio() -> html.Div:
    options = [
        {"label": projection.value.capitalize(), "value": projection.value}
        for projection in ProjectionType
    ]
    checklist = html.Div(
        dbc.RadioItems(
            options=options,
            id="projection-radio",
            inline=True,
            style={"fontSize": "18px"},
        )
    )
    return checklist


def create_station_data() -> go.Figure:
    station_data = go.Figure()

    station_data.update_layout(
        title="Данные",
        title_font=dict(size=28, color="black"),
        margin=dict(l=0, t=60, r=0, b=0),
        xaxis_title="Время",
        yaxis_title="Данные",
    )
    return station_data


def create_station_checklist() -> html.Div:
    checklist = html.Div(
        [
            html.H3("Станции"),
            dbc.Checklist(
                options=[
                    {"label": "Станция 1", "value": 1},
                    {"label": "Станция 2", "value": 2},
                    {"label": "Станция 3", "value": 3},
                    {"label": "Станция 4", "value": 4},
                    {"label": "Станция 5", "value": 5},
                    {"label": "Станция 6", "value": 6},
                    {"label": "Станция 7", "value": 7},
                ],
                value=[1, 3, 5, 7],
                id="station-checklist",
                style={"margin-top": "20px"},
            ),
        ],
        style={"margin-left": "30px"},
    )
    return checklist
