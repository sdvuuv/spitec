from dash import html, dcc
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from .data_processing import Site
from enum import Enum
import numpy as np

class ProjectionType(Enum):
    MERCATOR = "mercator"
    ROBINSON = "robinson"
    ORTHOGRAPHIC = "orthographic"

def create_layout(station_map, station_data) -> html.Div:
    #station_checklist = create_station_checklist()
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
                        dcc.Graph(
                            id = "graph-station-map",
                            figure=station_map
                        ),
                        width={"size": size_map},
                    ),
                    #dbc.Col(station_checklist, width={"size": 2}),
                    dbc.Col(
                        dcc.Graph(
                            figure=station_data
                        ),
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
            )
        ],
        style={
            "margin-top": "30px",
            "margin-left": "50px",
            "margin-right": "50px",
        },
    )
    return layout

def create_station_map(
        site_names: np.ndarray[Site], 
        latitudes_array: np.ndarray[float], 
        longitudes_array: np.ndarray[float]
    )-> go.Figure:
    station_map = go.Scattergeo(
        lat=latitudes_array,
        lon=longitudes_array,
        text=site_names,
        mode='markers+text', 
        marker=dict(
            size=8,
            color='silver',
            line=dict(
                color='gray',
                width=1  
            )
        ),
         hoverlabel=dict(
             bgcolor='white'
        ),
        textposition='top center',
        hoverinfo='lat+lon'  # Отображаем только текст при наведении

    )

    figure = go.Figure(station_map)
    figure.update_layout(
        title="Карта",
        title_font=dict(size=28, color="black"),
        margin=dict(l=0, t=60, r=0, b=0),
    )
    figure.update_geos(
        landcolor = 'white'
    )

    return figure

def _create_projection_radio() -> html.Div:
    options =  [{"label": projection.value.capitalize(), "value": projection.value}
                for projection in ProjectionType]
    checklist = html.Div(
        dbc.RadioItems(
                options=options,
                value=ProjectionType.MERCATOR.value,
                id="projection-radio",
                inline=True,
                style={"fontSize": "18px"}
        )
    )
    return checklist

def create_station_data() -> go.Figure:
    x = [1, 2, 3, 4, 5]
    y1 = [10, 15, 13, 17, 18]
    y2 = [16, 5, 11, 9, 7]
    y3 = [12, 9, 1, 0, 3]
    y4 = [5, 8, 9, 14, 6]

    station_data = go.Figure()
    station_data.add_trace(
        go.Scatter(x=x, y=y1, mode="lines", name="Станция 1")
    )
    station_data.add_trace(
        go.Scatter(x=x, y=y2, mode="lines", name="Станция 3")
    )
    station_data.add_trace(
        go.Scatter(x=x, y=y3, mode="lines", name="Станция 5")
    )
    station_data.add_trace(
        go.Scatter(x=x, y=y4, mode="lines", name="Станция 7")
    )

    station_data.update_layout(
        title="Данные",
        title_font=dict(size=28, color="black"),
        margin=dict(l=0, t=60, r=0, b=0),
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
