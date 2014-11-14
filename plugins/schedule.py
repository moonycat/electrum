from PyQt4.QtGui import *
from PyQt4.QtCore import *

from electrum.plugins import BasePlugin, hook
from gui.qt.util import HelpButton, EnterButton

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
        self.win.update_status()

    def close(self):
        self.lable_time.hide()
        self.time_e.hide()
        self.time_help.hide()
        self.new_send_button.hide()
        self.win.update_status()

    def add_time_edit(self):
        self.lable_time = QLabel('Time')
        self.time_e = QDateTimeEdit()
        self.time_e.setMinimumDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.time_help = HelpButton('Schedule a transaction.' + '\n\n' + 'Set time for a transaction.')
        #self.new_send_button = EnterButton('Send', self.do_schedule)
        self.win.send_grid.addWidget(self.lable_time, 6, 0)
        self.win.send_grid.addWidget(self.time_e, 6, 1, 1, 2)
        self.win.send_grid.addWidget(self.time_help, 6, 3)
        #self.win.send_grid.addWidget(self.new_send_button, 7, 1)

    def do_schedule(self):
        pass

