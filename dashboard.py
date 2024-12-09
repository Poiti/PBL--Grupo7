import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import os
from datetime import datetime
import csv
import numpy as np

# Inicializa o app
app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

# Caminho para o arquivo CSV
DATA_FILE = 'sensor_data.csv'

def read_sensor_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
        
            return df
        except Exception as e:
            print(f"Erro ao ler o arquivo CSV: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def load_patient_feedback(patient_name):
    filename = f'{patient_name}_sessions.csv'
    if os.path.exists(filename):
        try:
            df = pd.read_csv(filename, encoding='ISO-8859-1', on_bad_lines='skip')
            return df
        except pd.errors.EmptyDataError:
            return pd.DataFrame()
    return pd.DataFrame()

def calculate_g7_metric_from_plotted_data(df_feedback, joint):
    """
    Calcula a Métrica G7 com base nos valores transformados e plotados no gráfico de Ângulo por Tempo.
    """
    # Filtra os dados para a articulação selecionada
    df_filtered = df_feedback[df_feedback['Articulação'] == joint]

    # Inicializa listas para armazenar os valores máximos
    max_with_current = None
    max_without_current = None

    for _, row in df_filtered.iterrows():
        # Extrai os ângulos já processados e usados no gráfico (Transformação: 180 - angle)
        angles = row['Trimmed Angle']  # Usa os valores normalizados e ajustados plotados no gráfico

        if row['Condition'] == 'Corrente':
            # Obtém o máximo dos valores plotados para "Corrente"
            max_with_current = max(max_with_current or 0, max(angles))
        elif row['Condition'] == 'Sem Corrente':
            # Obtém o máximo dos valores plotados para "Sem Corrente"
            max_without_current = max(max_without_current or 0, max(angles))

    # Verifica se há dados suficientes para o cálculo
    if max_with_current is None or max_without_current is None:
        return "Erro: Dados insuficientes para calcular a Métrica G7."

    # Verifica se o pico sem corrente é zero (evita divisão por zero)
    if max_without_current == 0:
        return "Erro: Pico máximo sem corrente é zero. Não é possível calcular a Métrica G7."

    # Calcula a Métrica G7
    metric_g7 = ((max_with_current - max_without_current) / max_without_current) * 1

    return metric_g7








# Função para carregar o histórico do paciente e calcular métricas
# Função para carregar o histórico do paciente e lidar com os valores salvos
def load_patient_history(patient_name):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(BASE_DIR, f'{patient_name}_sessions.csv')

    # Lista de colunas esperadas na ordem correta
    expected_columns = ['Patient Name', 'Session Time', 'Condition', 'Articulação',
                        'Valor Corrente', 'Pitch 1', 'Roll 1', 'Pitch 2', 'Roll 2', 'Angle Between Sensors']

    if os.path.exists(filename):
        try:
            if os.stat(filename).st_size == 0:
                print(f"Arquivo {filename} está vazio!")
                return pd.DataFrame(columns=expected_columns)

            # Lê o arquivo ignorando o cabeçalho e atribui os nomes das colunas manualmente
            df = pd.read_csv(
                filename,
                header=None,  # Ignora o cabeçalho do arquivo
                names=expected_columns,  # Define os nomes das colunas manualmente
                skiprows=1,
                encoding='utf-8',
                na_values=["", " "],
                quotechar='"',
                on_bad_lines='skip'
            )

             # Converte listas para strings para colunas problemáticas
            if 'Angle Between Sensors' in df.columns:
                df['Angle Between Sensors'] = df['Angle Between Sensors'].apply(
                    lambda x: ', '.join(map(str, x)) if isinstance(x, list) else x
                )

            print("Colunas ajustadas:", df.columns)
            print("Primeiras linhas do DataFrame:", df.head())
            return df
                                
            return df

        except Exception as e:
            print(f"Erro ao carregar o arquivo: {e}")
            return pd.DataFrame(columns=expected_columns)
    print(f"Arquivo {filename} não encontrado!")
    return pd.DataFrame(columns=expected_columns)


def preprocess_angle_data(df_feedback):
    # Aplica alterações específicas para certos pacientes, articulações e condições
    for index, row in df_feedback.iterrows():
        if row['Patient Name'] == 'Perso' and row['Articulação'] == 'Punho' and row['Condition'] == 'Corrente' and row['Valor Corrente'] == 23:
            # Inverte o sinal e aplica o valor absoluto
            angles = list(map(float, row['Angle Between Sensors'].split(', ')))
            adjusted_angles = [abs(x) for x in [-x for x in angles]]  # Inverte o sinal e usa o valor absoluto
            df_feedback.at[index, 'Angle Between Sensors'] = ', '.join(map(str, adjusted_angles))

    return df_feedback

@app.callback(
    [Output('condition-status', 'children'),
     Output('mark-condition', 'children')],  # Atualiza o texto do status e do botão
    [Input('mark-condition', 'n_clicks')]
)
def toggle_condition(n_clicks):
    # Define a condição com base no número de cliques
    if n_clicks % 2 == 1:  # Ímpar -> Corrente
        return "Condição: Corrente", "Alterar para Sem Corrente"
    else:  # Par ou 0 -> Sem Corrente
        return "Condição: Sem Corrente", "Alterar para Corrente"

@app.callback(
    [Output('joint-status', 'children'),
     Output('mark-joint', 'children')],  # Atualiza o status e o texto do botão
    [Input('mark-joint', 'n_clicks')]
)
def toggle_joint(n_clicks):
    # Define a articulação com base no número de cliques
    if n_clicks % 2 == 1:  # Ímpar -> Cotovelo
        return "Articulação: Cotovelo", "Alterar para Punho"
    else:  # Par ou 0 -> Punho
        return "Articulação: Punho", "Alterar para Cotovelo"
    
@app.callback(
    Output('current-condition-input-container', 'style'),
    [Input('mark-condition', 'n_clicks')]
)
def toggle_current_condition_input(n_clicks):
    # Exibe a caixa de texto apenas se o número de cliques for ímpar (Corrente ativa)
    if n_clicks % 2 == 1:
        return {'display': 'block', 'marginTop': '10px'}
    return {'display': 'none', 'marginTop': '10px'}

# Função para o layout inicial de login
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
                        style={'width': '100%', 'padding': '10px 0', 'backgroundColor': '#3498db', 'color': 'white',
                               'border': 'none', 'borderRadius': '10px'}),
            html.Div(id='login-output', style={'color': 'red', 'marginTop': '10px'})
        ]
    )

# Layout do dashboard
dashboard_layout = lambda patient_name: html.Div(style={'padding': '20px'}, children=[
    html.H1(f"Dashboard do Paciente: {patient_name}", style={'color': '#2c3e50', 'textAlign': 'center'}),

    # Divisão para exibir informações gerais e os botões de controle
    html.Div(
        style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'flex-start',
            'marginBottom': '20px'
        },
        children=[
            # Caixa de dados gerais
            html.Div(
                style={
                    'width': '30%',
                    'backgroundColor': '#f4f4f4',
                    'padding': '10px',
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)'
                },
                children=[
                    html.H4("Dados Gerais", style={'marginBottom': '10px'}),
                    html.Div(id="general-info", style={'fontSize': '16px'})
                ]
            ),
            # Botões de controle
            html.Div([
                dcc.Input(id="patient-name", type="text", value=patient_name, readOnly=True, style={'display': 'none'}),
                html.Button('Iniciar Análise', id='start-analysis', n_clicks=0, 
                    style={'padding': '10px 20px', 'backgroundColor': '#e74c3c', 'color': 'white', 
                           'border': 'none', 'borderRadius': '5px'}),
                html.Div(id='analysis-status', style={'color': 'green', 'marginTop': '10px','marginBottom': '10px'}),
                html.Div(
                    style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'flex-start', 'gap': '20px'},
                    children=[
                        # Botão Corrente / Sem Corrente com status abaixo
                        html.Div(
                            children=[
                                html.Button('Alterar para Corrente', id='mark-condition', n_clicks=0, 
                                            style={'padding': '10px 20px', 'backgroundColor': '#9b59b6', 'color': 'white',
                                                'border': 'none', 'borderRadius': '5px','marginTop': '10px'}),
                                html.Div(id='condition-status', style={'color': 'blue', 'marginTop': '5px'})
                            ],
                            style={'textAlign': 'center'}
                        ),
                        html.Div(
                            id='current-condition-input-container',
                            style={'display': 'none', 'marginTop': '10px'},  # Inicialmente escondido
                            children=[
                                html.Label("Valor da corrente: ", style={'color': 'green', 'fontSize': '20px'}),
                                dcc.Input(
                                    id='current-condition-value',
                                    type='number',
                                    placeholder='Digite um número',
                                    style={'width': '100px', 'padding': '5px', 'marginTop': '5px'}
                                )
                            ]
                        ),
                        # Botão Punho / Cotovelo com status abaixo
                        html.Div(
                            children=[
                                html.Button('Alterar para Cotovelo', id='mark-joint', n_clicks=0, 
                                            style={'padding': '10px 20px', 'backgroundColor': '#8e44ad', 'color': 'white',
                                                'border': 'none', 'borderRadius': '5px','marginTop': '10px'}),
                                html.Div(id='joint-status', style={'color': 'blue', 'marginTop': '5px'})
                            ],
                            style={'textAlign': 'center'}
                        )
                    ]
                ),
                html.Button('Salvar Dados do Paciente', id='save-session', n_clicks=0,
                            style={'padding': '10px 20px', 'backgroundColor': '#2ecc71', 'color': 'white',
                                   'border': 'none', 'borderRadius': '5px','marginTop': '10px'}),
                html.Div(id='save-output', style={'color': 'green',}),
            ], style={'textAlign': 'center'})
        ]
    ),

    # Abas de navegação
    dcc.Tabs(id="tabs-example", value='tab-1', children=[
        dcc.Tab(label='Gráficos em Tempo Real', value='tab-1', style={'backgroundColor': '#3498db', 'color': 'white'}),
        dcc.Tab(label='Histórico do Paciente', value='tab-2', style={'backgroundColor': '#3498db', 'color': 'white'}),
        dcc.Tab(label='Feedback Visual', value='tab-3', style={'backgroundColor': '#3498db', 'color': 'white'}),
    ]),

    html.Div(id='tabs-content'),

    # Intervalo para atualização em tempo real
    dcc.Interval(
        id='interval-component',
        interval=1*500,  # Atualiza a cada 1 segundo
        n_intervals=0
    )
])

@app.callback(
    Output('general-info', 'children'),
    [Input('patient-name', 'value'),
     Input('joint-status', 'children'),
     Input('condition-status', 'children'),
     Input('save-session', 'n_clicks'),
     Input('tabs-example', 'value')],
    [State('current-condition-value', 'value')]
)
def update_general_info(patient_name, joint_status, condition_status, save_clicks, active_tab, current_value):
    # Determina se os dados foram salvos

    df_history = load_patient_history(patient_name)

    # Conta o número de testes realizados (linhas no histórico)
    tests_done = len(df_history) if not df_history.empty else 0

    save_status = "Sim" if save_clicks > 0 else "Não"


    # Monta a informação geral
    return html.Div([
        html.P(f"Nome do Paciente: {patient_name}"),
        html.P(f" {joint_status}"),
        html.P(f"{condition_status}"),
        html.P(f"Corrente Ativa: {current_value if current_value else 'Nenhuma'}"),
        html.P(f"Dados Salvos: {save_status}"),
        html.P(f"Testes Realizados: {tests_done}")
    ])



# Callback para lidar com o login
@app.callback(
    Output('page-content', 'children'),
    [Input('login-button', 'n_clicks')],
    [State('username', 'value')]
)
def successful_login(n_clicks, username):
    if n_clicks > 0 and username:
        return dashboard_layout(username)  # Exibe o dashboard após login bem-sucedido
    return login_layout()

@app.callback(
    [Output('interval-component', 'disabled'),  # Controla o gráfico em tempo real
     Output('analysis-status', 'children'),  # Atualiza o status da análise
     Output('start-analysis', 'children')],  # Atualiza o texto do botão
    [Input('start-analysis', 'n_clicks')]  # Botão de análise
)
def toggle_analysis(n_clicks):
    if n_clicks > 0:
        is_running = n_clicks % 2 == 1  # Ímpar: iniciar; Par: parar
        if is_running:
            # Apaga os dados do sensor_data.csv, mas mantém os cabeçalhos
            with open('sensor_data.csv', 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Timestamp', 'Pitch 1', 'Roll 1', 'Pitch 2', 'Roll 2', 'Angle Between Sensors'])
            return False, "Análise iniciada. Gráfico em tempo real ativo.", "Parar Análise"
        else:
            return True, "Análise pausada.", "Iniciar Análise"
    return True, "Clique no botão para iniciar a análise.", "Iniciar Análise"


@app.callback(
    Output('tabs-content', 'children'),
    [Input('tabs-example', 'value'),  # Aba selecionada
     Input('interval-component', 'n_intervals')],  # Atualização em tempo real
    [State('patient-name', 'value')]  # Nome do paciente
)
def render_content(tab, n_intervals, patient_name):
    df = read_sensor_data()  # Lê os dados do sensor_data.csv
    if df.empty:
        return html.Div([html.H3("Nenhum dado disponível em tempo real.")])

    if tab == 'tab-1':  # Gráficos em Tempo Real
        if 'Timestamp' in df.columns and 'Angle Between Sensors' in df.columns:
            # Converte 'Timestamp' para segundos
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df['Seconds'] = (df['Timestamp'] - df['Timestamp'].iloc[0]).dt.total_seconds()

            # Inverte os valores de 'Angle Between Sensors' para mudar a direção
            df['Angle Between Sensors'] = 180 - df['Angle Between Sensors']

            # Cria o gráfico
            fig = go.Figure(go.Scatter(x=df['Seconds'], y=df['Angle Between Sensors'], mode='lines+markers'))
            fig.update_layout(
                title="Ângulo entre Sensores ao Longo do Tempo (Tempo Real)",
                xaxis_title="Tempo (segundos)",
                yaxis_title="Ângulo (°)"
            )
            return html.Div([dcc.Graph(figure=fig)])
        return html.Div([html.H3("Colunas 'Timestamp' ou 'Angle Between Sensors' não encontradas no sensor_data.csv.")])

    elif tab == 'tab-2':  # Histórico do Paciente
        df_history = load_patient_history(patient_name)
        if not df_history.empty:
            return html.Div([
                html.H3("Histórico de Sessões Recentes"),
                dash.dash_table.DataTable(
                    data=df_history.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in df_history.columns],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'}
                )
            ])
        return html.Div([html.H3("Nenhuma sessão encontrada para o paciente.")])

    elif tab == 'tab-3':
        return html.Div([
            html.Label("Selecione o Tipo de Teste:", style={'fontSize': '18px', 'marginBottom': '10px'}),
            dcc.Dropdown(
                id='test-selector',
                options=[
                    {'label': 'Ângulo por Tempo', 'value': 'angle_time'},
                    {'label': 'Velocidade por Tempo', 'value': 'speed_time'},
                    {'label': 'Métrica G7', 'value': 'metric_g7'}
                ],
                value='angle_time',  # Valor padrão
                clearable=False,
                style={'width': '50%', 'marginBottom': '20px'}
            ),
            html.Label("Selecione a Articulação:", style={'fontSize': '18px', 'marginBottom': '10px'}),
            dcc.Dropdown(
                id='joint-selector',
                options=[
                    {'label': 'Punho', 'value': 'Punho'},
                    {'label': 'Cotovelo', 'value': 'Cotovelo'}
                ],
                value='Punho',  # Valor padrão
                clearable=False,
                style={'width': '50%', 'marginBottom': '10px'}
            ),
            html.Div(id='feedback-graph-container')
        ])



# Callback para salvar os dados do paciente
@app.callback(
    Output('save-output', 'children'),
    [Input('save-session', 'n_clicks')],
    [State('patient-name', 'value'),
     State('mark-condition', 'n_clicks'),
     State('current-condition-value', 'value'),
     State('mark-joint', 'n_clicks')]
)
def save_patient_data(n_clicks, patient_name, condition_n_clicks, current_value, joint_n_clicks):
    df = read_sensor_data()
    if n_clicks > 0 and not df.empty:
        session_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        filename = f'{patient_name}_sessions.csv'

        # Determina a condição e a articulação com base nos cliques
        condition = "Corrente" if condition_n_clicks % 2 == 1 else "Sem Corrente"
        joint = "Cotovelo" if joint_n_clicks % 2 == 1 else "Punho"

        # Calcula os valores de Pitch, Roll e Ângulo entre Sensores
        pitch1_values = ", ".join(map(str, df['Pitch 1'].tolist())) if 'Pitch 1' in df.columns else ""
        roll1_values = ", ".join(map(str, df['Roll 1'].tolist())) if 'Roll 1' in df.columns else ""
        pitch2_values = ", ".join(map(str, df['Pitch 2'].tolist())) if 'Pitch 2' in df.columns else ""
        roll2_values = ", ".join(map(str, df['Roll 2'].tolist())) if 'Roll 2' in df.columns else ""
        angle_values = ", ".join(map(str, df['Angle Between Sensors'].tolist())) if 'Angle Between Sensors' in df.columns else ""

        # Verifica se o arquivo já existe
        file_exists = os.path.exists(filename)

        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)

            # Escreve o cabeçalho somente se o arquivo ainda não existir
            if not file_exists:
                writer.writerow([
                    'Patient Name',
                    'Session Time',
                    'Condition',
                    'Articulação',
                    'Valor Corrente',  # Nova coluna
                    'Pitch 1',
                    'Roll 1',
                    'Pitch 2',
                    'Roll 2',
                    'Angle Between Sensors'
                ])

            # Salva apenas uma linha com todos os valores detalhados
            writer.writerow([
                patient_name,  # Nome do paciente
                session_time,  # Tempo da sessão
                condition,  # Condição
                joint,  # Articulação
                current_value if condition == "Corrente" else None,  # Valor Corrente (apenas se Corrente estiver ativa)
                pitch1_values,  # Todos os valores de Pitch 1
                roll1_values,  # Todos os valores de Roll 1
                pitch2_values,  # Todos os valores de Pitch 2
                roll2_values,  # Todos os valores de Roll 2
                angle_values  # Todos os valores de Ângulo entre Sensores
            ])

        return f"Dados da sessão do paciente '{patient_name}' salvos com sucesso!"
    return "Nenhuma sessão foi salva."


@app.callback(
    Output('feedback-graph-container', 'children'),
    [Input('joint-selector', 'value'),
     Input('test-selector','value')],  # Entrada do dropdown para articulação
    [State('patient-name', 'value')]  # Nome do paciente
)
def update_feedback_graph(selected_joint, selected_test, patient_name):
    # Carrega os dados do histórico do paciente
    df_feedback = load_patient_history(patient_name)
    if df_feedback.empty:
        return html.Div([html.H3("Nenhum dado de feedback disponível para o paciente.")])


    df_feedback = preprocess_angle_data(df_feedback)
     # Filtra os dados pela articulação selecionada
    df_feedback = df_feedback[df_feedback['Articulação'] == selected_joint]
    if df_feedback.empty:
        return html.Div([html.H3(f"Nenhum dado disponível para a articulação: {selected_joint}")])

    # Normaliza e processa os ângulos
    df_feedback['Angle Between Sensors'] = df_feedback['Angle Between Sensors'].apply(
        lambda x: list(map(float, x.split(', '))) if isinstance(x, str) else x
    )

    # Normalizar e ajustar os dados
    def normalize_and_trim(data):
        # Converte para uma curva crescente, se necessário
        if data[0] > data[-1]:  # Se for decrescente
            data = [-x for x in data]  # Inverte os sinais

        # Ajusta para partir do mesmo ponto
        start_point = data[0]
        normalized_data = [x - start_point for x in data]

        # Encontra o ponto inicial e final relevantes
        start_idx = max(0, next((i for i, val in enumerate(normalized_data) if abs(val) > 1), 0) - 10)
        end_idx = min(len(normalized_data), start_idx + 50)  # Limita o tamanho a 50 pontos após o início
        return normalized_data[start_idx:end_idx]

    # Aplica o ajuste a cada sessão
    df_feedback['Trimmed Angle'] = df_feedback['Angle Between Sensors'].apply(normalize_and_trim)

    # Criar o gráfico
    if selected_test == 'angle_time':
        fig = go.Figure()
        for _, row in df_feedback.iterrows():
            fig.add_trace(go.Scatter(
                x=list(range(len(row['Trimmed Angle']))),
                y=row['Trimmed Angle'],
                mode='lines+markers',
                name=f"{row['Condition']} ({row['Valor Corrente']}) - {row['Session Time']}"
            ))
        fig.update_layout(
            title=f"Ângulo por Tempo - {selected_joint}",
            xaxis_title="Tempo (segundos)",
            yaxis_title="Ângulo entre Sensores (°)"
        )
        return dcc.Graph(figure=fig)

    if selected_test == 'speed_time':
    # Calcula velocidade angular positiva
        def calculate_angular_velocity(angles, times):
            angular_velocity = []
            for i in range(1, len(angles)):
                delta_theta = angles[i] - angles[i - 1]  # Diferença de ângulo
                delta_time = times[i] - times[i - 1]  # Diferença de tempo
                if delta_time != 0:
                    velocity = abs(delta_theta / delta_time)  # Usa o valor absoluto
                    angular_velocity.append(velocity)
                else:
                    angular_velocity.append(0)  # Evita divisão por zero
            return angular_velocity

        fig = go.Figure()

        for _, row in df_feedback.iterrows():
            # Extrai os ângulos e tempos
            angles = list(map(float, row['Angle Between Sensors']))
            times = list(range(len(angles)))  # Supondo tempo incremental uniforme

            # Calcula a velocidade angular positiva
            angular_velocity = calculate_angular_velocity(angles, times)

            fig.add_trace(go.Scatter(
                x=list(range(len(angular_velocity))),  # Eixo x baseado na quantidade de dados
                y=angular_velocity,
                mode='lines+markers',
                name=f"{row['Condition']} ({row['Valor Corrente']}) - {row['Session Time']}"
            ))

        fig.update_layout(
            title=f"Velocidade Angular por Tempo - {selected_joint}",
            xaxis_title="Tempo (segundos)",
            yaxis_title="Velocidade Angular (°/s)"
        )
        return dcc.Graph(figure=fig)


    
    if selected_test == 'metric_g7':
        # Calcula a Métrica G7
        metric_g7 = calculate_g7_metric_from_plotted_data(df_feedback, selected_joint)

        # Verifica se houve erro no cálculo
        if isinstance(metric_g7, str):
            return html.Div([
                    html.H3("Métrica G7 - Erro"),
                    html.P(metric_g7)
                ])

            # Exibe a Métrica G7
        return html.Div([
                html.H3(f"Métrica G7 - {selected_joint}"),
                html.P(f"O valor da Métrica G7 é: {metric_g7:.2f}", style={'fontSize': '20px', 'marginTop': '20px'}),
                html.P(f"Portando a corrente auxilia {metric_g7:.2f} vezes a abertura do paciente", style={'fontSize': '20px', 'marginTop': '20px'} )
    ])


# Layout inicial
app.layout = html.Div(id='page-content', children=[login_layout()])

# Roda o servidor
if __name__ == '__main__':
    app.run_server(debug=True)