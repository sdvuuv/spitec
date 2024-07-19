import pytest
from spitec import *

def test_create_site_map():
    site_map = go.Scattergeo(
        mode="markers+text",
        marker=dict(size=8, line=dict(color="gray", width=1)),
        hoverlabel=dict(bgcolor="white"),
        textposition="top center",
        hoverinfo="lat+lon",
    )
    fig = go.Figure(site_map)
    fig.update_layout(
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
    )
    fig.update_geos(
        landcolor="white",
    )
    assert create_site_map() == fig

def test_create_site_data():
    fig = go.Figure()
    fig.update_layout(
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
    assert create_site_data() == fig
