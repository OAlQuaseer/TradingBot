# Tkinter is the only framework that's built into the Python standard library.
import tkinter
import pprint
from interface.styling import *
from interface.logging_component import LoggingComponent
from interface.watchlist_component import WatchlistComponent
import time
from connectors.binance_futures import BinanceFuturesClient
import logging
from interface.trades_component import TradesWatchListComponent
from interface.strategy_component import StrategyEditor

logger = logging.getLogger()


class Root(tkinter.Tk):
    def __init__(self, binance_futures_client: BinanceFuturesClient):
        super().__init__()
        self.binance_futures_client = binance_futures_client
        self.title("Trading Bot")
        self.configure(bg=BG_COLOR)

        self._left_frame = tkinter.Frame(self, bg=BG_COLOR)
        self._left_frame.pack(side=tkinter.LEFT)

        self._right_frame = tkinter.Frame(self, bg=BG_COLOR)
        self._right_frame.pack(side=tkinter.LEFT)

        self.logging_frame = LoggingComponent(self._left_frame, bg=BG_COLOR)
        self.logging_frame.pack(side=tkinter.TOP)

        self._watchlist_component_frame = WatchlistComponent(self.binance_futures_client.contracts
                                                             , self._left_frame, bg=BG_COLOR)
        self._watchlist_component_frame.pack(side=tkinter.TOP)

        self._strategy_editor = StrategyEditor(self, binance_futures_client, self._right_frame, bg=BG_COLOR)
        self._strategy_editor.pack(side=tkinter.TOP)

        self._trades_watchlist_component_frame = TradesWatchListComponent(self._right_frame, bg=BG_COLOR)
        self._trades_watchlist_component_frame.pack(side=tkinter.TOP)

        self._update_ui()

    def _update_ui(self):
        # updating the logging component
        for log in self.binance_futures_client.logs_to_display:
            if not log['displayed']:
                self.logging_frame.add_log(log['log'])
                log['displayed'] = True

        # updating the Trades component and the logging component

        for client in [self.binance_futures_client]:
            try:
                for key, strategy in client.strategies.items():
                    for log in strategy.logs:
                        if log['displayed'] is False:
                            self.logging_frame.add_log(log['message'])
                            log['displayed'] = True

                    for trade in strategy.trades:
                        if trade.time not in self._trades_watchlist_component_frame.body_widgets['symbol'].keys():
                            self._trades_watchlist_component_frame.add_trade(trade)
                        else:
                            self._trades_watchlist_component_frame.update_trade(trade)

            except RuntimeError as e:
                logger.error("Error while looping through strategies dictionary: %s", e)


        # updating the watchlist component
        try:
            for key, value in self._watchlist_component_frame.body_widgets['symbol'].items():
                symbol = value.cget('text')
                exchange = self._watchlist_component_frame.body_widgets['exchange'][key].cget('text')

                prices = dict()
                if exchange == 'Binance':
                    if symbol not in self.binance_futures_client.contracts.keys():
                        continue

                    if symbol not in self.binance_futures_client.prices.keys():
                        self.binance_futures_client.get_bid_ask_price(self.binance_futures_client.contracts[symbol])
                        continue
                    prices = self.binance_futures_client.prices[symbol]
                elif exchange == 'Bitmex':
                    continue
                else:
                    continue

                if prices['bid'] is not None:
                    self._watchlist_component_frame.body_widgets['bid_var'][key].set(prices['bid'])
                if prices['ask'] is not None:
                    self._watchlist_component_frame.body_widgets['ask_var'][key].set(prices['ask'])
        except RuntimeError as e:
            logger.error("Error while looping through watchlist dictionary: %s", e)

        self.after(1000, self._update_ui)


