# Batery-Live! Provides a low battery alert similar to the one used on
# Windows 10 but for Linux
from PyQt5.QtCore import Qt, QTimer, QSettings, QDir, QFileInfo
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu,\
    QDialog
import MainWindow_GUI, Dialog_Settings
import sys, psutil

desktop_file = '''[Desktop Entry]
Name=Batery-Live!
TryExec=batery-live
Exec=batery-live
Icon=batery-live
Type=Application
Categories=System,Utility'''

# PATH to autostart
# .config/autostart/batery-live.desktop

# /sys/class/power_supply/BAT0/status
# Full
# Discharging
# Charging

# TODO save and load user settings
class DialogSettings(QDialog, Dialog_Settings.Ui_Dialog):
    def __init__(self, settings, parent=None,):
        super(DialogSettings, self).__init__(parent)
        self.setupUi(self)
        self.settings = settings
        self.load_settings()

    def load_settings(self):
        self.spinBox_batteryw.setValue(self.settings["battery_warning"])
        self.checkBox_autostart.setChecked(self.settings["autostart"])
        self.spinBox_update.setValue(self.settings["update_time"])


class MainWindow(QMainWindow, MainWindow_GUI.Ui_MainWindow):
    def __init__(self, app, parent=None):
        super(MainWindow, self).__init__(parent)

        self.settings = {"update_time":3, "autostart":False,
                              "battery_warning":20}
        self.app = app
        self.battery_threshold1 = False
        self.batter_warning = 20
        self.dialog_settings = DialogSettings(self.settings)

        # System Tray creation
        # TODO reorganize project directory structure
        self.icon_tray = QSystemTrayIcon(QIcon(
            QPixmap(":/icon-official.png")))
        self.icon_tray.setToolTip("Battery Live!")
        self.icon_tray.show()
        self.create_menu()
        self.icon_tray.setContextMenu(self.menu)
        self.icon_tray.activated.connect(self.show_configs)

        # Window GUI attributes
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setupUi(self)

        # Grab desktop size
        print(app.desktop().screen().rect().width())
        width = app.desktop().screen().rect().width()
        height = app.desktop().screen().rect().height()
        # self.resize(width, height/3)
        # self.move(width, height/3)

        # Timer to get battery info periodically
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_battery_info)
        self.timer.start(3000)

        self.pushButton.clicked.connect(self.hide)

    def create_menu(self):
        self.menu = QMenu()
        settings_action = self.menu.addAction("Settings")
        quit_action = self.menu.addAction("Quit")

        settings_action.triggered.connect(self.open_settings)
        quit_action.triggered.connect(sys.exit)

    # TODO check if user clicked CANCEL or OK
    def open_settings(self):
        if self.dialog_settings.exec_():
            self.settings["battery_warning"] = self.dialog_settings.spinBox_batteryw.value()
            self.settings["autostart"] = self.dialog_settings.checkBox_autostart.isChecked()
            self.settings["update_time"] = self.dialog_settings.spinBox_update.value()
            self.timer.start(self.settings["update_time"]  * 1000)

    def show_configs(self, reason):
        # Si nuestro click al icono fue un click derecho no manejamos el evento
        if reason == QSystemTrayIcon.Context:
            return False
        else:
            self.open_settings()

    # Get Battery Info
    def update_battery_info(self):
        battery_info = psutil.sensors_battery()
        if battery_info is not None:
            print(battery_info.percent)
            if not battery_info.power_plugged and\
                    battery_info.percent <= self.settings.get("battery_warning")\
                    and not self.battery_threshold1:
                self.battery_threshold1 = True
                self.showFullScreen()
        else:
            self.read_BAT()

    def read_BAT(self):
        current_charge = None
        full_capacity = None

        file_BAT0_current = "/sys/class/power_supply/BAT0/charge_now"
        file_info = QFileInfo(file_BAT0_current)
        if file_info.isFile() and file_info.isReadable():
            with open(file_BAT0_current) as bat_file:
                current_charge = bat_file.readline()

        file_BAT0_capacity = "/sys/class/power_supply/BAT0/charge_full"
        file_info_current = QFileInfo(file_BAT0_capacity)
        if file_info_current.isFile() and file_info_current.isReadable():
            with open(file_BAT0_capacity) as bat_file:
                full_capacity = bat_file.readline()

        if current_charge is not None and full_capacity is not None:
            print("FULL: ", current_charge)
            print("FULL: ", full_capacity)

            bat_percentage = int(current_charge) // int(full_capacity)
            print("Percentage: ", (bat_percentage)*100)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow(app)
    app.exec_()