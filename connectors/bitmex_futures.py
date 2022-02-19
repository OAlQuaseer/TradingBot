import logging
import requests


logger = logging.getLogger()


def get_active_contracts():
    logger.info('get the BitMEX active contracts')
    response = requests.get('https://www.bitmex.com/api/v1/instrument/active')
    symbols_list = response.json()
    return [symbol['symbol'] for symbol in symbols_list]




