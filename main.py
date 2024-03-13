from spitec import Theme
from spitec import View

if __name__ == "__main__":
    app = View(Theme.FLATLY)
    app.create_layout()
    app.app.run_server(debug=True)