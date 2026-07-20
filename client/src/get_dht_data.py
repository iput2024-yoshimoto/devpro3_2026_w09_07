import time
import dht22_takemoto as dht22

dht22_instance = dht22.DHT22(gpio=26)


def get_dht_data():

    while True:

        try:

            temp, hum, check = dht22_instance.read()

            print("Temperature: %.1f C" % temp)
            print("Humidity: %.1f %%" % hum)

            return float(temp), float(hum)

        except dht22.DHT22CRCError:

            print("DHT22 CRC Error")

            time.sleep(2)

        except dht22.DHT22MissingDataError:

            print("DHT22 Missing Data Error")

            time.sleep(2)

if __name__ == "__main__":
    get_dht_data() 