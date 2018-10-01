// rf69 demo tx rx.pde
// -*- mode: C++ -*-
// Example sketch showing how to create a simple addressed, reliable messaging client
// with the RH_RF69 class. RH_RF69 class does not provide for addressing or
// reliability, so you should only use RH_RF69  if you do not need the higher
// level messaging abilities.
// It is designed to work with the other example rf69_server.
// Demonstrates the use of AES encryption, setting the frequency and modem 
// configuration

#include <RTCZero.h>
#include <SPI.h>
#include <RH_RF69.h>
#include <RHReliableDatagram.h>
#include "Adafruit_Si7021.h"

//#define DEBUG

Adafruit_Si7021 sensor_si7021 = Adafruit_Si7021();

/************ Radio Setup ***************/

// Change to 434.0 or other frequency, must match RX's freq!
#define RF69_FREQ 915.0

// Where to send packets to!
#define DEST_ADDRESS  1
// change addresses for each client board, any number :)
#define MY_ADDRESS    2

#define RFM69_CS      8
#define RFM69_INT     3
#define RFM69_RST     4
#define LED           13
#define VBATPIN       A7

//local sensor data structure
typedef struct {
  float temperature;
  float humidity;
  float altitude;
  float pressure;
  float battery;
} LOCALSENSORDATA, *PLOCALSENSORDATA;

LOCALSENSORDATA localsensordata;

RTCZero rtc;
//volatile bool alarm;

// Singleton instance of the radio driver
RH_RF69 rf69(RFM69_CS, RFM69_INT);

// Class to manage message delivery and receipt, using the driver declared above
RHReliableDatagram rf69_manager(rf69, MY_ADDRESS);

byte packetnum = 0;  // packet counter, we increment per xmission


////////////////////////////////////////////////////////////////////////////////
// Setup Arduino serial
////////////////////////////////////////////////////////////////////////////////
void setup_serial(int rate)
{
  Serial.begin(rate);

  // wait for serial port to open
  while (!Serial) 
  {
    delay(10);
  }
}

////////////////////////////////////////////////////////////////////////////////
// Setup Arduino RTC
////////////////////////////////////////////////////////////////////////////////
void setup_rtc()
{
  // * Change these values to set the current initial time * /
  const byte hours   = 0;
  const byte minutes = 0;
  const byte seconds = 50;
  // * Change these values to set the current initial date * /
  const byte year    = 66;  
  const byte month   = 4;
  const byte day     = 29;
  
  rtc.begin();
  rtc.setTime(hours, minutes, seconds);
  rtc.setDate(day, month, year);
  rtc.setAlarmSeconds((MY_ADDRESS - 2) * 2);
  rtc.enableAlarm(rtc.MATCH_SS);
  rtc.attachInterrupt(rtc_isr); 
}

void setup_sensors()
{
  //pinMode(10, OUTPUT);
  //digitalWrite(10, HIGH);  // power on sensor

#ifdef DEBUG
  Serial.println("REMOTE Si7021 setup");
#endif // DEBUG

  if (!sensor_si7021.begin()) 
  {
#ifdef DEBUG
    Serial.println("Did not find Si7021 sensor!");
#endif // DEBUG
    while (true);
  }
}

void rtc_isr()
{
}

////////////////////////////////////////////////////////////////////////////////
// Read Feather M0 battery voltage
////////////////////////////////////////////////////////////////////////////////
void read_battery(PLOCALSENSORDATA data)
{
  float measuredvbat = analogRead(VBATPIN);
  measuredvbat *= 2;    // we divided by 2, so multiply back
  measuredvbat *= 3.3;  // Multiply by 3.3V, our reference voltage
  measuredvbat /= 1024; // convert to voltage
  data->battery = measuredvbat;

  /*
  Serial.print("VBat: " ); 
  Serial.println(data->battery);
  */
}

////////////////////////////////////////////////////////////////////////////////
// Read temperature/humidity and optional pressure sensors
//   Gateway node has more capable BME280 temp/hum/press sensor
//   Remote node has cheaper Si7021 temp/hum/press sensor
////////////////////////////////////////////////////////////////////////////////
void read_sensors(PLOCALSENSORDATA data)
{
  //digitalWrite(SDA, HIGH); // enable internal pullup
  //digitalWrite(SCL, HIGH);  // enable internal pullup
  //digitalWrite(10, HIGH);  // power on sensor
  //delay(100);
  
  data->pressure = 0.0F;
  data->altitude = 0.0F;
  data->temperature = sensor_si7021.readTemperature();
  data->humidity = sensor_si7021.readHumidity();

  //digitalWrite(SDA, LOW); // disable internal pullup
  //digitalWrite(SCL, LOW);  // disable internal pullup
  //digitalWrite(10, LOW);  // power on sensor

  /*
  Serial.print("Humidity:    "); Serial.print(data->humidity, 2);
  Serial.print("\tTemperature: "); Serial.println(data->temperature, 2);
  */
}

void setup() 
{
  pinMode(LED, OUTPUT);

  //delay to allow usb programmer time to connect before deep sleep
  digitalWrite(LED, HIGH);
  delay(5000);
  digitalWrite(LED, LOW);

#ifdef DEBUG
  DEBUG  setup_serial(115200);
#endif // DEBUG
  
  setup_rtc();
  setup_sensors();

  pinMode(LED, OUTPUT);     
  pinMode(RFM69_RST, OUTPUT);
  digitalWrite(RFM69_RST, LOW);

#ifdef DEBUG
  Serial.println("Feather Addressed RFM69 remote");
  Serial.println();
#endif // DEBUG

  // manual reset
  digitalWrite(RFM69_RST, HIGH);
  delay(10);
  digitalWrite(RFM69_RST, LOW);
  delay(10);
  
  if (!rf69_manager.init()) {
#ifdef DEBUG
    Serial.println("RFM69 radio init failed");
#endif // DEBUG
    while (1);
  }
#ifdef DEBUG
  Serial.println("RFM69 radio init OK!");
#endif // DEBUG
  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM (for low power module)
  // No encryption
  if (!rf69.setFrequency(RF69_FREQ)) {
#ifdef DEBUG
    Serial.println("setFrequency failed");
#endif // DEBUG
  }

  // If you are using a high power RF69 eg RFM69HW, you *must* set a Tx power with the
  // ishighpowermodule flag set like this:
  rf69.setTxPower(20, true);  // range from 14-20 for power, 2nd arg must be true for 69HCW

  // The encryption key has to be the same as the one in the server
  uint8_t key[] = { 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01,
                    0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01};
  rf69.setEncryptionKey(key);
  
  pinMode(LED, OUTPUT);

#ifdef DEBUG
  Serial.print("RFM69 radio @");  
  Serial.print((int)RF69_FREQ);  
  Serial.println(" MHz");
#endif // DEBUG
}

////////////////////////////////////////////////////////////////////////////////
// Send local sensor data to host
////////////////////////////////////////////////////////////////////////////////
void output_local_sensor_data(LOCALSENSORDATA data)
{
#ifdef DEBUG
  Serial.print("BAT," ); 
  Serial.print(data.battery);
  Serial.print(",TMP," ); 
  Serial.print(data.temperature);
  Serial.print(",HUM," ); 
  Serial.println(data.humidity);
#endif // DEBUG
}


char *ftoa(double f, char *a, int precision) {
// Convert float to ascii!
  long p[] = {0,10,100,1000,10000,100000,1000000,10000000,100000000};
  char *ret = a;
  long heiltal = (long)f;
  itoa(heiltal, a, 10);
  while (*a != '\0') a++;
  *a++ = '.';
  long desimal = abs((long)((f - heiltal) * p[precision]));
  if (desimal< p[precision-1])  //are there leading zeros?
    { *a='0'; a++; }
  itoa(desimal, a, 10);
  return ret;
} 

char timestr[12];

char *timestamp(char *timestr, int len)
{
   int seconds = rtc.getSeconds();
   int minutes = rtc.getMinutes();
   int hours = rtc.getHours();

   memset(timestr, 0, len);
   sprintf(timestr, "%02d:%02d:%02d", 
      hours,
      minutes,
      seconds);

   return timestr;
}


// Dont put this on the stack:
uint8_t buf[RH_RF69_MAX_MESSAGE_LEN];
char fltbuf_bat[8];
char fltbuf_tmp[8];
char fltbuf_hum[8];
char radiopacket[RH_RF69_MAX_MESSAGE_LEN];

void loop() {
  memset(fltbuf_bat, 0, 8);
  memset(fltbuf_tmp, 0, 8);
  memset(fltbuf_hum, 0, 8);
  memset(buf, 0, RH_RF69_MAX_MESSAGE_LEN);
  memset(radiopacket, 0, RH_RF69_MAX_MESSAGE_LEN);
  
  read_battery(&localsensordata);
  read_sensors(&localsensordata);
  output_local_sensor_data(localsensordata);

  ftoa(localsensordata.battery, fltbuf_bat, 2);
  ftoa(localsensordata.temperature, fltbuf_tmp, 2);
  ftoa(localsensordata.humidity, fltbuf_hum, 2);

  if(packetnum++ == 255)
  {
    packetnum = 0;
  }

  char version_remote[] = "0.01";
  sprintf(radiopacket, "%s,V,%s,%03d,B,%s,T,%s,H,%s",
   timestamp(timestr, 12),
   version_remote,
   packetnum, 
   fltbuf_bat,
   fltbuf_tmp,
   fltbuf_hum);

#ifdef DEBUG
  Serial.print("Sending "); 
  Serial.println(radiopacket);
#endif // DEBUG
  
  // Send a message to the DESTINATION!
  if (rf69_manager.sendtoWait((uint8_t *)radiopacket, strlen(radiopacket), DEST_ADDRESS)) {
    // Now wait for a reply from the server
    uint8_t len = sizeof(buf);
    uint8_t from;   
    if (rf69_manager.recvfromAckTimeout(buf, &len, 2000, &from)) {
      buf[len] = 0; // zero out remaining string

      Blink(LED, 40, 3); //blink LED 3 times, 40ms between blinks
      
#ifdef DEBUG
      Serial.print("Reply,"); 
      Serial.print(from);
      Serial.print(",RSSI,");
      Serial.print(rf69.lastRssi());
      Serial.print(",");
      Serial.println((char*)buf);           
#endif // DEBUG
    } else {
#ifdef DEBUG
      Serial.println("No reply, is anyone listening?");
#endif // DEBUG
    }
  } else {
#ifdef DEBUG
    Serial.println("Sending failed (no ack)");
#endif // DEBUG
  }
  
  rf69.sleep();

#ifdef DEBUG
  delay(10000);
#else
  rtc.standbyMode();
#endif // DEBUG
}

void Blink(byte PIN, byte DELAY_MS, byte loops) {
  for (byte i=0; i<loops; i++)  {
    digitalWrite(PIN,HIGH);
    delay(DELAY_MS);
    digitalWrite(PIN,LOW);
    delay(DELAY_MS);
  }
}
