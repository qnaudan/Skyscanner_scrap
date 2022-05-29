import pandas as pd
from openpyxl import load_workbook

from src.config import COLUMNS_ONEWAY, COLUMNS_RETURN


def init_workbook(filename, stay_in_days = 0):
    if stay_in_days:
        df = pd.DataFrame(columns=COLUMNS_RETURN)
    else:
        df = pd.DataFrame(columns=COLUMNS_ONEWAY)
    df.to_excel(filename, index=False)
    return 1


def save_df_to_workbook(filename, df):
    book = load_workbook(filename) 
    writer = pd.ExcelWriter(filename, engine='openpyxl')
    writer.book=book  # Save former sheets
    df.to_excel(writer, sheet_name='Sheet1', index=False)
    writer.save()
    return 1


def final_workbook(filename):
    """
    Concat all sheets (from each browser parallelisation) in one sheet    
    """
    df = pd.read_excel(filename, sheet_name=None)            
    sheets = [k for k in df.keys() if not df[k].empty]
    df_final = df[sheets.pop(0)]
    for sheet in sheets:
        df_final = pd.concat([df_final, df[sheet]], axis=0)
    df_final.to_csv(filename.replace('.xslx', '.csv'), index=False)
    return 1
