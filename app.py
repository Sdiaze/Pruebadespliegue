from dash import Dash, html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import pandas as pd
import pyodbc
from flask import Response
from conexion_bd import (
    crear_usuario,
    verificar_credenciales,
    asignar_ubicacion,
    liberar_ubicacion,
    obtener_opciones_disponibles,
    obtener_todas_las_posiciones,
    ingresar_pallet,
    conectar_bd    
)



# --- Inicialización de la Aplicación ---
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

from flask import Response

@server.route("/health")
def health_check():
    return Response("200", status=200, mimetype='text/plain')



# --- Layouts ---
def sidebar():
    return dbc.Col(
        dbc.Nav(
            [
                dbc.NavLink("Ingresar Pallet", href="/ingresar_pallet", active="exact"),
                dbc.NavLink("Gestión", href="/gestion", active="exact"),
                dbc.NavLink("Liberar Ubicación", href="/liberar", active="exact"),
                dbc.NavLink("Visualización", href="/visualizacion", active="exact"),
                dbc.NavLink("Visualización en Tiempo Real", href="/visualizacion_realtime", active="exact"),
                dbc.NavLink("Cerrar Sesión", href="/", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
        width=2,
        style={
            "backgroundColor": "#f8f9fa",
            "padding": "20px",
            "height": "100vh",
        },
    )





def login_layout():
    """Layout para la página de inicio de sesión."""
    return html.Div(
        style={
            "backgroundImage": 'url("/assets/almacen.jpg")',
            "backgroundSize": "cover",
            "height": "100vh",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "center",
            "alignItems": "center",
        },
        children=[
            html.Div(id="login-content", children=[  # Cambiado el id a "login-content"
                html.H1(
                    "Bienvenidos al sistema de control de inventario",
                    style={
                        "color": "black",
                        "textAlign": "center",
                        "marginBottom": "30px",
                        "fontSize": "2.5rem",
                        "textShadow": "2px 2px 5px rgba(0, 0, 0, 0.5)",
                    },
                ),
                dbc.Card(
                    dbc.CardBody([
                        html.H4("Iniciar Sesión", className="card-title", style={"textAlign": "center"}),
                        dbc.Input(id="login-username", placeholder="Usuario", type="text", className="mb-2"),
                        dbc.Input(id="login-password", placeholder="Contraseña", type="password", className="mb-3"),
                        dbc.Button("Ingresar", id="login-button", color="primary", className="w-100"),
                        html.Div(id="login-feedback", className="mt-2 text-danger"),
                        dbc.Button(
                            "Crear nuevo usuario",
                            id="open-create-user-modal",
                            color="secondary",
                            className="mt-3 w-100",
                        ),
                    ]),
                    style={
                        "width": "400px",
                        "padding": "20px",
                        "boxShadow": "0px 4px 10px rgba(0, 0, 0, 0.3)",
                        "margin": "auto",
                        "displey": "block"
                    },
                ),
                # Modal para crear usuario
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Crear Usuario")),
                        dbc.ModalBody([
                            dbc.Input(id="new-username", placeholder="Nuevo Usuario", type="text", className="mb-2"),
                            dbc.Input(id="new-password", placeholder="Nueva Contraseña", type="password", className="mb-3"),
                            html.Div(id="create-user-feedback", className="mt-2 text-danger"),  # Feedback agregado aquí
                        ]),
                        dbc.ModalFooter([
                            dbc.Button("Crear Usuario", id="create-user-button", color="primary"),
                            dbc.Button("Cerrar", id="close-create-user-modal", className="ms-2"),
                        ]),
                    ],
                    id="create-user-modal",
                    is_open=False,
                ),
            ]),
        ],
    )


def gestion_layout():
    """Layout para la página de gestión de ubicaciones."""
    return html.Div([
        dbc.Row([
            sidebar(),
            dbc.Col(
                dbc.Container([
                    html.H2("Gestión de Ubicaciones de Pallets"),
                    dbc.Row([
                        dbc.Col([
                            dcc.Dropdown(id="tipo-almacen-select", placeholder="Seleccione Tipo de Almacén", options=[]),
                            dcc.Dropdown(id="piso-select", placeholder="Seleccione Piso", options=[]),
                            dcc.Dropdown(id="rack-select", placeholder="Seleccione Rack", options=[]),
                            dcc.Dropdown(id="letra-select", placeholder="Seleccione Letra", options=[]),
                            # Cambiamos el placeholder para reflejar que se ingresará NPallet
                            dbc.Input(id="pallet-id", placeholder="Ingrese el NPallet", type="text", className="mt-2"),
                            dbc.Button("Asignar Ubicación", id="assign-button", className="mt-3", color="success"),
                            html.Div(id="assign-feedback", className="mt-3"),
                        ], width=6),
                    ]),
                ]),
                width=10,
            ),
        ]),
    ])


def liberar_layout():
    """Layout para la página de liberación de ubicaciones."""
    return html.Div([
        dbc.Row([
            sidebar(),
            dbc.Col(
                dbc.Container([
                    html.H2("Liberar Ubicación de Pallet"),
                    dbc.Row([
                        dbc.Col([
                            # Cambiamos el placeholder para reflejar que se espera un string completo
                            dbc.Input(id="pallet-id-liberar", placeholder="Ingrese los datos del pallet ", type="text", className="mb-2"),
                            dbc.Button("Liberar Ubicación", id="liberar-button", color="danger", className="mt-3"),
                            html.Div(id="liberar-feedback", className="mt-3"),
                        ], width=6),
                    ]),
                ]),
                width=10,
            ),
        ]),
    ])



def visualizacion_layout():
    """Layout para la página de visualización del almacén."""
    
    # Los dropdowns ahora hacen referencia a NPallet en lugar de ID de Pallet
    filtro_dropdown = dcc.Dropdown(
        id="filtro-id-pallet",
        options=[],
        placeholder="Seleccione uno o más NPallet",
        multi=True,
        style={"marginBottom": "20px"}
    )
    filtro_variedad_dropdown = dcc.Dropdown(
        id="filtro-variedad-pallet",
        options=[],
        placeholder="Seleccione una o más Variedades",
        multi=True,
        style={"marginBottom": "20px"}
    )
    filtro_mercado_dropdown = dcc.Dropdown(
        id="filtro-mercado-pallet",
        options=[],
        placeholder="Seleccione uno o más Mercados",
        multi=True,
        style={"marginBottom": "20px"}
    )
    filtro_fecha_dropdown = dcc.Dropdown(
        id="filtro-fecha-faena",
        options=[],
        placeholder="Seleccione una o más Fechas de Faena",
        multi=True,
        style={"marginBottom": "20px"}
    )

    # Columna derecha con métricas generales, filtros y otras estadísticas
    columna_derecha = html.Div([
        # Métricas generales
        html.H4("Resumen General", className="text-primary", style={"marginBottom": "20px"}),

        # Utilización general
        html.Div([
            html.H5("Utilización General:", style={"marginBottom": "5px"}),
            html.H2(id="utilizacion-general-html", className="text-success"),  # ID para callback
        ], style={"marginBottom": "20px"}),

        # Espacios disponibles generales
        html.Div([
            html.H5("Espacios Disponibles Totales:", style={"marginBottom": "5px"}),
            html.H2(id="espacios-disponibles-general-html", className="text-success"),  # ID para callback
        ]),
        html.Hr(),

        # Filtros
        html.H5("Filtrar por NPallet", style={"marginTop": "20px"}),
        filtro_dropdown,
        html.H5("Filtrar por Variedad", style={"marginTop": "20px"}),
        filtro_variedad_dropdown,
        html.H5("Filtrar por Mercado", style={"marginTop": "20px"}),
        filtro_mercado_dropdown,
        html.H5("Filtrar por Fecha de Faena", style={"marginTop": "20px"}),
        filtro_fecha_dropdown,
        html.Hr(),
    ], style={
        "backgroundColor": "#f8f9fa",
        "padding": "20px",
        "borderRadius": "5px",
    })

    # Layout completo
    return html.Div([
        dbc.Row([
            # Barra lateral
            dbc.Col(
                sidebar(),
                xs=12, sm=12, md=3, lg=2, xl=2,
                style={"backgroundColor": "#f8f9fa", "padding": "20px", "minHeight": "100vh"}
            ),
            # Contenido principal
            dbc.Col(
                dbc.Container([
                    html.H2("Visualización del Almacén", style={"marginBottom": "30px"}),

                    # Rack 1
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H4("Utilización:", className="text-primary", style={"marginRight": "10px", "display": "inline-block"}),
                                html.H2(id="utilizacion-rack1-html", className="text-success", style={"marginRight": "30px", "display": "inline-block"}),
                                html.H4("Espacios disponibles:", className="text-primary", style={"marginRight": "10px", "display": "inline-block"}),
                                html.H2(id="disponibles-rack1-html", className="text-success", style={"display": "inline-block"}),
                            ], style={"display": "flex", "alignItems": "center", "marginBottom": "15px"}),
                        ]),
                        html.Div(id="rack1-html"),
                    ], style={"marginBottom": "50px"}),

                    # Rack 2
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H4("Utilización:", className="text-primary", style={"marginRight": "10px", "display": "inline-block"}),
                                html.H2(id="utilizacion-rack2-html", className="text-success", style={"marginRight": "30px", "display": "inline-block"}),
                                html.H4("Espacios disponibles:", className="text-primary", style={"marginRight": "10px", "display": "inline-block"}),
                                html.H2(id="disponibles-rack2-html", className="text-success", style={"display": "inline-block"}),
                            ], style={"display": "flex", "alignItems": "center", "marginBottom": "15px"}),
                        ]),
                        html.Div(id="rack2-html"),
                    ]),
                ]),
                xs=12, sm=12, md=7, lg=8, xl=8,
            ),
            # Columna derecha con métricas generales y filtros
            dbc.Col(
                columna_derecha,
                xs=12, sm=12, md=3, lg=2, xl=2,
            ),
        ], className="g-0"),
    ])


def ingresar_pallet_layout():
    """Layout para la página de ingreso de pallets usando el código QR."""
    return html.Div([
        dbc.Row([
            sidebar(),
            dbc.Col(
                dbc.Container([
                    html.H2("Ingresar Pallet desde Código QR", className="mb-4"),
                    dbc.Input(id="qr-data-input", placeholder="Escanee o ingrese el código QR", type="text", className="mb-3"),
                    dbc.Button("Ingresar Pallet", id="ingresar-pallet-button", color="primary", className="mb-4"),
                    html.Div(id="ingresar-pallet-feedback", className="mt-2")
                ]),
                width=10,
            ),
        ]),
    ])


def visualizacion_realtime_layout():
    """Layout para la página de visualización en tiempo real del almacén."""
    return html.Div([
        dbc.Row([
            sidebar(),
            dbc.Col(
                dbc.Container([
                    html.H2("Visualización en Tiempo Real del Almacén", style={"marginBottom": "30px"}),

                    # Intervalo para actualizaciones en tiempo real
                    dcc.Interval(
                        id="interval-realtime",
                        interval=5000,  # Actualiza cada 5000ms (5 segundos)
                        n_intervals=0
                    ),

                    # Rack 1
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H4("Utilización:", className="text-primary", style={"marginRight": "10px", "display": "inline-block"}),
                                html.H2(id="utilizacion-rack1-realtime-html", className="text-success", style={"marginRight": "30px", "display": "inline-block"}),
                                html.H4("Espacios disponibles:", className="text-primary", style={"marginRight": "10px", "display": "inline-block"}),
                                html.H2(id="disponibles-rack1-realtime-html", className="text-success", style={"display": "inline-block"}),
                            ], style={"display": "flex", "alignItems": "center", "marginBottom": "15px"}),
                        ]),
                        html.Div(id="rack1-realtime-html"),
                    ], style={"marginBottom": "50px"}),

                    # Rack 2
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H4("Utilización:", className="text-primary", style={"marginRight": "10px", "display": "inline-block"}),
                                html.H2(id="utilizacion-rack2-realtime-html", className="text-success", style={"marginRight": "30px", "display": "inline-block"}),
                                html.H4("Espacios disponibles:", className="text-primary", style={"marginRight": "10px", "display": "inline-block"}),
                                html.H2(id="disponibles-rack2-realtime-html", className="text-success", style={"display": "inline-block"}),
                            ], style={"display": "flex", "alignItems": "center", "marginBottom": "15px"}),
                        ]),
                        html.Div(id="rack2-realtime-html"),
                    ]),
                ]),
                xs=12, sm=12, md=10, lg=10, xl=10,
            ),
        ]),
    ])


def visualizacion_realtime_layout():
    """Layout para la página de visualización en tiempo real del almacén."""
    return html.Div([
        dbc.Row([
            sidebar(),
            dbc.Col(
                dbc.Container([
                    html.H2("Visualización en Tiempo Real del Almacén", style={"marginBottom": "30px"}),

                    # Intervalo para actualizaciones en tiempo real
                    dcc.Interval(
                        id="interval-realtime",
                        interval=2000,  # Actualiza cada 2000ms (2 segundos)
                        n_intervals=0
                    ),

                    # Rack 1
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H4("Utilización:", className="text-primary", style={"marginRight": "10px", "display": "inline-block"}),
                                html.H2(id="utilizacion-rack1-realtime-html", className="text-success", style={"marginRight": "30px", "display": "inline-block"}),
                                html.H4("Espacios disponibles:", className="text-primary", style={"marginRight": "10px", "display": "inline-block"}),
                                html.H2(id="disponibles-rack1-realtime-html", className="text-success", style={"display": "inline-block"}),
                            ], style={"display": "flex", "alignItems": "center", "marginBottom": "15px"}),
                        ]),
                        html.Div(id="rack1-realtime-html"),
                    ], style={"marginBottom": "50px"}),

                    # Rack 2
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H4("Utilización:", className="text-primary", style={"marginRight": "10px", "display": "inline-block"}),
                                html.H2(id="utilizacion-rack2-realtime-html", className="text-success", style={"marginRight": "30px", "display": "inline-block"}),
                                html.H4("Espacios disponibles:", className="text-primary", style={"marginRight": "10px", "display": "inline-block"}),
                                html.H2(id="disponibles-rack2-realtime-html", className="text-success", style={"display": "inline-block"}),
                            ], style={"display": "flex", "alignItems": "center", "marginBottom": "15px"}),
                        ]),
                        html.Div(id="rack2-realtime-html"),
                    ]),
                ]),
                xs=12, sm=12, md=10, lg=10, xl=10,
            ),
        ]),
    ])


@app.callback(
    [
        Output("rack1-realtime-html", "children"),
        Output("rack2-realtime-html", "children"),
        Output("utilizacion-rack1-realtime-html", "children"),
        Output("utilizacion-rack2-realtime-html", "children"),
        Output("disponibles-rack1-realtime-html", "children"),
        Output("disponibles-rack2-realtime-html", "children"),
    ],
    Input("interval-realtime", "n_intervals")
)
def actualizar_vista_realtime(n_intervals):
    """Actualiza los datos en tiempo real."""

    # Generar HTML de tablas dinámicas
    def generar_html_matriz(df, titulo):
        """Genera el HTML para la tabla dinámica de un rack."""
        filas = []
        encabezados = ["Piso", "Posición Pallet"] + list(df.columns)
        filas.append(html.Tr([html.Th(col, style={"textAlign": "center"}) for col in encabezados]))

        for index, row in df.iterrows():
            celdas = []
            piso, posicion = index if isinstance(index, tuple) else (index, "")
            celdas.append(html.Td(piso, style={"textAlign": "center"}))
            celdas.append(html.Td(posicion, style={"textAlign": "center"}))

            for col, val in row.items():
                estilo = {"textAlign": "center", "fontWeight": "bold", "color": "white"}
                if val == "Libre":
                    estilo["backgroundColor"] = "green"
                else:
                    estilo["backgroundColor"] = "red"
                celdas.append(html.Td(val, style=estilo))

            filas.append(html.Tr(celdas))

        return html.Div([
            html.H4(titulo, style={"marginTop": "20px", "marginBottom": "10px"}),
            html.Table(filas, className="table table-bordered table-hover", style={"marginTop": "20px"})
        ])

    # Recuperar posiciones
    posiciones = obtener_todas_las_posiciones()
    if not posiciones:
        return "Error: No hay datos disponibles", "", "", "", "", ""

    df_posiciones = pd.DataFrame.from_records(posiciones, columns=[
        "Tipo Almacén", "Piso", "Rack", "Letra", "Posición Pallet", "Estado Ubicación",
        "id_pallet_asignado", "Descripción", "Variedad", "Mercado", "Fecha Faena", "NPallet"
    ])
    df_posiciones["NPallet"] = df_posiciones["NPallet"].fillna("Libre")

    # Filtrar racks
    df_rack1 = df_posiciones[df_posiciones["Rack"] == 1]
    df_rack2 = df_posiciones[df_posiciones["Rack"] == 2]

    # Calcular métricas
    total_rack1 = len(df_rack1)
    total_rack2 = len(df_rack2)
    ocupados_rack1 = len(df_rack1[df_rack1["NPallet"] != "Libre"])
    ocupados_rack2 = len(df_rack2[df_rack2["NPallet"] != "Libre"])
    disponibles_rack1 = total_rack1 - ocupados_rack1
    disponibles_rack2 = total_rack2 - ocupados_rack2
    utilizacion_rack1 = f"{(ocupados_rack1 / total_rack1 * 100):.2f}%" if total_rack1 > 0 else "0.00%"
    utilizacion_rack2 = f"{(ocupados_rack2 / total_rack2 * 100):.2f}%" if total_rack2 > 0 else "0.00%"

    # Crear tablas dinámicas
    matriz_rack1 = pd.crosstab(
        index=[df_rack1["Piso"], df_rack1["Posición Pallet"]],
        columns=df_rack1["Letra"],
        values=df_rack1["NPallet"],
        aggfunc="first"
    ).fillna("Libre").sort_index(ascending=[False, False])

    matriz_rack2 = pd.crosstab(
        index=[df_rack2["Piso"], df_rack2["Posición Pallet"]],
        columns=df_rack2["Letra"],
        values=df_rack2["NPallet"],
        aggfunc="first"
    ).fillna("Libre").sort_index(ascending=[False, False])

    rack1_html = generar_html_matriz(matriz_rack1, "Rack 1")
    rack2_html = generar_html_matriz(matriz_rack2, "Rack 2")

    return rack1_html, rack2_html, utilizacion_rack1, utilizacion_rack2, f"{disponibles_rack1} espacios", f"{disponibles_rack2} espacios"


@app.callback(
    [Output("ingresar-pallet-feedback", "children"),
     Output("qr-data-input", "value")],
    [Input("ingresar-pallet-button", "n_clicks")],
    [State("qr-data-input", "value")],
    prevent_initial_call=True
)
def manejar_ingresar_pallet(n_clicks, qr_data):
    """Maneja el ingreso del pallet a la base de datos."""
    if qr_data:
        feedback = ingresar_pallet(qr_data)
    else:
        feedback = ""
    return feedback, ""




@app.callback(
    [Output("rack1-html", "children"),
     Output("rack2-html", "children"),
     Output("utilizacion-rack1-html", "children"),
     Output("utilizacion-rack2-html", "children"),
     Output("disponibles-rack1-html", "children"),
     Output("disponibles-rack2-html", "children"),
     Output("utilizacion-general-html", "children"),
     Output("espacios-disponibles-general-html", "children"),
     Output("filtro-id-pallet", "options"),
     Output("filtro-variedad-pallet", "options"),
     Output("filtro-mercado-pallet", "options"),
     Output("filtro-fecha-faena", "options")],
    [Input("filtro-id-pallet", "value"),
     Input("filtro-variedad-pallet", "value"),
     Input("filtro-mercado-pallet", "value"),
     Input("filtro-fecha-faena", "value")]
)
def actualizar_colores(filtro_ids, filtro_variedad, filtro_mercado, filtro_fecha_faena):
    """Actualiza las tablas, la utilización, los espacios disponibles, las métricas generales y los filtros."""
    posiciones = obtener_todas_las_posiciones()
    df_posiciones = pd.DataFrame.from_records(posiciones, columns=[
        "Tipo Almacén", "Piso", "Rack", "Letra", "Posición Pallet", "Estado Ubicación",
        "id_pallet_asignado", "Descripción", "Variedad", "Mercado", "Fecha Faena", "NPallet"
    ])
    df_posiciones["NPallet"] = df_posiciones["NPallet"].fillna("Libre")

    # Filtrar datos por racks
    df_rack1 = df_posiciones[df_posiciones["Rack"] == 1]
    df_rack2 = df_posiciones[df_posiciones["Rack"] == 2]

    # Calcular utilización y espacios disponibles por rack
    total_rack1 = len(df_rack1)
    total_rack2 = len(df_rack2)
    ocupados_rack1 = len(df_rack1[df_rack1["NPallet"] != "Libre"])
    ocupados_rack2 = len(df_rack2[df_rack2["NPallet"] != "Libre"])
    disponibles_rack1 = total_rack1 - ocupados_rack1
    disponibles_rack2 = total_rack2 - ocupados_rack2
    utilizacion_rack1 = f"{(ocupados_rack1 / total_rack1 * 100):.2f}%" if total_rack1 > 0 else "0.00%"
    utilizacion_rack2 = f"{(ocupados_rack2 / total_rack2 * 100):.2f}%" if total_rack2 > 0 else "0.00%"

    # Calcular métricas generales
    total_general = total_rack1 + total_rack2
    ocupados_general = ocupados_rack1 + ocupados_rack2
    disponibles_general = total_general - ocupados_general
    utilizacion_general = f"{(ocupados_general / total_general * 100):.2f}%" if total_general > 0 else "0.00%"

    # Crear matrices dinámicas para Rack 1 y Rack 2
    matriz_rack1 = pd.crosstab(
        index=[df_rack1["Piso"], df_rack1["Posición Pallet"]],
        columns=df_rack1["Letra"],
        values=df_rack1["NPallet"],
        aggfunc="first"
    ).fillna("Libre").sort_index(ascending=[False, False])

    matriz_rack2 = pd.crosstab(
        index=[df_rack2["Piso"], df_rack2["Posición Pallet"]],
        columns=df_rack2["Letra"],
        values=df_rack2["NPallet"],
        aggfunc="first"
    ).fillna("Libre").sort_index(ascending=[False, False])

    # Crear opciones para los dropdowns dinámicos
    id_pallet_options = [{"label": val, "value": val} for val in df_posiciones["NPallet"].unique() if val != "Libre"]
    variedad_options = [{"label": val, "value": val} for val in df_posiciones["Variedad"].dropna().unique()]
    mercado_options = [{"label": val, "value": val} for val in df_posiciones["Mercado"].dropna().unique()]
    fecha_faena_options = [{"label": str(val), "value": str(val)} for val in df_posiciones["Fecha Faena"].dropna().unique()]

    # Generar HTML de tablas con colores dinámicos
    def generar_html_matriz(df, titulo):
        filas = []
        encabezados = ["Piso", "Posición Pallet"] + list(df.columns)
        filas.append(html.Tr([html.Th(col, style={"textAlign": "center"}) for col in encabezados]))

        for index, row in df.iterrows():
            celdas = []
            piso, posicion = index
            celdas.append(html.Td(piso, style={"textAlign": "center"}))
            celdas.append(html.Td(posicion, style={"textAlign": "center"}))

            for col, val in row.items():
                estilo = {"textAlign": "center", "fontWeight": "bold", "color": "white"}

                if val == "Libre":
                    estilo["backgroundColor"] = "green"
                else:
                    variedad = df_posiciones.loc[df_posiciones["NPallet"] == val, "Variedad"].values[0]
                    mercado = df_posiciones.loc[df_posiciones["NPallet"] == val, "Mercado"].values[0]
                    fecha_faena = df_posiciones.loc[df_posiciones["NPallet"] == val, "Fecha Faena"].values[0]

                    if (
                        (filtro_ids and val in filtro_ids) or
                        (filtro_variedad and variedad in filtro_variedad) or
                        (filtro_mercado and mercado in filtro_mercado) or
                        (filtro_fecha_faena and str(fecha_faena) in filtro_fecha_faena)
                    ):
                        estilo["backgroundColor"] = "blue"
                    else:
                        estilo["backgroundColor"] = "red"

                celdas.append(html.Td(val, style=estilo))
            filas.append(html.Tr(celdas))

        return html.Div([
            html.H4(titulo, style={"marginTop": "20px", "marginBottom": "10px"}),
            html.Table(filas, className="table table-bordered table-hover", style={"marginTop": "20px"})
        ])

    rack1_html = generar_html_matriz(matriz_rack1, "Rack 1")
    rack2_html = generar_html_matriz(matriz_rack2, "Rack 2")

    return (
        rack1_html,
        rack2_html,
        utilizacion_rack1,
        utilizacion_rack2,
        f"{disponibles_rack1} espacios",
        f"{disponibles_rack2} espacios",
        utilizacion_general,
        f"{disponibles_general} espacios",
        id_pallet_options,
        variedad_options,
        mercado_options,
        fecha_faena_options
    )



# --- Callbacks ---
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if pathname == "/ingresar_pallet":
        return ingresar_pallet_layout()
    elif pathname == "/gestion":
        return gestion_layout()
    elif pathname == "/liberar":
        return liberar_layout()
    elif pathname == "/visualizacion":
        return visualizacion_layout()
    elif pathname == "/visualizacion_realtime":
        return visualizacion_realtime_layout()
    return login_layout()


@app.callback(
    [
        Output("assign-feedback", "children"),
        Output("tipo-almacen-select", "options"),
        Output("piso-select", "options"),
        Output("rack-select", "options"),
        Output("letra-select", "options"),
        Output("pallet-id", "value"),  # Limpiar el campo después del clic
    ],
    [
        Input("tipo-almacen-select", "value"),
        Input("piso-select", "value"),
        Input("rack-select", "value"),
        Input("assign-button", "n_clicks"),
    ],
    [
        State("letra-select", "value"),
        State("pallet-id", "value"),  # Aquí se ingresará el string completo
    ],
)
def asignar_y_refrescar(tipo_almacen, piso, rack, n_clicks, letra, pallet_data):
    # Obtener las opciones disponibles basadas en los filtros seleccionados
    tipos_almacen, pisos, racks, letras = obtener_opciones_disponibles(
        tipo_almacen=tipo_almacen, piso=piso, rack=rack, letra=letra
    )

    # Convertir resultados a formato para dropdowns
    tipos_almacen_options = [{"label": t, "value": t} for t in tipos_almacen]
    pisos_options = [{"label": p, "value": p} for p in pisos]
    racks_options = [{"label": r, "value": r} for r in racks]
    letras_options = [{"label": l, "value": l} for l in letras]

    # Verificar si el botón de asignar fue presionado
    if n_clicks:
        # Validar que todos los campos requeridos estén llenos
        if not all([tipo_almacen, piso, rack, letra, pallet_data]):
            return (
                dbc.Alert(
                    "Por favor, complete todos los campos antes de asignar.",
                    color="danger",
                ),
                tipos_almacen_options,
                pisos_options,
                racks_options,
                letras_options,
                pallet_data,  # No limpiar el campo si hay error
            )

        # Extraer el NPallet del string ingresado
        try:
            n_pallet = pallet_data.split(",")[-1].strip()  # Extraer el último campo (NPallet)
            if len(n_pallet) != 8 or not n_pallet.isdigit():
                raise ValueError("El NPallet extraído no es válido.")
        except Exception as e:
            return (
                dbc.Alert(
                    f"Error al procesar el dato ingresado: {str(e)}. Asegúrese de usar el formato correcto.",
                    color="danger",
                ),
                tipos_almacen_options,
                pisos_options,
                racks_options,
                letras_options,
                pallet_data,  # No limpiar el campo si hay error
            )

        # Convertir el NPallet al id_pallet
        conn = conectar_bd()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id_pallet FROM pallets WHERE NPallet = ?", (n_pallet,))
            result = cursor.fetchone()
            if result is None:
                return (
                    dbc.Alert(f"El NPallet '{n_pallet}' no existe en la base de datos.", color="danger"),
                    tipos_almacen_options,
                    pisos_options,
                    racks_options,
                    letras_options,
                    pallet_data,  # No limpiar el campo si hay error
                )
            id_pallet = result[0]  # Obtener el id_pallet correspondiente
        except pyodbc.Error as e:
            return (
                dbc.Alert(f"Error al buscar el NPallet: {e}", color="danger"),
                tipos_almacen_options,
                pisos_options,
                racks_options,
                letras_options,
                pallet_data,  # No limpiar el campo si hay error
            )
        finally:
            conn.close()

        # Intentar asignar el pallet usando id_pallet
        mensaje = asignar_ubicacion(id_pallet, tipo_almacen, piso, rack, letra)

        # Retornar mensaje de éxito o error
        color = "success" if "Error" not in mensaje else "danger"
        if color == "success":
            mensaje = f"Pallet con NPallet {n_pallet} asignado a la ubicación {tipo_almacen}, {piso}, {rack}, {letra}."
            return (
                dbc.Alert(mensaje, color=color),
                tipos_almacen_options,
                pisos_options,
                racks_options,
                letras_options,
                "",  # Limpiar el campo si se asignó correctamente
            )
        else:
            return (
                dbc.Alert(mensaje, color=color),
                tipos_almacen_options,
                pisos_options,
                racks_options,
                letras_options,
                pallet_data,  # No limpiar el campo si hay error
            )

    # Si no se presionó el botón, solo actualiza las opciones dinámicas
    return "", tipos_almacen_options, pisos_options, racks_options, letras_options, pallet_data




@app.callback(
    Output("liberar-feedback", "children"),
    Input("liberar-button", "n_clicks"),
    State("pallet-id-liberar", "value")
)
def handle_liberar_pallet(n_clicks, pallet_data):
    """Libera la ubicación del pallet especificado utilizando NPallet."""
    if n_clicks:
        if not pallet_data:
            return dbc.Alert("Ingrese los datos del pallet.", color="danger")

        # Extraer el NPallet del string ingresado
        try:
            n_pallet = pallet_data.split(",")[-1].strip()  # Extraer el último campo (NPallet)
            if len(n_pallet) != 8 or not n_pallet.isdigit():
                raise ValueError("El NPallet extraído no es válido.")
        except Exception as e:
            return dbc.Alert(
                f"Error al procesar los datos ingresados: {str(e)}. Asegúrese de usar el formato correcto.",
                color="danger"
            )

        # Convertir el NPallet al id_pallet
        conn = conectar_bd()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id_pallet FROM pallets WHERE NPallet = ?", (n_pallet,))
            result = cursor.fetchone()
            if result is None:
                return dbc.Alert(f"El NPallet '{n_pallet}' no existe en la base de datos.", color="danger")
            id_pallet = result[0]  # Obtener el id_pallet correspondiente
        except pyodbc.Error as e:
            return dbc.Alert(f"Error al buscar el NPallet: {e}", color="danger")
        finally:
            conn.close()

        # Liberar la ubicación utilizando el id_pallet
        mensaje = liberar_ubicacion(id_pallet)

        # Ajustar el mensaje final
        if "Ubicación liberada y reorganizada" in mensaje:
            mensaje = f"Pallet ({n_pallet}) liberado y ubicación reorganizada exitosamente."
            color = "success"
        elif "posición 1" in mensaje:
            mensaje = f"Error: Solo se puede liberar el Pallet con NPallet {n_pallet} desde la posición 1."
            color = "danger"
        elif "no está asignado a ninguna ubicación" in mensaje:
            mensaje = f"Error: El Pallet con NPallet {n_pallet} no está asignado a ninguna ubicación."
            color = "danger"
        else:
            mensaje = f"Error al liberar la ubicación para el Pallet con NPallet {n_pallet}: {mensaje}"
            color = "danger"

        return dbc.Alert(mensaje, color=color)

    return ""








@app.callback(
    Output("create-user-modal", "is_open"),
    [Input("open-create-user-modal", "n_clicks"),
     Input("close-create-user-modal", "n_clicks")],
    [State("create-user-modal", "is_open")]
)
def toggle_create_user_modal(open_clicks, close_clicks, is_open):
    if open_clicks or close_clicks:
        return not is_open
    return is_open


@app.callback(
    [Output("login-feedback", "children"), Output("url", "pathname")],
    Input("login-button", "n_clicks"),
    [State("login-username", "value"), State("login-password", "value")],
    prevent_initial_call=True  # Evita que el callback se ejecute al cargar la página
)
def handle_login(n_clicks, username, password):
    """Maneja el inicio de sesión y valida las credenciales."""
    if n_clicks:
        # Verificar si los campos están vacíos
        if not username or not password:
            return dbc.Alert("Por favor, complete los campos de usuario y contraseña.", color="warning"), no_update

        # Validar las credenciales
        if verificar_credenciales(username, password):
            # Inicio de sesión exitoso, permite la redirección
            return "", "/gestion"

        # Credenciales incorrectas
        return dbc.Alert("Credenciales incorrectas. Por favor, intente de nuevo.", color="danger"), no_update

    # Estado inicial: sin interacción
    return "", no_update






@app.callback(
    [
        Output("new-username", "value"),  # Limpia el campo de nuevo usuario
        Output("new-password", "value"),  # Limpia el campo de nueva contraseña
        Output("create-user-feedback", "children"),  # Muestra el mensaje de feedback
    ],
    Input("create-user-button", "n_clicks"),
    State("new-username", "value"),
    State("new-password", "value"),
    prevent_initial_call=True  # Evita que el callback se dispare al cargar la página
)
def handle_create_user(n_clicks, username, password):
    """Maneja la creación de usuarios y limpia los campos si es exitoso."""
    if n_clicks:
        if username and password:
            resultado = crear_usuario(username, password)
            if resultado is True:
                # Usuario creado con éxito; limpia los campos y muestra feedback
                return "", "", dbc.Alert("Usuario creado exitosamente.", color="success")
            else:
                # Error al crear usuario; no limpia los campos
                return no_update, no_update, dbc.Alert("Error al crear usuario. Es posible que el usuario ya exista.", color="danger")
        # Campos incompletos
        return no_update, no_update, dbc.Alert("Por favor, complete todos los campos.", color="danger")
    # Retorno inicial (en teoría, no debería ejecutarse debido a prevent_initial_call)
    return no_update, no_update, ""



# --- Layout Inicial ---
app.layout = html.Div([
    dcc.Location(id="url", refresh=True),  # Maneja las redirecciones
    html.Div(id="page-content")  # Contenedor para el contenido de la página
])


# --- Ejecutar la Aplicación ---
if __name__ == "__main__":
    app.run_server(debug=True)