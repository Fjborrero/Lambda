
# Lambda CoinMarketCap

Una funcion que extrae los valores del Bitcoin y Ethereum para insertarlo en una base de datos. Esta función tiene la intención de ser una función lambda de AWS.


## Dependencias

- Request
- Mysqlconnector

## Lambda

Lambda ejecuta el código en una infraestructura de computación de alta disponibilidad y realiza todas las tareas de administración de los recursos de computación, incluido el mantenimiento del servidor y del sistema operativo, el aprovisionamiento de capacidad y el escalado automático, así como las funciones de registro. 


# Conexión Lambda RDS
Para la conexion de la Lambda con la RDS se deben conectar en la misma VPC(subredes privadas y públicas)para que no exista ningún problema de conexión.

Finalmente para que lambda tenga una conexion a internet configure un NAT gateway para que tenga el acceso a internet para que se pueda consumir la Api.

# Creacion de la base de datos 

Para la creacion de la base de datos se utilizo la capa gratuita que brinda AWS con Mysql.

Se crea una tabla para almacenar el id de la moneda, nombre, precio y la fecha de carga.
```sql
CREATE TABLE cryptocurrency_data(
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_coin VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    date_price TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

```
## Funcion Lambda

Inicialmente se importan las librerias que se mencionan anteriormente adicionalmente agregando json y OS con el objetivo de manejar la respuesta json de la peticion a la api y las variables de entorno respectivamente.

```python
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import os
import mysql.connector

```

Se crea una funcion fetch_api_data para poder conectarse a la API 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest' la cual tiene informacion actualizada de las las criptomonedas seleccionadas, se pueden filtrar por los parametros id, slug y symbol pero para este caso se usara  slug para obtener las criptomonedas ethereum y bitcoin. 

```python
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

```

Se crea una funcion connect_to_database para poder conectarse a la base de datos para luego almacenarlos.

```python

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
```

Al final se crea una ultima funcion que lo que hace es almacenar los datos que se recive de la funcion fetch_api_data para almacenarlos en la base de datos yeniendo encuenta de que el objeto recibido de la api por lo que se obtiene la informacion como el id de la moneda, el nombre, precio y la fecha.

```python

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
```


Por ultimo se define la funcion lambda_handler la cual permite que se haga todo el proceso anterior.


```python
def lambda_handler(event, execution)::
    credentials = connect_to_database()
    if credentials:
        data = fetch_api_data()
        if data:
            insert_data_to_database(credentials, data)
        credentials.close()
```
## EventBridge

Amazon EventBridge es el servicio escogido para la toma de los datos en un periodo de tiempo de cada 6 horas. 