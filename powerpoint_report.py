"""Offline, editable PowerPoint reports from DistroFit's frozen analysis.

PresentationML and SpreadsheetML are Office's documented XML formats. Keeping
this writer local avoids macros, Office automation and a new runtime package.
"""
import argparse
from io import BytesIO
import math
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr
from zipfile import ZIP_DEFLATED, ZipFile

P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
C = 'http://schemas.openxmlformats.org/drawingml/2006/chart'
S = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
ROOT = f'xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}"'
EMU = 914400


def _x(value):
    # Reject illegal control characters rather than write a broken Office file.
    value = str(value)
    if any(ord(c) < 32 and c not in '\t\n\r' for c in value):
        raise ValueError('Text contains an XML control character')
    return escape(value)


def _rels(items):
    return ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + ''.join(f'<Relationship Id="rId{i}" Type="{R}/{kind}" Target={quoteattr(target)}/>'
                      for i, (kind, target) in enumerate(items, 1)) + '</Relationships>')


def _group():
    return ('<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
            '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>')


def _paragraph(value, size=2000, color='tx1', link=None):
    hyperlink = f'<a:hlinkClick r:id="rId{link}" action="ppaction://hlinksldjump"/>' if link else ''
    size_attribute = f' sz="{size}"' if size else ''
    return (f'<a:p><a:r><a:rPr lang="en-US"{size_attribute}><a:solidFill>'
            f'<a:schemeClr val="{color}"/></a:solidFill>{hyperlink}</a:rPr>'
            f'<a:t>{_x(value)}</a:t></a:r><a:endParaRPr lang="en-US"{size_attribute}/></a:p>')


def _box(identifier, name, value, x, y, w, h, size=2000, link=None, placeholder=None, inherit=False):
    geometry = (f'<a:xfrm><a:off x="{int(x*EMU)}" y="{int(y*EMU)}"/>'
                f'<a:ext cx="{int(w*EMU)}" cy="{int(h*EMU)}"/></a:xfrm>'
                '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>') if not inherit else ''
    ph = f'<p:ph type="{placeholder}" idx="{0 if placeholder == "title" else 1}"/>' if placeholder else ''
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{identifier}" name={quoteattr(name)} descr={quoteattr(name)}/>'
            f'<p:cNvSpPr txBox="1"/><p:nvPr>{ph}</p:nvPr></p:nvSpPr><p:spPr>'
            f'{geometry}</p:spPr>'
            '<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0"/>'
            '<a:lstStyle/>' + ''.join(_paragraph(line, None if inherit else size, 'accent1' if link else 'tx1', link)
                                      for line in str(value).split('\n')) + '</p:txBody></p:sp>')


def _chart_frame(chart_id, description):
    return (f'<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="8" name="Chart" descr={quoteattr(description)}/>'
            '<p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm>'
            f'<a:off x="{int(.7*EMU)}" y="{int(1.7*EMU)}"/><a:ext cx="{int(11.9*EMU)}" cy="{int(4.7*EMU)}"/>'
            '</p:xfrm><a:graphic><a:graphicData uri="' + C + '">'
            f'<c:chart xmlns:c="{C}" r:id="rId{chart_id}"/></a:graphicData></a:graphic></p:graphicFrame>')


def _table(rows):
    width = int(11.8*EMU)
    cols = [int(width*.46), width-int(width*.46)]
    body = ''
    for row in rows:
        body += f'<a:tr h="{int(.5*EMU)}">'
        for cell in row:
            body += ('<a:tc><a:txBody><a:bodyPr/><a:lstStyle/>' + _paragraph(cell, 2000)
                     + '</a:txBody><a:tcPr/></a:tc>')
        body += '</a:tr>'
    return ('<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="9" name="Fitted parameters"/>'
            '<p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm>'
            f'<a:off x="{int(.7*EMU)}" y="{int(2.2*EMU)}"/><a:ext cx="{width}" cy="{int(len(rows)*.5*EMU)}"/>'
            '</p:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">'
            '<a:tbl><a:tblPr firstRow="1" bandRow="1"/><a:tblGrid>'
            + ''.join(f'<a:gridCol w="{c}"/>' for c in cols) + '</a:tblGrid>' + body
            + '</a:tbl></a:graphicData></a:graphic></p:graphicFrame>')


class _Package:
    def __init__(self):
        self.parts = {}
        self.types = {}

    def add(self, path, content, kind=None):
        self.parts[path] = content.encode('utf-8') if isinstance(content, str) else content
        if kind:
            self.types[path] = kind

    def finish(self):
        defaults = ('<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                    '<Default Extension="xml" ContentType="application/xml"/>'
                    '<Default Extension="xlsx" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"/>')
        overrides = ''.join(f'<Override PartName="/{path}" ContentType="{kind}"/>' for path, kind in self.types.items())
        self.add('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                 + defaults + overrides + '</Types>')
        output = BytesIO()
        with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
            for name, data in self.parts.items():
                archive.writestr(name, data)
        return output.getvalue()


PPT_TYPE = 'application/vnd.openxmlformats-officedocument.presentationml.'


def _workbook(labels, series):
    book = _Package()
    book.add('_rels/.rels', _rels([('officeDocument', 'xl/workbook.xml')]))
    book.add('xl/workbook.xml', f'<workbook xmlns="{S}" xmlns:r="{R}"><sheets>'
             '<sheet name="Data" sheetId="1" r:id="rId1"/></sheets></workbook>',
             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml')
    book.add('xl/_rels/workbook.xml.rels', _rels([('worksheet', 'worksheets/sheet1.xml')]))
    rows = [['Candidate'] + [name for name, _ in series]]
    rows += [[label] + [values[i] for _, values in series] for i, label in enumerate(labels)]
    content = ''
    for i, row in enumerate(rows, 1):
        content += f'<row r="{i}">'
        for j, value in enumerate(row):
            ref = f'{chr(65+j)}{i}'
            content += (f'<c r="{ref}"><v>{value!r}</v></c>' if isinstance(value, (int, float)) else
                        f'<c r="{ref}" t="inlineStr"><is><t>{_x(value)}</t></is></c>')
        content += '</row>'
    book.add('xl/worksheets/sheet1.xml', f'<worksheet xmlns="{S}"><sheetData>{content}</sheetData></worksheet>',
             'application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml')
    return book.finish()


def _cache(tag, values):
    return (f'<c:{tag}><c:ptCount val="{len(values)}"/>' + ''.join(
        f'<c:pt idx="{i}"><c:v>{_x(v)}</c:v></c:pt>' for i, v in enumerate(values)) + f'</c:{tag}>')


def _chart(labels, series, percent=False):
    result = ''
    for i, (name, values) in enumerate(series):
        column = chr(66+i)
        result += (f'<c:ser><c:idx val="{i}"/><c:order val="{i}"/>'
                   f'<c:tx><c:strRef><c:f>Data!${column}$1</c:f>{_cache("strCache", [name])}</c:strRef></c:tx>'
                   '<c:spPr><a:solidFill><a:schemeClr val="accent' + str(i+1) + '"/></a:solidFill></c:spPr>'
                   f'<c:cat><c:strRef><c:f>Data!$A$2:$A${len(labels)+1}</c:f>'
                   + _cache('strCache', labels) + '</c:strRef></c:cat>'
                   f'<c:val><c:numRef><c:f>Data!${column}$2:${column}${len(labels)+1}</c:f>'
                   '<c:numCache><c:formatCode>General</c:formatCode>'
                   + _cache('numCache', values).replace('<c:numCache>', '').replace('</c:numCache>', '')
                   + '</c:numCache></c:numRef></c:val></c:ser>')
    numeric = [value for _, values in series for value in values]
    lower, upper = min(0., min(numeric)), max(0., max(numeric))
    if lower == upper:
        upper = lower + 1.
    axes = ('<c:catAx><c:axId val="1"/><c:scaling><c:orientation val="minMax"/></c:scaling>'
            '<c:axPos val="l"/><c:tickLblPos val="nextTo"/>'
            '<c:crossAx val="2"/><c:crosses val="autoZero"/><c:lblAlgn val="ctr"/><c:lblOffset val="100"/></c:catAx>'
            '<c:valAx><c:axId val="2"/><c:scaling><c:orientation val="minMax"/>'
            + ('<c:max val="1"/><c:min val="0"/>' if percent else
               f'<c:max val="{upper}"/><c:min val="{lower}"/>') + '</c:scaling>'
            '<c:axPos val="b"/><c:majorGridlines/>'
            f'<c:numFmt formatCode="{"0%" if percent else "0.00"}" sourceLinked="0"/>'
            '<c:tickLblPos val="nextTo"/><c:crossAx val="1"/><c:crosses val="autoZero"/>'
            '<c:crossBetween val="between"/></c:valAx>')
    return (f'<c:chartSpace xmlns:c="{C}" xmlns:a="{A}" xmlns:r="{R}"><c:lang val="en-US"/>'
            '<c:chart><c:autoTitleDeleted val="1"/><c:plotArea><c:layout/><c:barChart>'
            '<c:barDir val="bar"/><c:grouping val="clustered"/>'
            + result + '<c:gapWidth val="90"/><c:axId val="1"/><c:axId val="2"/></c:barChart>' + axes
            + '</c:plotArea><c:legend><c:legendPos val="b"/></c:legend><c:plotVisOnly val="1"/></c:chart>'
            f'<c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="{1200 if len(labels) > 8 else 1400}">'
            '<a:latin typeface="Arial"/></a:defRPr></a:pPr><a:endParaRPr lang="en-US"/></a:p></c:txPr>'
            '<c:externalData r:id="rId1"><c:autoUpdate val="0"/></c:externalData></c:chartSpace>')


def _theme():
    colors = [('dk1', '162D3D'), ('lt1', 'FFFFFF'), ('dk2', '304D5D'), ('lt2', 'F3F6F7'),
              ('accent1', '087F8C'), ('accent2', 'C77828'), ('accent3', '665899'),
              ('accent4', '3E7B54'), ('accent5', 'AF4545'), ('accent6', '607885'),
              ('hlink', '087F8C'), ('folHlink', '665899')]
    color_xml = ''.join(f'<a:{name}><a:srgbClr val="{color}"/></a:{name}>' for name, color in colors)
    font = ''.join(f'<a:{name}Font><a:latin typeface="Arial"/><a:ea typeface=""/>'
                   f'<a:cs typeface=""/></a:{name}Font>' for name in ('major', 'minor'))
    fill = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    line = '<a:ln w="12700">' + fill + '<a:prstDash val="solid"/></a:ln>'
    return (f'<a:theme xmlns:a="{A}" name="DistroFit"><a:themeElements>'
            '<a:clrScheme name="DistroFit">' + color_xml + '</a:clrScheme>'
            '<a:fontScheme name="DistroFit">' + font + '</a:fontScheme>'
            '<a:fmtScheme name="DistroFit"><a:fillStyleLst>' + fill*3 + '</a:fillStyleLst>'
            '<a:lnStyleLst>' + line*3 + '</a:lnStyleLst><a:effectStyleLst>'
            + '<a:effectStyle><a:effectLst/></a:effectStyle>'*3 + '</a:effectStyleLst>'
            '<a:bgFillStyleLst>' + fill*3 + '</a:bgFillStyleLst></a:fmtScheme>'
            '</a:themeElements></a:theme>')


COLOR_MAP = ('<p:clrMap accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" '
             'accent5="accent5" accent6="accent6" bg1="lt1" bg2="lt2" folHlink="folHlink" '
             'hlink="hlink" tx1="dk1" tx2="dk2"/>')


def _template(package):
    package.add('ppt/theme/theme1.xml', _theme(), 'application/vnd.openxmlformats-officedocument.theme+xml')
    layouts = ''.join(f'<p:sldLayoutId id="{2147483648+i}" r:id="rId{i+1}"/>' for i in range(1, 4))
    master = (f'<p:sldMaster {ROOT}><p:cSld><p:bg><p:bgPr><a:solidFill><a:schemeClr val="bg1"/>'
              '</a:solidFill><a:effectLst/></p:bgPr></p:bg><p:spTree>' + _group()
              + _box(2, 'DistroFit footer', 'DistroFit / frozen analysis', .7, 7.05, 8, .25, 1200)
              + '</p:spTree></p:cSld>' + COLOR_MAP + '<p:sldLayoutIdLst>' + layouts
              + '</p:sldLayoutIdLst><p:txStyles><p:titleStyle><a:lvl1pPr><a:defRPr sz="3200">'
              '<a:latin typeface="+mj-lt"/></a:defRPr></a:lvl1pPr></p:titleStyle>'
              '<p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>')
    package.add('ppt/slideMasters/slideMaster1.xml', master, PPT_TYPE+'slideMaster+xml')
    package.add('ppt/slideMasters/_rels/slideMaster1.xml.rels', _rels(
        [('theme', '../theme/theme1.xml')] + [('slideLayout', f'../slideLayouts/slideLayout{i}.xml') for i in range(1, 4)]))
    for i, name in enumerate(('Summary', 'Chart', 'Detail'), 1):
        package.add(f'ppt/slideLayouts/slideLayout{i}.xml',
                    f'<p:sldLayout {ROOT} type="obj" preserve="1"><p:cSld name="{name}"><p:spTree>'
                    + _group() + _box(2, 'Title', '', .7, .45, 11.9, .65, 3200, placeholder='title')
                    + '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>',
                    PPT_TYPE+'slideLayout+xml')
        package.add(f'ppt/slideLayouts/_rels/slideLayout{i}.xml.rels', _rels([('slideMaster', '../slideMasters/slideMaster1.xml')]))
    package.add('ppt/notesMasters/notesMaster1.xml',
                f'<p:notesMaster {ROOT}><p:cSld><p:spTree>' + _group() + '</p:spTree></p:cSld>'
                + COLOR_MAP + '<p:notesStyle/></p:notesMaster>', PPT_TYPE+'notesMaster+xml')
    package.add('ppt/notesMasters/_rels/notesMaster1.xml.rels', _rels([('theme', '../theme/theme1.xml')]))


def _finite(value):
    try:
        return math.isfinite(float(value))
    except (ValueError, TypeError):
        return False


def create_powerpoint(payload, title='DistroFit analysis'):
    """Return native PPTX bytes without refitting or including raw observations."""
    if not isinstance(title, str) or not title.strip() or len(title) > 80:
        raise ValueError('Use a nonempty title of at most 80 characters')
    # Measure with a bundled font and a conservative margin for Arial/viewer
    # differences. Reject an overwide title instead of silently shrinking it.
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextToPath
    width, _, _ = TextToPath().get_text_width_height_descent(
        title, FontProperties(family='DejaVu Sans', size=32), ismath=False)
    if '\n' in title or '\r' in title or width > 700:
        raise ValueError('The title is too wide for one line; shorten it')
    rows = payload['results']
    if len(rows) > 14:
        raise ValueError('At most 14 candidates are supported')
    finite = sorted([row for row in rows if _finite(row['Held-out NLL'])], key=lambda row: float(row['Held-out NLL']))
    excluded = [row['Distribution'] for row in rows if not _finite(row['Held-out NLL'])]
    count = len(rows)+4
    package = _Package()
    _template(package)
    package.add('_rels/.rels', _rels([('officeDocument', 'ppt/presentation.xml')]))
    presentation_rels = [('slideMaster', 'slideMasters/slideMaster1.xml'), ('notesMaster', 'notesMasters/notesMaster1.xml')]
    presentation_rels += [('slide', f'slides/slide{i}.xml') for i in range(1, count+1)]
    ids = ''.join(f'<p:sldId id="{255+i}" r:id="rId{i+2}"/>' for i in range(1, count+1))
    shows = ''
    for i, (name, indices) in enumerate([('Quick discussion', [1, 2, 3, count]), ('Full review', range(1, count+1))]):
        shows += (f'<p:custShow name="{name}" id="{i}"><p:sldLst>'
                  + ''.join(f'<p:sld r:id="rId{n+2}"/>' for n in indices) + '</p:sldLst></p:custShow>')
    package.add('ppt/presentation.xml', f'<p:presentation {ROOT}><p:sldMasterIdLst>'
                '<p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
                '<p:notesMasterIdLst><p:notesMasterId r:id="rId2"/></p:notesMasterIdLst>'
                '<p:sldIdLst>' + ids + '</p:sldIdLst><p:sldSz cx="12192000" cy="6858000" type="screen16x9"/>'
                '<p:notesSz cx="6858000" cy="9144000"/><p:custShowLst>' + shows + '</p:custShowLst></p:presentation>', PPT_TYPE+'presentation.main+xml')
    package.add('ppt/_rels/presentation.xml.rels', _rels(presentation_rels))

    settings = payload['settings']
    common_notes = (f"{payload['method']}\nSeed: {settings['seed']}. Held-out fraction: {settings['held_out_fraction']}. "
                    f"Histogram bins: {settings['bins']}. Filtering: {settings.get('outlier_method', 'not recorded')}. "
                    f"Removed observations: {settings.get('removed_count', 'not recorded')}. "
                    f"Package versions: {settings.get('versions', {})}.\n"
                    'Chart data are snapshots. Editing them in PowerPoint does not refit a model. '
                    'Raw observations are omitted. The PDF report is the full reproducibility record. '
                    'Manual adjustments and scenario results are omitted from this held-out comparison.\n'
                    f"Fit failures: {payload['failures']}")

    def slide(number, heading, body='', links=(), chart=None, table=None, notes=''):
        relations = [('slideLayout', f'../slideLayouts/slideLayout{1 if number == 1 else 2 if chart else 3}.xml'),
                     ('notesSlide', f'../notesSlides/notesSlide{number}.xml')]
        shapes = _group() + _box(2, 'Title', heading, .7, .45, 11.9, .65, 3200, placeholder='title', inherit=True)
        if body:
            shapes += _box(3, 'Analysis description', body, .7, 1.2, 11.9, 4.7 if not chart and not table else .5, 2000)
        if chart:
            identifier, labels, series, percent = chart
            relations.append(('chart', f'../charts/chart{identifier}.xml'))
            shapes += _chart_frame(len(relations), 'Expected and observed tail shares' if percent else 'Mean held-out negative log likelihood; lower is better')
            package.add(f'ppt/charts/chart{identifier}.xml', _chart(labels, series, percent), 'application/vnd.openxmlformats-officedocument.drawingml.chart+xml')
            package.add(f'ppt/charts/_rels/chart{identifier}.xml.rels', _rels([('package', f'../embeddings/data{identifier}.xlsx')]))
            package.add(f'ppt/embeddings/data{identifier}.xlsx', _workbook(labels, series))
        if table:
            shapes += _table(table)
        # Navigation occupies its own band below charts, never over chart labels.
        for index, (label, target) in enumerate(links):
            relations.append(('slide', f'slide{target}.xml'))
            shapes += _box(20+index, label, label, .7+(index % 3)*4.1,
                           6.55+(index//3)*.36, 4, .3, 1600, link=len(relations))
        package.add(f'ppt/slides/slide{number}.xml', f'<p:sld {ROOT}><p:cSld name={quoteattr(heading)}><p:spTree>'
                    + shapes + '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>', PPT_TYPE+'slide+xml')
        package.add(f'ppt/slides/_rels/slide{number}.xml.rels', _rels(relations))
        package.add(f'ppt/notesSlides/notesSlide{number}.xml', f'<p:notes {ROOT}><p:cSld><p:spTree>' + _group()
                    + _box(2, 'Presenter notes', common_notes+'\n'+notes, .5, 1, 6.5, 8, 1200, placeholder='body')
                    + '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>', PPT_TYPE+'notesSlide+xml')
        package.add(f'ppt/notesSlides/_rels/notesSlide{number}.xml.rels', _rels(
            [('notesMaster', '../notesMasters/notesMaster1.xml'), ('slide', f'../slides/slide{number}.xml')]))

    winner = (f"Lowest finite held-out loss: {finite[0]['Distribution']} ({float(finite[0]['Held-out NLL']):.4g})"
              if finite else 'No finite held-out winner')
    slide(1, title, f"{winner}\n\n{len(payload['train_indices'])} training / {len(payload['held_indices'])} held out\n\n"
          'I fitted curves on training measurements, then compared them on measurements set aside.\n\n'
          'A lower loss means a better predictive density on this split.\n'
          'One split cannot establish which curve describes the real process.',
          [('Compare scores', 2), ('Inspect tails', 3), ('Method and limits', count)])
    score_body = 'Mean held-out negative log likelihood (NLL). Lower is better.'
    if excluded:
        # The full list stays in notes. A short visible count avoids overflow.
        warning = ', '.join(excluded)
        score_body = 'Excluded from score chart: ' + (warning if len(warning) < 70 else f'{len(excluded)} nonfinite scores (see notes)')
    candidate_links = [('Summary', 1)] + ([('Candidate details', 4)] if rows else [])
    score_notes = 'Excluded scores: '+', '.join(excluded) if excluded else 'All held-out scores are finite.'
    slide(2, 'Held-out score comparison', score_body if finite else 'No finite scores to plot. See candidate details and method notes.',
          candidate_links, (1, [r['Distribution'] for r in finite], [('Held-out NLL (lower is better)', [float(r['Held-out NLL']) for r in finite])], False) if finite else None,
          notes=score_notes)
    slide(3, 'Observations above the training 95th percentile',
          'Model probability and held-out share. Flags are exploratory, not proof of a poor model.' if rows else 'No successful fits to compare.',
          [('Summary', 1)], (2, [r['Distribution'] for r in rows],
              [('Model probability', [float(r['Tail']['model_share']) for r in rows]),
               ('Held-out share', [float(r['Tail']['observed_share']) for r in rows])], True) if rows else None)
    for i, row in enumerate(rows, 4):
        params = row['Parameters']
        names = [f'Shape {n+1}' for n in range(len(params)-2)] + ['Location', 'Scale']
        table = [('Parameter', 'Training estimate')] + [(name, f'{float(value):.8g}') for name, value in zip(names, params)]
        table += [('Held-out NLL', f"{float(row['Held-out NLL']):.6g}"),
                  ('Exploratory tail flag', 'Flagged' if row['Tail']['flagged'] else 'Within prediction interval')]
        slide(i, row['Distribution'], 'Parameters stay fixed after training. Charts and tables are editable snapshots.',
              [('Summary', 1), ('Score comparison', 2), ('Next candidate' if i < count-1 else 'Method and limits', i+1)], table=table,
              notes=f"Tail check: {row['Tail']}. Training NLL: {row['Train NLL']}.")
    failure_names = ', '.join(payload['failures'])
    failures = f'{len(payload["failures"])} failed fits. Details are in presenter notes.' if len(failure_names) > 60 else f'Failed fits: {failure_names or "none"}.'
    slide(count, 'Method and limits',
          f"Random split seed: {settings['seed']}. Held-out share: {settings['held_out_fraction']:.0%}.\n\n"
          'Fitting uses training measurements only. Comparison uses held-out loss.\n'
          'The tail threshold comes from the training 95th percentile.\n\n'
          'Filtering can hide extreme values. Repeated tuning weakens this comparison.\n'
          'Time series and related measurements need a different validation design.\n\n'
          + failures + '\nDetailed settings and caveats are in presenter notes.', [('Summary', 1)])
    return package.finish()


def main(argv=None):
    parser = argparse.ArgumentParser(description='Export an editable PowerPoint analysis report')
    parser.add_argument('csv', nargs='?', type=Path)
    parser.add_argument('--sample', action='store_true', help='Use 240 synthetic Gamma observations')
    parser.add_argument('--column', help='Numeric CSV column name (required for CSV input)')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.sample == bool(args.csv):
        parser.error('Choose --sample or one CSV file')
    import numpy as np
    from analysis import fit_candidates, read_csv, prepare_data, report_payload
    try:
        if args.sample:
            data = np.random.default_rng(27).gamma(2, 2, 240)
        else:
            if not args.column:
                parser.error('--column is required for CSV input')
            with args.csv.open('rb') as source:
                data = read_csv(source)[args.column].to_numpy(dtype=float)
        clean, removed = prepare_data(data)
        payload = report_payload(fit_candidates(clean, ['Normal', 'Gamma', 'Exponential']), data,
                                 {'outlier_method': 'None', 'removed_count': removed})
        content = create_powerpoint(payload)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(content)
        print(f'Saved {len(payload["results"])+4} editable slides to {args.out}')
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
