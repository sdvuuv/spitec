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


def create_layout(
    station_map: go.Figure,
    station_data: go.Figure,
    projection_radio: dbc.RadioItems,
    time_slider: dcc.RangeSlider,
    checkbox_site: dbc.Checkbox,
) -> html.Div:
    left_side = create_left_side(station_map, projection_radio, checkbox_site)
    data_tab = create_data_tab(station_data, time_slider)
    selection_tab_lat_lon = create_selection_tab_lat_lon()

    size_map = 5
    size_data = 7
    layout = html.Div(
        [
            dcc.Store(id="data-store", storage_type="session"),
            dbc.Row(
                [
                    dbc.Col(
                        left_side,
                        width={"size": size_map},
                        style={"padding-left": "0px"},
                    ),
                    dbc.Col(
                        dbc.Tabs(
                            [
                                dbc.Tab(
                                    data_tab,
                                    label="Данные",
                                    tab_style={"marginLeft": "auto"},
                                    label_style={"color": "gray"},
                                    active_label_style={
                                        "font-weight": "bold",
                                        "color": "#2C3E50",
                                    },
                                ),
                                dbc.Tab(
                                    selection_tab_lat_lon,
                                    label="Выборка по широте и долготе",
                                    label_style={"color": "gray"},
                                    active_label_style={
                                        "font-weight": "bold",
                                        "color": "#2C3E50",
                                    },
                                    style={"text-align": "center"},
                                ),
                                dbc.Tab(
                                    html.Div("great circle"),
                                    label="Выборка по длине большого круга",
                                    label_style={"color": "gray"},
                                    active_label_style={
                                        "font-weight": "bold",
                                        "color": "#2C3E50",
                                    },
                                ),
                            ],
                        ),
                        width={"size": size_data},
                        style={"padding-right": "0px"},
                    ),
                ]
            ),
        ],
        style={
            "margin-top": "30px",
            "margin-left": "50px",
            "margin-right": "50px",
        },
    )
    return layout


def create_data_tab(
    station_data: go.Figure, time_slider: dcc.RangeSlider
) -> list[dbc.Row]:
    data_tab = [
        dbc.Row(
            dcc.Graph(id="graph-station-data", figure=station_data),
            style={"margin-top": "28px"},
        ),
        dbc.Row(
            html.Div(time_slider, id="div-time-slider"),
            style={"margin-top": "30px"},
        ),
        dbc.Row(
            dbc.Col(
                dbc.Button("Очистить всё", id="clear-all", class_name="me-1")
            ),
            style={
                "margin-top": "20px",
                "fontSize": "18px",
                "text-align": "center",
            },
        ),
    ]
    return data_tab


def create_selection_tab_lat_lon() -> list[dbc.Row]:
    tab_lat_lon = [
        dbc.Row(
            [
                dbc.Label("Мин. шир.", width=2),
                dbc.Col(
                    dbc.Input(
                        type="number",
                        id="min-lat",
                        min=-90,
                        max=90,
                        invalid=False,
                    ),
                    width=4,
                    style={"margin-left": "-30px"},
                ),
                dbc.Label("Макс. шир.", width=2),
                dbc.Col(
                    dbc.Input(
                        type="number",
                        id="max-lat",
                        min=-90,
                        max=90,
                        invalid=False,
                    ),
                    width=4,
                    style={"margin-left": "-30px"},
                ),
            ],
            class_name="me-1",
            style={"margin-top": "30px", "margin-left": "25px"},
        ),
        dbc.Row(
            [
                dbc.Label("Мин. долг.", width=2),
                dbc.Col(
                    dbc.Input(
                        type="number",
                        id="min-lon",
                        min=-180,
                        max=180,
                        invalid=False,
                    ),
                    width=4,
                    style={"margin-left": "-30px"},
                ),
                dbc.Label("Макс. долг.", width=2),
                dbc.Col(
                    dbc.Input(
                        type="number",
                        id="max-lon",
                        min=-180,
                        max=180,
                        invalid=False,
                    ),
                    width=4,
                    style={"margin-left": "-30px"},
                ),
            ],
            class_name="me-1",
            style={"margin-top": "15px", "margin-left": "25px"},
        ),
        dbc.Button(
            "Применить",
            id="apply-lat-lon",
            class_name="me-1",
            style={"margin-top": "20px"},
        ),
        dbc.Row(
            dbc.Col(
                dbc.Button(
                    "Очистить выборку",
                    id="clear-lat-lon",
                    class_name="me-1",
                    style={"margin-top": "20px"},
                ),
                width={"size": 3, "offset": 9},
            ),
        ),
    ]
    return tab_lat_lon


def create_left_side(
    station_map: go.Figure,
    projection_radio: dbc.RadioItems,
    checkbox_site: dbc.Checkbox,
) -> list[dbc.Row]:
    left_side = [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Button("Загрузить"),
                        dbc.Button(
                            "Открыть",
                            style={"margin-left": "15px"},
                        ),
                        dbc.Button(
                            "Настройки",
                            style={"margin-left": "15px"},
                        ),
                    ]
                ),
            ],
            className="me-1",
        ),
        dbc.Row(
            dcc.Graph(id="graph-station-map", figure=station_map),
            style={"margin-top": "30px"},
        ),
        dbc.Row(
            html.Div(projection_radio),
            style={
                "margin-top": "30px",
                "text-align": "center",
                "fontSize": "18px",
            },
        ),
        dbc.Row(
            html.Div(
                checkbox_site,
                style={
                    "display": "flex",
                    "justify-content": "center",
                    "fontSize": "18px",
                    "margin-top": "20px",
                },
            ),
        ),
    ]
    return left_side


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
        geo=dict(projection_type=ProjectionType.MERCATOR.value),
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


def create_projection_radio() -> dbc.RadioItems:
    options = [
        {"label": projection.value.capitalize(), "value": projection.value}
        for projection in ProjectionType
    ]
    radio_items = dbc.RadioItems(
        options=options,
        id="projection-radio",
        inline=True,
        value=ProjectionType.MERCATOR.value,
    )
    return radio_items


def create_station_data() -> go.Figure:
    station_data = go.Figure()

    station_data.update_layout(
        title="Данные",
        title_font=dict(size=28, color="black"),
        margin=dict(l=0, t=60, r=0, b=0),
        xaxis=dict(title="Время"),
    )
    return station_data


def create_time_slider() -> dcc.RangeSlider:
    marks = {i: f"{i:02d}:00" if i % 3 == 0 else "" for i in range(25)}
    time_slider = dcc.RangeSlider(
        id="time-slider",
        min=0,
        max=24,
        step=1,
        marks=marks,
        value=[0, 24],
        allowCross=False,
        tooltip={
            "placement": "top",
            "style": {"fontSize": "18px"},
            "template": "{value}:00",
        },
        disabled=True,
    )
    return time_slider


def create_checkbox_site() -> dbc.Checkbox:
    checkbox = dbc.Checkbox(
        id="hide-show-site", label="Имена станций", value=True
    )
    return checkbox
