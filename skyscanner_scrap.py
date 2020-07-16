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
N_processes = 4

# Number of web browsers opened at same time (can depend empirically of internet speed)
N_browsers = 3


# In how many days and for which range to look up flight fares
Start, Iterations = 50, 10

# Saving to csv rate
pages_lookup_before_saving = 12


# URL body for this situation : 1 adult, French website, EUR currency
url_body_1 = "https://www.skyscanner.fr/transport/vols/"
url_body_2 = "/?adults=1&children=0&adultsv2=1&childrenv2=&infants=0" + \
    "&cabinclass=economy&rtn=0&preferdirects=false&outboundaltsenabled=" + \
    "false&inboundaltsenabled=false&ref=home"

columns_OneWay = ['From','To','Date','Departure time','Duration',
				  'Company','Direct flight','Price','Currency']
columns_Return = ['From','To','Date - OneWay','Departure time - OneWay',
            'Duration - OneWay','Direct flight - OneWay','Company - OneWay',
            'Date - Return','Departure time - Return','Duration - Return',
            'Direct flight - Return','Company - Return','Price','Currency']


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
    browser.find_element_by_id("fsc-origin-search").click()
    browser.find_element_by_id("fsc-destination-search").click()
    browser.find_element_by_xpath('//button[contains(text(), "Trouver un vol")]').click()
    sleep(2.5)
    # Bot detection : manual intervention for this session
    if bot_detect(browser):
    	print("You have 100 seconds to complete captcha test !")
    	sleep(100) # 100 seconds to pass captcha test
    url = browser.current_url
    url = url.replace(url_body_1, '')
    url = url.replace(url_body_2, '')
    
    # Cities nomenclature in Skyscanner's URL
    Dict_cities[From] = url.split('/')[0]
    Dict_cities[To] = url.split('/')[1]
    
    browser.close()
    
    if len(Dict_cities[From])==0 or len(Dict_cities[To])==0: # Trip isn't supported
        return([], False)
    else:
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
        return(Trips, True)

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
    
def bot_detect(browser):
    """
    <section class="App_App__headline__fdpD_">Êtes-vous une personne ou un robot ?</section>
    <section class="App_App__instruction__3GRTU">Cochez la case pour continuer :</section>
    <div class="recaptcha-checkbox-border" role="presentation" style=""></div>
    """
    try:
    	browser.find_element_by_xpath('//section[contains(text(), "Êtes-vous une personne ou un robot ?")]')
    	return 1
    except:
        return 0

def init_workbook(filename, Return):
    if Return==0:
        DF = pd.DataFrame(columns=columns_OneWay)
    else:
        DF = pd.DataFrame(columns=columns_Return)
    DF.to_excel(filename, index=False) # Initiate Workbook
    return 1

def save_DF_to_workbook(filename, DF):
    book = load_workbook(filename) 
    writer = pd.ExcelWriter(filename, engine='openpyxl')
    writer.book=book #Save former sheets
    DF.to_excel(writer, sheet_name='Sheet1', index=False)
    writer.save()
    return 1

def page_results_OneWay(browser, trip, DF, banners):
    """
    For a given browser (Selenium object) and a given trip (string concatening
    Departure, Arrival and Date), appends results of web page to DataFrame
    Note that there are several banners to handle only once
    """
    browser.get(url_body_1 + trip + url_body_2)
    WebDriverWait(browser, 25).until(EC.presence_of_element_located((By.ID, "Layer_1")))
    
    # Bot
    if bot_detect(browser):
        browser.close()
        browser = webdriver.Firefox(executable_path = "./geckodriver",
                          firefox_profile=webdriver.FirefoxProfile() \
                          .set_preference("browser.privatebrowsing.autostart",
                                          True))
        sleep(1)
        browser.get(url_body_1 + trip + url_body_2)
        WebDriverWait(browser, 25).until(EC.presence_of_element_located((By.ID,
                     "Layer_1")))
    
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
        price_currency.strip()
        assert len(price_currency.split(' ')) == 2 
        direct_or_stops = boxes[j].find_element_by_xpath('.//div[contains(@class, "LegInfo_stopsLabelContainer_")]').text
        try:
            comp = boxes[j].find_element_by_xpath('.//div[contains(@class, "LegLogo_legImage_")]') \
                            .find_element_by_tag_name("img").get_attribute("alt")
        except:
            comp = boxes[j].find_element_by_xpath('.//div[contains(@class, "TicketBody_legLogo_")]').text
        DF.at[trip+'_'+str(j)] = [From, To,
              trip.split('/')[2],
              boxes[j].find_element_by_xpath('.//span[contains(@class, "LegInfo_routePartialTime_")]').text, # Departure Time
              boxes[j].find_element_by_xpath('.//span[contains(@class, "Duration_duration_")]').text, # Flight Length
              direct_or_stops.split("\n")[0], # Direct ?
              comp, # Airtravel Company
              int(price_currency.split(' ')[0]), # Price
              price_currency.split(' ')[1] # Currency
              ]
    del boxes
    return(DF)

def main_OneWay(Trips):
    """
    Initialize a browser and search results for a list of trips,
    appends results to output DataFrame
    """
    global filename
    DF = pd.DataFrame(columns=columns_OneWay)
    banners = {'cookie':False, 'covid':False, 'price_alert':False}
    b = webdriver.Firefox(executable_path = "./geckodriver",
                          firefox_profile=webdriver.FirefoxProfile() \
                          .set_preference("browser.privatebrowsing.autostart", True))
    for j in range(len(Trips)):
        DF = page_results_OneWay(b, Trips[j], DF, banners)
        if (j+1) % pages_lookup_before_saving == 0:
            save_DF_to_workbook(filename, DF)
            print("Intermediate save of data to workbook")
            DF = pd.DataFrame(columns=columns_OneWay)
    b.close()
    save_DF_to_workbook(filename, DF)
    return(DF)


def page_results_Return(browser, trip, DF, banners):
    """
    For a given browser (Selenium object) and a given trip (string concatening
    Departure, Arrival and Date), appends results of web page to DataFrame
    Note that there are several banners to handle only once
    """
    browser.get(url_body_1 + trip + url_body_2)
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
        # NOTE TO MYSELF : " .// " in the xpath, otherwise whole page is read 
        price_currency = boxes[j].find_element_by_xpath('.//div[starts-with(@class, "Price_mainPriceContainer_")]').text
        price_currency.strip()
        assert len(price_currency.split(' ')) == 2 
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
        DF.at[trip+'_'+str(j)] = [From, To,
              trip.split('/')[2],
              ways[0].find_element_by_xpath('.//span[contains(@class, "LegInfo_routePartialTime_")]').text, # Departure Time
              ways[0].find_element_by_xpath('.//span[contains(@class, "Duration_duration_")]').text, # Flight Length
              direct_or_stops_1.split("\n")[0], # Direct ?
              comp_1, # Airtravel Company
              trip.split('/')[3],
              ways[1].find_element_by_xpath('.//span[contains(@class, "LegInfo_routePartialTime_")]').text, # Departure Time
              ways[1].find_element_by_xpath('.//span[contains(@class, "Duration_duration_")]').text, # Flight Length
              direct_or_stops_2.split("\n")[0], # Direct ?
              comp_2, # Airtravel Company
              int(price_currency.split(' ')[0]), # Price
              price_currency.split(' ')[1] # Currency
              ]
        del ways
    del boxes
    return(DF)


def main_Return(Trips):
    """
    Initialize a browser and search results for a list of trips,
    appends results to output DataFrame
    """
    global filename
    DF = pd.DataFrame(columns=columns_Return)
    banners = {'cookie':False, 'covid':False, 'price_alert':False}
    b = webdriver.Firefox(executable_path = "./geckodriver",
                          firefox_profile=webdriver.FirefoxProfile() \
                          .set_preference("browser.privatebrowsing.autostart", True))
    for j in range(len(Trips)):
        DF = page_results_Return(b, Trips[j], DF, banners)
        if (j+1) % pages_lookup_before_saving == 0:
            save_DF_to_workbook(filename, DF)
            print("Intermediate save of data to workbook")
            DF = pd.DataFrame(columns=columns_Return)
    b.close()
    save_DF_to_workbook(filename, DF)
    return(DF)


def final_workbook(filename):
    """
    Concat all sheets (from each browser parallelisation) in one sheet    
    """
    DF = pd.read_excel(filename, sheet_name=None)            
    sheets = [k for k in DF.keys() if not DF[k].empty]
    DF1 = DF[sheets.pop(0)]
    for sheet in sheets:
        DF1 = pd.concat([DF1, DF[sheet]], axis=0)
    DF1.to_excel(filename, index=False)
    return 1


# =============================================================================
# --- MAIN PROGRAM ---
# =============================================================================


# Our Departure and Arrival Cities / One-Way or Return flights
From = input("Departure City : ")
To = input("Destination City : ")
Return = int( \
         input("Estimated stay in number of days (0 for One-Way flight) : "))


# Trips
Trips, exist = create_trips(From, To, Return, Start, Iterations)


if not exist:
    print("This trip isn't supported by the app")
else:
    # Workbook for results
    filename = "Workbooks/Skyscanner_from_" + From + "_To_" + To + "_" + \
                    ("One-Way.xlsx" if Return==0 else "Return.xlsx")
    # Check if filename exists and has former data saved on 'Sheet1'
    try:
    	dummy = pd.read_excel(filename)
    except:
    	init_workbook(filename, Return)
    # Divide task into N browsers
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
    final_workbook(filename)
###
