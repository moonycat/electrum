from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import QtSql

from electrum.i18n import _, set_language
from electrum import Transaction
from electrum.plugins import BasePlugin, hook
from gui.qt.util import HelpButton, EnterButton

import sqlite3
import threading, time
import sys, traceback

class Plugin(BasePlugin):

    def fullname(self):
        return "Transaction Scheduling sqlite"

    def description(self):
        return """Provide function to schedule a transaction"""

    @hook
    def load_wallet(self, wallet):
        self.wallet = wallet

    @hook
    def init_qt(self, gui):
        self.gui = gui
        self.win = self.gui.main_window
        self.win.send_button.hide()
        self.win.payto_sig.hide()
        self.win.send_grid.itemAtPosition(6, 2).widget().hide()
        self.add_time_edit()
        self.add_schedule_table()
        self.win.update_status()
        threads = []
        t = threading.Thread(target=self.worker)
        threads.append(t)
        t.start()

    def close(self):
        self.lable_time.hide()
        self.instant_r.hide()
        self.schedule_r.hide()
        self.time_e.hide()
        self.time_help.hide()
        self.new_send_button.hide()
        self.new_clear_button.hide()
        self.label_request.hide()
        self.view.hide()
        self.win.send_button.show()
        self.win.payto_sig.show()
        self.win.send_grid.itemAtPosition(6, 2).widget().show()
        self.win.update_status()

    def add_time_edit(self):
        self.lable_time = QLabel(_('Time'))
        self.group = QButtonGroup()
        self.instant_r = QRadioButton(_('instant'))
        self.group.addButton(self.instant_r)
        self.schedule_r = QRadioButton(_('schedule'))
        self.group.addButton(self.schedule_r) 
        self.instant_r.setChecked(True)
        self.time_e = QDateTimeEdit()
        self.time_e.setMinimumDateTime(QDateTime.currentDateTime().addSecs(60))
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

    def add_schedule_table(self):
        self.win.send_grid.setRowStretch(8, 1)
        self.label_request = QLabel(_('Saved Schedule'))
        self.db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName("/tmp/schedule.db")
        self.db.open()
        self.model = QtSql.QSqlTableModel(self.win.send_grid, self.db)
        self.initialize_model(self.model)
        self.view = self.create_view(self.model)
        self.db.close()
        QtSql.QSqlDatabase.removeDatabase(self.db.connectionName())
        self.win.send_grid.addWidget(self.label_request, 8, 0)
        self.win.send_grid.addWidget(self.view, 9, 0, 1, 6)

    def read_send_tab(self):
        if self.instant_r.isChecked():
            #self.win.do_send()
            return
        elif self.schedule_r.isChecked():
            self.do_schedule()
        else:
            QMessageBox.warning(None, _('Error'), _("Please select either 'instant' or 'schedule'"), _('OK'))
            return

    def do_schedule(self):
        r = self.win.read_send_tab()
        if not r:
            return
        #print 'do schedule:', r[2]

        now = QDateTime.currentDateTime()
        t = now.secsTo(self.time_e.dateTime())
        if t <= 240:
            QMessageBox.warning(None, _('Error'), _("Please select a time at least five minutes later than current time"), _('OK'))
            return

        time = self.time_e.dateTime().toTime_t()
        amount = self.win.amount_e.get_amount()
        fee = self.win.fee_e.get_amount()
        addr = self.win.payto_e.get_outputs()[0][1]

        conn = sqlite3.connect('/tmp/schedule.db')
        c = conn.cursor()
        #c.execute("DROP TABLE IF EXISTS list;")
        c.execute("CREATE TABLE IF NOT EXISTS list (timestamp INTEGER, amount INTEGER, fee INTEGER, address TEXT);")
        c.execute("INSERT INTO list VALUES (?, ?, ?, ?);", (time, amount, fee, addr))
        conn.commit()
        conn.close()
        self.label_request.hide()
        self.view.hide()
        self.add_schedule_table()

    def worker(self):
        conn = sqlite3.connect('/tmp/schedule.db')
        c = conn.cursor()
        n = c.execute("SELECT count(*);")
        while n:
            for row in c.execute('SELECT * FROM list'):
                if row[0] < time.time():
                    pass
            time.sleep(3000)
        conn.commit()
        conn.close()

    def do_send(self, amount, fee, addr):
        outputs = ('address', str(addr), amount)
        label = ''
        coins = self.win.get_coins()
        print outputs, label, fee

    def initialize_model(self, model):
        model.setTable("list")
        model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
        model.select()
        model.setHeaderData(0, Qt.Horizontal, "Date (Timestamp)")
        model.setHeaderData(1, Qt.Horizontal, "Amount (Satoshis)")
        model.setHeaderData(2, Qt.Horizontal, "Fee  (Satoshis)")
        model.setHeaderData(3, Qt.Horizontal, "Address")

    def create_view(self, model):
        view = QTableView()
        view.setModel(model)
        view.setColumnWidth(0, 170)
        view.setColumnWidth(1, 150)
        view.setColumnWidth(2, 150)
        view.horizontalHeader().setStretchLastSection(True)
        return view

