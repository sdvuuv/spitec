import diskcache
from dash import DiskcacheManager, Dash
import dash_bootstrap_components as dbc
from spitec.view.visualization import create_layout, create_index_string
from spitec.callbacks.callbacks import register_callbacks

cache = diskcache.Cache("./cache")
background_callback_manager = DiskcacheManager(cache)

app = Dash(
    __name__,
    background_callback_manager=background_callback_manager,
    external_stylesheets=[dbc.themes.FLATLY],
    title='Spitec',
    suppress_callback_exceptions=True,
)
app.index_string = create_index_string()
server = app.server

app.layout = create_layout()

register_callbacks(app)

if __name__ == "__main__":
    app.run_server()
