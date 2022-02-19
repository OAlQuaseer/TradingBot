import tkinter
from interface.styling import *
import logging
import typing
from models import Contract

logger = logging.getLogger()


class WatchlistComponent(tkinter.Frame):
    def __init__(self, binance_contracts: typing.Dict[str, Contract], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.binance_symbols = list(binance_contracts.keys())

        # Upper frame structure #######start######
        self.upper_frame = tkinter.Frame(self, bg=BG_COLOR)
        self.upper_frame.pack(side=tkinter.TOP)

        self.binance_label = tkinter.Label(self.upper_frame, text='Binance', bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT)
        self.binance_label.grid(row=0, column=0)

        self.binance_input_box = tkinter.Entry(self.upper_frame, fg=FG_COLOR, justify=tkinter.CENTER,
                                               insertbackground=FG_COLOR, bg=BG_COLOR_2)
        self.binance_input_box.grid(row=1, column=0)
        self.binance_input_box.bind('<Return>', self._on_binance_entry)

        self.bitmex_label = tkinter.Label(self.upper_frame, text='Bitmex', bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT)
        self.bitmex_label.grid(row=0, column=1)

        self.bitmex_input_box = tkinter.Entry(self.upper_frame, fg=FG_COLOR, justify=tkinter.CENTER,
                                              insertbackground=FG_COLOR, bg=BG_COLOR_2)
        self.bitmex_input_box.grid(row=1, column=1)
        self.bitmex_input_box.bind('<Return>', self._on_bitmex_entry)

        # Upper frame structure #######end######

        # Lower frame structure #######start######
        self.lower_frame = tkinter.Frame(self, bg=BG_COLOR)
        self.lower_frame.pack(side=tkinter.TOP)

        self._headers = ['symbol', 'exchange', 'ask', 'bid', 'remove']
        for index, header in enumerate(self._headers):
            tkinter.Label(self.lower_frame, text=header, bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT)\
                .grid(row=0, column=index)

        self.body_widgets = dict()
        for header in self._headers:
            self.body_widgets[header] = dict()
            if header in ['ask', 'bid']:
                self.body_widgets[header + '_var'] = dict()
        self.body_widgets_index = 1  # starting index as we already used index 0 in structuring the headers
        # Lower frame structure #######end######

    def _on_binance_entry(self, event):
        symbol = event.widget.get()
        if symbol in self.binance_symbols:
            self._add_symbol_to_watchlist_table(symbol, 'Binance')
            event.widget.delete(0, tkinter.END)

    def _on_bitmex_entry(self, event):
        return

    def _add_symbol_to_watchlist_table(self, symbol: str, exchange: str):
        logger.info(self._add_symbol_to_watchlist_table.__name__ + ' method called')
        logger.debug('parameters: %s %s', symbol, exchange)
        body_widgets_index = self.body_widgets_index
        self.body_widgets['symbol'][body_widgets_index] = tkinter.Label(self.lower_frame, text=symbol, bg=BG_COLOR,
                                                                             fg=FG_COLOR,font=GLOBAL_FONT)
        self.body_widgets['symbol'][body_widgets_index].grid(row=body_widgets_index, column=0)

        self.body_widgets['exchange'][body_widgets_index] = tkinter.Label(self.lower_frame, text=exchange, bg=BG_COLOR,
                                                                             fg=FG_COLOR, font=GLOBAL_FONT)
        self.body_widgets['exchange'][body_widgets_index].grid(row=body_widgets_index, column=1)

        self.body_widgets['ask_var'][body_widgets_index] = tkinter.StringVar()
        self.body_widgets['ask'][body_widgets_index] = tkinter.Label(self.lower_frame,
                                                                          textvariable=self.body_widgets['ask_var'][body_widgets_index]
                                                                          , bg=BG_COLOR, fg=FG_COLOR, font=GLOBAL_FONT)
        self.body_widgets['ask'][body_widgets_index].grid(row=body_widgets_index, column=2)

        self.body_widgets['bid_var'][body_widgets_index] = tkinter.StringVar()
        self.body_widgets['bid'][body_widgets_index] = tkinter.Label(self.lower_frame,
                                                                          textvariable=self.body_widgets['bid_var'][body_widgets_index]
                                                                          , bg=BG_COLOR, fg=FG_COLOR, font=GLOBAL_FONT)
        self.body_widgets['bid'][body_widgets_index].grid(row=body_widgets_index, column=3)

        self.body_widgets['remove'][body_widgets_index] = tkinter.Button(self.lower_frame, text='X', bg='darkred',
                                                                         fg=FG_COLOR, font=GLOBAL_FONT,
                                                                         command=lambda: self._add_symbol_from_watchlist_table(body_widgets_index))

        self.body_widgets['remove'][body_widgets_index].grid(row=body_widgets_index, column=4)

        self.body_widgets_index = body_widgets_index + 1

    def _add_symbol_from_watchlist_table(self, row_index: int):
        for header in self._headers:
            self.body_widgets[header][row_index].grid_forget()
            del self.body_widgets[header][row_index]

