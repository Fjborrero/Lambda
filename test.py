import unittest
from unittest.mock import patch
from lambda_function import fetch_cryptocurrency_data
import json

class TestFetchCryptocurrencyData(unittest.TestCase):

    @patch('lambda_function.mysql.connector.connect')
    @patch('lambda_function.Session.get')
    def test_fetch_cryptocurrency_data(self, mock_get, mock_connect):
        mock_connect.return_value.is_connected.return_value = True
        mock_cursor = mock_connect.return_value.cursor.return_value

        mock_response = {
            "data": {
                "1": {
                    'symbol': 'BTC',
                    "name": "Bitcoin",
                    "quote": {
                        "USD": {
                            "price": 50000,
                            "last_updated": "2024-04-21T12:00:00Z"
                        }
                    }
                },
                "1027": {
                    'symbol': 'ETH',
                    "name": "Ethereum",
                    "quote": {
                        "USD": {
                            "price": 2500,
                            "last_updated": "2024-04-21T12:00:00Z"
                        }
                    }
                }
            }
        }
        mock_get.return_value.text = json.dumps(mock_response)

        result = fetch_cryptocurrency_data()

        # Assert the function returns the fetched data
        self.assertEqual(result, mock_response)

        # Assert the database insertion
        mock_cursor.execute.assert_any_call(
            "INSERT INTO cryptocurrency_data(id_coin, Name, Price, date_price) VALUES (%s, %s, %s, %s)",
            ('BTC','Bitcoin', 50000, '2024-04-21T12:00:00Z')
        )
        mock_cursor.execute.assert_any_call(
            "INSERT INTO cryptocurrency_data(id_coin, Name, Price, date_price) VALUES (%s, %s, %s, %s)",
            ('ETH','Ethereum', 2500, '2024-04-21T12:00:00Z')
        )

if __name__ == '__main__':
    unittest.main()