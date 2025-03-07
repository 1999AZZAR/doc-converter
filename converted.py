import sys
import os
import pypandoc
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QLabel,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QTextEdit,
    QGridLayout,
    QMessageBox,
)
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor
from PyQt6.QtCore import Qt, QMimeData

# Suppress KDE-related warnings
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.*.debug=false"

# Supported file formats
SUPPORTED_INPUT_FORMATS = [
    "md",
    "docx",
    "odt",
    "latex",
    "html",
    "txt",
    "rtf",
    "epub",
]  # Removed PDF as input
SUPPORTED_OUTPUT_FORMATS = [
    "md",
    "docx",
    "odt",
    "latex",
    "html",
    "txt",
    "rtf",
    "epub",
    "pdf",
]


class DragDropListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    file_extension = os.path.splitext(file_path)[1][
                        1:
                    ].lower()  # Get file extension
                    if file_extension in SUPPORTED_INPUT_FORMATS:
                        self.addItem(QListWidgetItem(file_path))
                    else:
                        QMessageBox.warning(
                            self.parent(),
                            "Unsupported File",
                            f"The file '{os.path.basename(file_path)}' is not supported.",
                        )


class FileConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.set_dark_theme()  # Apply dark theme

    def initUI(self):
        self.setWindowTitle("Frea File Converter")
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        main_layout = QGridLayout()

        # Selected Files List
        self.selected_files_label = QLabel("Selected Files:", self)
        main_layout.addWidget(self.selected_files_label, 1, 0, 1, 2)

        self.file_list = DragDropListWidget(self)
        main_layout.addWidget(self.file_list, 2, 0, 1, 2)

        # Add and Remove Buttons
        button_layout = QHBoxLayout()
        self.btn_add_files = QPushButton("Add Files", self)
        self.btn_add_files.setIcon(QIcon.fromTheme("document-open"))
        self.btn_add_files.setToolTip("Add files to convert")
        self.btn_add_files.clicked.connect(self.add_files)
        button_layout.addWidget(self.btn_add_files)

        self.btn_remove_file = QPushButton("Remove Selected", self)
        self.btn_remove_file.setIcon(QIcon.fromTheme("edit-delete"))
        self.btn_remove_file.setToolTip("Remove selected files")
        self.btn_remove_file.clicked.connect(self.remove_file)
        button_layout.addWidget(self.btn_remove_file)

        main_layout.addLayout(button_layout, 3, 0, 1, 2)

        # Output Format Selection (Input format is auto-detected)
        self.output_format_label = QLabel("Output Format:", self)
        main_layout.addWidget(self.output_format_label, 4, 0)

        self.output_format_combo = QComboBox(self)
        self.output_format_combo.addItems(SUPPORTED_OUTPUT_FORMATS)
        self.output_format_combo.setToolTip("Select the output format for conversion")
        main_layout.addWidget(self.output_format_combo, 4, 1)

        # File Preview Section
        self.preview_label = QLabel("File Preview:", self)
        main_layout.addWidget(self.preview_label, 5, 0, 1, 2)

        self.preview_text = QTextEdit(self)
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText(
            "Preview of the selected file will appear here."
        )
        main_layout.addWidget(self.preview_text, 6, 0, 1, 2)

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar, 7, 0, 1, 2)

        # Status Label
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label, 8, 0, 1, 2)

        # Convert Button
        self.btn_convert = QPushButton("Convert", self)
        self.btn_convert.setIcon(QIcon.fromTheme("document-save"))
        self.btn_convert.setToolTip("Convert selected files")
        self.btn_convert.clicked.connect(self.convert_files)
        main_layout.addWidget(self.btn_convert, 9, 0, 1, 2)

        self.setLayout(main_layout)

        # Connect file selection to preview
        self.file_list.itemSelectionChanged.connect(self.update_preview)

    def add_files(self):
        options = QFileDialog.Option.DontUseNativeDialog  # Use enum value directly
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            "",
            "All Files (*);;Markdown Files (*.md);;Word Files (*.docx);;OpenDocument Files (*.odt);;LaTeX Files (*.tex);;HTML Files (*.html);;Text Files (*.txt);;RTF Files (*.rtf);;EPUB Files (*.epub)",
            options=options,
        )
        if files:
            for file in files:
                file_extension = os.path.splitext(file)[1][
                    1:
                ].lower()  # Get file extension
                if file_extension in SUPPORTED_INPUT_FORMATS:
                    item = QListWidgetItem(file)
                    self.file_list.addItem(item)
                else:
                    QMessageBox.warning(
                        self,
                        "Unsupported File",
                        f"The file '{os.path.basename(file)}' is not supported.",
                    )

    def remove_file(self):
        selected_items = self.file_list.selectedItems()
        for item in selected_items:
            self.file_list.takeItem(self.file_list.row(item))

    def update_preview(self):
        selected_item = self.file_list.currentItem()
        if selected_item:
            file_path = selected_item.text()
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.preview_text.setText(content)
            except Exception as e:
                self.preview_text.setText(f"Error reading file: {str(e)}")
        else:
            self.preview_text.clear()

    def convert_files(self):
        if self.file_list.count() == 0:
            self.status_label.setText("Please select at least one file.")
            return

        output_format = self.output_format_combo.currentText()

        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(self.file_list.count())

        for i in range(self.file_list.count()):
            file = self.file_list.item(i).text()
            file_extension = os.path.splitext(file)[1][1:].lower()  # Get file extension
            input_format = file_extension  # Auto-detect input format

            try:
                # Create "converted" folder in the same directory as the input file
                input_dir = os.path.dirname(file)
                output_dir = os.path.join(input_dir, "converted")
                os.makedirs(output_dir, exist_ok=True)

                # Generate output file path
                original_name = os.path.splitext(os.path.basename(file))[0]
                output_file = os.path.join(
                    output_dir, f"{original_name}.{output_format}"
                )

                # Convert the file with additional options to preserve formatting
                pypandoc.convert_file(
                    file,
                    output_format,
                    outputfile=output_file,
                    format=input_format,
                    extra_args=["--wrap=preserve"],  # Preserve line breaks
                )

                # Update progress bar
                self.progress_bar.setValue(i + 1)
                QApplication.processEvents()  # Ensure the UI updates

            except Exception as e:
                self.status_label.setText(
                    f"Failed to convert {os.path.basename(file)}: {str(e)}"
                )
                return

        # Hide progress bar after completion
        self.progress_bar.setVisible(False)
        self.status_label.setText("All files converted successfully!")

    def set_dark_theme(self):
        """Apply a dark theme using QPalette."""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)

        QApplication.setPalette(palette)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    ex = FileConverterApp()
    ex.show()
    sys.exit(app.exec())  # Use exec() instead of exec_()
