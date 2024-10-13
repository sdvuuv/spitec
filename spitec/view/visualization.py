from dash import html, dcc
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from enum import Enum
from .languages import languages
from datetime import datetime, date, timedelta
from ..processing import DataProducts


language = languages["en"]


class ProjectionType(Enum):
    MERCATOR = "mercator"
    ROBINSON = "robinson"
    ORTHOGRAPHIC = "orthographic"


class PointColor(Enum):
    SILVER = "silver"
    RED = "red"
    GREEN = "green"


def create_layout() -> html.Div:
    left_side = _create_left_side()
    data_tab = _create_data_tab()
    tab_sampling_region = _create_form_lat_lon()
    form_great_circle_distance = _create_form_great_circle_distance()
    tab_sampling_region.extend(form_great_circle_distance)
    tab_add_points = _create_add_points_tab()

    size_map = 5
    size_data = 7
    layout = html.Div(
        [
            dcc.Store(id="region-site-names-store", storage_type="session"),
            dcc.Store(id="local-file-store", storage_type="session"),
            dcc.Store(id="site-coords-store", storage_type="session"),
            dcc.Store(id="site-data-store", storage_type="session"),
            dcc.Store(id="satellites-options-store", storage_type="session"),
            dcc.Store(id="downloading-file-store", storage_type="session"),
            dcc.Store(id="scale-map-store", storage_type="session", data=1),
            dcc.Store(id="relayout-map-store", storage_type="session"),
            dcc.Store(id="sip-tag-time-store", storage_type="session"),
            dcc.Store(id="new-points-store", storage_type="session"),
            dcc.Location(id="url", refresh=False),
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
                                    label=language["data-tab"]["label"],
                                    tab_style={"marginLeft": "auto"},
                                    label_style={"color": "gray"},
                                    active_label_style={
                                        "font-weight": "bold",
                                        "color": "#2C3E50",
                                    },
                                ),
                                dbc.Tab(
                                    tab_sampling_region,
                                    label=language["tab-sampling-region"]["label"],
                                    label_style={"color": "gray"},
                                    active_label_style={
                                        "font-weight": "bold",
                                        "color": "#2C3E50",
                                    },
                                    style={"text-align": "center"},
                                ),
                                dbc.Tab(
                                    tab_add_points,
                                    label=language["tab-add-points"]["label"],
                                    label_style={"color": "gray"},
                                    active_label_style={
                                        "font-weight": "bold",
                                        "color": "#2C3E50",
                                    },
                                    style={"text-align": "center"},
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


def _create_left_side() -> list[dbc.Row]:
    site_map_points = create_site_map_with_points()
    site_map = create_fig_for_map(site_map_points)
    projection_radio = _create_projection_radio()
    checkbox_site = _create_checkbox_site()
    download_window = _create_download_window()
    open_window = _create_open_window()
    input_hm = _create_input_hm()
    input_time = _create_input_time()
    left_side = [
        dbc.Row(
            [
                dbc.Col(
                    [
                        download_window,
                        html.Div(
                            open_window,
                            style={"margin-left": "15px"},
                        ),
                    ],
                    style={"display": "flex", "justify-content": "flex-start"},
                ),
            ],
        ),
        dbc.Row(
            html.Div(
                checkbox_site,
                style={
                    "display": "flex",
                    "justify-content": "flex-end",
                    "fontSize": "16px",
                    "margin-top": "-3px",
                    "margin-left": "-95px",
                },
            ),
        ),
        dbc.Row(
            dcc.Graph(id="graph-site-map", figure=site_map),
        ),
        dbc.Row(
            html.Div(projection_radio),
            style={
                "margin-top": "23px",
                "text-align": "center",
                "fontSize": "18px",
            },
        ),
        dbc.Row(
            html.Div(
                language["trajectory"]["error"],
                id="trajectory-error",
                style={
                    "visibility": "hidden"
                },
            ),
        ),
        dbc.Row(
            dbc.Col(
                [
                    dbc.Label(language["trajectory"]["hm"]+":", width=1),
                    html.Div(
                        input_hm,
                        style={"margin-right": "25px"}
                    ),
                    dbc.Label(language["trajectory"]["hms"]+":", width=1,
                              style={"margin-left": "25px"}),
                    html.Div(
                        input_time,
                    ),
                    dbc.Button(
                            language["trajectory"]["show-tag-sip"],
                            id="show-tag-sip",
                            style={"margin-left": "20px"}
                        ),
                ],
                style={"display": "flex", "justify-content": "center"},
            ),
            style={
                "margin-top": "10px",
                "fontSize": "18px",
            },      
        ),
    ]
    return left_side


def _create_download_window() -> html.Div:
    boot_progress_window = _create_boot_progress_window()
    download_window = html.Div(
        [
            dbc.Button(language["buttons"]["download"], id="download"),
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(language["buttons"]["download"])
                    ),
                    dbc.ModalBody(
                        [
                            dbc.Label(
                                language["download_window"]["label"],
                                style={"font-size": "18px"},
                            ),
                            dcc.DatePickerSingle(
                                id="date-selection",
                                min_date_allowed=date(1998, 1, 1),
                                max_date_allowed=datetime.now()
                                - timedelta(days=1),
                                display_format="YYYY-MM-DD",
                                placeholder="YYYY-MM-DD",
                                date=datetime.now().strftime("%Y-%m-%d"),
                                style={"margin-left": "15px"},
                            ),
                            html.Div(
                                language["download_window"]["file-size"],
                                id="file-size",
                                style={
                                    "font-size": "18px",
                                    "margin-top": "20px",
                                },
                            ),
                            html.Div(
                                [
                                    dbc.Button(
                                        language["buttons"]["check-file-size"],
                                        id="check-file-size",
                                        style={"margin-right": "10px"},
                                    ),
                                    dbc.Button(
                                        language["buttons"]["download"],
                                        id="download-file",
                                        style={"margin-left": "10px"},
                                    ),
                                ],
                                style={
                                    "text-align": "center",
                                    "margin-top": "20px",
                                },
                            ),
                        ]
                    ),
                ],
                id="download-window",
                is_open=False,
            ),
            boot_progress_window,
        ]
    )
    return download_window


def _create_boot_progress_window() -> dbc.Modal:
    modal = dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle(language["boot-progress-window"]["header"]),
                id="loading-process-modal-header",
            ),
            dbc.ModalBody(
                [
                    html.Div(
                        [
                            html.Div("0%", id="load-per"),
                            dbc.Progress(id="boot-process", value=0),
                            html.Div(
                                "",
                                id="downloaded",
                                style={
                                    "visibility": "hidden",
                                },
                            ),
                        ],
                        style={"text-align": "center"},
                    ),
                    html.Div(
                        dbc.Button(
                            language["boot-progress-window"][
                                "cancel-download"
                            ],
                            id="cancel-download",
                        ),
                        style={"text-align": "right", "margin-top": "20px"},
                    ),
                ]
            ),
        ],
        id="boot-progress-window",
        is_open=False,
        backdrop="static",
    )
    return modal


def _create_open_window() -> html.Div:
    open_window = html.Div(
        [
            dbc.Button(language["buttons"]["open"], id="open"),
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(language["buttons"]["open"])
                    ),
                    dbc.ModalBody(
                        [
                            html.Div(
                                [
                                    dbc.Label(
                                        language["open_window"]["label"],
                                        style={
                                            "font-size": "18px",
                                            "margin-top": "5px",
                                        },
                                    ),
                                    dbc.Select(
                                        id="select-file",
                                        options=[],
                                        style={
                                            "width": "50%",
                                            "margin-left": "15px",
                                        },
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "justify-content": "flex-start",
                                },
                            ),
                            html.Div(
                                dbc.Button(
                                    language["buttons"]["open"],
                                    id="open-file",
                                ),
                                style={
                                    "text-align": "center",
                                    "margin-top": "20px",
                                },
                            ),
                        ]
                    ),
                ],
                id="open-window",
                is_open=False,
            ),
        ]
    )
    return open_window


def create_site_map_with_points() -> go.Scattergeo:
    site_map_points = go.Scattergeo(
        mode="markers+text",
        marker=dict(size=8, line=dict(color="gray", width=1)),
        hoverlabel=dict(bgcolor="white"),
        textposition="top center",
        hoverinfo="lat+lon",
    )

    return site_map_points

def create_site_map_with_trajectories() -> go.Scattergeo:
    site_map_trajs = go.Scattergeo(
        mode='lines',
        line=dict(width=2),
        hoverinfo='skip'
    )
    return site_map_trajs

def create_site_map_with_tag(
        size: int = 5, 
        symbol: str = 'diamond'  # Маркер ромб
    ) -> go.Scattergeo:
    site_map_end_trajs = go.Scattergeo(
        mode='markers',
        marker=dict(size=size, symbol=symbol), 
        hovertemplate='%{lat}, %{lon}<extra></extra>'
    )
    return site_map_end_trajs

def create_fig_for_map(sites: go.Scattergeo) -> go.Figure:
    figure = go.Figure(sites)
    figure.update_layout(
        title=language["graph-site-map"]["title"],
        title_font=dict(size=24, color="black"),
        margin=dict(l=0, t=60, r=0, b=0),
        geo=dict(
            projection_type=ProjectionType.MERCATOR.value,
            lonaxis=dict(
                showgrid=True,
                gridwidth=0.5,
                gridcolor="LightGrey",
                tick0=-180,
                dtick=10,
            ),
            lataxis=dict(
                showgrid=True,
                gridwidth=0.5,
                gridcolor="LightGrey",
                tick0=-90,
                dtick=5,
            )
        ),
        showlegend=False
    )
    figure.update_geos(
        landcolor="white",
    )
    return figure

def _create_input_hm() -> dbc.Input:
    input = dbc.Input(
        id="input-hm",
        type="number",
        step="0.1",
        value=300,
        persistence=300,
        persistence_type="session",
        style={"width": "85px"},
    )
    return input

def _create_input_time() -> dbc.Input:
    input = dbc.Input(
        id="input-sip-tag-time",
        type="time",
        step=1,
        value="00:00:00",
        persistence="00:00:00",
        persistence_type="session",
        style={"width": "130px"},
    )
    return input


def _create_projection_radio() -> dbc.RadioItems:
    options = [
        {
            "label": language["projection-radio"][projection.value],
            "value": projection.value,
        }
        for projection in ProjectionType
    ]
    radio_items = dbc.RadioItems(
        options=options,
        id="projection-radio",
        inline=True,
        value=ProjectionType.MERCATOR.value,
        persistence=True,
        persistence_type="session",
    )
    return radio_items


def _create_checkbox_site() -> dbc.Checkbox:
    checkbox = dbc.Checkbox(
        id="hide-show-site",
        label=language["hide-show-site"],
        value=True,
        persistence=True,
        persistence_type="session",
    )
    return checkbox


def _create_data_tab() -> list[dbc.Row]:
    site_data = create_site_data()
    time_slider = _create_time_slider()
    selection_data_types = _create_selection_data_types()
    selection_satellites = _create_empty_selection_satellites()
    input_shift = _create_input_shift()
    data_tab = [
        dbc.Row(
            dcc.Graph(id="graph-site-data", figure=site_data),
            style={"margin-top": "28px"},
        ),
        dbc.Row(
            html.Div(time_slider, id="div-time-slider"),
            style={"margin-top": "25px"},
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        selection_satellites,
                        selection_data_types,
                        input_shift,
                        dbc.Button(
                            language["buttons"]["clear-all"],
                            id="clear-all",
                        ),
                    ],
                    style={"display": "flex", "justify-content": "flex-end"},
                ),
            ],
            style={
                "margin-top": "20px",
            },
        ),
    ]
    return data_tab


def _create_input_shift() -> dbc.Input:
    input = dbc.Input(
        id="input-shift",
        type="number",
        step="0.5",
        value=-0.5,
        persistence=-0.5,
        persistence_type="session",
        style={"width": "80px", "margin-right": "20px"},
    )
    return input


def _create_selection_data_types() -> dbc.Select:
    options = [
        {
            "label": "2-10 minute TEC variations",
            "value": DataProducts.dtec_2_10.name,
        },
        {
            "label": "10-20 minute TEC variations",
            "value": DataProducts.dtec_10_20.name,
        },
        {
            "label": "20-60 minute TEC variations",
            "value": DataProducts.dtec_20_60.name,
        },
        {"label": "ROTI", "value": DataProducts.roti.name},
        {"label": "Adjusted TEC", "value": DataProducts.tec.name},
        {"label": "Elevation angle", "value": DataProducts.elevation.name},
        {"label": "Azimuth angle", "value": DataProducts.azimuth.name},
    ]
    select = dbc.Select(
        id="selection-data-types",
        options=options,
        value=DataProducts.dtec_2_10.name,
        style={"width": "250px", "margin-right": "20px"},
        persistence=DataProducts.dtec_2_10.name,
        persistence_type="session",
    )
    return select


def _create_empty_selection_satellites() -> dbc.Select:
    select = dbc.Select(
        id="selection-satellites",
        options=[],
        placeholder=language["data-tab"]["selection-satellites"],
        style={"width": "150px", "margin-right": "20px"},
        persistence=True,
        persistence_type="session",
    )
    return select


def create_site_data() -> go.Figure:
    site_data = go.Figure()

    site_data.update_layout(
        title=language["data-tab"]["graph-site-data"]["title"],
        title_font=dict(size=24, color="black"),
        plot_bgcolor="white",
        margin=dict(l=0, t=60, r=0, b=0),
        xaxis=dict(
            title=language["data-tab"]["graph-site-data"]["xaxis"],
            gridcolor="#E1E2E2",
            linecolor="black",
            showline=True,
            mirror=True,
        ),
        yaxis=dict(
            gridcolor="#E1E2E2",
            linecolor="black",
            showline=True,
            mirror=True,
        )
    )
    return site_data


def _create_time_slider() -> dcc.RangeSlider:
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
        persistence=True,
        persistence_type="session",
    )
    return time_slider


def _create_form_lat_lon() -> list[dbc.Row]:
    form_lat_lon = [
        dbc.Row(
            html.Div(
                language["tab-sampling-region"]["title-lat-lon"],
            ),
            style={"margin-top": "30px", "font-size": "20px"},
        ),
        dbc.Row(
            [
                dbc.Label(language["tab-sampling-region"]["min-lat"], width=2),
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
                dbc.Label(language["tab-sampling-region"]["max-lat"], width=2),
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
            style={"margin-top": "20px", "margin-left": "25px"},
        ),
        dbc.Row(
            [
                dbc.Label(language["tab-sampling-region"]["min-lon"], width=2),
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
                dbc.Label(language["tab-sampling-region"]["max-lon"], width=2),
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
            style={"margin-top": "15px", "margin-left": "25px"},
        ),
        dbc.Button(
            language["buttons"]["apply-selection-by-region"],
            id="apply-lat-lon",
            style={"margin-top": "20px"},
        ),
    ]
    return form_lat_lon


def _create_form_great_circle_distance() -> list[dbc.Row]:
    form_great_circle_distance = [
        dbc.Row(
            html.Div(
                language["tab-sampling-region"]["title-great-circle-distance"],
            ),
            style={"margin-top": "40px", "font-size": "20px"},
        ),
        dbc.Row(
            [
                dbc.Label(
                    language["tab-sampling-region"]["distance"], width=3
                ),
                dbc.Col(
                    dbc.Input(
                        type="number",
                        id="distance",
                        min=0,
                        invalid=False,
                        style={"width": "97%"},
                    ),
                    width=4,
                    style={"margin-left": "-46px"},
                ),
            ],
            style={"margin-top": "20px", "margin-left": "20px"},
        ),
        dbc.Row(
            [
                dbc.Label(
                    language["tab-sampling-region"]["center-point-lat"],
                    width=2,
                ),
                dbc.Col(
                    dbc.Input(
                        type="number",
                        id="center-point-lat",
                        min=-90,
                        max=90,
                        invalid=False,
                    ),
                    width=4,
                    style={"margin-left": "5px"},
                ),
                dbc.Label(
                    language["tab-sampling-region"]["center-point-lon"],
                    width=2,
                ),
                dbc.Col(
                    dbc.Input(
                        type="number",
                        id="center-point-lon",
                        min=-180,
                        max=180,
                        invalid=False,
                    ),
                    width=4,
                    style={"margin-left": "-25px"},
                ),
            ],
            style={"margin-top": "15px", "margin-left": "40px"},
        ),
        dbc.Button(
            language["buttons"]["apply-selection-by-region"],
            id="apply-great-circle-distance",
            style={"margin-top": "20px"},
        ),
        dbc.Row(
            dbc.Col(
                dbc.Button(
                    language["buttons"]["clear-selection-by-region"],
                    id="clear-selection-by-region",
                    style={"margin-top": "20px"},
                ),
                width={"size": 3, "offset": 9},
            ),
        ),
    ]
    return form_great_circle_distance

def _create_add_points_tab() -> list[dbc.Row]:
    tab_add_points = [
        dbc.Row(
            [
                dbc.Label(language["tab-add-points"]["name-point"], width=2),
                dbc.Col(
                    dbc.Input(
                        type="text",
                        id="name-point",
                        minlength=1,
                        maxlength=50,
                        invalid=False,
                    ),
                    width=4,
                    style={"margin-left": "-30px"},
                )
            ],
            style={"margin-top": "20px", "margin-left": "25px"},
        ),
        dbc.Row(
            [
                dbc.Label(language["tab-add-points"]["point-marker"], width=2),
                dbc.Col(
                    dbc.Select(
                        id="point-marker",
                        options=['Circle', 'Square', 'Diamond', 'Cross', 'X', 'Star', 'Hourglass'],
                        value='Circle',
                    ),
                    width=4,
                    style={"margin-left": "-30px"},
                ),
                dbc.Label(language["tab-add-points"]["point-color"], width=2),
                dbc.Col(
                    dbc.Input(
                        type="color",
                        id="point-color",
                        value="#43df4e", 
                        style={"height": "38px"},
                    ),
                    width=4,
                    style={"margin-left": "-30px"},
                ),
            ],
            style={"margin-top": "20px", "margin-left": "25px"},
        ),
        dbc.Row(
            [
                dbc.Label(language["tab-add-points"]["point-lat"], width=2),
                dbc.Col(
                    dbc.Input(
                        type="number",
                        id="point-lat",
                        min=-90,
                        max=90,
                        invalid=False,
                    ),
                    width=4,
                    style={"margin-left": "-30px"},
                ),
                dbc.Label(language["tab-add-points"]["point-lon"], width=2),
                dbc.Col(
                    dbc.Input(
                        type="number",
                        id="point-lon",
                        min=-180,
                        max=180,
                        invalid=False,
                    ),
                    width=4,
                    style={"margin-left": "-30px"},
                ),
            ],
            style={"margin-top": "15px", "margin-left": "25px"},
        ),
        dbc.Row(
            html.Div(
                language["tab-add-points"]["error"],
                id="add-points-error",
                style={
                    "visibility": "hidden"
                },
            ),
        ),
        dbc.Button(
            language["buttons"]["add-point"],
            id="add-point",
            style={"margin-top": "10px"},
        ),
        dbc.Row(
            dbc.Col(
                dbc.Button(
                    language["buttons"]["delete-all-points"],
                    id="delete-all-points",
                    style={"margin-top": "20px"},
                ),
                width={"size": 3, "offset": 9},
            ),
        ),
    ]
    return tab_add_points