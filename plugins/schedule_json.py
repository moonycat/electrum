from PyQt4.QtGui import *
from PyQt4.QtCore import *

from electrum.i18n import _, set_language
from electrum.plugins import BasePlugin, hook
from gui.qt.util import HelpButton, EnterButton, MyTreeWidget

class Plugin(BasePlugin):

    def fullname(self):
        return "Transaction Scheduling json"

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
        self.add_schedule_widget()
        self.update_schedule_widget()
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
        self.schedule_list.hide()
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
        self.time_e.setMinimumDateTime(QDateTime.currentDateTime().addSecs(300))
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

    def add_schedule_widget(self):
        self.win.send_grid.setRowStretch(8, 1)
        self.label_request = QLabel(_('Saved Schedule'))
        self.schedule_list = MyTreeWidget(None)
        self.schedule_list.setColumnCount(4)
        self.schedule_list.customContextMenuRequested.connect(self.schedule_list_menu)
        self.schedule_list.setHeaderLabels( [_('Date'), _('Amount'), _('Fee'), ('Address')] )
        self.schedule_list.setColumnWidth(0, 150)
        self.schedule_list.setColumnWidth(1, 150)
        self.schedule_list.setColumnWidth(2, 150)

        self.win.send_grid.addWidget(self.label_request, 9, 0)
        self.win.send_grid.addWidget(self.schedule_list, 10, 0, 1, 6)

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
        now = QDateTime.currentDateTime()
        t = now.secsTo(self.time_e.dateTime())
        if not r:
            return
        if t <= 240:
            QMessageBox.warning(None, _('Error'), _("Please select a time at least five minutes later than current time"), _('OK'))
            return
        print t
        time = self.time_e.dateTime().toTime_t()
        amount = self.win.amount_e.get_amount()
        fee = self.win.fee_e.get_amount()
        addr = self.win.payto_e.get_outputs()[0][1]

        self.schedule_requests = self.wallet.storage.get('schedule_requests',{}) 
        self.schedule_requests[time] = (amount, fee, addr)
        self.wallet.storage.put('schedule_requests', self.schedule_requests)
        self.update_schedule_widget()

    def schedule_list_menu(self, position):
        item = self.schedule_list.itemAt(position)
        menu = QMenu()
        #menu.addAction(_("Delete"), lambda: self.schedule_list_delete(item))
        menu.exec_(self.schedule_list.viewport().mapToGlobal(position))

    def update_schedule_widget(self):
        b = len(self.schedule_requests) > 0
        self.schedule_list.setVisible(b)

        self.schedule_list.clear()
        for time, v in self.schedule_requests.items():
            amount, fee, addr = v
            item = QTreeWidgetItem( [ time, self.win.format_amount(amount) if amount else "", self.win.format_amount(fee) if amount else "", addr])
            item.setFont(0, QFont(MONOSPACE_FONT))
            self.schedule_list.addTopLevelItem(item)

