from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import pandas as pd
from time import sleep
from openpyxl import load_workbook
import multiprocessing as mp


# =============================================================================
# PROGRAM PARAMETERS
# =============================================================================

# multiprocessing library
N_processes = 3

# Number of web browsers opened at same time (depends empirically of internet speed)
N_browsers = 3

# Our Departure and Arrival Cities / One-Way or Return flights
From = input("Departure City : ")
To = input("Destination City : ")
Return = int( \
         input("Estimated stay in number of days (0 for One-Way flight) : "))

# In how many days and for which range to look up flight fares
# Default : starting next month and for 3 months
Start, Iterations = 30, 50


# URL body for this situation : 1 adult, French website, EUR currency
url_body_1 = "https://www.skyscanner.fr/transport/vols/"
url_body_2 = "/?adults=1&children=0&adultsv2=1&childrenv2=&infants=0" + \
    "&cabinclass=economy&rtn=0&preferdirects=false&outboundaltsenabled=" + \
    "false&inboundaltsenabled=false&ref=home"




# =============================================================================
# PROGRAM FUNCTIONS
# =============================================================================

def create_trips(From, To, Return, Start, Iterations):
    """
    Create a list of Trips to search for (a trip is a String object that
    concatenate Departure, Arrival and Date information)
    """
    # First step : get the cities nomenclature in URL
    Dict_cities = {}
    browser = webdriver.Firefox(executable_path = "./geckodriver",
                            firefox_profile=webdriver.FirefoxProfile()\
                            .set_preference("browser.privatebrowsing.autostart", True))
    browser.get("https://www.skyscanner.fr/")
    try: # cookie banner
        browser.find_element_by_xpath('//button[contains(text(), "OK")]').click()
    except:
        pass
    browser.find_element_by_id("fsc-origin-search").clear()
    browser.find_element_by_id("fsc-origin-search").send_keys(From)
    browser.find_element_by_id("fsc-destination-search").send_keys(To)
    browser.find_element_by_id("fsc-trip-type-selector-one-way").click()
    browser.find_element_by_xpath('//button[contains(text(), "Trouver un vol")]').click()
    sleep(0.5)
    url = browser.current_url
    url = url.replace(url_body_1, '')
    url = url.replace(url_body_2, '')
    
    # Cities nomenclature in Skyscanner's URL
    Dict_cities[From] = url.split('/')[0]
    Dict_cities[To] = url.split('/')[1]
    
    browser.close()
    # Second step : create list of trips by incrementing Timestamp
    Days = [pd.Timestamp.now()+pd.Timedelta(days=Start+i) for i in range(Iterations)]
    if Return==0:
        Trips = [Dict_cities[From]+'/'+Dict_cities[To]+'/'+str(x)[2:4]+ \
                 str(x)[5:7]+str(x)[8:10] for x in Days]
    else: # Returning fligths
        """
        The stay length in days is shorten or broaden by 50% in the research
        """
        Trips = [Dict_cities[From]+'/'+Dict_cities[To]+'/'+str(x)[2:4]+ \
                 str(x)[5:7]+str(x)[8:10] +"/"+ \
                 str(x+pd.Timedelta(days=d + Return))[2:4] + \
                 str(x+pd.Timedelta(days=d + Return))[5:7] + \
                 str(x+pd.Timedelta(days=d + Return))[8:10] \
                 for x in Days for d in range(-1 * Return//2, Return//2)]
    return(Trips, Dict_cities)

# create_trips('Paris','Dubai',0,20,10)
# create_trips('Paris','Dubai',10,20,5)


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

def bot_detection(browser):
    return(browser)

def init_workbook(filename, Return):
    if Return==0:
        DF = pd.DataFrame(columns=['From','To','Date','Departure time',
                    'Duration','Company','Direct flight','Price','Currency'])
    else:
        DF = pd.DataFrame(columns=['From','To','Date - OneWay','Departure time - OneWay',
            'Duration - OneWay','Direct flight - OneWay','Company - OneWay',
            'Date - Return','Departure time - Return','Duration - Return',
            'Direct flight - Return','Company - Return','Price','Currency'])
    DF.to_excel(filename, index=False) # Initiate Workbook
    return 1

def save_DF_to_workbook(filename, DF):
    book = load_workbook(filename, index=False), 
    writer = pd.ExcelWriter(filename, engine='openpyxl')
    writer.book=book #Save former sheets
    DF.to_excel(writer, index=False)
    writer.save()
    return 1

def page_results_OneWay(browser, trip, DF, banners):
    """
    For a given browser (Selenium object) and a given trip (string concatening
    Departure, Arrival and Date), appends results of web page to DataFrame
    Note that there are several banners to handle only once
    """
    browser.get(url_body_1 + trip.split('_')[0]+"/"+ trip.split('_')[1] + \
                "/" + trip.split('_')[2] + url_body_2)
    WebDriverWait(browser, 15).until(EC.presence_of_element_located((By.ID, "Layer_1")))
    
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
        sleep(8) # Security at set up to dodge banners
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
        direct_or_stops = boxes[j].find_element_by_xpath('.//div[contains(@class, "LegInfo_stopsLabelContainer_")]').text
        try:
            comp = boxes[j].find_element_by_xpath('.//div[contains(@class, "LegLogo_legImage_")]') \
                            .find_element_by_tag_name("img").get_attribute("alt")
        except:
            comp = boxes[j].find_element_by_xpath('.//div[contains(@class, "TicketBody_legLogo_")]').text
        DF.at[trip+'_'+str(j)] = [trip.split('_')[0], trip.split('_')[1], trip.split('_')[2],
              boxes[j].find_element_by_xpath('.//span[contains(@class, "LegInfo_routePartialTime_")]').text, # Departure Time
              boxes[j].find_element_by_xpath('.//span[contains(@class, "Duration_duration_")]').text, # Flight Length
              direct_or_stops.split("\n")[0], # Direct ?
              comp, # Airtravel Company
              price_currency.split(' ')[0], # Price
              price_currency.split(' ')[1] # Currency
              ]
    del boxes
    return 1

def main_OneWay(Trips):
    """
    Initialize a browser and search results for a list of trips,
    appends results to output DataFrame
    """
    global filename
    DF = pd.DataFrame(columns=['From','To','Date','Departure time','Duration',
                               'Direct flight','Company','Price','Currency'])
    banners = {'cookie':False, 'covid':False, 'price_alert':False}
    b = webdriver.Firefox(executable_path = "./geckodriver",
                          firefox_profile=webdriver.FirefoxProfile() \
                          .set_preference("browser.privatebrowsing.autostart", True))
    for j in range(len(Trips)):
        page_results_OneWay(b, Trips[j], DF, banners)
        if (j+1) % 5 == 0:
            save_DF_to_workbook(filename, DF)
            DF = pd.DataFrame(columns=['From','To','Date','Departure time',
                    'Duration','Direct flight','Price','Currency','Company'])
    b.close()
    save_DF_to_workbook(filename, DF)
    return(DF)


def page_results_Return(browser, trip, DF, banners):
    """
    For a given browser (Selenium object) and a given trip (string concatening
    Departure, Arrival and Date), appends results of web page to DataFrame
    Note that there are several banners to handle only once
    """
    browser.get(url_body_1 + trip.split('_')[0]+"/"+ trip.split('_')[1] + \
                "/"+trip.split('_')[2] +"/"+ trip.split('_')[3] + url_body_2)
    WebDriverWait(browser, 15).until(EC.presence_of_element_located((By.ID, "Layer_1")))
    
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
        sleep(8) # Security at set up to dodge banners
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
        # NOTE TO MYSELF : " .// " in the xpath, otherwise whole page is read 
        price_currency = boxes[j].find_element_by_xpath('.//div[starts-with(@class, "Price_mainPriceContainer_")]').text   
        # One Way and Return
        ways = boxes[j].find_elements_by_xpath('.//div[starts-with(@class, "LegDetails_container_")]')
        assert len(ways)==2
        direct_or_stops_1 = ways[0].find_element_by_xpath('.//div[contains(@class, "LegInfo_stopsLabelContainer_")]').text
        direct_or_stops_2 = ways[1].find_element_by_xpath('.//div[contains(@class, "LegInfo_stopsLabelContainer_")]').text
        try:
            comp_1 = ways[0].find_element_by_xpath('.//div[contains(@class, "LegLogo_legImage_")]') \
                              .find_element_by_tag_name("img").get_attribute("alt")
        except:
            comp_1 = ways[0].find_element_by_xpath('.//div[contains(@class, "TicketBody_legLogo_")]').text
        try:
            comp_2 = ways[1].find_element_by_xpath('.//div[contains(@class, "LegLogo_legImage_")]') \
                              .find_element_by_tag_name("img").get_attribute("alt")
        except:
            comp_2 = ways[1].find_element_by_xpath('.//div[contains(@class, "TicketBody_legLogo_")]').text
        DF.at[trip+'_'+str(j)] = [trip.split('_')[0], trip.split('_')[1], trip.split('_')[2],
              ways[0].find_element_by_xpath('.//span[contains(@class, "LegInfo_routePartialTime_")]').text, # Departure Time
              ways[0].find_element_by_xpath('.//span[contains(@class, "Duration_duration_")]').text, # Flight Length
              direct_or_stops_1.split("\n")[0], # Direct ?
              comp_1, # Airtravel Company
              trip.split('_')[3],
              ways[1].find_element_by_xpath('.//span[contains(@class, "LegInfo_routePartialTime_")]').text, # Departure Time
              ways[1].find_element_by_xpath('.//span[contains(@class, "Duration_duration_")]').text, # Flight Length
              direct_or_stops_2.split("\n")[0], # Direct ?
              comp_2, # Airtravel Company
              price_currency.split(' ')[0], # Price
              price_currency.split(' ')[1] # Currency
              ]
        del ways
    del boxes
    return 1


def main_Return(Trips):
    """
    Initialize a browser and search results for a list of trips,
    appends results to output DataFrame
    """
    global filename
    DF = pd.DataFrame(columns=['From','To','Date - OneWay','Departure time - OneWay',
            'Duration - OneWay','Direct flight - OneWay','Company - OneWay',
            'Date - Return','Departure time - Return','Duration - Return',
            'Direct flight - Return','Company - Return','Price','Currency'])
    banners = {'cookie':False, 'covid':False, 'price_alert':False}
    b = webdriver.Firefox(executable_path = "./geckodriver",
                          firefox_profile=webdriver.FirefoxProfile() \
                          .set_preference("browser.privatebrowsing.autostart", True))
    for j in range(len(Trips)):
        page_results_Return(b, Trips[j], DF, banners)
        if (j+1) % 5 == 0:
            save_DF_to_workbook(filename, DF)
            DF = pd.DataFrame(columns=['From','To','Date - OneWay','Departure time - OneWay',
            'Duration - OneWay','Direct flight - OneWay','Company - OneWay',
            'Date - Return','Departure time - Return','Duration - Return',
            'Direct flight - Return','Company - Return','Price','Currency'])
    b.close()
    save_DF_to_workbook(filename, DF)
    return(DF)


# =============================================================================
# --- MAIN PROGRAM ---
# =============================================================================

# Workbook for results
filename = "Workbooks/Skyscanner_from_" + From + "_To_" + To + "_" + \
                ("One-Way.xlsx" if Return==0 else "Return.xlsx")
init_workbook(filename, Return)

# Trips
Trips, Dict_cities = create_trips(From, To, Return, Start, Iterations)

# Divide task in N browsers
N = len(Trips)
Inputs = []
for i in range(N_browsers):
    Inputs.append(Trips[i*(N//N_browsers):(i+1)*(N//N_browsers)])

with mp.Pool(N_processes) as p:
    if Return==0:
        DF_list = p.map(main_OneWay, Inputs)
    else:
        DF_list = p.map(main_Return, Inputs)
#
print(DF_list)

"""

NEXT STEP : BOT PAGE DETECTION


try: # êtes-vous un robot?
    detect = browser.find_element_by_xpath('//button[contains(text(), "Êtes-vous une personne ou un robot ?")]')
    browser.close()
    DF.to_excel("Skyscanner_PARIS.xlsx", index=False)
    print('Bot detect !'), print(A)
except:
    pass
"""
###