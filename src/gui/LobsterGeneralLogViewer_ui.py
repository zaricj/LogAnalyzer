# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'LobsterGeneralLogViewer.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QLayout, QLineEdit, QMainWindow, QMenu,
    QMenuBar, QPlainTextEdit, QProgressBar, QPushButton,
    QRadioButton, QSizePolicy, QSpinBox, QSplitter,
    QStatusBar, QTabWidget, QTableView, QTextEdit,
    QTreeView, QVBoxLayout, QWidget)
from gui.assets.qrc import LobsterLogReporter_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1199, 913)
        font = QFont()
        font.setPointSize(12)
        MainWindow.setFont(font)
        icon = QIcon()
        icon.addFile(u":/icons/Geis.ico", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setIconSize(QSize(64, 64))
        self.actionDark = QAction(MainWindow)
        self.actionDark.setObjectName(u"actionDark")
        self.actionDark.setCheckable(True)
        self.actionDark.setChecked(True)
        icon1 = QIcon()
        icon1.addFile(u":/images/moon_light_mode_32x32.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionDark.setIcon(icon1)
        self.actionLight = QAction(MainWindow)
        self.actionLight.setObjectName(u"actionLight")
        self.actionLight.setCheckable(True)
        icon2 = QIcon()
        icon2.addFile(u":/images/sun_light_mode_32x32.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionLight.setIcon(icon2)
        self.actionInput_Directory = QAction(MainWindow)
        self.actionInput_Directory.setObjectName(u"actionInput_Directory")
        self.actionInput_Directory1 = QAction(MainWindow)
        self.actionInput_Directory1.setObjectName(u"actionInput_Directory1")
        icon3 = QIcon()
        icon3.addFile(u":/images/input_folder_light_512x512.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionInput_Directory1.setIcon(icon3)
        self.actionOutput_Directory = QAction(MainWindow)
        self.actionOutput_Directory.setObjectName(u"actionOutput_Directory")
        icon4 = QIcon()
        icon4.addFile(u":/images/output_folder_light_512x512.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionOutput_Directory.setIcon(icon4)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widgetTop = QWidget(self.centralwidget)
        self.widgetTop.setObjectName(u"widgetTop")
        self.verticalLayout_11 = QVBoxLayout(self.widgetTop)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.verticalLayout_11.setContentsMargins(-1, 0, -1, 3)
        self.splitterTop = QSplitter(self.widgetTop)
        self.splitterTop.setObjectName(u"splitterTop")
        self.splitterTop.setMinimumSize(QSize(0, 300))
        self.splitterTop.setOrientation(Qt.Orientation.Horizontal)
        self.verticalGroupBox_information = QGroupBox(self.splitterTop)
        self.verticalGroupBox_information.setObjectName(u"verticalGroupBox_information")
        self.verticalGroupBox_information.setFlat(False)
        self.verticalLeftLogView = QVBoxLayout(self.verticalGroupBox_information)
        self.verticalLeftLogView.setSpacing(6)
        self.verticalLeftLogView.setObjectName(u"verticalLeftLogView")
        self.verticalLeftLogView.setContentsMargins(4, 5, 4, 3)
        self.text_edit_program_output = QTextEdit(self.verticalGroupBox_information)
        self.text_edit_program_output.setObjectName(u"text_edit_program_output")
        self.text_edit_program_output.setMinimumSize(QSize(0, 0))
        self.text_edit_program_output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        self.verticalLeftLogView.addWidget(self.text_edit_program_output)

        self.line_separator = QFrame(self.verticalGroupBox_information)
        self.line_separator.setObjectName(u"line_separator")
        self.line_separator.setWindowModality(Qt.WindowModality.NonModal)
        self.line_separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.line_separator.setLineWidth(1)
        self.line_separator.setMidLineWidth(1)
        self.line_separator.setFrameShape(QFrame.Shape.HLine)

        self.verticalLeftLogView.addWidget(self.line_separator)

        self.widget_configuration = QWidget(self.verticalGroupBox_information)
        self.widget_configuration.setObjectName(u"widget_configuration")
        self.widget_configuration.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout_3 = QVBoxLayout(self.widget_configuration)
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(9, 0, 9, 3)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_files_directory = QLabel(self.widget_configuration)
        self.label_files_directory.setObjectName(u"label_files_directory")

        self.horizontalLayout_3.addWidget(self.label_files_directory)

        self.input_browse_folder = QLineEdit(self.widget_configuration)
        self.input_browse_folder.setObjectName(u"input_browse_folder")
        self.input_browse_folder.setClearButtonEnabled(True)

        self.horizontalLayout_3.addWidget(self.input_browse_folder)

        self.button_browse_folder = QPushButton(self.widget_configuration)
        self.button_browse_folder.setObjectName(u"button_browse_folder")
        font1 = QFont()
        font1.setPointSize(12)
        font1.setBold(True)
        self.button_browse_folder.setFont(font1)

        self.horizontalLayout_3.addWidget(self.button_browse_folder)


        self.verticalLayout_3.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_04 = QHBoxLayout()
        self.horizontalLayout_04.setObjectName(u"horizontalLayout_04")
        self.label_file_pattern = QLabel(self.widget_configuration)
        self.label_file_pattern.setObjectName(u"label_file_pattern")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_file_pattern.sizePolicy().hasHeightForWidth())
        self.label_file_pattern.setSizePolicy(sizePolicy)
        self.label_file_pattern.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_04.addWidget(self.label_file_pattern)

        self.input_file_pattern = QLineEdit(self.widget_configuration)
        self.input_file_pattern.setObjectName(u"input_file_pattern")
        self.input_file_pattern.setMinimumSize(QSize(0, 0))
        self.input_file_pattern.setClearButtonEnabled(True)

        self.horizontalLayout_04.addWidget(self.input_file_pattern)


        self.verticalLayout_3.addLayout(self.horizontalLayout_04)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_pattern_configuration = QLabel(self.widget_configuration)
        self.label_pattern_configuration.setObjectName(u"label_pattern_configuration")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_pattern_configuration.sizePolicy().hasHeightForWidth())
        self.label_pattern_configuration.setSizePolicy(sizePolicy1)

        self.horizontalLayout_2.addWidget(self.label_pattern_configuration)

        self.combobox_configuration = QComboBox(self.widget_configuration)
        self.combobox_configuration.setObjectName(u"combobox_configuration")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.combobox_configuration.sizePolicy().hasHeightForWidth())
        self.combobox_configuration.setSizePolicy(sizePolicy2)

        self.horizontalLayout_2.addWidget(self.combobox_configuration)

        self.button_refresh_configuration = QPushButton(self.widget_configuration)
        self.button_refresh_configuration.setObjectName(u"button_refresh_configuration")
        icon5 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ViewRefresh))
        self.button_refresh_configuration.setIcon(icon5)

        self.horizontalLayout_2.addWidget(self.button_refresh_configuration)

        self.button_pattern_configuration_info = QPushButton(self.widget_configuration)
        self.button_pattern_configuration_info.setObjectName(u"button_pattern_configuration_info")
        icon6 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.HelpAbout))
        self.button_pattern_configuration_info.setIcon(icon6)

        self.horizontalLayout_2.addWidget(self.button_pattern_configuration_info)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.button_parse_files = QPushButton(self.widget_configuration)
        self.button_parse_files.setObjectName(u"button_parse_files")
        self.button_parse_files.setFont(font1)

        self.verticalLayout_3.addWidget(self.button_parse_files)


        self.verticalLeftLogView.addWidget(self.widget_configuration)

        self.progressbar = QProgressBar(self.verticalGroupBox_information)
        self.progressbar.setObjectName(u"progressbar")
        self.progressbar.setFont(font1)
        self.progressbar.setValue(24)

        self.verticalLeftLogView.addWidget(self.progressbar)

        self.splitterTop.addWidget(self.verticalGroupBox_information)
        self.verticalGroupBox_directory_view = QGroupBox(self.splitterTop)
        self.verticalGroupBox_directory_view.setObjectName(u"verticalGroupBox_directory_view")
        self.verticalRightTreeView = QVBoxLayout(self.verticalGroupBox_directory_view)
        self.verticalRightTreeView.setSpacing(6)
        self.verticalRightTreeView.setObjectName(u"verticalRightTreeView")
        self.verticalRightTreeView.setContentsMargins(4, 5, 4, 3)
        self.treeview_directory_view = QTreeView(self.verticalGroupBox_directory_view)
        self.treeview_directory_view.setObjectName(u"treeview_directory_view")

        self.verticalRightTreeView.addWidget(self.treeview_directory_view)

        self.splitterTop.addWidget(self.verticalGroupBox_directory_view)

        self.verticalLayout_11.addWidget(self.splitterTop)


        self.verticalLayout.addWidget(self.widgetTop)

        self.widgetBottom = QWidget(self.centralwidget)
        self.widgetBottom.setObjectName(u"widgetBottom")
        self.verticalLayout_4 = QVBoxLayout(self.widgetBottom)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(-1, 0, -1, 3)
        self.tabWidget_parsed_data_result = QTabWidget(self.widgetBottom)
        self.tabWidget_parsed_data_result.setObjectName(u"tabWidget_parsed_data_result")
        self.tabWidget_parsed_data_result.setFont(font1)
        self.tabWidget_parsed_data_result.setTabShape(QTabWidget.TabShape.Rounded)
        self.tabWidget_parsed_data_result.setTabBarAutoHide(False)
        self.tabWidget_parsed_data_page = QWidget()
        self.tabWidget_parsed_data_page.setObjectName(u"tabWidget_parsed_data_page")
        font2 = QFont()
        font2.setPointSize(12)
        font2.setBold(False)
        self.tabWidget_parsed_data_page.setFont(font2)
        self.verticalLayout_2 = QVBoxLayout(self.tabWidget_parsed_data_page)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.verticalLayout_2.setContentsMargins(9, 0, 9, 3)
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(-1, 3, -1, -1)
        self.button_import_csv = QPushButton(self.tabWidget_parsed_data_page)
        self.button_import_csv.setObjectName(u"button_import_csv")
        self.button_import_csv.setFont(font1)

        self.horizontalLayout_4.addWidget(self.button_import_csv)

        self.label_export_as = QLabel(self.tabWidget_parsed_data_page)
        self.label_export_as.setObjectName(u"label_export_as")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.label_export_as.sizePolicy().hasHeightForWidth())
        self.label_export_as.setSizePolicy(sizePolicy3)

        self.horizontalLayout_4.addWidget(self.label_export_as)

        self.radiobutton_csv = QRadioButton(self.tabWidget_parsed_data_page)
        self.radiobutton_csv.setObjectName(u"radiobutton_csv")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.radiobutton_csv.sizePolicy().hasHeightForWidth())
        self.radiobutton_csv.setSizePolicy(sizePolicy4)
        self.radiobutton_csv.setFont(font1)
        self.radiobutton_csv.setChecked(True)

        self.horizontalLayout_4.addWidget(self.radiobutton_csv)

        self.radiobutton_excel = QRadioButton(self.tabWidget_parsed_data_page)
        self.radiobutton_excel.setObjectName(u"radiobutton_excel")
        sizePolicy4.setHeightForWidth(self.radiobutton_excel.sizePolicy().hasHeightForWidth())
        self.radiobutton_excel.setSizePolicy(sizePolicy4)
        self.radiobutton_excel.setFont(font1)

        self.horizontalLayout_4.addWidget(self.radiobutton_excel)

        self.button_export = QPushButton(self.tabWidget_parsed_data_page)
        self.button_export.setObjectName(u"button_export")
        self.button_export.setFont(font1)

        self.horizontalLayout_4.addWidget(self.button_export)

        self.line_separator_vertical = QFrame(self.tabWidget_parsed_data_page)
        self.line_separator_vertical.setObjectName(u"line_separator_vertical")
        self.line_separator_vertical.setFrameShape(QFrame.Shape.VLine)
        self.line_separator_vertical.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout_4.addWidget(self.line_separator_vertical)

        self.button_clear_table = QPushButton(self.tabWidget_parsed_data_page)
        self.button_clear_table.setObjectName(u"button_clear_table")
        self.button_clear_table.setEnabled(False)
        self.button_clear_table.setFont(font1)

        self.horizontalLayout_4.addWidget(self.button_clear_table)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.table_view_result = QTableView(self.tabWidget_parsed_data_page)
        self.table_view_result.setObjectName(u"table_view_result")
        self.table_view_result.setShowGrid(True)
        self.table_view_result.setGridStyle(Qt.PenStyle.SolidLine)
        self.table_view_result.setSortingEnabled(True)

        self.verticalLayout_2.addWidget(self.table_view_result)

        self.input_filter_table = QLineEdit(self.tabWidget_parsed_data_page)
        self.input_filter_table.setObjectName(u"input_filter_table")

        self.verticalLayout_2.addWidget(self.input_filter_table)

        self.tabWidget_parsed_data_result.addTab(self.tabWidget_parsed_data_page, "")
        self.tabWidget_log_preview_page = QWidget()
        self.tabWidget_log_preview_page.setObjectName(u"tabWidget_log_preview_page")
        self.tabWidget_log_preview_page.setFont(font2)
        self.verticalLayout_5 = QVBoxLayout(self.tabWidget_log_preview_page)
        self.verticalLayout_5.setSpacing(6)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(9, 0, 9, 3)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 3, -1, -1)
        self.label_log_preview_sort_by_date = QLabel(self.tabWidget_log_preview_page)
        self.label_log_preview_sort_by_date.setObjectName(u"label_log_preview_sort_by_date")
        sizePolicy3.setHeightForWidth(self.label_log_preview_sort_by_date.sizePolicy().hasHeightForWidth())
        self.label_log_preview_sort_by_date.setSizePolicy(sizePolicy3)

        self.horizontalLayout.addWidget(self.label_log_preview_sort_by_date)

        self.combobox_time = QComboBox(self.tabWidget_log_preview_page)
        self.combobox_time.setObjectName(u"combobox_time")

        self.horizontalLayout.addWidget(self.combobox_time)

        self.checkbox_log_preview_wrap_text = QCheckBox(self.tabWidget_log_preview_page)
        self.checkbox_log_preview_wrap_text.setObjectName(u"checkbox_log_preview_wrap_text")
        self.checkbox_log_preview_wrap_text.setChecked(True)

        self.horizontalLayout.addWidget(self.checkbox_log_preview_wrap_text)

        self.line = QFrame(self.tabWidget_log_preview_page)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.VLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout.addWidget(self.line)

        self.checkbox_truncate_preview = QCheckBox(self.tabWidget_log_preview_page)
        self.checkbox_truncate_preview.setObjectName(u"checkbox_truncate_preview")

        self.horizontalLayout.addWidget(self.checkbox_truncate_preview)

        self.label_max_filesize = QLabel(self.tabWidget_log_preview_page)
        self.label_max_filesize.setObjectName(u"label_max_filesize")
        self.label_max_filesize.setEnabled(False)

        self.horizontalLayout.addWidget(self.label_max_filesize)

        self.spinbox_max_filesize_preview = QSpinBox(self.tabWidget_log_preview_page)
        self.spinbox_max_filesize_preview.setObjectName(u"spinbox_max_filesize_preview")
        self.spinbox_max_filesize_preview.setEnabled(False)
        self.spinbox_max_filesize_preview.setMinimum(256)
        self.spinbox_max_filesize_preview.setMaximum(51200)
        self.spinbox_max_filesize_preview.setSingleStep(256)
        self.spinbox_max_filesize_preview.setDisplayIntegerBase(10)

        self.horizontalLayout.addWidget(self.spinbox_max_filesize_preview)


        self.verticalLayout_5.addLayout(self.horizontalLayout)

        self.text_edit_log_preview = QPlainTextEdit(self.tabWidget_log_preview_page)
        self.text_edit_log_preview.setObjectName(u"text_edit_log_preview")

        self.verticalLayout_5.addWidget(self.text_edit_log_preview)

        self.tabWidget_parsed_data_result.addTab(self.tabWidget_log_preview_page, "")

        self.verticalLayout_4.addWidget(self.tabWidget_parsed_data_result)


        self.verticalLayout.addWidget(self.widgetBottom)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1199, 33))
        self.menuSettings = QMenu(self.menubar)
        self.menuSettings.setObjectName(u"menuSettings")
        self.menuAppearance = QMenu(self.menuSettings)
        self.menuAppearance.setObjectName(u"menuAppearance")
        self.menuAppearance.setEnabled(True)
        self.menuAppearance.setFont(font2)
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuOpen = QMenu(self.menuFile)
        self.menuOpen.setObjectName(u"menuOpen")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuSettings.menuAction())
        self.menuSettings.addAction(self.menuAppearance.menuAction())
        self.menuAppearance.addAction(self.actionDark)
        self.menuAppearance.addAction(self.actionLight)
        self.menuFile.addAction(self.menuOpen.menuAction())
        self.menuOpen.addAction(self.actionInput_Directory1)
        self.menuOpen.addAction(self.actionOutput_Directory)

        self.retranslateUi(MainWindow)

        self.tabWidget_parsed_data_result.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"App", None))
        self.actionDark.setText(QCoreApplication.translate("MainWindow", u"Dark", None))
        self.actionLight.setText(QCoreApplication.translate("MainWindow", u"Light", None))
        self.actionInput_Directory.setText(QCoreApplication.translate("MainWindow", u"Input Directory", None))
        self.actionInput_Directory1.setText(QCoreApplication.translate("MainWindow", u"Input Directory", None))
        self.actionOutput_Directory.setText(QCoreApplication.translate("MainWindow", u"Output Directory", None))
        self.verticalGroupBox_information.setTitle(QCoreApplication.translate("MainWindow", u"Information", None))
        self.label_files_directory.setText(QCoreApplication.translate("MainWindow", u"Files Directory:", None))
        self.input_browse_folder.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Select a folder containing text based files to search...", None))
#if QT_CONFIG(tooltip)
        self.button_browse_folder.setToolTip(QCoreApplication.translate("MainWindow", u"Browse folder directory.", None))
#endif // QT_CONFIG(tooltip)
        self.button_browse_folder.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.label_file_pattern.setText(QCoreApplication.translate("MainWindow", u"File Pattern:", None))
        self.input_file_pattern.setPlaceholderText(QCoreApplication.translate("MainWindow", u"(Optional) Enter patterns to search only specific files (comma-separated)", None))
        self.label_pattern_configuration.setText(QCoreApplication.translate("MainWindow", u"Pattern Configuration:", None))
#if QT_CONFIG(tooltip)
        self.button_refresh_configuration.setToolTip(QCoreApplication.translate("MainWindow", u"Refresh the \u00fcatterns if new files were added to the patterns folder.", None))
#endif // QT_CONFIG(tooltip)
        self.button_refresh_configuration.setText("")
#if QT_CONFIG(tooltip)
        self.button_pattern_configuration_info.setToolTip(QCoreApplication.translate("MainWindow", u"Show relevant info about the selected pattern configuration.", None))
#endif // QT_CONFIG(tooltip)
        self.button_pattern_configuration_info.setText("")
#if QT_CONFIG(tooltip)
        self.button_parse_files.setToolTip(QCoreApplication.translate("MainWindow", u"Parse and search the found files in the folder and display it's results into the table below.", None))
#endif // QT_CONFIG(tooltip)
        self.button_parse_files.setText(QCoreApplication.translate("MainWindow", u"Parse Files", None))
        self.verticalGroupBox_directory_view.setTitle(QCoreApplication.translate("MainWindow", u"Directory View", None))
#if QT_CONFIG(tooltip)
        self.button_import_csv.setToolTip(QCoreApplication.translate("MainWindow", u"Import a CSV file into the table.", None))
#endif // QT_CONFIG(tooltip)
        self.button_import_csv.setText(QCoreApplication.translate("MainWindow", u"Import CSV", None))
        self.label_export_as.setText(QCoreApplication.translate("MainWindow", u"Export as:", None))
        self.radiobutton_csv.setText(QCoreApplication.translate("MainWindow", u"CSV", None))
        self.radiobutton_excel.setText(QCoreApplication.translate("MainWindow", u"Excel", None))
#if QT_CONFIG(tooltip)
        self.button_export.setToolTip(QCoreApplication.translate("MainWindow", u"Export the table data.", None))
#endif // QT_CONFIG(tooltip)
        self.button_export.setText(QCoreApplication.translate("MainWindow", u"Export", None))
#if QT_CONFIG(tooltip)
        self.button_clear_table.setToolTip(QCoreApplication.translate("MainWindow", u"Clear table results.", None))
#endif // QT_CONFIG(tooltip)
        self.button_clear_table.setText(QCoreApplication.translate("MainWindow", u"Clear Table", None))
#if QT_CONFIG(tooltip)
        self.input_filter_table.setToolTip(QCoreApplication.translate("MainWindow", u"Filter table data.", None))
#endif // QT_CONFIG(tooltip)
        self.input_filter_table.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Filter table data by text...", None))
        self.tabWidget_parsed_data_result.setTabText(self.tabWidget_parsed_data_result.indexOf(self.tabWidget_parsed_data_page), QCoreApplication.translate("MainWindow", u"Result Table", None))
        self.label_log_preview_sort_by_date.setText(QCoreApplication.translate("MainWindow", u"Filter Content by Date/Time:", None))
        self.checkbox_log_preview_wrap_text.setText(QCoreApplication.translate("MainWindow", u"Wrap Text", None))
        self.checkbox_truncate_preview.setText(QCoreApplication.translate("MainWindow", u"Truncate Preview", None))
        self.label_max_filesize.setText(QCoreApplication.translate("MainWindow", u"Max file size to preview:", None))
        self.spinbox_max_filesize_preview.setSpecialValueText("")
        self.spinbox_max_filesize_preview.setSuffix(QCoreApplication.translate("MainWindow", u" KB", None))
        self.spinbox_max_filesize_preview.setPrefix(QCoreApplication.translate("MainWindow", u"Read first ", None))
        self.tabWidget_parsed_data_result.setTabText(self.tabWidget_parsed_data_result.indexOf(self.tabWidget_log_preview_page), QCoreApplication.translate("MainWindow", u"File Preview", None))
        self.menuSettings.setTitle(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.menuAppearance.setTitle(QCoreApplication.translate("MainWindow", u"Appearance", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuOpen.setTitle(QCoreApplication.translate("MainWindow", u"Open", None))
    # retranslateUi

