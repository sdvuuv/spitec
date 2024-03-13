import dash
from dash import html, dcc
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from .themes import Theme
from enum import Enum


class ProjectionType(Enum):
    MERCATOR = "mercator"
    ROBINSON = "robinson"
    ORTHOGRAPHIC = "orthographic"


class View:
    def __init__(self, theme: Theme):
        self.app = dash.Dash(__name__, external_stylesheets=[theme.value])

    def create_layout(self) -> None:
        checklist = self.create_checklist()
        station_map = self.create_station_map(ProjectionType.MERCATOR)
        station_data = self.create_station_data()
        self.app.layout = html.Div(
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
                                figure=station_map, style={"width": "600px"}
                            ),
                            width={"size": 5},
                        ),
                        dbc.Col(checklist, width={"size": 2}),
                        dbc.Col(
                            dcc.Graph(
                                figure=station_data, style={"width": "600px"}
                            ),
                            width={"size": 5},
                        ),
                    ],
                    style={"margin-top": "30px"},
                ),
            ],
            style={
                "margin-top": "30px",
                "margin-left": "50px",
                "margin-right": "50px",
            },
        )

    def create_checklist(self) -> html.Div:
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
                    id="checklist-input",
                    style={"margin-top": "20px"},
                ),
            ],
            style={"margin-left": "30px"},
        )
        return checklist

    def create_station_map(self, projection_type: ProjectionType) -> go.Figure:
        station_map = go.Figure(go.Scattergeo())
        station_map.update_layout(
            title="Карта",
            title_font=dict(size=28, color="black"),
            margin=dict(l=0, t=60, r=0, b=0),
        )
        station_map.update_geos(projection_type=projection_type.value)
        return station_map

    def create_station_data(self) -> go.Figure:
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
