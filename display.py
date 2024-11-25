import socket
import math
from filterpy.kalman import KalmanFilter
import numpy as np
import pandas as pd
import os

# Substitua pelo IP exibido no Serial Monitor do ESP32
esp32_ip = "172.20.10.2"
esp32_port = 12345

# Arquivo CSV
csv_file = "sensor_data.csv"

# Inicializar DataFrame para salvar os dados
columns = ["Timestamp", "Pitch 1", "Roll 1", "Pitch 2", "Roll 2", "Pitch 3", "Roll 3", "Angle 1 and 2", "Angle 2 and 3"]

# Criação inicial do arquivo Excel
if not os.path.exists(csv_file):
    pd.DataFrame(columns=columns).to_csv(csv_file, index=False)


def parse_sensor_data(raw_data):
    """
    Extrai as acelerações dos sensores da mensagem recebida.
    Retorna um dicionário contendo os valores de aceleração para cada sensor.
    """
    sensors = {}
    try:
        # Divide os dados recebidos em partes separadas para cada sensor
        data_parts = raw_data.split("Sensor")
        for part in data_parts:
            if "acel" in part:
                sensor_id = int(part.split()[0])  # Obtém o ID do sensor (1, 2 ou 3)
                # Extrai os valores de aceleração x, y, z
                accel_data = part.split("x=")[1]
                x, y, z = [float(val.split("=")[1]) if "=" in val else float(val) 
                           for val in accel_data.replace("y=", "").replace("z=", "").split()]
                sensors[f"Sensor {sensor_id}"] = {"x": x, "y": y, "z": z}
    except Exception as e:
        print(f"Erro ao processar dados: {e}")
    return sensors

def calculate_pitch_roll(accel):
    """
    Calcula os ângulos de pitch e roll com base nas acelerações.
    """
    x, y, z = accel["x"], accel["y"], accel["z"]
    pitch = math.atan2(-x, math.sqrt(y**2 + z**2)) * (180 / math.pi)  # Em graus
    roll = math.atan2(y, z) * (180 / math.pi)  # Em graus
    return pitch, roll

def calculate_angle_between(pitch1, roll1, pitch2, roll2):
    """
    Calcula o ângulo entre os vetores (pitch1, roll1) e (pitch2, roll2).
    """
    vec1 = np.array([pitch1, roll1])
    vec2 = np.array([pitch2, roll2])
    dot_product = np.dot(vec1, vec2)
    magnitude1 = np.linalg.norm(vec1)
    magnitude2 = np.linalg.norm(vec2)
    angle = math.acos(dot_product / (magnitude1 * magnitude2)) * (180 / math.pi)
    return angle

# Inicializar filtro de Kalman
def init_kalman():
    """
    Configura um filtro de Kalman para suavizar os ângulos.
    """
    kf = KalmanFilter(dim_x=2, dim_z=2)  # Dois estados (pitch, roll), duas observações
    kf.x = np.array([0, 0])  # Estado inicial (pitch, roll)
    kf.F = np.eye(2)  # Matriz de transição
    kf.H = np.eye(2)  # Matriz de observação
    kf.P *= 10  # Covariância inicial
    kf.R = np.eye(2) * 0.1  # Ruído de medição
    kf.Q = np.eye(2) * 0.01  # Ruído do processo
    return kf

try:
    print("Tentando conectar ao ESP32...")
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((esp32_ip, esp32_port))
    print("Conectado ao ESP32!")

    # Filtros de Kalman para os três sensores
    kalman_sensor1 = init_kalman()
    kalman_sensor2 = init_kalman()
    kalman_sensor3 = init_kalman()

    while True:
        raw_data = client_socket.recv(4096).decode('utf-8').strip()  # Ajustando para receber pacotes maiores
        if raw_data:
            print(f"Dado recebido: {raw_data}")
            # Processa os dados recebidos
            sensors = parse_sensor_data(raw_data)

            # Calcula pitch e roll de cada sensor
            if "Sensor 1" in sensors and "Sensor 2" in sensors and "Sensor 3" in sensors:
                pitch1, roll1 = calculate_pitch_roll(sensors["Sensor 1"])
                pitch2, roll2 = calculate_pitch_roll(sensors["Sensor 2"])
                pitch3, roll3 = calculate_pitch_roll(sensors["Sensor 3"])

                # Aplica o filtro de Kalman
                kalman_sensor1.predict()
                kalman_sensor1.update([pitch1, roll1])
                filtered_pitch1, filtered_roll1 = kalman_sensor1.x

                kalman_sensor2.predict()
                kalman_sensor2.update([pitch2, roll2])
                filtered_pitch2, filtered_roll2 = kalman_sensor2.x

                kalman_sensor3.predict()
                kalman_sensor3.update([pitch3, roll3])
                filtered_pitch3, filtered_roll3 = kalman_sensor3.x

                # Calcula os ângulos entre os sensores
                angle_1_2 = calculate_angle_between(
                    filtered_pitch1, filtered_roll1, filtered_pitch2, filtered_roll2
                )
                angle_2_3 = calculate_angle_between(
                    filtered_pitch2, filtered_roll2, filtered_pitch3, filtered_roll3
                )

                print(f"Sensor 1 -> Pitch: {filtered_pitch1:.2f}°, Roll: {filtered_roll1:.2f}°")
                print(f"Sensor 2 -> Pitch: {filtered_pitch2:.2f}°, Roll: {filtered_roll2:.2f}°")
                print(f"Sensor 3 -> Pitch: {filtered_pitch3:.2f}°, Roll: {filtered_roll3:.2f}°")
                print(f"Ângulo entre Sensor 1 e 2: {angle_1_2:.2f}°")
                print(f"Ângulo entre Sensor 2 e 3: {angle_2_3:.2f}°")

                # Adiciona os dados ao DataFrame
                new_data = {
                    "Timestamp": pd.Timestamp.now(),
                    "Pitch 1": filtered_pitch1,
                    "Roll 1": filtered_roll1,
                    "Pitch 2": filtered_pitch2,
                    "Roll 2": filtered_roll2,
                    "Pitch 3": filtered_pitch3,
                    "Roll 3": filtered_roll3,
                    "Angle 1 and 2": angle_1_2,
                    "Angle 2 and 3": angle_2_3,
                }
                pd.DataFrame([new_data]).to_csv(csv_file, mode="a", header=False, index=False)

except KeyboardInterrupt:
    print("Encerrando conexão.")

finally:
    client_socket.close()
