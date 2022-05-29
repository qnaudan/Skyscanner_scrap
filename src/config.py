import argparse

CITY_CODES_PATH = './static/codes.json'

# multiprocessing library
N_PROCESSES = 2

# Number of web browsers opened at same time (can depend empirically of internet speed)
N_BROWSERS = 1

# Range of days from start date to look up for flight fares
SPAN_WINDOW = 15

# Range of days to look up before and after expected number of days in stay
RETURN_WINDOW = 10

# Saving to csv rate
SAVING_RATE = 12

# URL body for this situation : 1 adult, French website, EUR currency
PRE_URL = "https://www.skyscanner.fr/transport/vols/"
URL_PARAMS = {
    'adults': 1,
    'children': 0,
    'adultsv2': 1,
    'childrenv2': 0,
    'infants': 0,
    'cabinclass': 'economy',
    'rtn': 0,
    'preferdirects': 'false',
    'outboundaltsenabled': 'false',
    'inboundaltsenabled': 'false',
    'ref': 'home'
}
POST_URL = "/?" + '&'.join([key + '=' + str(value) for key, value in URL_PARAMS.items()])

COLUMNS_ONEWAY = [
    'From', 'To', 'Date', 'Departure time', 'Duration', 'Company', 'Direct flight', 'Price', 'Currency'
]
COLUMNS_RETURN = [
    'From', 'To', 'Date - OneWay', 'Departure time - OneWay', 'Duration - OneWay', 'Direct flight - OneWay',
    'Company - OneWay', 'Date - Return', 'Departure time - Return', 'Duration - Return', 'Direct flight - Return',
    'Company - Return', 'Price', 'Currency'
]


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', help='Departure airport', required=True)
    parser.add_argument('-a', help='Arrival airport', required=True)
    parser.add_argument('-s', help='Start date to look up', required=True)
    parser.add_argument('--days', help='Stay in days before return (0 if one way flight)', default=0)
    args = parser.parse_args()
    return args
