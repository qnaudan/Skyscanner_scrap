from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from time import sleep

from src.config import PRE_URL, POST_URL


# TODO : class browser
def init_browser():
    """
    Initialize the browser
    """
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--incognito")
    browser = Chrome(options=chrome_options)
    return browser


def cookie_banner(browser):
    try:
        browser.find_element_by_xpath('//button[contains(text(), "OK")]') \
                .click()
        return 1
    except:
        return 0


def covid_banner(browser):
    try:
        browser.find_element_by_xpath('//a[contains(text(), "Cancel")]') \
                .click()
        return 1
    except:
        return 0


def price_alert_banner(browser):
    try:
        browser.find_element_by_xpath('//button[contains(@class, "BpkCloseButton_bpk-close-button_")]') \
                .click()
        return 1
    except:
        return 0


def bot_is_detected(browser):
    """
    <section class="App_App__headline__fdpD_">Êtes-vous une personne ou un robot ?</section>
    <section class="App_App__instruction__3GRTU">Cochez la case pour continuer :</section>
    <div class="recaptcha-checkbox-border" role="presentation" style=""></div>
    """
    try:
        _ = browser.find_element_by_xpath('//section[contains(text(), "Êtes-vous une personne ou un robot ?")]')
        return 1
    except:
        return 0


def format_page_results(browser, trip, df, banners, is_one_way):
    """
    For a given browser (Selenium object) and a given trip (string concatening
    Departure, Arrival and Date), appends results of web page to DataFrame
    Note that there are several banners to handle only once
    """
    browser.get(PRE_URL + trip + POST_URL)
    WebDriverWait(browser, 25).until(EC.presence_of_element_located((By.ID, "Layer_1")))
    
    # Bot
    if bot_is_detected(browser):
        browser.close()
        browser = init_browser()
        sleep(1)
        browser.get(PRE_URL + trip + POST_URL)
        WebDriverWait(browser, 25).until(EC.presence_of_element_located((By.ID, "Layer_1")))

    # Cookie banner
    if not banners['cookie']:
        sleep(1)
        if cookie_banner(browser):
            banners['cookie'] = True
            
    # Price alert banner
    if not banners['price_alert']:
        sleep(8) # Security at set up to dodge banners
        if price_alert_banner(browser):
            banners['price_alert'] = True
    
    # Covid banner
    if not banners['covid']:
        sleep(15) # Security at set up to dodge banners
        if covid_banner(browser):
            banners['covid'] = True
         
    # Results
    try: # Plus de résultats
        plus = browser.find_element_by_xpath('//button[contains(text(), "Plus de résultats")]')
        plus.click()
    except:
        pass
    sleep(2)

    # Flight boxes
    boxes = browser.find_elements_by_xpath('//div[starts-with(@class, "EcoTicketWrapper_itineraryContainer_")]')
    for j in range(len(boxes)):
        # NOTE TO MYSELF : " .// " in the xpath, otherwise whole page is read !
        price_currency = boxes[j].find_element_by_xpath('.//div[starts-with(@class, "Price_mainPriceContainer_")]').text
        price_currency.strip()
        assert len(price_currency.split(' ')) == 2
        if is_one_way:
            direct_or_stops = boxes[j].find_element_by_xpath('.//div[contains(@class, "LegInfo_stopsLabelContainer_")]').text
            try:
                company = boxes[j].find_element_by_xpath('.//div[contains(@class, "LegLogo_legImage_")]') \
                    .find_element_by_tag_name("img").get_attribute("alt")
            except:
                company = boxes[j].find_element_by_xpath('.//div[contains(@class, "TicketBody_legLogo_")]').text
            df.at[trip + '_' + str(j)] = [
                trip.split('/')[0],
                trip.split('/')[1],
                trip.split('/')[2],
                boxes[j].find_element_by_xpath('.//span[contains(@class, "LegInfo_routePartialTime_")]').text, # Departure Time
                boxes[j].find_element_by_xpath('.//span[contains(@class, "Duration_duration_")]').text, # Flight Length
                direct_or_stops.split("\n")[0], # Direct ?
                company, # Airtravel Company
                int(price_currency.split(' ')[0]), # Price
                price_currency.split(' ')[1] # Currency
            ]
        else:
            ways = boxes[j].find_elements_by_xpath('.//div[starts-with(@class, "LegDetails_container_")]')
            assert len(ways)==2
            direct_or_stops_1 = ways[0].find_element_by_xpath('.//div[contains(@class, "LegInfo_stopsLabelContainer_")]').text
            direct_or_stops_2 = ways[1].find_element_by_xpath('.//div[contains(@class, "LegInfo_stopsLabelContainer_")]').text
            try:
                company_1 = ways[0].find_element_by_xpath('.//div[contains(@class, "LegLogo_legImage_")]') \
                                .find_element_by_tag_name("img").get_attribute("alt")
            except:
                company_1 = ways[0].find_element_by_xpath('.//div[contains(@class, "TicketBody_legLogo_")]').text
            try:
                company_2 = ways[1].find_element_by_xpath('.//div[contains(@class, "LegLogo_legImage_")]') \
                                .find_element_by_tag_name("img").get_attribute("alt")
            except:
                company_2 = ways[1].find_element_by_xpath('.//div[contains(@class, "TicketBody_legLogo_")]').text
            df.at[trip + '_' + str(j)] = [
                trip.split('/')[0],
                trip.split('/')[1],
                trip.split('/')[2],
                ways[0].find_element_by_xpath('.//span[contains(@class, "LegInfo_routePartialTime_")]').text, # Departure Time
                ways[0].find_element_by_xpath('.//span[contains(@class, "Duration_duration_")]').text, # Flight Length
                direct_or_stops_1.split("\n")[0], # Direct ?
                company_1, # Airtravel Company
                trip.split('/')[3],
                ways[1].find_element_by_xpath('.//span[contains(@class, "LegInfo_routePartialTime_")]').text, # Departure Time
                ways[1].find_element_by_xpath('.//span[contains(@class, "Duration_duration_")]').text, # Flight Length
                direct_or_stops_2.split("\n")[0], # Direct ?
                company_2, # Airtravel Company
                int(price_currency.split(' ')[0]), # Price
                price_currency.split(' ')[1] # Currency
            ]
            del ways
    del boxes
    return df
