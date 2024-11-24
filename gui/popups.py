from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import os
import subprocess

class AboutPopup(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setGeometry(800, 400, 300, 200)

        # Layout and Widgets
        layout = QVBoxLayout()

        # Message Label
        label = QLabel(message)
        layout.addWidget(label, alignment=Qt.AlignCenter)  # Align the message to the center

        # Close Button
        close_button = QPushButton("OK")
        close_button.setFixedSize(100, 30)
        close_button.clicked.connect(self.accept)  # Use accept to close and return from dialog
        layout.addWidget(close_button, alignment=Qt.AlignCenter)  # Align the button to the centre

        self.setLayout(layout)

class BatchPopup(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Processing")
        self.setGeometry(800, 400, 300, 200)

        layout = QVBoxLayout()

        # Message Label
        label = QLabel(message)
        layout.addWidget(label, alignment=Qt.AlignCenter)

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

    def create_command(self, input_file, output_file):
        """Creates the command to run PVRTexToolCLI based on settings."""
        exe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PVRTexToolCLI.exe")
        
        # Determine resize option
        resize_option = ""
        if self.custom_dim_checkbox.isChecked():
            selected_dim = self.dim_dropdown.currentText()
            width, height = selected_dim.split("x")
            resize_option = f" -r {width},{height} -rfilter linear"

        # Get the selected compression format
        compression_format = self.compression_dropdown.currentText()
        
        # Construct and return the command
        return f'"{exe_path}" -i "{input_file}" -o "{output_file}" -f {compression_format}{resize_option} -m'

    def convert_single_file(self):
        try:
            input_file = self.input_file.text()
            if not input_file:
                self.show_error_message("No input file selected.")
                return

            # Construct the output file name by replacing the extension with .dds
            output_file = os.path.splitext(input_file)[0] + ".dds"
            command = self.create_command(input_file, output_file)
            print(f"Running Command: {command}")

            # Run the command
            subprocess.run(command, shell=True, check=True)
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

            exe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PVRTexToolCLI.exe")

            # Search and count files
            texture_files = []
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(('.pvr', '.ktx', '.astc')):
                        texture_files.append(os.path.join(root, file))

            if not texture_files:
                self.show_error_message("No .pvr, .ktx, or .astc files found in the selected folder.")
                return

            # Initialize progress bar
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(len(texture_files))
            converted_files = 0

            # Process each file
            for i, input_file in enumerate(texture_files, 1):
                output_file = os.path.splitext(input_file)[0] + ".dds"
                command = self.create_command(input_file, output_file)
                print(f"Running Command: {command}")

                try:
                    subprocess.run(command, shell=True, check=True)
                    converted_files += 1
                except subprocess.CalledProcessError as e:
                    print(f"Failed to convert {input_file}. Error: {str(e)}")
                except Exception as e:
                    print(f"An unexpected error occurred with {input_file}: {str(e)}")

                # Update progress bar
                self.progress_bar.setValue(i)

            QMessageBox.information(self, "Batch Conversion", f"Batch conversion completed. {converted_files}/{len(texture_files)} files converted.")
            self.progress_bar.setValue(0)

        except Exception as e:
            self.show_error_message(f"An unexpected error occurred during batch conversion: {str(e)}")
