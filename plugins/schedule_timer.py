from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import QtSql

from electrum.i18n import _, set_language
from electrum import SimpleConfig, Transaction
from electrum.plugins import BasePlugin, hook
from gui.qt.util import HelpButton, EnterButton

import sqlite3, time
import sys, traceback

class Plugin(BasePlugin):

    def fullname(self):
        return "Transaction Scheduling timer"

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
        self.check_schedule()
        self.win.update_status()

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

    def check_schedule(self):
        conn = sqlite3.connect('/tmp/schedule.db')
        c = conn.cursor()
        i = 0
        self.time = []
        for row in c.execute('SELECT * FROM list'):
                t = row[0] - time.time()
                self.time.append(QTimer())
                if t > 0:    
                    self.time[i].singleShot(t, self.do_send(row[1], row[2], row[3]))
                    print row[0], time.time(), t
                i += 1

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
        self.check_schedule()

    def do_send(self, amount, fee, addr):
        outputs = ('address', str(addr), amount)
        label = ''
        coins = self.win.get_coins()
        #print outputs, label, fee
        try:
            tx = self.wallet.make_unsigned_transaction(outputs, fee, None, coins = coins)
            tx.error = None
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            self.win.show_message(str(e))
            return

        if tx.requires_fee(self.wallet.verifier) and tx.get_fee() < MIN_RELAY_TX_FEE:
            QMessageBox.warning(self, _('Error'), _("This transaction requires a higher fee, or it will not be propagated by the network."), _('OK'))
            return

        if not self.config.get('can_edit_fees', False):
            if not self.question(_("A fee of %(fee)s will be added to this transaction.\nProceed?")%{ 'fee' : self.win.format_amount(fee) + ' '+ self.win.base_unit()}):
                return
        else:
            confirm_fee = self.config.get('confirm_fee', 100000)
            if fee >= confirm_fee:
                if not self.win.question(_("The fee for this transaction seems unusually high.\nAre you really sure you want to pay %(fee)s in fees?")%{ 'fee' : self.win.format_amount(fee) + ' '+ self.win.base_unit()}):
                    return

        self.win.send_tx(tx, label)

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

