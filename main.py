import diskcache
from dash import DiskcacheManager, Dash
from spitec import *

cache = diskcache.Cache("./cache")
background_callback_manager = DiskcacheManager(cache)

app = Dash(
    __name__,
    background_callback_manager=background_callback_manager,
    external_stylesheets=[dbc.themes.FLATLY],
    title='Spitec'
)
app.index_string = create_index_string()
server = app.server

app.layout = create_layout()

register_callbacks(app)

if __name__ == "__main__":
    app.run_server()
