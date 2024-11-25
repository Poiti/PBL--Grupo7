import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import os

# Inicializa o app
app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

# Caminho dos arquivos Excel
data_file = "dados_sensores.xlsx"
historico_file = "historico_pacientes.xlsx"
last_modified = 0
df_sensores = None  # Dados iniciais carregados dinamicamente

# Função para recarregar os dados do Excel somente se o arquivo foi modificado
def reload_data_if_needed():
    global last_modified, df_sensores
    if os.path.exists(data_file):
        current_modified = os.path.getmtime(data_file)
        if current_modified > last_modified:
            last_modified = current_modified
            with pd.ExcelFile(data_file) as xls:
                df_sensores = pd.read_excel(xls)
    else:
        raise FileNotFoundError(f"Arquivo {data_file} não encontrado.")

# Função para salvar o histórico de cada paciente
def save_to_historico(patient_name, pitch, roll):
    if not os.path.exists(historico_file):
        df_historico = pd.DataFrame(columns=["Paciente", "Pitch", "Roll", "Timestamp"])
    else:
        df_historico = pd.read_excel(historico_file)
    
    # Adicionar novo registro ao histórico
    new_data = pd.DataFrame({
        "Paciente": [patient_name],
        "Pitch": [pitch],
        "Roll": [roll],
        "Timestamp": [pd.Timestamp.now()]
    })
    df_historico = pd.concat([df_historico, new_data], ignore_index=True)
    df_historico.to_excel(historico_file, index=False)

# Função para carregar o histórico de um paciente
def load_historico(patient_name):
    if os.path.exists(historico_file):
        df_historico = pd.read_excel(historico_file)
        return df_historico[df_historico["Paciente"] == patient_name]
    return pd.DataFrame(columns=["Paciente", "Pitch", "Roll", "Timestamp"])

# Função para limpar o arquivo dados_sensores.xlsx
def clear_data_file():
    if os.path.exists(data_file):
        df_empty = pd.DataFrame(columns=["Accel_X", "Accel_Y", "Accel_Z", "Gyro_X", "Gyro_Y", "Gyro_Z", "Pitch_Filtered", "Roll_Filtered"])
        df_empty.to_excel(data_file, index=False)

# Layout de login
def login_layout():
    return html.Div(
        style={
            'width': '30%', 'margin': 'auto', 'padding': '40px', 'backgroundColor': 'white', 'borderRadius': '10px',
            'boxShadow': '0 4px 8px rgba(0, 0, 0, 0.1)', 'textAlign': 'center'
        },
        children=[
            html.H2("Login do Paciente", style={'color': '#2c3e50', 'marginBottom': '30px'}),
            dcc.Input(id="username", type="text", placeholder="Nome do Paciente",
                      style={'width': '100%', 'padding': '10px', 'margin': '10px 0'}),
            html.Button('Login', id='login-button', n_clicks=0,
                        style={'width': '100%', 'padding': '10px', 'backgroundColor': '#3498db', 'color': 'white',
                               'border': 'none', 'borderRadius': '5px'}),
            html.Div(id='login-output', style={'color': 'red', 'marginTop': '10px'})
        ]
    )

# Layout do dashboard com abas
def dashboard_layout(patient_name):
    return html.Div(style={'padding': '20px'}, children=[
        html.H1(f"Dashboard do Paciente: {patient_name}", style={'color': '#2c3e50', 'textAlign': 'center'}),
        dcc.Store(id='patient-name-store', data=patient_name),  # Armazenar o nome do paciente
        html.Button('Apagar Todos os Dados', id='clear-all-button', n_clicks=0, 
                    style={
                        'marginBottom': '20px', 'backgroundColor': '#e74c3c', 'color': 'white', 
                        'border': 'none', 'padding': '10px', 'borderRadius': '5px'
                    }),
        dcc.Tabs(id="tabs-example", value='tab-1', children=[
            dcc.Tab(label='Gráficos Pitch e Roll', value='tab-1'),
            dcc.Tab(label='Histórico do Paciente', value='tab-2'),
        ]),
        html.Div(id='tabs-content'),
        dcc.Interval(id='interval-component', interval=2*1000, n_intervals=0)  # Atualiza a cada 2 segundos
    ])

# Callback para lidar com o login
@app.callback(
    Output('page-content', 'children'),
    [Input('login-button', 'n_clicks')],
    [State('username', 'value')]
)
def successful_login(n_clicks, username):
    if n_clicks > 0 and username:
        return dashboard_layout(username)
    return login_layout()

# Callback para renderizar o conteúdo das abas
@app.callback(
    Output('tabs-content', 'children'),
    [Input('tabs-example', 'value'),
     Input('interval-component', 'n_intervals')],
    [State('patient-name-store', 'data')]
)
def render_tabs(tab, n_intervals, patient_name):
    try:
        reload_data_if_needed()
    except FileNotFoundError as e:
        return html.Div(f"Erro: {e}")

    if tab == 'tab-1':
        # Criar gráficos interativos para Pitch e Roll
        fig_pitch = go.Figure(go.Scatter(x=df_sensores.index, y=df_sensores['Pitch_Filtered'], mode='lines+markers'))
        fig_pitch.update_layout(title="Pitch Filtrado ao Longo do Tempo", xaxis_title="Tempo", yaxis_title="Pitch")

        fig_roll = go.Figure(go.Scatter(x=df_sensores.index, y=df_sensores['Roll_Filtered'], mode='lines+markers'))
        fig_roll.update_layout(title="Roll Filtrado ao Longo do Tempo", xaxis_title="Tempo", yaxis_title="Roll")

        return html.Div([
            html.Div([dcc.Graph(figure=fig_pitch)], style={'width': '48%', 'display': 'inline-block'}),
            html.Div([dcc.Graph(figure=fig_roll)], style={'width': '48%', 'display': 'inline-block'}),
        ])

    elif tab == 'tab-2':
        # Exibir o histórico do paciente
        df_historico = load_historico(patient_name)
        table = html.Table([
            html.Thead(html.Tr([html.Th(col) for col in df_historico.columns])),
            html.Tbody([
                html.Tr([html.Td(df_historico.iloc[i][col]) for col in df_historico.columns])
                for i in range(len(df_historico))
            ])
        ])

        return html.Div([
            html.H3("Histórico do Paciente"),
            table,
            html.Button('Limpar Dados de Sensores', id='clear-button', n_clicks=0, style={
                'marginTop': '20px', 'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'padding': '10px',
                'borderRadius': '5px'
            })
        ])

# Callback para limpar os dados de uma aba específica
@app.callback(
    Output('tabs-content', 'children'),
    [Input('clear-button', 'n_clicks')],
    [State('tabs-example', 'value'), State('patient-name-store', 'data')]
)
def clear_data(n_clicks, tab, patient_name):
    if n_clicks > 0:
        clear_data_file()
    return render_tabs(tab, 0, patient_name)

# Callback para limpar todos os dados
@app.callback(
    Output('tabs-content', 'children'),
    [Input('clear-all-button', 'n_clicks')],
    [State('tabs-example', 'value'), State('patient-name-store', 'data')]
)
def clear_all_data(n_clicks, tab, patient_name):
    if n_clicks > 0:
        clear_data_file()
    return render_tabs(tab, 0, patient_name)

# Layout inicial
app.layout = html.Div(id='page-content', children=[login_layout()])

# Roda o servidor
if __name__ == '__main__':
    app.run_server(debug=True)
