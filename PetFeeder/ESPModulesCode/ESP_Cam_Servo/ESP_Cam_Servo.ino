#include <Arduino.h>
#include <WebServer.h>
#include <WiFi.h>
#include <esp32cam.h>
#include <ESP32Servo.h>
#include <WiFiManager.h>
#include <DHT11.h>



// ESP32 cam flash led = pin 4
const int ledPin = 4;

const char *ssid = "Cuong Linh-2.4Ghz";       
const char *password = "cuonglinh01";  

DHT11 dht11(13);
#define LED_XANH_PIN 15    
#define LED_DO_PIN 2      
unsigned long previousMillisTemp = 0;
const long tempInterval = 1000;

// Initialize webserver on port 8080
WebServer server(8080);


const int servoPin = 14;

int pos = 0;

Servo myservo;
 
static auto loRes = esp32cam::Resolution::find(320, 240);
static auto midRes = esp32cam::Resolution::find(350, 530);
static auto hiRes = esp32cam::Resolution::find(800, 600);

// Hàm chụp ảnh và gửi ảnh qua HTTP response.
void serveJpg()
{
  auto frame = esp32cam::capture();
  if (frame == nullptr) {
    Serial.println("CAPTURE FAIL");
    server.send(503, "", "");
    return;
  }
  Serial.printf("CAPTURE OK %dx%d %db\n", frame->getWidth(), frame->getHeight(),
                static_cast<int>(frame->size()));
 
  server.setContentLength(frame->size());
  server.send(200, "image/jpeg");
  WiFiClient client = server.client();
  frame->writeTo(client);
}
 // Các hàm thay đổi độ phân giải camera và chụp ảnh.
void handleJpgLo()
{
  if (!esp32cam::Camera.changeResolution(loRes)) {
    Serial.println("SET-LO-RES FAIL");
  }
  serveJpg();
}
 
void handleJpgHi()
{
  if (!esp32cam::Camera.changeResolution(hiRes)) {
    Serial.println("SET-HI-RES FAIL");
  }
  serveJpg();
}
 
void handleJpgMid()
{
  if (!esp32cam::Camera.changeResolution(midRes)) {
    Serial.println("SET-MID-RES FAIL");
  }
  serveJpg();
}
 
 
void  setup(){
  Serial.begin(115200);
  pinMode(LED_XANH_PIN, OUTPUT);
  pinMode(LED_DO_PIN, OUTPUT);
  Serial.println();
  {
    using namespace esp32cam;
    Config cfg;
    cfg.setPins(pins::AiThinker);
    cfg.setResolution(hiRes);
    cfg.setBufferCount(2);
    cfg.setJpeg(80);
 
    bool ok = Camera.begin(cfg);
    Serial.println(ok ? "CAMERA OK" : "CAMERA FAIL");
  }

  ESP32PWM::allocateTimer(5);
  myservo.setPeriodHertz(50);
  myservo.attach(servoPin, 500, 2500);

  WiFi.mode(WIFI_STA);  
  WiFi.begin(ssid, password);  
  Serial.print("Connecting to WiFi");
 
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }

  
  Serial.print("Server IP address: ");
  Serial.println(WiFi.localIP());

  Serial.print("http://");
  Serial.println(WiFi.localIP());
  Serial.println("  /cam-lo.jpg");
  Serial.println("  /cam-hi.jpg");
  Serial.println("  /cam-mid.jpg");
 
  // server.on("/cam-lo.jpg", handleJpgLo);
  server.on("/cam-hi.jpg", handleJpgHi);
  // server.on("/cam-mid.jpg", handleJpgMid);
 
  server.on("/", handleRoot);
  server.begin(); // Bắt đầu server HTTP.
  Serial.println("HTTP server started");

  
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);
}
 
void loop()
{
  // Call functions set with server.on()
  server.handleClient();

  unsigned long currentMillis = millis();
  if (currentMillis - previousMillisTemp >= tempInterval) {
    previousMillisTemp = currentMillis;
    int temperature = dht11.readTemperature(); // Đọc nhiệt độ.

    if (temperature != DHT11::ERROR_CHECKSUM && temperature != DHT11::ERROR_TIMEOUT) {
        Serial.print("Temperature: ");
        Serial.print(temperature);
        Serial.println(" °C");
    } else {
        Serial.println(DHT11::getErrorString(temperature));
    }
    
    if (temperature >= 30) {
      digitalWrite(LED_XANH_PIN, HIGH);
      digitalWrite(LED_DO_PIN, LOW);
    } else if (temperature <= 26) {
      digitalWrite(LED_XANH_PIN, LOW);
      digitalWrite(LED_DO_PIN, HIGH);
    } else {
      digitalWrite(LED_XANH_PIN, LOW);
      digitalWrite(LED_DO_PIN, LOW);
    }
  }
}

void moveServo(int repetitions) {
  for (int i = 0; i < repetitions; i++) {
    for (pos = 0; pos <= 180; pos += 1) { // goes from 0 degrees to 180 degrees
    myservo.write(pos);    // tell servo to go to position in variable 'pos'
    delay(5);             // waits 15ms for the servo to reach the position
  }
    delay(500);
    for (pos = 180; pos >= 0; pos -= 1) { // goes from 180 degrees to 0 degrees
      myservo.write(pos);    // tell servo to go to position in variable 'pos'
      delay(5);             // waits 15ms for the servo to reach the position
    }
    delay(500);
  }
}

void handleRoot() {
  // Kiểm tra nếu có yêu cầu POST từ client.
  if (server.method() == HTTP_POST) {
    String message = server.arg("message");
    Serial.print("Received message: ");
    Serial.println(message);

    if (message.equals("FLASHON")) { // Nếu thông điệp là "FLASHON".
      Serial.println("Turning on flash");
      digitalWrite(ledPin, HIGH);
      server.send(200, "text/plain", "Flash ON");

    } else if (message.equals("FLASHOFF")) {
      digitalWrite(ledPin, LOW);
      Serial.println("Turning off flash");
      server.send(200, "text/plain", "Flash OFF");

    } else if (message.equals("SMALL")) {
      Serial.println("Rotating servo");
      server.send(200, "text/plain", "ESP32: Feeding small portion");
      moveServo(1);
      delay(1000);

    } else if (message.equals("MED")) {
      Serial.println("Rotating servo");
      server.send(200, "text/plain", "ESP32: Feeding medium portion");
      moveServo(2);
      delay(1000);

    } else if (message.equals("LARGE")) {
      Serial.println("Rotating servo");
      server.send(200, "text/plain", "ESP32: Feeding large portion");
      moveServo(3);
      delay(1000);

    } else if (message.equals("TEST")) {
      Serial.println("Test message recieved from Python");
      server.send(200, "text/plain", "Communications established. Test passed.");

    } 
    
    else {
      Serial.println("Invalid message received");
    }

    server.send(200, "text/plain", "Message received. ESP32 CAM Connected");
  
  // Send Hello message to show connection
  } else {
    server.send(200, "text/plain", "Hello from ESP32 CAM!");
  }
}
