# we are building here a Trading Bot application using the tkinter framework.
import pprint
import tkinter as tk
from interface.root_component import Root
import logging
from connectors.binance_futures import BinanceFuturesClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# to show the logs on the console we need to initialize and configure a stream handler
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# to print the logs on a file we need to initialize and configure a file handler
file_handler = logging.FileHandler('info.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def position_label_widgets_using_pack_method(l_w: tk.Label):
    # starting from the top, we can even start from the bottom, left, or right.
    l_w.pack(side=tk.TOP)


def position_label_widgets_using_grid_method(l_w: tk.Label, col, r):
    # starting from the top, we can even start from the bottom, left, or right.
    l_w.grid(column=col, row=r)


def display_each_contract(contracts: dict):
    column = 0
    row = 0
    for contract in contracts:
        label_widget = tk.Label(master=root, text=contract, width=13, borderwidth=1, relief=tk.SOLID)
        position_label_widgets_using_grid_method(label_widget, column, row)
        row = row + 1
        if row % 15 == 0:
            column = column + 1
            row = 0
    return None


if __name__ == '__main__':
    binance_futures_client = BinanceFuturesClient(
        public_api_key='e071685257644f428f0bec65d4d6769b9c40008985be904ca48514ab44a7c29d',
        secret_api_key='78e27651533d2c9bef57b35b56b77c1850e5a2fad3e82e844e1b88f29f634077',
        testnet=True
    )
    # active_contracts = binance_futures_client.get_contracts()
    #
    # # we need to display each contract in separate label widget.
    # display_each_contract(active_contracts)
    #
    # print(binance_futures_client.get_bid_ask_price('BTCUSDT'))
    # pprint.pprint(binance_futures_client.get_historical_candles('BTCUSDT', '1h'))
    # print('****')
    # pprint.pprint(binance_futures_client.get_account_info())

    # the root window (main window of our application)
    root = Root(binance_futures_client)

    # we need to call a blocking function to prevent the program from terminating.
    # the function that we will use will start whats called an event loop. its an infinite loop that waits for action
    # from the user like mouse clicks of keyboard entries.
    root.mainloop()






