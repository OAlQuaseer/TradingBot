import tkinter as tk
import typing

from interface.styling import *

from connectors.binance_futures import BinanceFuturesClient

from strategies import TechnicalStrategy, BreakoutStrategy


class StrategyEditor(tk.Frame):
    def __init__(self, root, binance_futures_client: BinanceFuturesClient, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.root = root

        self._exchanges = {"Binance": binance_futures_client}

        self._all_contracts_in_dropdown_menu = []
        self._construct_values_contract_dropdown_menu()

        self._all_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h"]

        self._commands_frame = tk.Frame(self, bg=BG_COLOR)
        self._commands_frame.pack(side=tk.TOP)

        self._table_frame = tk.Frame(self, bg=BG_COLOR)
        self._table_frame.pack(side=tk.TOP)

        self._add_button = tk.Button(self._commands_frame, text="Add strategy", font=GLOBAL_FONT,
                                     command=self._add_strategy_row, bg=BG_COLOR_2, fg=FG_COLOR)
        self._add_button.pack(side=tk.TOP)

        self.body_widgets = dict()

        self._headers = ["Strategy", "Contract", "Timeframe", "Balance %", "TP %", "SL %"]

        self._additional_parameters = dict()
        self._extra_input = dict()

        self._base_params = [
            {"code_name": "strategy_type", "widget": tk.OptionMenu, "data_type": str,
             "values": ["Technical", "Breakout"], "width": 10},
            {"code_name": "contract", "widget": tk.OptionMenu, "data_type": str, "values": self._all_contracts_in_dropdown_menu,
             "width": 15},
            {"code_name": "timeframe", "widget": tk.OptionMenu, "data_type": str, "values": self._all_timeframes,
             "width": 7},
            {"code_name": "balance_pct", "widget": tk.Entry, "data_type": float, "width": 7},
            {"code_name": "take_profit", "widget": tk.Entry, "data_type": float, "width": 7},
            {"code_name": "stop_loss", "widget": tk.Entry, "data_type": float, "width": 7},
            {"code_name": "parameters", "widget": tk.Button, "data_type": float, "text": "Parameters",
             "bg": BG_COLOR_2, "command": self._show_popup},
            {"code_name": "activation", "widget": tk.Button, "data_type": float, "text": "OFF",
             "bg": "darkred", "command": self._switch_strategy},
            {"code_name": "delete", "widget": tk.Button, "data_type": float, "text": "X",
             "bg": "darkred", "command": self._delete_row},

        ]

        # extra parameters needed for each strategy.
        self._extra_params = {
            "Technical": [
                {"code_name": "ema_fast", "name": "MACD Fast Length", "widget": tk.Entry, "data_type": int},
                {"code_name": "ema_slow", "name": "MACD Slow Length", "widget": tk.Entry, "data_type": int},
                {"code_name": "ema_signal", "name": "MACD Signal Length", "widget": tk.Entry, "data_type": int},
            ],
            "Breakout": [
                {"code_name": "min_volume", "name": "Minimum Volume", "widget": tk.Entry, "data_type": float},
            ]
        }

        self._build_table_headers()

        # initialize the body widgets dict object with the initial data structure
        self._initialize_body_widgets()

        self._initialize_table_body_index()

    def _construct_values_contract_dropdown_menu(self):
        for exchange, client in self._exchanges.items():
            for symbol, contract in client.contracts.items():
                self._all_contracts_in_dropdown_menu.append(symbol + "_" + exchange.capitalize())

    def _initialize_table_body_index(self):
        self._body_index = 1

    def _initialize_body_widgets(self):
        for param in self._base_params:
            self.body_widgets[param['code_name']] = dict()
            if param['code_name'] in ["strategy_type", "contract", "timeframe"]:
                self.body_widgets[param['code_name'] + "_var"] = dict()

    def _build_table_headers(self):
        for index, header in enumerate(self._headers):
            # index presents the table column here
            tk.Label(self._table_frame, text=header, bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT).grid(row=0, column=index)

    def _add_strategy_row(self):

        body_index = self._body_index

        for col, base_param in enumerate(self._base_params):
            code_name = base_param['code_name']
            if base_param['widget'] == tk.OptionMenu:
                self.body_widgets[code_name + "_var"][body_index] = tk.StringVar()
                # set the default value of the dropdown menu to the first element of options.
                self.body_widgets[code_name + "_var"][body_index].set(base_param['values'][0])
                self.body_widgets[code_name][body_index] = tk.OptionMenu(self._table_frame,
                                                                      self.body_widgets[code_name + "_var"][body_index],
                                                                      *base_param['values'])
                self.body_widgets[code_name][body_index].config(width=base_param['width'])

            elif base_param['widget'] == tk.Entry:
                self.body_widgets[code_name][body_index] = tk.Entry(self._table_frame, justify=tk.CENTER)
            elif base_param['widget'] == tk.Button:
                self.body_widgets[code_name][body_index] = tk.Button(self._table_frame, text=base_param['text'],
                                        bg=base_param['bg'], fg=FG_COLOR,
                                        command=lambda frozen_command=base_param['command']: frozen_command(body_index))
            else:
                continue

            self.body_widgets[code_name][body_index].grid(row=body_index, column=col)

        self._additional_parameters[body_index] = dict()

        for strategy, params in self._extra_params.items():
            for param in params:
                self._additional_parameters[body_index][param['code_name']] = None

        self._body_index += 1

    def _delete_row(self, b_index: int):

        for element in self._base_params:
            self.body_widgets[element['code_name']][b_index].grid_forget()

            del self.body_widgets[element['code_name']][b_index]

    def _show_popup(self, b_index: int):

        x = self.body_widgets["parameters"][b_index].winfo_rootx()
        y = self.body_widgets["parameters"][b_index].winfo_rooty()

        self._popup_window = tk.Toplevel(self)
        self._popup_window.wm_title("Parameters")

        self._popup_window.config(bg=BG_COLOR)
        self._popup_window.attributes("-topmost", "true")
        self._popup_window.grab_set()

        self._popup_window.geometry(f"+{x - 80}+{y + 30}")

        strategy_selected = self.body_widgets['strategy_type_var'][b_index].get()

        row_nb = 0

        for param in self._extra_params[strategy_selected]:
            code_name = param['code_name']

            temp_label = tk.Label(self._popup_window, bg=BG_COLOR, fg=FG_COLOR, text=param['name'], font=BOLD_FONT)
            temp_label.grid(row=row_nb, column=0)

            if param['widget'] == tk.Entry:
                self._extra_input[code_name] = tk.Entry(self._popup_window, bg=BG_COLOR_2, justify=tk.CENTER, fg=FG_COLOR,
                                      insertbackground=FG_COLOR)
                if self._additional_parameters[b_index][code_name] is not None:
                    self._extra_input[code_name].insert(tk.END, str(self._additional_parameters[b_index][code_name]))
            else:
                continue

            self._extra_input[code_name].grid(row=row_nb, column=1)

            row_nb += 1

        # Validation Button

        validation_button = tk.Button(self._popup_window, text="Validate", bg=BG_COLOR_2, fg=FG_COLOR,
                                      command=lambda: self._validate_parameters(b_index))
        validation_button.grid(row=row_nb, column=0, columnspan=2)

    def _validate_parameters(self, b_index: int):

        strat_selected = self.body_widgets['strategy_type_var'][b_index].get()

        for param in self._extra_params[strat_selected]:
            code_name = param['code_name']

            if self._extra_input[code_name].get() == "":
                self._additional_parameters[b_index][code_name] = None
            else:
                self._additional_parameters[b_index][code_name] = param['data_type'](self._extra_input[code_name].get())

        self._popup_window.destroy()

    def _switch_strategy(self, b_index: int):

        # balance_pct, take_profit, stop_loss -> its mandatory to fill out those fields.
        for param in ["balance_pct", "take_profit", "stop_loss"]:
            if self.body_widgets[param][b_index].get() == "":
                self.root.logging_frame.add_log(f"Missing {param} parameter")
                return

        strategy_selected = self.body_widgets['strategy_type_var'][b_index].get()

        for param in self._extra_params[strategy_selected]:
            if self._additional_parameters[b_index][param['code_name']] is None:
                self.root.logging_frame.add_log(f"Missing {param['code_name']} parameter")
                return

        symbol = self.body_widgets['contract_var'][b_index].get().split("_")[0]
        time_frame = self.body_widgets['timeframe_var'][b_index].get()
        exchange = self.body_widgets['contract_var'][b_index].get().split("_")[1]

        balance_pct = float(self.body_widgets['balance_pct'][b_index].get())
        take_profit = float(self.body_widgets['take_profit'][b_index].get())
        stop_loss = float(self.body_widgets['stop_loss'][b_index].get())
        contract = self._exchanges[exchange].contracts[symbol]


        if self.body_widgets['activation'][b_index].cget("text") == "OFF":

            if strategy_selected == 'Technical':
                other_params = {
                    'ema_fast': self._additional_parameters[b_index]['ema_fast'],
                    'ema_slow': self._additional_parameters[b_index]['ema_slow'],
                    'ema_signal': self._additional_parameters[b_index]['ema_signal'],
                }
                new_strategy = TechnicalStrategy(self._exchanges[exchange], contract, exchange, time_frame, balance_pct,
                                                 take_profit, stop_loss, other_params)
            elif strategy_selected == 'Breakout':
                other_params = {
                    'min_volume': self._additional_parameters[b_index]['min_volume']
                }
                new_strategy = BreakoutStrategy(self._exchanges[exchange], contract, exchange, time_frame, balance_pct,
                                                take_profit, stop_loss, other_params)
            else:
                return

            new_strategy.candles = self._exchanges[exchange].get_historical_candles(contract, time_frame)

            if len(new_strategy.candles) == 0:
                self.root.logging_frame.add_log(f'there was an error while fetching the candles data for this contract '
                                                f'{contract.symbol} with this timeframe {time_frame}')
                return

            if exchange == 'Binance':
                self._exchanges[exchange].subscribe_to_stream(f'{contract.symbol.lower()}@aggTrade')

            self._exchanges[exchange].strategies[b_index] = new_strategy

            for param in self._base_params:
                code_name = param['code_name']
                if code_name != "activation" and "_var" not in code_name:
                    self.body_widgets[code_name][b_index].config(state=tk.DISABLED)

            self.body_widgets['activation'][b_index].config(bg="darkgreen", text="ON")
            self.root.logging_frame.add_log(f"{strategy_selected} strategy on {symbol} / {time_frame} started")

        else:
            del self._exchanges[exchange].strategies[b_index]

            for param in self._base_params:
                code_name = param['code_name']

                if code_name != "activation" and "_var" not in code_name:
                    self.body_widgets[code_name][b_index].config(state=tk.NORMAL)

            self.body_widgets['activation'][b_index].config(bg="darkred", text="OFF")
            self.root.logging_frame.add_log(f"{strategy_selected} strategy on {symbol} / {time_frame} stopped")

