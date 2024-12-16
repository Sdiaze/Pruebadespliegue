from dash import Dash, html

app = Dash(__name__)

app.layout = html.Div([
    html.H1("¡Hola, Azure!"),
    html.P("Esta es una aplicación simple de Dash.")
])

if __name__ == "__main__":
    app.run_server(debug=True)
