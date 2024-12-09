#include "FastIMU.h"
#include <Wire.h>
#include <WiFi.h>
#include <AsyncTCP.h>
// #include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>


#define IMU_ADDRESS1 0x68    // Address for the first IMU (AD0 = GND)
#define IMU_ADDRESS2 0x69    // Address for the second IMU (AD0 = 3.3V)
#define PERFORM_CALIBRATION // Comment to disable startup calibration
#define LED_PIN 2

MPU6500 IMU1;               // First IMU instance
MPU6500 IMU2;               // Second IMU instance

calData calib1 = { 0 };     // Calibration data for IMU1
AccelData accelData1;       // Accelerometer data for IMU1
GyroData gyroData1;         // Gyroscope data for IMU1
MagData magData1;           // Magnetometer data for IMU1

calData calib2 = { 0 };     // Calibration data for IMU2
AccelData accelData2;       // Accelerometer data for IMU2
GyroData gyroData2;         // Gyroscope data for IMU2
MagData magData2;           // Magnetometer data for IMU2

const char* ssid = "scilingosc";
const char* password = "momor2612";
WiFiServer server(12345); 
// Serial log buffer
const size_t logBufferSize = 1024;
char logBuffer[logBufferSize];
size_t logWriteIndex = 0;

StaticJsonDocument<512> jsonDoc;

// WebSocket and server instances
// AsyncWebServer server(80);
// AsyncWebSocket ws("/ws");

// Function to store logs in the buffer
void storeLog(const char* message) {
  size_t len = strlen(message);
  if (len > logBufferSize) return; // Ignore large messages
  for (size_t i = 0; i < len; ++i) {
    logBuffer[logWriteIndex] = message[i];
    logWriteIndex = (logWriteIndex + 1) % logBufferSize;
  }
}

// Function to broadcast serial logs
// void sendLogBuffer(AsyncWebSocketClient* client) {
//   String logs = "";
//   for (size_t i = 0; i < logBufferSize; ++i) {
//     logs += logBuffer[(logWriteIndex + i) % logBufferSize];
//   }
//   client->text(logs);
// }

// // Override Serial.print and Serial.println
// #define SerialPrint(x) { Serial.print(x); storeLog(x); }
// #define SerialPrintln(x) { Serial.println(x); storeLog((String(x) + "\n").c_str()); }

// // Function to broadcast sensor data over WebSocket
// void notifyClients() {
//   String output;
//   serializeJson(jsonDoc, output);
//   ws.textAll(output);
// }

// Simulate sensor data
void updateSensorData() {
  //clear the json doc
  jsonDoc.clear();
// Update IMU1
IMU1.update();
IMU1.getAccel(&accelData1);
IMU1.getGyro(&gyroData1);
if (IMU1.hasMagnetometer()) IMU1.getMag(&magData1);

// Update IMU2
IMU2.update();
IMU2.getAccel(&accelData2);
IMU2.getGyro(&gyroData2);
if (IMU2.hasMagnetometer()) IMU2.getMag(&magData2);

// Populate JSON data for IMU1
JsonObject imu1 = jsonDoc.createNestedObject("IMU1");
JsonObject imu1Accel = imu1.createNestedObject("Accel");
imu1Accel["X"] = accelData1.accelX;
imu1Accel["Y"] = accelData1.accelY;
imu1Accel["Z"] = accelData1.accelZ;

JsonObject imu1Gyro = imu1.createNestedObject("Gyro");
imu1Gyro["X"] = gyroData1.gyroX;
imu1Gyro["Y"] = gyroData1.gyroY;
imu1Gyro["Z"] = gyroData1.gyroZ;

if (IMU1.hasMagnetometer()) {
  JsonObject imu1Mag = imu1.createNestedObject("Mag");
  imu1Mag["X"] = magData1.magX;
  imu1Mag["Y"] = magData1.magY;
  imu1Mag["Z"] = magData1.magZ;
}

// Populate JSON data for IMU2
JsonObject imu2 = jsonDoc.createNestedObject("IMU2");
JsonObject imu2Accel = imu2.createNestedObject("Accel");
imu2Accel["X"] = accelData2.accelX;
imu2Accel["Y"] = accelData2.accelY;
imu2Accel["Z"] = accelData2.accelZ;

JsonObject imu2Gyro = imu2.createNestedObject("Gyro");
imu2Gyro["X"] = gyroData2.gyroX;
imu2Gyro["Y"] = gyroData2.gyroY;
imu2Gyro["Z"] = gyroData2.gyroZ;

if (IMU2.hasMagnetometer()) {
  JsonObject imu2Mag = imu2.createNestedObject("Mag");
  imu2Mag["X"] = magData2.magX;
  imu2Mag["Y"] = magData2.magY;
  imu2Mag["Z"] = magData2.magZ;
}
}

// Serialize and print JSON data

// WebSocket events
// void onWebSocketEvent(AsyncWebSocket* server, AsyncWebSocketClient* client, AwsEventType type, void* arg, uint8_t* data, size_t len) {
//   if (type == WS_EVT_CONNECT) {
//     SerialPrintln("WebSocket client connected");
//     client->ping();
//   } else if (type == WS_EVT_DISCONNECT) {
//     SerialPrintln("WebSocket client disconnected");
//   } else if (type == WS_EVT_DATA) {
//     String message = String((char*)data).substring(0, len);
//     if (message == "getLogs") {
//       sendLogBuffer(client);
//     } else if (message == "reset") {
//       SerialPrintln("Reset command received!");
//       ESP.restart();
//     }
//   }
// }



void setup() {
  Wire.begin();
  Wire.setClock(400000); // 400 kHz clock
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT); // Initialize LED pin
  digitalWrite(LED_PIN, LOW); // Turn off LED initially
  while (!Serial);

  WiFi.begin(ssid,password);
  // Aguarda a conexão com o Wi-Fi
    while (WiFi.status() != WL_CONNECTED) {
      delay(1000);
      Serial.println("Conectando ao Wi-Fi...");
    }

    Serial.println("Conectado ao Wi-Fi!");
    Serial.println("IP do ESP32: ");
    Serial.println(WiFi.localIP());  // Exibe o IP do ESP32

    server.begin();  // Inicia o servidor


  // Initialize IMU1
  if (IMU1.init(calib1, IMU_ADDRESS1) != 0) {
    Serial.println("Error initializing IMU1");
    while (true);
  }

  // Initialize IMU2
  if (IMU2.init(calib2, IMU_ADDRESS2) != 0) {
    Serial.println("Error initializing IMU2");
    while (true);
  }

  

// #ifdef PERFORM_CALIBRATION
//   performCalibration(IMU1, calib1, "IMU1");
//   performCalibration(IMU2, calib2, "IMU2");
//   digitalWrite(LED_PIN, HIGH);
// #endif

//now for the wifi part
  // Setup Wi-Fi as Access Point
  // WiFi.softAP(ssid);
  // Serial.print("AP IP address: ");
  // Serial.println(WiFi.softAPIP());

  // // Setup WebSocket
  // ws.onEvent(onWebSocketEvent);
  // server.addHandler(&ws);

  // // Allow CORS for all endpoints
  // DefaultHeaders::Instance().addHeader("Access-Control-Allow-Origin", "*");

  // // Start the server
  // server.begin();
  // Serial.println("WebSocket server started!");

}

void performCalibration(MPU6500 &imu, calData &calib, const char *imuName) {
  Serial.print(imuName);
  Serial.println(" calibration & data example");

  if (imu.hasMagnetometer()) {
    delay(1000);
    Serial.println("Move IMU in figure 8 pattern until done.");
    delay(3000);
    imu.calibrateMag(&calib);
    Serial.println("Magnetic calibration done!");
  } else {
    delay(5000);
  }

  delay(5000);
  Serial.println("Keep IMU level.");
  delay(5000);
  imu.calibrateAccelGyro(&calib);
  Serial.println("Calibration done!");
}

// void loop() {
  
//   WiFiClient client = server.available();  // Verifica se há um cliente conectado
//     if (client) {
//       Serial.println("Cliente conectado.");
    
//       while (client.connected()) {
//             static uint32_t prev_ms = millis();
//             if (millis() > prev_ms + 25) {
//                 IMU1.update();
//                 IMU1.getAccel(&accelData1);
//                 IMU2.update();
//                 IMU2.getAccel(&accelData2);
//                 client.println("Sensor 1 acel - x=" + String(accelData1.accelX) + 
//                         " y=" + String(accelData1.accelY) + " z=" + String(accelData1.accelZ)+ 
//                         " Sensor 3 acel - x=" + String(accelData2.accelX) + 
//                         " y=" + String(accelData2.accelY) + " z=" + String(accelData2.accelZ)); 
//                 prev_ms = millis();
//             }
        

        
//       }
//     }
//     client.stop();  // Desconecta o cliente
//         Serial.println("Cliente desconectado.");
// }

void loop() {
  WiFiClient client = server.available();  // Verifica se há um cliente conectado
  if (client) {
    Serial.println("Cliente conectado.");
    
    while (client.connected()) {
      // Aguarde um comando ou tempo antes de desconectar
      static uint32_t prev_ms = millis();
      if (millis() > prev_ms + 200) { // Atualiza a cada 25ms
        // Atualiza dados dos sensores
        IMU1.update();
        IMU1.getAccel(&accelData1);
        IMU2.update();
        IMU2.getAccel(&accelData2);
        
        // Envia dados ao cliente
        String sensorData = "Sensor 1 acel - x=" + String(accelData1.accelX) +
                            " y=" + String(accelData1.accelY) + 
                            " z=" + String(accelData1.accelZ) +
                            " Sensor 2 acel - x=" + String(accelData2.accelX) + 
                            " y=" + String(accelData2.accelY) + 
                            " z=" + String(accelData2.accelZ);
        client.println(sensorData);
        Serial.println(sensorData);  // Imprime no Serial para debug
        
        prev_ms = millis();
      }
    }
    client.stop();  // Desconecta o cliente após o término
    Serial.println("Cliente desconectado.");
  }
}
