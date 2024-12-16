from dash import Dash, html

app = Dash(__name__)

app.layout = html.Div([
    html.H1("¡Hola, Azure!"),
    html.P("Esta es una aplicación simple de Dash.")
])

# No uses debug=True en producción
server = app.server

if __name__ == "__main__":
    app.run_server()

