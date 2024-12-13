#include "mbed.h"
#include <Arduino.h>
#include <rtos.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <PDM.h>
#include <math.h>
#include "camera.h"
#include "himax.h"
#include <base64.h>
using namespace mbed;
using namespace rtos;
using namespace std::chrono_literals;

HM01B0 himax;
Camera cam(himax);

#define IMAGE_MODE CAMERA_GRAYSCALE
FrameBuffer fb(320, 240, 2);

#define SAMPLE_RATE     16000
#define NUM_CHANNELS    1
#define RECORD_DURATION 5
#define TOTAL_SAMPLES   (SAMPLE_RATE * RECORD_DURATION * NUM_CHANNELS)

int16_t audioBuffer[TOTAL_SAMPLES];
volatile int samplesRead = 0;
volatile bool audioReady = false;

// Wi-Fi credentials
// const char* ssid = "Sunrise_2.4GHz_535660";
// const char* password = "w1F2tm16xnwN";

// Wi-Fi credentials
const char* ssid = "1+";
const char* password = "h49iyc4u";

// Server details
const char* serverIP = "192.168.86.20";
const int serverPort = 9999;

WiFiClient client;

Thread cameraThread(osPriorityNormal, 8192, nullptr, "CameraThread");
Thread audioThread(osPriorityNormal, 8192, nullptr, "AudioThread");
Thread networkThread(osPriorityNormal, 16384, nullptr, "NetworkThread"); // Increased stack size
Mutex bufferMutex;

// Chunk size for image transmission
const size_t CHUNK_SIZE = 512;

// static unsigned char output[110000];

void onPDMData() {
    int bytesAvailable = PDM.available();
    int16_t tempBuffer[bytesAvailable / sizeof(int16_t)];
    PDM.read(tempBuffer, bytesAvailable);

    for (int i = 0; i < (bytesAvailable / sizeof(int16_t)); i++) {
        if (samplesRead < TOTAL_SAMPLES) {
            audioBuffer[samplesRead++] = tempBuffer[i];
        }
        if (samplesRead >= TOTAL_SAMPLES) {
            audioReady = true;
            break;
        }
    }
}

void audioTask() {
    while (true) {
        samplesRead = 0;
        audioReady = false;
        memset(audioBuffer, 0, sizeof(audioBuffer));

        // Wait for audio to be ready
        while (!audioReady) {
            ThisThread::sleep_for(10ms);
        }

        bufferMutex.lock(); // i should actually move the rest of the logic here
        Serial.println("Audio recording complete!");
        bufferMutex.unlock();

        // Wait before next recording
        ThisThread::sleep_for(5s);
    }
}

void cameraTask() {
    while (true) {
        bufferMutex.lock();
        if (cam.grabFrame(fb, 3000) == 0) {
            Serial.println("Image captured!");
        } else {
            Serial.println("Failed to capture image.");
        }
        bufferMutex.unlock();

        ThisThread::sleep_for(5s);
    }
}

void networkTask() {
    while (true) {
        // Wait until we have some data
        bufferMutex.lock();
        // Compute audio stats
        double sumSquared = 0.0;
        for (int i = 0; i < samplesRead; i++) {
            double sample = (double)audioBuffer[i];
            sumSquared += sample * sample;
        }

        double rms = sqrt(sumSquared / samplesRead);
        double averageDb = 20.0 * log10(rms + 1e-8);

        // Connect and send data
        if (!client.connected()) {
            Serial.println("Attempting to connect to server...");
            if (client.connect(serverIP, serverPort)) {
                Serial.println("Connected to server!");
            } else {
                Serial.println("Failed to connect to server.");
                bufferMutex.unlock();
                ThisThread::sleep_for(2s);
                continue; // Skip to the next iteration
            }
        }

            byte* input_buffer = fb.getBuffer();
            size_t bufferSize = cam.frameSize();

            const size_t capacity = JSON_OBJECT_SIZE(5) + 100;
            DynamicJsonDocument jsonDoc(capacity);
            jsonDoc["gps_lat"] = "37.7749";
            jsonDoc["gps_lon"] = "-122.4194";
            jsonDoc["noise"] = String(averageDb, 2);
            jsonDoc["date"] = "2023-10-01 12:00:00";
            jsonDoc["id"] = "device_123";

            String jsonString;
            serializeJson(jsonDoc, jsonString);
            Serial.println(jsonString);





            int content_length = jsonString.length() + bufferSize + 2;

            // send HTTP POST request to server
            client.println("POST /upload HTTP/1.1");
            client.print("Host: ");
            client.print(serverIP);
            client.print(":");
            client.println(serverPort);
            client.println("Content-Type: application/octet-stream");

            client.println("Content-Length: " + String(content_length));
            client.println();
            client.println(jsonString);



            // Send image data in chunks with error handling
            size_t bytesSent = 0;
            int retries = 0;
            const int maxRetries = 3;

            while (bytesSent < bufferSize && retries < maxRetries) {
                size_t bytesToSend = min(CHUNK_SIZE, bufferSize - bytesSent);
                size_t bytesWritten = client.write(input_buffer + bytesSent, bytesToSend);

                if (bytesWritten == bytesToSend) {
                    bytesSent += bytesWritten;
                    retries = 0; // Reset retries on success
                    Serial.print("Sent chunk: ");
                    Serial.print(bytesSent);
                    Serial.println(" / " + String(bufferSize));
                } else {
                    Serial.println("Error sending chunk. Retrying...");
                    retries++;
                    ThisThread::sleep_for(500ms * retries);
                }
            }

            if (retries >= maxRetries) {
                Serial.println("Failed to send image after multiple retries.");
                client.stop();
                Serial.println("Disconnected from server");
            } else {
                Serial.println("Image sent successfully!");
            }


            // Wait for server response
            unsigned long startTime = millis();
            const unsigned long responseTimeout = 5000;

            while (client.available() == 0 && (millis() - startTime < responseTimeout)) {
                ThisThread::sleep_for(10ms);
            }

            if (client.available() == 0) {
                Serial.println("Timeout waiting for server response.");
                client.stop();
                Serial.println("Disconnected from server");
            }

            if (client.connected()) {
            client.stop();
            Serial.println("Disconnected from server");
            }

            bufferMutex.unlock();
            ThisThread::sleep_for(5s);
    }
}

void setup() {
    Serial.begin(115200);
    while (!Serial){
      ;
    }

    // Initialize camera
    if (!cam.begin(CAMERA_R320x240, IMAGE_MODE, 30)) {
        Serial.println("Failed to initialize camera");
        while (1);
    }

    // Initialize PDM mic
    if (!PDM.begin(NUM_CHANNELS, SAMPLE_RATE)) {
        Serial.println("Failed to initialize PDM mic!");
        while (1);
    }
    PDM.onReceive(onPDMData);

    // Connect to Wi-Fi
    Serial.print("Connecting to Wi-Fi...");
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");

        }

    Serial.println("\nWi-Fi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());

    // Start the tasks
    cameraThread.start(cameraTask);
    audioThread.start(audioTask);
    networkThread.start(networkTask);
}

void loop() {

}