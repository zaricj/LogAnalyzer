from PySide6.QtCore import QAbstractTableModel, Qt
import pandas as pd


class ResultsTableWidget(QAbstractTableModel):
    """A lightweight model to display a pandas DataFrame in a QTableView."""

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.dataframe = df

    def rowCount(self, parent=None):
        return len(self.dataframe.index)

    def columnCount(self, parent=None):
        return len(self.dataframe.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            value = self.dataframe.iat[index.row(), index.column()]
            return "" if pd.isna(value) else str(value)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return str(self.dataframe.columns[section])
        else:
            return str(self.dataframe.index[section])
