# Projeto: Monitoramento de Movimento com IMUs - Grupo 7 (FICSAE - 4º Semestre)

Este repositório contém os códigos e tabelas utilizados para o **Project Based Learning** do quarto semestre do grupo 7 dos alunos da **Faculdade Israelita de Ciências da Saúde Albert Einstein (FICSAE)**.

## Descrição do Projeto

O projeto consiste no monitoramento de movimentos de **extensão** e **flexão** de cotovelo e punho, utilizando dois sensores **MPU9250** (IMUs) localizados no braço do paciente. 

### Funcionalidades do Sistema

1. O código `IMU.ino`, carregado no **ESP32**, registra as leituras de aceleração dos dois sensores IMU.
2. As informações são transmitidas via **WiFi** para um computador na mesma rede.
3. O código `display.py`, executado no computador, recebe os dados dos sensores, calcula métricas importantes como:
   - **Pitch** (inclinação),
   - **Roll** (rotação),
   - **Ângulo entre os sensores**.
4. O código `dashboard.py` gera um **dashboard interativo** para cada paciente, onde as informações da condição do paciente são registradas e armazenadas.

## Arquivos no Repositório

- **`IMU.ino`**  
  Código para o **ESP32**, responsável por coletar e transmitir os dados dos sensores MPU9250 via WiFi.

- **`display.py`**  
  Código executado no computador para:
  - Receber os dados transmitidos pelo ESP32.
  - Processar e calcular métricas como **Pitch**, **Roll** e o **ângulo entre os sensores**.

- **`dashboard.py`**  
  Código para criar um **dashboard interativo** com as informações coletadas, registrando e armazenando o estado do paciente para futuras análises.

---

Sinta-se à vontade para contribuir ou enviar sugestões para melhorar o projeto! 😊
