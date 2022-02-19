import tkinter
from interface.styling import *

from datetime import datetime


class LoggingComponent(tkinter.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._logging_text = tkinter.Text(self, height=20, width=60, state=tkinter.DISABLED, bg=BG_COLOR, fg=FG_COLOR_2
                                          , font=GLOBAL_FONT)
        self._logging_text.pack(side=tkinter.TOP)

    def add_log(self, message: str):
        self._logging_text.configure(state=tkinter.NORMAL)
        self._logging_text.insert("1.0", datetime.utcnow().strftime("%a %H:%M:%S :: ")+ message + "\n")
        self._logging_text.configure(state=tkinter.DISABLED)
