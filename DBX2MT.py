import sys
from PyQt5.QtCore import QTimer, QSettings
import os
from PyQt5.QtWidgets import QApplication, QFileDialog, QDialogButtonBox
from PyQt5.QtCore import QTimer
from PyQt5 import uic

def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.abspath(__file__))

        return os.path.join(base_path, relative_path)

class DBX2ModToggle:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.ventana = uic.loadUi(resource_path("DBX2MT.ui"))
        self.gamePath = ""
        self.mod_disabled_file = "xinput1_3(DisabledMod).dll"
        self.mod_normal_file = "xinput1_3.dll"
        
        # Load saved path
        self.load_game_path()
        
        # Connect signals
        self.connect_signals()
        
    def save_game_path(self, path):
        """Save game path to QSettings (INI format)"""
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, "DBX2ModToggle", "Settings")
        settings.setValue("game_path", path)
    
    def load_game_path(self):
        """Load game path from QSettings (INI format)"""
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, "DBX2ModToggle", "Settings")
        path = settings.value("game_path", "", type=str)
        if path:
            self.gamePath = path
            self.ventana.gamePath.setText(self.gamePath)
            # Verify xinput1_3.dll exists before changing page
            if self.check_xinput_exists():
                self.verify_mods_status()
                self.ventana.stackedWidget.setCurrentIndex(1)

    
    def get_mod_file_paths(self):
        """Get full paths for mod files"""
        return {
            'disabled': os.path.join(self.gamePath, self.mod_disabled_file),
            'normal': os.path.join(self.gamePath, self.mod_normal_file)
        }
    
    def check_mods_status(self):
        """Check current mod status"""
        if not self.gamePath or not os.path.exists(self.gamePath):
            return None
            
        paths = self.get_mod_file_paths()
        
        if os.path.exists(paths['disabled']):
            return False  # Mods disabled
        elif os.path.exists(paths['normal']):
            return True   # Mods enabled
        else:
            return None   # No mods found
    
    def update_mod_status_display(self, status):
        """Update the mod status display"""
        try:
            if status is True:
                self.ventana.modStatus.setText("Enabled")
                self.ventana.modStatus.setStyleSheet("color: green")
            elif status is False:
                self.ventana.modStatus.setText("Disabled")
                self.ventana.modStatus.setStyleSheet("color: red")
            else:
                self.ventana.label_error.setText("No mods installed")
        except AttributeError as e:
            print(f"UI element not found: {e}")
    
    def verify_mods_status(self):
        """Verify mods status on startup and navigate accordingly"""
        status = self.check_mods_status()
        
        if status is not None and self.check_xinput_exists():
            self.ventana.stackedWidget.setCurrentIndex(1)
            self.update_mod_status_display(status)
        else:
            self.update_mod_status_display(None)
    
    def toggle_mods(self):
        """Toggle mod status"""
        current_status = self.check_mods_status()
        
        if current_status is None:
            return "No mods installed"
        
        paths = self.get_mod_file_paths()
        
        try:
            if current_status:  # Currently enabled -> disable
                os.rename(paths['normal'], paths['disabled'])
                self.update_mod_status_display(False)
                return "Mods disabled successfully"
            else:  # Currently disabled -> enable
                os.rename(paths['disabled'], paths['normal'])
                self.update_mod_status_display(True)
                return "Mods enabled successfully"
        except OSError as e:
            return f"Error changing mods: {e}"
    
    def browse_folder(self):
        """Browse for DBXV2.exe file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.ventana, 
            "Select DBXV2.exe", 
            "", 
            "DBXV2.exe (DBXV2.exe);;All Files (*)"
        )
        if file_path:
            # Verify the file is DBXV2.exe
            if os.path.basename(file_path).lower() == "dbxv2.exe":
                folder = os.path.dirname(file_path)
                self.gamePath = folder
                self.ventana.gamePath.setText(folder)
                self.save_game_path(folder)
            else:
                self.ventana.label_error.setText("You must select DBXV2.exe")
    
    def check_xinput_exists(self):
        """Check if xinput1_3.dll or xinput1_3(DisabledMod).dll exists in game path"""
        if not self.gamePath:
            self.ventana.label_error.setText("No path selected")
            return False
        
        paths = self.get_mod_file_paths()
        normal_exists = os.path.exists(paths['normal'])
        disabled_exists = os.path.exists(paths['disabled'])
        
        if not normal_exists and not disabled_exists:
            self.ventana.label_error.setText("xinput1_3.dll not found in the selected path")
            return False
        
        return True
    
    def handle_btn_siguiente(self):
        """Handle Next button click with verification"""
        if self.check_xinput_exists():
            self.save_game_path(self.ventana.gamePath.text())
            self.verify_mods_status()
            self.ventana.stackedWidget.setCurrentIndex(1)
    
    def check_game_running(self):
        """Check if DBXV2.exe is currently running"""
        try:
            import subprocess
            result = subprocess.run(['tasklist'], capture_output=True, text=True)
            return 'DBXV2.exe' in result.stdout
        except Exception:
            return False
    
    def handle_button_box(self, button):
        """Handle buttonBox clicks"""
        button_text = button.text().replace('&', '')  # Quitar ampersands
        
        if button_text == "Yes":  # Aceptar - cambiar mods
            # Check if game is running
            if self.check_game_running():
                try:
                    self.ventana.label_4.setText("Error: DBXV2.exe is running")
                    self.ventana.label_4.setStyleSheet("color: red")
                except AttributeError:
                    pass
                # Close after delay
                QTimer.singleShot(2000, self.app.quit)
                return
            else:
                self.toggle_mods()
                # Cambiar label_4 a "Successful!"
                try:
                    self.ventana.label_4.setText("Successful!")
                except AttributeError:
                    pass
                # Ocultar buttonBox
                try:
                    self.ventana.buttonBox.setEnabled(False)
                except AttributeError:
                    pass
                # Force UI update and close after delay
                self.ventana.update()
                QApplication.processEvents()
                QTimer.singleShot(2000, self.app.quit)
        elif button_text == "No":  # Rechazar - cerrar sin cambios
            self.app.quit()
    
    def connect_signals(self):
        """Connect all UI signals"""
        # Game path text change
        self.ventana.gamePath.textChanged.connect(
            lambda: setattr(self, 'gamePath', self.ventana.gamePath.text())
        )
        
        # Browse button
        try:
            self.ventana.btnExplorer.clicked.connect(self.browse_folder)
        except AttributeError:
            print("btnExplorer not found in UI")
        
        # Next button
        try:
            self.ventana.btnSiguiente.clicked.connect(self.handle_btn_siguiente)
        except AttributeError:
            print("btnSiguiente not found in UI")
        
        # Button box
        try:
            self.ventana.buttonBox.clicked.connect(self.handle_button_box)
        except AttributeError:
            print("buttonBox not found in UI")
    
    def run(self):
        """Start the application"""
        self.ventana.show()
        sys.exit(self.app.exec_())

# Run the application
if __name__ == "__main__":
    app = DBX2ModToggle()
    app.run()