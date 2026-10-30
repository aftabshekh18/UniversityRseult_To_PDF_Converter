from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd


SUBJECTS = [
    ("BTCOC501", "DATABASE SYSTEMS"),
    ("BTCOC502", "THEORY OF COMPUTATIONS"),
    ("BTCOC503", "SOFTWARE ENGINEERING"),
    ("BTCOE504A", "HUMAN COMPUTER INTERACTION"),
    ("BTCOF408", "FIELD TRAINING / INTERNSHIP / INDUSTRIAL TRAINING - II"),
    ("BTCOL506", "DATABASE SYSTEM AND SOFTWARE ENGINEERING LAB"),
    ("BTCOM507", "MINI PROJECT I"),
    ("BTHM505B", "BUSINESS COMMUNICATION"),
]


def create_excel(dataframe, output_file):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "University Results"

    thin = Side(style="thin")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    header_fill = PatternFill(fill_type="solid", fgColor="D9EAF7")
    group_fill = PatternFill(fill_type="solid", fgColor="B4C7E7")
    header_font = Font(bold=True)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Student information now includes Percentage and Rank.
    fixed_columns = [
        "Seat No",
        "Student Name",
        "Result",
        "SGPA",
        "Total Grade Point",
        "Total Credit",
        "Total Marks",
        "Percentage",
        "Rank",
    ]

    # Row 1: group header
    current_col = 1
    ws = worksheet

    ws.merge_cells(
        start_row=1,
        start_column=current_col,
        end_row=1,
        end_column=current_col + len(fixed_columns) - 1,
    )
    cell = ws.cell(row=1, column=current_col)
    cell.value = "STUDENT INFORMATION"
    cell.font = header_font
    cell.fill = group_fill
    cell.alignment = center

    current_col += len(fixed_columns)

    for code, subject_name in SUBJECTS:
        start_col = current_col
        end_col = current_col + 4

        ws.merge_cells(
            start_row=1,
            start_column=start_col,
            end_row=1,
            end_column=end_col,
        )

        cell = ws.cell(row=1, column=start_col)
        cell.value = code
        cell.font = header_font
        cell.fill = group_fill
        cell.alignment = center

        current_col += 5

    # Row 2: column headers
    current_col = 1

    for column in fixed_columns:
        cell = ws.cell(row=2, column=current_col)
        cell.value = column
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        current_col += 1

    for code, subject_name in SUBJECTS:
        for sub_column in ["ESE", "CA Internal", "Mid Internal", "Total", "Grade"]:
            cell = ws.cell(row=2, column=current_col)
            cell.value = sub_column
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center
            current_col += 1

    # Data starts on row 3.
    for row_number, (_, row) in enumerate(dataframe.iterrows(), start=3):
        current_col = 1

        for column in fixed_columns:
            value = row.get(column, "")
            if pd.isna(value):
                value = ""

            cell = ws.cell(row=row_number, column=current_col)
            cell.value = value
            cell.alignment = center
            cell.border = border

            if column == "Percentage" and value != "":
                cell.number_format = "0.00"

            current_col += 1

        for code, subject_name in SUBJECTS:
            subject_columns = [
                f"{code} ESE",
                f"{code} CA Internal",
                f"{code} Mid Internal",
                f"{code} Total",
                f"{code} Grade",
            ]

            for column in subject_columns:
                value = row.get(column, "")
                if pd.isna(value):
                    value = ""

                cell = ws.cell(row=row_number, column=current_col)
                cell.value = value
                cell.alignment = center
                cell.border = border
                current_col += 1

    # Header borders
    for row in ws.iter_rows(min_row=1, max_row=2):
        for cell in row:
            cell.border = border
            cell.alignment = center

    # Column widths
    widths = {
        "A": 18,
        "B": 32,
        "C": 12,
        "D": 12,
        "E": 18,
        "F": 15,
        "G": 15,
        "H": 14,
        "I": 10,
    }

    for column, width in widths.items():
        ws.column_dimensions[column].width = width

    for col in range(10, ws.max_column + 1):
        ws.column_dimensions[get_column_letter(col)].width = 14

    ws.row_dimensions[1].height = 30
    ws.row_dimensions[2].height = 35
    ws.freeze_panes = "A3"
    ws.auto_filter.ref = f"A2:{get_column_letter(ws.max_column)}{ws.max_row}"

    workbook.save(output_file)
