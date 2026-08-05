# ============================================================
# Styled Excel sheet helper — shared by the admin & coordinator exports
# ============================================================
# Four sheets across routes/admin.py and routes/coordinator.py were built by the same
# ~45-line sequence: set column widths, write a blue header row, then write data rows with
# a thin border, alternating fill, and per-column alignment. Only the columns, the
# left-aligned column indices, and whether the sheet gets an autofilter actually differed.
# ============================================================

import io

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from fastapi.responses import StreamingResponse

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
HEADER_ALIGN = Alignment(horizontal="center", vertical="center")

THIN_BORDER = Border(
    left=Side(style="thin", color="D9D9D9"),
    right=Side(style="thin", color="D9D9D9"),
    top=Side(style="thin", color="D9D9D9"),
    bottom=Side(style="thin", color="D9D9D9"),
)
CENTER_ALIGN = Alignment(horizontal="center", vertical="center")
LEFT_ALIGN = Alignment(horizontal="left", vertical="center", indent=1)
EVEN_FILL = PatternFill(start_color="F2F7FB", end_color="F2F7FB", fill_type="solid")

HEADER_ROW_HEIGHT = 28
DATA_ROW_HEIGHT = 22


def write_styled_sheet(
    sheet,
    columns: list[tuple[str, int]],
    rows: list[list],
    *,
    left_align_cols: tuple[int, ...] = (2,),
    autofilter: bool = False,
    freeze_header: bool = False,
) -> None:
    """
    Write a header row and data rows onto `sheet` in the house style.

    columns          -- (header, width) per column, in order
    rows             -- one list of cell values per data row, matching `columns`
    left_align_cols  -- 1-based column indices to left-align; everything else centres
    autofilter       -- add an Excel filter across the written range
    freeze_header    -- keep row 1 visible while scrolling
    """
    for col_idx, (_, width) in enumerate(columns, start=1):
        sheet.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = width

    for col_idx, (title, _) in enumerate(columns, start=1):
        cell = sheet.cell(row=1, column=col_idx, value=title)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = HEADER_ALIGN
    sheet.row_dimensions[1].height = HEADER_ROW_HEIGHT

    for index, row_data in enumerate(rows, start=1):
        row_num = index + 1  # row 1 is the header
        for col_idx, value in enumerate(row_data, start=1):
            cell = sheet.cell(row=row_num, column=col_idx, value=value)
            cell.border = THIN_BORDER
            cell.alignment = LEFT_ALIGN if col_idx in left_align_cols else CENTER_ALIGN
            if index % 2 == 0:
                cell.fill = EVEN_FILL
        sheet.row_dimensions[row_num].height = DATA_ROW_HEIGHT

    if autofilter:
        last_col = openpyxl.utils.get_column_letter(len(columns))
        sheet.auto_filter.ref = f"A1:{last_col}{len(rows) + 1}"
    if freeze_header:
        sheet.freeze_panes = "A2"


def workbook_response(wb, filename: str) -> StreamingResponse:
    """Serialize a workbook to an .xlsx download."""
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
