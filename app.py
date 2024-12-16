import dash
from dash import html

# Inicializa la aplicación
app = dash.Dash(__name__)
server = app.server  # Necesario para Azure y Gunicorn

# Layout básico
app.layout = html.Div([
    html.H1("¡Hola, Azure!"),
    html.P("Esta es una aplicación de Dash desplegada correctamente.")
])

if __name__ == "__main__":
    app.run_server(debug=True)


