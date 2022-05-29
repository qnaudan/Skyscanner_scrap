import pandas as pd
import multiprocessing as mp

from src.config import COLUMNS_ONEWAY, COLUMNS_RETURN, get_args, N_BROWSERS, N_PROCESSES, SAVING_RATE
from src.setup_webscrap import setup_webscrap
from src.workbook import init_workbook, final_workbook, save_df_to_workbook
from src.browser import format_page_results, init_browser


def main_oneway():
    """ Initialize a browser and search results for a list of trips,
    appends results to output DataFrame """
    global filename
    df = pd.DataFrame(columns=COLUMNS_ONEWAY)
    banners = {'cookie': False, 'covid': False, 'price_alert': False}
    browser = init_browser()
    for j in range(len(trips)):
        df = format_page_results(browser, trips[j], df, banners, is_one_way=True)
        if (j+1) % SAVING_RATE == 0:
            save_df_to_workbook(filename, df)
            print("Intermediate save of data to workbook")
            df = pd.DataFrame(columns=COLUMNS_ONEWAY)
    browser.close()
    save_df_to_workbook(filename, df)
    return df


def main_return(trips):
    """ Initialize a browser and search results for a list of trips,
    appends results to output DataFrame """
    global filename
    df = pd.DataFrame(columns=COLUMNS_RETURN)
    banners = {'cookie': False, 'covid': False, 'price_alert': False}
    browser = init_browser()
    for j in range(len(trips)):
        df = format_page_results(browser, trips[j], df, banners, is_one_way=False)
        if (j+1) % SAVING_RATE == 0:
            save_df_to_workbook(filename, df)
            print("Intermediate save of data to workbook")
            df = pd.DataFrame(columns=COLUMNS_RETURN)
    browser.close()
    save_df_to_workbook(filename, df)
    return df


if __name__ == '__main__':
    args = get_args()
    print(args)
    trips = setup_webscrap(args.d, args.a, args.s, int(args.days))
    if trips:
        # Workbook for results
        filename = (
            "./workbooks/Skyscanner_from_" + args.d + "_To_" + args.a + "_"
            + ("One-Way.xlsx" if args.days==0 else "Return.xlsx")
        )
        # Check if filename exists and has former data saved on 'Sheet1'
        try:
            _ = pd.read_excel(filename)
        except:
            init_workbook(filename, args.days)
        # Divide task into N browser:
        inputs = []
        for i in range(N_BROWSERS):
            inputs.append(trips[i * (len(trips) // N_BROWSERS):(i + 1) * (len(trips) // N_BROWSERS)])

        with mp.Pool(N_PROCESSES) as p:
            if args.days == 0:
                df_list = p.map(main_oneway, inputs)
            else:
                df_list = p.map(main_return, inputs)
        final_workbook(filename)
