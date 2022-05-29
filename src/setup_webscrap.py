from time import sleep

import pandas as pd
import json

from src.browser import bot_is_detected, cookie_banner, init_browser
from src.config import POST_URL, PRE_URL, SPAN_WINDOW, RETURN_WINDOW, CITY_CODES_PATH


def get_city_codes_on_skyscanner(departure, arrival):
    """ Get the cities nomenclature in URL """
    dict_cities = {}
    browser = init_browser()
    browser.get("https://www.skyscanner.fr/")
    cookie_banner(browser)
    browser.find_element_by_id("fsc-origin-search").clear()
    browser.find_element_by_id("fsc-origin-search").send_keys(departure)
    browser.find_element_by_id("fsc-destination-search").send_keys(arrival)
    browser.find_element_by_id("fsc-trip-type-selector-one-way").click()
    browser.find_element_by_id("fsc-origin-search").click()
    browser.find_element_by_id("fsc-destination-search").click()
    browser.find_element_by_xpath('//button[contains(text(), "Trouver un vol")]').click()
    sleep(2.5)

    # Bot detection : manual intervention for this session
    if bot_is_detected(browser):
        print("You have 100 seconds to complete captcha test !")
        t = sleep(100)  # 100 seconds to pass captcha test

    url = browser.current_url
    url = url.replace(PRE_URL, '')
    url = url.replace(POST_URL, '')
    
    # Cities nomenclature in Skyscanner's URL
    dict_cities['departure'] = {'name': departure, 'code': url.split('/')[0]}
    dict_cities['arrival'] = {'name': arrival, 'code': url.split('/')[1]}
    
    browser.close()
    return dict_cities


def get_city_codes(departure, arrival):
    with open(CITY_CODES_PATH, 'r') as f:
        codes = json.load(f)
    dict_cities = {
        'departure': {'name': departure, 'code': codes.get(departure, '')},
        'arrival': {'name': arrival, 'code': codes.get(arrival, '')}
    }
    if not (dict_cities['departure']['code'] and dict_cities['arrival']['code']):
        dict_cities = get_city_codes(departure, arrival)
    return dict_cities



def create_trips_timetable(dict_cities, start_date, stay_in_days = 0):
    """ Create list of trips by incrementing start date given span window
        and incrementing stay in days if return is expected """
    departure_delay = (pd.Timestamp(start_date) - pd.Timestamp.now()).days
    departure_days = [
        pd.Timestamp.now() + pd.Timedelta(days=departure_delay + i) for i in range(SPAN_WINDOW)
    ]
    if stay_in_days:
        # Return trip
        trips = [
            dict_cities['departure']['code'] + '/' + dict_cities['arrival']['code'] + '/' +
            str(x)[2:4] + str(x)[5:7] + str(x)[8:10] + "/"
            + str(x + pd.Timedelta(days=d + stay_in_days))[2:4]
            + str(x + pd.Timedelta(days=d + stay_in_days))[5:7]
            + str(x + pd.Timedelta(days=d + stay_in_days))[8:10]
            for x in departure_days for d in range(-1 * RETURN_WINDOW, RETURN_WINDOW)
        ]
    else:
        # One Way flight
        trips = [
            dict_cities['departure']['code'] + '/' + dict_cities['arrival']['code'] + '/' + str(x)[2:4]
            + str(x)[5:7] + str(x)[8:10] for x in departure_days
        ]
    return trips


def setup_webscrap(departure, arrival, start_date, stay_in_days = 0):
    """
    Create a list of Trips to search for (a trip is a String object that
    concatenate Departure, Arrival and Date information)
    """
    dict_cities = get_city_codes(departure, arrival)
    if not (dict_cities['departure']['code'] and dict_cities['arrival']['code']):
        return False
    trips = create_trips_timetable(dict_cities, start_date, stay_in_days)
    return trips
