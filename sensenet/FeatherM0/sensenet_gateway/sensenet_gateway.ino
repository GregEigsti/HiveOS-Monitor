// rf69 demo tx rx.pde
// -*- mode: C++ -*-
// Example sketch showing how to create a simple addressed, reliable messaging client
// with the RH_RF69 class. RH_RF69 class does not provide for addressing or
// reliability, so you should only use RH_RF69  if you do not need the higher
// level messaging abilities.
// It is designed to work with the other example rf69_server.
// Demonstrates the use of AES encryption, setting the frequency and modem 
// configuration

#include <Wire.h>
#include <RTCZero.h>
#include <SPI.h>
#include <RH_RF69.h>
#include <RHReliableDatagram.h>

//#include <Adafruit_Sensor.h>
//#include <Adafruit_BME280.h>
//Adafruit_BME280 sensor_bme280; // I2C
#define SEALEVELPRESSURE_HPA (1013.25)

#include <Adafruit_BMP085.h>
Adafruit_BMP085 sensor_bmp085;

#include "Adafruit_HTU21DF.h"
Adafruit_HTU21DF sensor_htu21df = Adafruit_HTU21DF();


/************ Radio Setup ***************/

// Change to 434.0 or other frequency, must match RX's freq!
#define RF69_FREQ 915.0

// who am i? (server address)
#define MY_ADDRESS     1

#define RFM69_CS      8
#define RFM69_INT     3
#define RFM69_RST     4
#define LED           13


//RTC object
RTCZero rtc;
volatile bool alarm;

// Singleton instance of the radio driver
RH_RF69 rf69(RFM69_CS, RFM69_INT);

// Class to manage message delivery and receipt, using the driver declared above
RHReliableDatagram rf69_manager(rf69, MY_ADDRESS);

int16_t packetnum = 0;  // packet counter, we increment per xmission

//local sensor data structure
typedef struct {
  float temperature;
  float humidity;
  float altitude;
  float pressure;
  //float battery;
} LOCALSENSORDATA, *PLOCALSENSORDATA;

LOCALSENSORDATA localsensordata;


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
  const byte seconds = 0;
  // * Change these values to set the current initial date * /
  const byte year    = 66;  
  const byte month   = 4;
  const byte day     = 29;
  
  rtc.begin();
  rtc.setTime(hours, minutes, seconds);
  rtc.setDate(day, month, year);
  rtc.setAlarmSeconds(59);
  rtc.enableAlarm(rtc.MATCH_SS);
  rtc.attachInterrupt(rtc_isr); 
}

void setup_sensors()
{
  /*
  if (!sensor_bme280.begin()) 
  {
      Serial.println("Did not find BME280 sensor!");
      //while (true);
  }
  */
  
  if (!sensor_htu21df.begin()) 
  {
    Serial.println("Couldn't find HTU21DF sensor!");
    while (1);
  }

  if (!sensor_bmp085.begin()) {
   Serial.println("Couldn't find BMP085 sensor!");
   while (1);
  }

/*    
  // weather monitoring
  Serial.println("-- Weather Station Scenario --");
  Serial.println("forced mode, 1x temperature / 1x humidity / 1x pressure oversampling,");
  Serial.println("filter off");
  sensor_bme280.setSampling(Adafruit_BME280::MODE_FORCED,
                  Adafruit_BME280::SAMPLING_X4, // temperature
                  Adafruit_BME280::SAMPLING_X4, // pressure
                  Adafruit_BME280::SAMPLING_X4, // humidity
                  Adafruit_BME280::FILTER_OFF,
                  Adafruit_BME280::STANDBY_MS_1000);
                      
    // humidity sensing
    Serial.println("-- Humidity Sensing Scenario --");
    Serial.println("forced mode, 1x temperature / 1x humidity / 0x pressure oversampling");
    Serial.println("= pressure off, filter off");
    bme.setSampling(Adafruit_BME280::MODE_FORCED,
                    Adafruit_BME280::SAMPLING_X1,   // temperature
                    Adafruit_BME280::SAMPLING_NONE, // pressure
                    Adafruit_BME280::SAMPLING_X1,   // humidity
                    Adafruit_BME280::FILTER_OFF );
                      
    // suggested rate is 1Hz (1s)
    delayTime = 1000;  // in milliseconds
*/
  
}

void rtc_isr()
{
  alarm = true;
}

////////////////////////////////////////////////////////////////////////////////
// Send local sensor data to host
////////////////////////////////////////////////////////////////////////////////
void output_local_sensor_data(LOCALSENSORDATA data)
{
  /*
  Serial.print("Temperature = ");
  Serial.print(data.temperature);
  Serial.println(" *C");
  Serial.print("Pressure = ");
  Serial.print(data.pressure);
  Serial.println(" hPa");
  Serial.print("Approx. Altitude = ");
  Serial.print(data.altitude);
  Serial.println(" m");
  Serial.print("Humidity = ");
  Serial.print(data.humidity);
  Serial.println(" %");
  */

  Serial.print("T," ); 
  Serial.print(data.temperature);
  Serial.print(",H," ); 
  Serial.print(data.humidity);
  Serial.print(",P," ); 
  Serial.print(data.pressure);
  Serial.print(",A," ); 
  Serial.println(data.altitude);
}

////////////////////////////////////////////////////////////////////////////////
// Read temperature/humidity and optional pressure sensors
//   Gateway node has more capable BME280 temp/hum/press sensor
//   Remote node has cheaper Si7021 temp/hum/press sensor
////////////////////////////////////////////////////////////////////////////////
void read_sensors(PLOCALSENSORDATA data)
{
  //sensor_bme280.takeForcedMeasurement();
  
  //data->temperature = sensor_bme280.readTemperature();
  //data->pressure = sensor_bme280.readPressure() / 100.0F;
  //data->altitude = sensor_bme280.readAltitude(SEALEVELPRESSURE_HPA);
  //data->humidity = sensor_bme280.readHumidity();

  //data->temperature = sensor_bmp085.readTemperature();
  data->pressure = sensor_bmp085.readPressure() / 100.0F;
  data->altitude = sensor_bmp085.readAltitude(SEALEVELPRESSURE_HPA);

  data->humidity = sensor_htu21df.readHumidity();
  data->temperature = sensor_htu21df.readTemperature();

  /*
  Serial.print("Temperature = ");
  Serial.print(data->temperature);
  Serial.println(" *C");
  Serial.print("Pressure = ");
  Serial.print(data->pressure);
  Serial.println(" hPa");
  Serial.print("Approx. Altitude = ");
  Serial.print(data->altitude);
  Serial.println(" m");
  Serial.print("Humidity = ");
  Serial.print(data->humidity);
  Serial.println(" %");
  Serial.println();
  */
}


void setup() 
{
  pinMode(LED, OUTPUT);

  //delay to allow usb programmer time to connect before deep sleep
  digitalWrite(LED, HIGH);
  delay(5000);
  digitalWrite(LED, LOW);

  setup_serial(115200);
  setup_rtc();

  setup_sensors();

  pinMode(LED, OUTPUT);     
  pinMode(RFM69_RST, OUTPUT);
  digitalWrite(RFM69_RST, LOW);

  Serial.println("SenseNet Gateway v0.1");

  // manual reset
  digitalWrite(RFM69_RST, HIGH);
  delay(10);
  digitalWrite(RFM69_RST, LOW);
  delay(10);
  
  if (!rf69_manager.init()) {
    Serial.println("RFM69 radio init failed");
    while (1);
  }

  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM (for low power module)
  // No encryption
  if (!rf69.setFrequency(RF69_FREQ)) {
    Serial.println("setFrequency failed");
  }

  // If you are using a high power RF69 eg RFM69HW, you *must* set a Tx power with the
  // ishighpowermodule flag set like this:
  rf69.setTxPower(20, true);  // range from 14-20 for power, 2nd arg must be true for 69HCW

  // The encryption key has to be the same as the one in the server
  uint8_t key[] = { 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01,
                    0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01};
  rf69.setEncryptionKey(key);
  
  Serial.print("RFM69 radio @ ");  
  Serial.print((int)RF69_FREQ);  
  Serial.println(" MHz");

  alarm = true;
}


// Dont put this on the stack:
uint8_t data[] = "00:+02:-18";
// Dont put this on the stack:
uint8_t buf[RH_RF69_MAX_MESSAGE_LEN];

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

void loop() {

  if(alarm)
  {
    alarm = false;
    Serial.print(timestamp(timestr, 12));
    Serial.print(",GW,");

    read_sensors(&localsensordata);
    output_local_sensor_data(localsensordata);
  }

  bool result = rf69_manager.waitAvailableTimeout(1000);
  if(result)
  //if (rf69_manager.available())
  {
    // Wait for a message addressed to us from the client
    uint8_t len = sizeof(buf);
    uint8_t from;
    if (rf69_manager.recvfromAck(buf, &len, &from)) {
      buf[len] = 0; // zero out remaining string

      Blink(LED, 40, 3); //blink LED 3 times, 40ms between blinks

      Serial.print(timestamp(timestr, 12));    
      Serial.print(",RX,");
      Serial.print(from);
      Serial.print(",RSSI,");
      Serial.print(rf69.lastRssi());
      Serial.print(",");
      Serial.println((char*)buf);


      //strcpy(timestr, data);

      
      // Send a reply back to the originator client
      if (!rf69_manager.sendtoWait(data, sizeof(data), from))
        Serial.println("Sending failed (no ack)");
    }
  }
}


void Blink(byte PIN, byte DELAY_MS, byte loops) {
  for (byte i=0; i<loops; i++)  {
    digitalWrite(PIN,HIGH);
    delay(DELAY_MS);
    digitalWrite(PIN,LOW);
    delay(DELAY_MS);
  }
}
