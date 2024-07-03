from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import os
import mysql.connector


def connect_to_database():
    try:
        credentials = mysql.connector.connect(
            host=os.environ["DB_HOST"], 
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"]
        )
        if credentials.is_connected():
            print('Conectado')
        return credentials
    except mysql.connector.Error as ex:
        print(f"Error: {ex}")
        return None

def fetch_api_data():
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    parameters = {
        'slug': 'bitcoin,ethereum', 
        'convert': 'USD'
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': '017fd881-c7fc-410c-8f0e-a6ff0d914d8b',
    }
    
    session = Session()
    session.headers.update(headers)
    
    try: 
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        return data
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
        return None

def insert_data_to_database(credentials, data):
    cursor = credentials.cursor()
    bitcoin_data = data['data']['1']
    ethereum_data = data['data']['1027']
    
    try:
        cursor.execute("INSERT INTO cryptocurrency_data(id_coin, Name, Price, date_price) VALUES (%s, %s, %s, %s)",
                      (bitcoin_data['symbol'],bitcoin_data['name'], bitcoin_data['quote']['USD']['price'], bitcoin_data['quote']['USD']['last_updated']))
        
        cursor.execute("INSERT INTO cryptocurrency_data(id_coin, Name, Price, date_price) VALUES (%s, %s, %s, %s)",
                      (ethereum_data['symbol'],ethereum_data['name'], ethereum_data['quote']['USD']['price'], ethereum_data['quote']['USD']['last_updated']))
        
        credentials.commit()
    except mysql.connector.Error as ex:
        print(f"Error: {ex}")
    finally:
        cursor.close()

def fetch_cryptocurrency_data():
    credentials = connect_to_database()
    if credentials:
        data = fetch_api_data()
        if data:
            insert_data_to_database(credentials, data)
        credentials.close()

fetch_cryptocurrency_data()