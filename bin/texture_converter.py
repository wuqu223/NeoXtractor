import sys
import os
from PyQt5.QtWidgets import *
import subprocess

class TextureWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('PVRTexToolCLI GUI')
        self.setGeometry(1000, 300, 300, 450)

        layout = QVBoxLayout()

        # Input file selection
        self.input_label = QLabel('Select Input File:', self)
        layout.addWidget(self.input_label)
        
        self.input_file = QLineEdit(self)
        layout.addWidget(self.input_file)
        
        self.input_button = QPushButton('Browse', self)
        self.input_button.clicked.connect(self.browse_input_file)
        layout.addWidget(self.input_button)

        # Custom dimensions checkbox
        self.custom_dim_checkbox = QCheckBox("Use Custom Dimensions")
        self.custom_dim_checkbox.stateChanged.connect(self.toggle_dimension_selection)
        layout.addWidget(self.custom_dim_checkbox)

        # Dropdown for dimension selection (initially disabled)
        self.dim_dropdown = QComboBox()
        self.dim_dropdown.addItems(["128x128", "256x256", "512x512", "1024x1024", "2048x2048"])
        self.dim_dropdown.setEnabled(False)
        layout.addWidget(self.dim_dropdown)

        # Compression format dropdown
        self.compression_dropdown = QComboBox()
        self.compression_dropdown.addItems(["BC1", "BC3", "BC5", "BC7"])
        layout.addWidget(QLabel("Select Compression Format:"))
        layout.addWidget(self.compression_dropdown)

        # Execute button for single file
        self.single_execute_button = QPushButton('Convert to DDS', self)
        self.single_execute_button.clicked.connect(self.convert_single_file)
        layout.addWidget(self.single_execute_button)

        # PVR folder selection
        self.folder_label = QLabel('Select Folder for Batch Conversion:', self)
        layout.addWidget(self.folder_label)
        
        self.folder_path = QLineEdit(self)
        layout.addWidget(self.folder_path)
        
        self.folder_button = QPushButton('Browse Folder', self)
        self.folder_button.clicked.connect(self.browse_folder)
        layout.addWidget(self.folder_button)

        # Execute button for batch conversion
        self.batch_execute_button = QPushButton('Batch Convert to DDS', self)
        self.batch_execute_button.clicked.connect(self.batch_convert)
        layout.addWidget(self.batch_execute_button)

        # Progress bar for batch processing
        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def toggle_dimension_selection(self):
        """Enable or disable the dropdown based on the checkbox state."""
        self.dim_dropdown.setEnabled(self.custom_dim_checkbox.isChecked())

    def browse_input_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'Texture Files (*.pvr *.ktx *.astc);;All Files (*)')
        if file_name:
            self.input_file.setText(file_name)

    def browse_folder(self):
        folder_name = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder_name:
            self.folder_path.setText(folder_name)

    def show_error_message(self, message):
        QMessageBox.critical(self, "Error", message)

    def convert_single_file(self):
        try:
            input_file = self.input_file.text()
            if not input_file:
                self.show_error_message("No input file selected.")
                return

            # Construct the output file name by replacing the extension with .dds
            output_file = os.path.splitext(input_file)[0] + ".dds"

            # Get the path of the executable
            exe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PVRTexToolCLI.exe")

            # Determine resize option using -r with width and height
            resize_option = ""
            if self.custom_dim_checkbox.isChecked():
                selected_dim = self.dim_dropdown.currentText()
                width, height = selected_dim.split("x")
                resize_option = f" -r {width},{height} -rfilter linear"

            # Get the selected compression format
            compression_format = self.compression_dropdown.currentText()

            # Command to run the PVRTexToolCLI with optional dimensions and compression format
            command = f'"{exe_path}" -i "{input_file}" -o "{output_file}" -f {compression_format}{resize_option} -m'
            print(f"Running Command: {command}")

            # Run the command
            result = subprocess.run(command, shell=True, check=True)

            # Show success message
            QMessageBox.information(self, "Success", f"Successfully converted {input_file} to DDS.")

        except subprocess.CalledProcessError as e:
            self.show_error_message(f"Failed to convert {input_file}. Error: {str(e)}")
        except Exception as e:
            self.show_error_message(f"An unexpected error occurred: {str(e)}")

    def batch_convert(self):
        try:
            folder_path = self.folder_path.text()

            if not folder_path:
                self.show_error_message("No folder selected.")
                return

            # Get the path of the executable
            exe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PVRTexToolCLI.exe")

            # Recursively search for texture files and count them
            total_files = sum([len(files) for r, d, files in os.walk(folder_path) if any(f.endswith(('.pvr', '.ktx', '.astc')) for f in files)])
            if total_files == 0:
                self.show_error_message("No .pvr or .ktx files found in the selected folder.")
                return

            converted_files = 0

            # Initialize the progress bar
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(total_files)

            # Recursively search for texture files and convert them
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(('.pvr', '.ktx', '.astc')):
                        input_file = os.path.join(root, file)
                        output_file = os.path.splitext(input_file)[0] + ".dds"

                        try:
                            # Command to run the PVRTexToolCLI with the .dds extension
                            command = f'"{exe_path}" -i "{input_file}" -o "{output_file}" -f BC3 -m'
                            print(f"Running Command: {command}")

                            # Run the command
                            subprocess.run(command, shell=True, check=True)
                            converted_files += 1

                        except subprocess.CalledProcessError as e:
                            print(f"Failed to convert {input_file}. Error: {str(e)}")
                        except Exception as e:
                            print(f"An unexpected error occurred with {input_file}: {str(e)}")

                        # Update the progress bar
                        self.progress_bar.setValue(converted_files)

            if converted_files > 0:
                QMessageBox.information(self, "Success", "Batch conversion completed successfully.")
            else:
                QMessageBox.information(self, "No Files Converted", "No .pvr or .ktx files were successfully converted.")

            # Reset progress bar
            self.progress_bar.setValue(0)

        except Exception as e:
            self.show_error_message(f"An unexpected error occurred during batch conversion: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TextureWindow()
    window.show()
    sys.exit(app.exec())
