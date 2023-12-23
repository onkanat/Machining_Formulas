#include <WiFi.h>
#include <time.h>
#include <WebServer.h>
#include <RTClib.h>

// Create an instance of the RTC library.
DS1307 rtc;

// Replace with your network credentials
const char* ssid = "SUPERONLINE-WiFi_5845";
const char* password = "A7TMW79VUKWH";
const char* ntpServer = "pool.ntp.org";
const long  gmtOffset_sec = 0;  // Adjust according to your timezone
const int   daylightOffset_sec = 0;  // Adjust if you have daylight saving

// Pin definitions
const int ledPin = 25;  // Adjust to your board's LED pin
const int relayPins[] = {4, 5, 6, 7};  // Adjust to your relay pins
bool relayStates[4] = {false, false, false, false};  // assuming you have 4 relays

WebServer server(80);
// Initialize relay states and timers
struct RelayTimer {
  String start;
  String stop;
} relayTimers[4];

// Dummy function to represent getting the current time
// Replace this with actual code to retrieve the current time
String getCurrentTime() {
  char timeStr[16];

  if (WiFi.status() == WL_CONNECTED) {
    // Fetch time from NTP
    time_t now = time(nullptr);
    struct tm* p_tm = localtime(&now);

    // Format time as HH:MM
    snprintf(timeStr, sizeof(timeStr), "%02d:%02d", p_tm->tm_hour, p_tm->tm_min);
  } else {
    // WiFi is not connected, fetch time from RTC
    DateTime now = rtc.now();

    // Format time as HH:MM
    snprintf(timeStr, sizeof(timeStr), "%02d:%02d", now.hour(), now.minute());
  }

  return String(timeStr);
}

// Define the Relay Control Function: This function will check the current time against the scheduled times
// for each relay and turn them on or off accordingly.
void controlRelays() {
  // Assuming you have a way to get the current time as a string in the format "HH:MM"
  String currentTime = getCurrentTime();

  for (int i = 0; i < 4; i++) {  // Assuming you have 4 relays
    // Check if the current time is within the start and stop times
    if (currentTime >= relayTimers[i].start && currentTime <= relayTimers[i].stop) {
      digitalWrite(relayPins[i], HIGH);  // Turn on the relay
      relayStates[i] = HIGH;  // Update the state tracking
    } else {
      digitalWrite(relayPins[i], LOW);   // Turn off the relay
      relayStates[i] = LOW;  // Update the state tracking
    }
  }
}
// Create a function that formats and sends the current relay states.
// This could be to a serial monitor, over a network, or to an LCD display.
void reportRelayStates() {
  Serial.print("Relay States: ");
  for (int i = 0; i < 4; i++) {
    Serial.print("Relay ");
    Serial.print(i+1);
    Serial.print(": ");
    Serial.print(relayStates[i] ? "ON" : "OFF");
    Serial.print(" | ");
  }
  Serial.println(getCurrentTime());
  Serial.println();  // End the line
}

void handleRoot() {
  String currentTime = getCurrentTime();  // Get the current time

  String html = "<html>\n"
                "<head><title>Relay Control</title></head>\n"
                "<body>\n"
                "<h1>Relay Control</h1>\n";

  // Add the current time
  html += "<h2>Current Time: " + currentTime + "</h2>\n";

  // Add the current status of each relay and their scheduled times
  html += "<h2>Relay Status and Schedule:</h2>\n";
  for (int i = 0; i < 4; i++) {
    html += "Relay " + String(i + 1) + ": " + (relayStates[i] ? "ON " : "OFF");
    html += " | Scheduled Start: " + relayTimers[i].start;
    html += " | Scheduled Stop: " + relayTimers[i].stop + "<br>\n";
    html += "<hr />";
  }

  // Continue with the form
  html += "<h2>Set Relay Times:</h2>\n"
          "<form action=\"/setRelay\" method=\"GET\">\n"
          "Relay Number: <input type=\"number\" name=\"relay\" min=\"1\" max=\"4\">\n"
          "<br>Start Time: <input type=\"time\" name=\"start\">\n"
          "Stop Time: <input type=\"time\" name=\"stop\">\n"
          "<br><input type=\"submit\" value=\"Set Relay Times\">\n"
          "</form>\n"
          "<footer><p>Onkanat Pico Relay Application</p></footer>"
          "</body>\n"
          "</html>";

  server.send(200, "text/html", html);
}



void handleSetRelay() {
  String relayNumber = server.arg("relay");  // Get the relay number from the form
  String startTime = server.arg("start");    // Get the start time from the form
  String stopTime = server.arg("stop");      // Get the stop time from the form

  // Convert relayNumber to an integer and validate it
  int relayIdx = relayNumber.toInt() - 1;
  if(relayIdx >= 0 && relayIdx < 4) {
    // Assuming relayTimers is an array of structs or classes that hold the start and stop times
    relayTimers[relayIdx].start = startTime;
    relayTimers[relayIdx].stop = stopTime;
    Serial.println("Set relay " + relayNumber + " to start at " + startTime + " and stop at " + stopTime);
  }

  // Redirect back to the root page
  server.sendHeader("Location", "/");
  server.send(303);
}

void setup() {
  Serial.begin(115200);
  
  // Initialize GPIOs
  pinMode(ledPin, OUTPUT);
  for (int i = 0; i < 4; i++) {
    pinMode(relayPins[i], OUTPUT);
    digitalWrite(relayPins[i], LOW);  // Ensure relays are off
  }

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
    Serial.println("Connected to WiFi");

  // Initialize NTP
    configTime(gmtOffset_sec, daylightOffset_sec, ntpServer, "time.nist.gov");

  
    if (!rtc.begin()) {
    Serial.println("Couldn't find RTC");
    while (1);
  }

  if (!rtc.isrunning()) {
    Serial.println("RTC is NOT running, let's set the time!");
    // Set the RTC to the date & time this sketch was compiled
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }


  // Start the server
  server.on("/", handleRoot);
  server.on("/setRelay", handleSetRelay);
  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient(); // Handle client requests
  controlRelays(); // Check and control the relay states 
}

void loop1() {
  static unsigned long lastReportTime = 0;
  unsigned long currentMillis = millis();
  if (currentMillis - lastReportTime >= 5000) {  // every 5 seconds
    reportRelayStates();
    lastReportTime = currentMillis;
  }
}
