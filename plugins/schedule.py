from PyQt4.QtGui import *
from PyQt4.QtCore import *

from electrum.plugins import BasePlugin, hook

class Plugin(BasePlugin):

    def fullname(self):
        return "Transaction Scheduling"

    def description(self):
        return """Provide function to schedule a transaction"""

    @hook
    def init_qt(self, gui):
        self.gui = gui
        self.win = self.gui.main_window
        self.add_time_edit()

    def add_time_edit(self):
        #self.time_e = QDateTimeEdit().setDateTime(QDateTime.currentDateTime())
        self.time_e = QDateTimeEdit()
        self.win.send_grid.addWidget(QLabel('Time'), 5, 0)
        self.win.send_grid.addWidget(self.time_e, 5, 1, Qt.AlignHCenter)

