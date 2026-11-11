"""Native Excel PivotTable and PivotChart parts for a workbook written by xlsxwriter.

xlsxwriter cannot write pivot tables, so this module adds the standard SpreadsheetML
parts after the workbook is saved: a pivot cache holding the source rows, the pivot
definition, and a link from a chart to that pivot. Excel refreshes the pivot when the
file opens. The rendered cells are written by the caller with ``count_grid``.
"""
from io import BytesIO
import re
from xml.sax.saxutils import escape, quoteattr
import zipfile

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
RELNS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CONTENT = "application/vnd.openxmlformats-officedocument.spreadsheetml."
GRAND = "Grand Total"


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _column(index):
    """Zero-based column index to an Excel letter, for example 0 -> A."""
    letters = ""
    index += 1
    while index:
        index, rest = divmod(index - 1, 26)
        letters = chr(65 + rest) + letters
    return letters


def count_grid(records, row_field, col_field, row_order, col_order, *,
               data_caption, row_caption, col_caption):
    """Rendered tabular layout of a count pivot: row and column items plus totals."""
    counts = {(r[row_field], r[col_field]): 0 for r in records}
    for record in records:
        counts[(record[row_field], record[col_field])] += 1
    grid = [[data_caption, col_caption] + [None] * (len(col_order) + 1),
            [row_caption] + list(col_order) + [GRAND]]
    for row_item in row_order:
        cells = [counts.get((row_item, col), 0) for col in col_order]
        grid.append([row_item] + cells + [sum(cells)])
    totals = [sum(counts.get((row, col), 0) for row in row_order) for col in col_order]
    grid.append([GRAND] + totals + [sum(totals)])
    return grid


def _cache_fields(headers, records, row_field, col_field, row_order, col_order):
    fields, shared = [], {}
    for index, name in enumerate(headers):
        values = [record[index] for record in records]
        if values and all(_is_number(v) for v in values):
            integer = all(isinstance(v, int) for v in values)
            integer_flag = ' containsInteger="1"' if integer else ""
            attrs = (f' containsSemiMixedTypes="0" containsString="0" containsNumber="1"{integer_flag}'
                     f' minValue="{min(values)!r}" maxValue="{max(values)!r}"')
            fields.append(f'<cacheField name={quoteattr(name)} numFmtId="0"><sharedItems{attrs}/></cacheField>')
            continue
        if index == row_field:
            items = list(row_order)
        elif index == col_field:
            items = list(col_order)
        else:
            items = list(dict.fromkeys(values))
        if not set(values) <= set(items):
            raise ValueError(f"Pivot field {name!r} has values outside its item order.")
        shared[index] = {item: i for i, item in enumerate(items)}
        listing = "".join(f"<s v={quoteattr(str(item))}/>" for item in items)
        fields.append(f'<cacheField name={quoteattr(name)} numFmtId="0">'
                      f'<sharedItems count="{len(items)}">{listing}</sharedItems></cacheField>')
    return fields, shared


def _cache_definition(headers, records, source_sheet, source_ref, fields):
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<pivotCacheDefinition xmlns="{MAIN}" xmlns:r="{RELNS}" r:id="rId1" refreshOnLoad="1" '
            f'createdVersion="6" refreshedVersion="6" minRefreshableVersion="3" recordCount="{len(records)}">'
            f'<cacheSource type="worksheet"><worksheetSource ref="{source_ref}" sheet={quoteattr(source_sheet)}/>'
            f'</cacheSource><cacheFields count="{len(fields)}">{"".join(fields)}</cacheFields>'
            f'</pivotCacheDefinition>')


def _records(records, shared):
    rows = []
    for record in records:
        cells = []
        for index, value in enumerate(record):
            if index in shared:
                cells.append(f'<x v="{shared[index][value]}"/>')
            else:
                cells.append(f'<n v="{value!r}"/>' if isinstance(value, float) else f'<n v="{value}"/>')
        rows.append("<r>" + "".join(cells) + "</r>")
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<pivotCacheRecords xmlns="{MAIN}" xmlns:r="{RELNS}" count="{len(records)}">'
            f'{"".join(rows)}</pivotCacheRecords>')


def _axis_field(items):
    listing = "".join(f'<item x="{i}"/>' for i in range(len(items)))
    return (f'<pivotField axis="{{axis}}" compact="0" outline="0" showAll="0">'
            f'<items count="{len(items) + 1}">{listing}<item t="default"/></items></pivotField>')


def _pivot_definition(name, headers, row_field, col_field, data_field, row_items, col_items,
                      location, data_caption, row_caption, col_caption):
    fields = []
    for index in range(len(headers)):
        if index == row_field:
            fields.append(_axis_field(row_items).replace("{axis}", "axisRow"))
        elif index == col_field:
            fields.append(_axis_field(col_items).replace("{axis}", "axisCol"))
        elif index == data_field:
            fields.append('<pivotField dataField="1" showAll="0"/>')
        else:
            fields.append('<pivotField showAll="0"/>')

    def items(count):
        body = ['<i><x/></i>'] + [f'<i><x v="{i}"/></i>' for i in range(1, count)]
        return f'{"".join(body)}<i t="grand"><x/></i>'

    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<pivotTableDefinition xmlns="{MAIN}" name={quoteattr(name)} cacheId="1" '
            f'applyNumberFormats="0" applyBorderFormats="0" applyFontFormats="0" applyPatternFormats="0" '
            f'applyAlignmentFormats="0" applyWidthHeightFormats="1" dataCaption="Values" '
            f'updatedVersion="6" minRefreshableVersion="3" useAutoFormatting="1" itemPrintTitles="1" '
            f'createdVersion="6" indent="0" outline="1" outlineData="1" compact="0" compactData="0" '
            f'multipleFieldFilters="0" rowHeaderCaption={quoteattr(row_caption)} '
            f'colHeaderCaption={quoteattr(col_caption)}>'
            f'<location ref="{location}" firstHeaderRow="1" firstDataRow="2" firstDataCol="1"/>'
            f'<pivotFields count="{len(headers)}">{"".join(fields)}</pivotFields>'
            f'<rowFields count="1"><field x="{row_field}"/></rowFields>'
            f'<rowItems count="{len(row_items) + 1}">{items(len(row_items))}</rowItems>'
            f'<colFields count="1"><field x="{col_field}"/></colFields>'
            f'<colItems count="{len(col_items) + 1}">{items(len(col_items))}</colItems>'
            f'<dataFields count="1"><dataField name={quoteattr(data_caption)} fld="{data_field}" '
            f'subtotal="count" baseField="0" baseItem="0"/></dataFields>'
            f'<pivotTableStyleInfo name="PivotStyleMedium2" showRowHeaders="1" showColHeaders="1" '
            f'showRowStripes="0" showColStripes="0" showLastColumn="1"/>'
            f'</pivotTableDefinition>')


def _relationships(entries):
    body = "".join(f'<Relationship Id="{i}" Type="{RELNS}/{t}" Target="{target}"/>'
                   for i, t, target in entries)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{body}</Relationships>')


def add_count_pivot(xlsx, *, source_sheet, header_row, headers, records, row_field, col_field,
                    row_order, col_order, pivot_sheet_part, pivot_name, top_row, data_caption,
                    row_caption, col_caption, data_field=0):
    """Return workbook bytes with a native count PivotTable over ``records``.

    ``records`` are rows aligned to ``headers`` that start at ``header_row`` (1-based) on
    ``source_sheet``. Text fields used on an axis must be listed in ``row_order``/``col_order``
    in display order; every observed value has to appear there.
    The pivot's rendered cells, from ``count_grid``, must start at ``top_row`` on the pivot sheet.
    """
    if not records or not row_order or not col_order:
        raise ValueError("A pivot needs records and at least one row and column item.")
    last_row = header_row + len(records)
    source_ref = f"A{header_row}:{_column(len(headers) - 1)}{last_row}"
    fields, shared = _cache_fields(headers, records, row_field, col_field, row_order, col_order)
    grid_rows = 2 + len(row_order) + 1
    grid_cols = 1 + len(col_order) + 1
    location = f"A{top_row}:{_column(grid_cols - 1)}{top_row + grid_rows - 1}"
    definition = _pivot_definition(pivot_name, headers, row_field, col_field, data_field,
                                   row_order, col_order, location, data_caption, row_caption, col_caption)
    parts = {
        "xl/pivotCache/pivotCacheDefinition1.xml": _cache_definition(headers, records, source_sheet, source_ref, fields),
        "xl/pivotCache/_rels/pivotCacheDefinition1.xml.rels": _relationships(
            [("rId1", "pivotCacheRecords", "pivotCacheRecords1.xml")]),
        "xl/pivotCache/pivotCacheRecords1.xml": _records(records, shared),
        "xl/pivotTables/pivotTable1.xml": definition,
        "xl/pivotTables/_rels/pivotTable1.xml.rels": _relationships(
            [("rId1", "pivotCacheDefinition", "../pivotCache/pivotCacheDefinition1.xml")]),
    }
    return _rewrite(xlsx, parts, pivot_sheet_part=pivot_sheet_part)


def _rewrite(xlsx, parts, *, pivot_sheet_part):
    source = zipfile.ZipFile(BytesIO(xlsx))
    output = BytesIO()
    folder, leaf = pivot_sheet_part.rsplit("/", 1)
    pivot_rels = f"{folder}/_rels/{leaf}.rels"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
        for item in source.infolist():
            data = source.read(item.filename)
            text = data.decode("utf-8") if item.filename.endswith((".xml", ".rels")) else None
            if item.filename == "[Content_Types].xml":
                overrides = {"/xl/pivotCache/pivotCacheDefinition1.xml": CONTENT + "pivotCacheDefinition+xml",
                             "/xl/pivotCache/pivotCacheRecords1.xml": CONTENT + "pivotCacheRecords+xml",
                             "/xl/pivotTables/pivotTable1.xml": CONTENT + "pivotTable+xml"}
                addition = "".join(f'<Override PartName="{p}" ContentType="{t}"/>' for p, t in overrides.items())
                data = text.replace("</Types>", addition + "</Types>").encode("utf-8")
            elif item.filename == "xl/workbook.xml":
                if not re.search(r"<calcPr[^>]*/>", text):
                    raise ValueError("Workbook has no calcPr element to anchor pivot caches.")
                text = re.sub(r"(<calcPr[^>]*/>)", r'\1<pivotCaches><pivotCache cacheId="1" r:id="rIdPivotCache1"/></pivotCaches>',
                              text, count=1)
                data = text.encode("utf-8")
            elif item.filename == "xl/_rels/workbook.xml.rels":
                addition = (f'<Relationship Id="rIdPivotCache1" Type="{RELNS}/pivotCacheDefinition" '
                            f'Target="pivotCache/pivotCacheDefinition1.xml"/>')
                data = text.replace("</Relationships>", addition + "</Relationships>").encode("utf-8")
            elif item.filename == pivot_rels:
                addition = (f'<Relationship Id="rIdPivotTable1" Type="{RELNS}/pivotTable" '
                            f'Target="../pivotTables/pivotTable1.xml"/>')
                data = text.replace("</Relationships>", addition + "</Relationships>").encode("utf-8")
            target.writestr(item, data)
        if pivot_rels not in source.namelist():
            target.writestr(pivot_rels, _relationships([("rIdPivotTable1", "pivotTable", "../pivotTables/pivotTable1.xml")]))
        for name, text in parts.items():
            target.writestr(name, text.encode("utf-8"))
    return output.getvalue()


def add_pivot_chart_link(xlsx, *, pivot_name, pivot_sheet, file_name):
    """Mark the chart that plots ``pivot_sheet`` as a PivotChart linked to ``pivot_name``."""
    source = zipfile.ZipFile(BytesIO(xlsx))
    output = BytesIO()
    linked = 0
    link = (f'<c:pivotSource><c:name>[{escape(file_name)}]{escape(pivot_sheet)}!{escape(pivot_name)}'
            f'</c:name><c:fmtId val="0"/></c:pivotSource>')
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
        for item in source.infolist():
            data = source.read(item.filename)
            text = data.decode("utf-8") if item.filename.startswith("xl/charts/chart") else ""
            if f"{pivot_sheet}!" in text:
                if "<c:chart>" not in text:
                    raise ValueError("Chart XML has no chart element to link.")
                data = text.replace("<c:chart>", link + "<c:chart>", 1).encode("utf-8")
                linked += 1
            target.writestr(item, data)
    if linked != 1:
        raise ValueError(f"Expected exactly one chart on {pivot_sheet}, found {linked}.")
    return output.getvalue()
