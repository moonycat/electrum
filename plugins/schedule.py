from PyQt4.QtGui import *
from PyQt4.QtCore import *

from electrum.i18n import _, set_language
from electrum.plugins import BasePlugin, hook
from gui.qt.util import HelpButton, EnterButton

import sqlite3

class Plugin(BasePlugin):

    def fullname(self):
        return "Transaction Scheduling"

    def description(self):
        return """Provide function to schedule a transaction"""

    @hook
    def init_qt(self, gui):
        self.gui = gui
        self.win = self.gui.main_window
        self.win.send_button.hide()
        self.win.payto_sig.hide()
        self.win.send_grid.itemAtPosition(6, 2).widget().hide()
        self.add_time_edit()
        self.win.tabs.addTab(self.create_schedule_tab(), _('Schedule'))
        self.win.update_status()

    def close(self):
        self.lable_time.hide()
        self.instant_r.hide()
        self.schedule_r.hide()
        self.time_e.hide()
        self.time_help.hide()
        self.new_send_button.hide()
        self.new_clear_button.hide()
        self.win.send_button.show()
        self.win.payto_sig.show()
        self.win.send_grid.itemAtPosition(6, 2).widget().show()
        self.win.update_status()

    def add_time_edit(self):
        self.lable_time = QLabel(_('Time'))
        self.instant_r = QRadioButton(_('instantly'))
        self.schedule_r = QRadioButton(_('schedule'))
        group = QButtonGroup()
        group.addButton(self.instant_r)
        group.addButton(self.schedule_r) 
        self.instant_r.setChecked(True)
        self.time_e = QDateTimeEdit()
        self.time_e.setMinimumDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.time_help = HelpButton(_('Schedule a transaction.') + '\n\n' + _('Set time for a transaction.'))
        self.new_send_button = EnterButton(_('Send'), self.read_send_tab)
        self.new_clear_button = EnterButton(_('Clear'), self.win.do_clear)
        self.win.send_grid.addWidget(self.lable_time, 6, 0)
        self.win.send_grid.addWidget(self.instant_r, 6, 1)
        self.win.send_grid.addWidget(self.schedule_r, 6, 2)
        self.win.send_grid.addWidget(self.time_e, 6, 3, Qt.AlignLeft)
        self.win.send_grid.addWidget(self.time_help, 6, 3, 1, 2, Qt.AlignHCenter )
        self.win.send_grid.addWidget(self.new_send_button, 7, 1, Qt.AlignLeft)
        self.win.send_grid.addWidget(self.new_clear_button, 7, 2, Qt.AlignLeft)

    def create_schedule_tab(self):
        pass

    def read_send_tab(self):
        r = self.win.read_send_tab()
        if self.schedule_r.isChecked():
            QMessageBox.warning(None, _('Error'), _('Time has past!'), _('OK'))
            return

    def do_schedule(self):
        conn = sqlite3.connect('schedule.db')
        c = conn.cursor()
        conn.close()

