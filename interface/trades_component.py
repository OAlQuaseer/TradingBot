import logging
import tkinter
from interface.styling import *
import logging


logger = logging.getLogger()


class TradesWatchListComponent(tkinter.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Trades watch list frame #####start###
        self._trades_watchlist_table_frame = tkinter.Frame(self, bg=BG_COLOR)
        self._trades_watchlist_table_frame.pack(side=tkinter.TOP)

        self._headers = ['time', 'symbol', 'exchange', 'strategy', 'side', 'quantity', 'status', 'pnl']
        for index, header in enumerate(self._headers):
            tkinter.Label(self._trades_watchlist_table_frame, text=header, bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT) \
                .grid(row=0, column=index)

        self.body_widgets = dict()
        for header in self._headers:
            self.body_widgets[header] = dict()
            if header in ['status', 'pnl']:
                self.body_widgets[header + '_var'] = dict()
        self.body_widgets_index = 1
        # Trades watch list frame #####end###

    def add_trade(self, data: dict):
        logger.info(self.add_trade.__name__ + ' method called')
        body_widgets_index = self.body_widgets_index
        time_index = data['time']

        self.body_widgets['time'][time_index] = tkinter.Label(self._trades_watchlist_table_frame, text=data['time'],
                                                              bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT)
        self.body_widgets['time'][time_index].grid(row=body_widgets_index, column=0)

        self.body_widgets['symbol'][time_index] = tkinter.Label(self._trades_watchlist_table_frame, text=data['symbol'],
                                                              bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT)
        self.body_widgets['symbol'][time_index].grid(row=body_widgets_index, column=1)

        self.body_widgets['exchange'][time_index] = tkinter.Label(self._trades_watchlist_table_frame, text=data['exchange'],
                                                                bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT)
        self.body_widgets['exchange'][time_index].grid(row=body_widgets_index, column=2)

        self.body_widgets['strategy'][time_index] = tkinter.Label(self._trades_watchlist_table_frame,
                                                                  text=data['strategy'],
                                                                  bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT)
        self.body_widgets['strategy'][time_index].grid(row=body_widgets_index, column=3)

        self.body_widgets['side'][time_index] = tkinter.Label(self._trades_watchlist_table_frame,
                                                                  text=data['side'],
                                                                  bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT)
        self.body_widgets['side'][time_index].grid(row=body_widgets_index, column=4)

        self.body_widgets['quantity'][time_index] = tkinter.Label(self._trades_watchlist_table_frame,
                                                              text=data['quantity'],
                                                              bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT)
        self.body_widgets['quantity'][time_index].grid(row=body_widgets_index, column=5)

        self.body_widgets['status_var'][time_index] = tkinter.StringVar()
        self.body_widgets['status'][time_index] = tkinter.Label(self._trades_watchlist_table_frame,
                                                                  text=data['status'],
                                                                textvariable=self.body_widgets['status_var'][time_index],
                                                                  bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT)
        self.body_widgets['status'][time_index].grid(row=body_widgets_index, column=6)

        self.body_widgets['pnl_var'][time_index] = tkinter.StringVar()
        self.body_widgets['pnl'][time_index] = tkinter.Label(self._trades_watchlist_table_frame,
                                                                text=data['pnl'],
                                                             textvariable=self.body_widgets['pnl_var'][time_index],
                                                                bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT)
        self.body_widgets['pnl'][time_index].grid(row=body_widgets_index, column=7)
        return
