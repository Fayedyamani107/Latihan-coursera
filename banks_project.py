import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime


URL = 'https://web.archive.org/web/20230908091635/https://en.wikipedia.org/wiki/List_of_largest_banks'
TABLE_ATTRIBS = ['Name', 'MC_USD_Billion']
CSV_PATH = './Largest_banks_data.csv'
DB_NAME = 'Banks.db'
TABLE_NAME = 'Largest_banks'
LOG_FILE = 'code_log.txt'
EXCHANGE_RATE_CSV = './exchange_rate.csv'



def log_progress(message):
    """Mencatat pesan log dengan timestamp ke file code_log.txt"""
    timestamp_format = '%Y-%h-%d-%H:%M:%S'
    now = datetime.now()
    timestamp = now.strftime(timestamp_format)
    with open(LOG_FILE, 'a') as f:
        f.write(timestamp + ' : ' + message + '\n')



def extract(url, table_attribs):
    """Mengekstrak tabel bank terbesar dari halaman Wikipedia ke DataFrame"""
    page = requests.get(url).text
    data = BeautifulSoup(page, 'html.parser')
    df = pd.DataFrame(columns=table_attribs)

    tables = data.find_all('tbody')
    rows = tables[0].find_all('tr')

    for row in rows:
        col = row.find_all('td')
        if len(col) != 0:
            if col[1].find('a') is not None:
                data_dict = {
                    'Name': col[1].find_all('a')[1].contents[0],
                    'MC_USD_Billion': float(col[2].contents[0][:-1])
                }
                df1 = pd.DataFrame(data_dict, index=[0])
                df = pd.concat([df, df1], ignore_index=True)

    return df



def transform(df, csv_path):
    """Menambahkan kolom Market Cap dalam GBP, EUR, dan INR berdasarkan nilai tukar"""
    exchange_rate = pd.read_csv(csv_path).set_index('Currency').to_dict()['Rate']

    df['MC_GBP_Billion'] = [np.round(x * exchange_rate['GBP'], 2) for x in df['MC_USD_Billion']]
    df['MC_EUR_Billion'] = [np.round(x * exchange_rate['EUR'], 2) for x in df['MC_USD_Billion']]
    df['MC_INR_Billion'] = [np.round(x * exchange_rate['INR'], 2) for x in df['MC_USD_Billion']]

    return df



def load_to_csv(df, output_path):
    """Menyimpan DataFrame ke file CSV di jalur yang ditentukan"""
    df.to_csv(output_path, index=False)



def load_to_db(df, sql_connection, table_name):
    """Menyimpan DataFrame ke dalam tabel basis data SQLite"""
    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)



def run_query(query_statement, sql_connection):
    """Mengeksekusi kueri SQL pada basis data, mencetak hasilnya, dan mencatat menggunakan log_progress()"""
    print(query_statement)
    query_output = pd.read_sql(query_statement, sql_connection)
    print(query_output)



if __name__ == '__main__':

    
    log_progress('Preliminaries complete. Initiating ETL process')

    
    df = extract(URL, TABLE_ATTRIBS)
    print('Data hasil extract:')
    print(df)
    log_progress('Data extraction complete. Initiating Transformation process')

    
    df = transform(df, EXCHANGE_RATE_CSV)
    print('\nData setelah transform:')
    print(df)
    log_progress('Data transformation complete. Initiating Loading process')

    
    load_to_csv(df, CSV_PATH)
    log_progress('Data saved to CSV file')

    
    sql_connection = sqlite3.connect(DB_NAME)
    log_progress('SQL Connection initiated')

    load_to_db(df, sql_connection, TABLE_NAME)
    log_progress('Data loaded to Database as a table, Executing queries')

    
    run_query(f'SELECT * FROM {TABLE_NAME}', sql_connection)
    log_progress('Process Complete')

    
    run_query(f'SELECT AVG(MC_GBP_Billion) FROM {TABLE_NAME}', sql_connection)
    log_progress('Process Complete')

    
    run_query(f'SELECT Name FROM {TABLE_NAME} LIMIT 5', sql_connection)
    log_progress('Process Complete')

    sql_connection.close()
    log_progress('Server Connection closed')
