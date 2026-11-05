// The real Office Script main runs against a small stateful workbook API sandbox.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class Range {
  constructor(sheet, row, col, rows, cols) { Object.assign(this, {sheet, row, col, rows, cols}); }
  getValues() { return Array.from({length:this.rows}, (_,r) => Array.from({length:this.cols}, (_,c) => this.sheet.cells[this.row+r]?.[this.col+c] ?? '')); }
  getRowIndex() { return this.row; }
  getColumnIndex() { return this.col; }
  getRowCount() { return this.rows; }
  getColumnCount() { return this.cols; }
  setValues(values) {
    assert.equal(values.length, this.rows);
    for (let r=0;r<this.rows;r++) {
      assert.equal(values[r].length, this.cols);
      const row = this.sheet.cells[this.row+r] ??= [];
      for(let c=0;c<this.cols;c++) row[this.col+c] = values[r][c];
    }
  }
  setNumberFormat(format) { this.sheet.formats.push(format); }
  clear() { this.sheet.cells = []; }
}
class Sheet {
  constructor(cells=[]) { this.cells = cells; this.formats=[]; }
  getUsedRange() { return this.cells.length ? new Range(this,0,0,this.cells.length,Math.max(...this.cells.map(r=>r.length))) : undefined; }
  getRangeByIndexes(...args) { return new Range(this,...args); }
}
function run(raw, min=0, max=20, existing={}) {
  const sheets = {Raw: new Sheet(raw), ...existing};
  const context = {book: {
    getWorksheet(name) { return sheets[name]; },
    addWorksheet(name) { assert.ok(!sheets[name]); return sheets[name]=new Sheet(); }
  }, min, max};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync('dist/clean.js','utf8')+'\nmain(book,min,max);',context);
  return sheets;
}
const raw = [[' dataset ', ' VALUE ', ' unit '], [' A ', '12.50',' MM '],['A','', 'mm'],['A','oops','mm'],['A',99,'mm'],['',1,'mm'],['A',0,'mm'],['A',20,'mm']];
test('main cleans types, retains rejects and writes hand-counted QA/QC totals', () => {
  const original = JSON.stringify(raw);
  const s=run(raw);
  assert.equal(JSON.stringify(raw),original);
  const rows=s.Cleaned.cells;
  assert.deepEqual(Array.from(rows[0]),['dataset','value','unit','source_row','flags']);
  assert.deepEqual(Array.from(rows[1]),['A',12.5,'mm',2,'OK']);
  assert.deepEqual(rows.slice(1).map(r=>r[4]),['OK','BLANK_VALUE','INVALID_NUMBER','OUT_OF_RANGE','BLANK_DATASET','OK','OK']);
  const summary=Object.fromEntries(s.QAQC.cells.slice(1));
  assert.equal(summary['Rows checked'],7);
  assert.equal(summary.Accepted,3);
  assert.equal(summary.Rejected,4);
  assert.equal(summary['Minimum (inclusive)'],0);
  assert.equal(summary['Maximum (inclusive)'],20);
});
test('reruns replace stale results without changing Raw', () => {
  const first=run(raw);
  const second=run([['dataset','value','unit'],['B','5','mm']],0,20,{Cleaned:first.Cleaned,QAQC:first.QAQC});
  assert.equal(second.Cleaned.cells.length,2);
  assert.equal(Object.fromEntries(second.QAQC.cells.slice(1)).Accepted,1);
});
test('bad bounds or ambiguous headers fail before changing outputs', () => {
  const output=new Sheet([['previous']]);
  for(const input of [[],[['dataset','value','VALUE','unit']],[['dataset','unit']], [['dataset','value','unit','extra']]]) {
    assert.throws(()=>run(input,0,20,{Cleaned:output}));
    assert.deepEqual(output.cells,[['previous']]);
  }
  assert.throws(()=>run(raw,20,0));
  assert.throws(()=>run(raw,NaN,20));
});
test('rejects booleans, partial numbers, infinities and decimal commas', () => {
  const s=run([['dataset','value','unit'],...['12bad','Infinity','0x10','12,5',true,'1e2'].map(v=>['A',v,'mm'])],0,100);
  assert.deepEqual(s.Cleaned.cells.slice(1).map(r=>r[4]),['INVALID_NUMBER','INVALID_NUMBER','INVALID_NUMBER','INVALID_NUMBER','INVALID_NUMBER','OK']);
});
test('formula-like strings are written to text-formatted output columns', () => {
  const s=run([['dataset','value','unit'],['=1+2','5','+mm']]);
  assert.ok(s.Cleaned.formats.some(format=>format==='@'));
  assert.equal(s.Cleaned.cells[1][0],"'=1+2");
  assert.equal(s.Cleaned.cells[1][2],"'+mm");
});
test('header-only tables produce zero counts', () => {
  const s=run([['dataset','value','unit']]);
  assert.equal(s.Cleaned.cells.length,1);
  assert.equal(Object.fromEntries(s.QAQC.cells.slice(1))['Rows checked'],0);
});
test('accepts reordered headers and records overlapping reasons', () => {
  const s=run([[' unit ', 'dataset','value'],['','', ''],[' MM ','A','1.5']]);
  assert.equal(s.Cleaned.cells[1][4],'BLANK_DATASET; BLANK_UNIT; BLANK_VALUE');
  assert.deepEqual(Array.from(s.Cleaned.cells[2]),['A',1.5,'mm',3,'OK']);
  const qa=Object.fromEntries(s.QAQC.cells.slice(1));
  assert.equal(qa.Rejected,1);
  assert.equal(qa['Blank units'],1);
});
test('refuses an oversized paste before reading values', () => {
  const sheet=new Sheet([['dataset','value','unit']]);
  sheet.getUsedRange=()=>({getRowIndex:()=>0,getColumnIndex:()=>0,getRowCount:()=>100002,getColumnCount:()=>3});
  assert.throws(()=>run([],0,20,{Raw:sheet}),/100,000/);
});
test('requires headers at A1', () => {
  const sheet=new Sheet([['dataset','value','unit']]);
  sheet.getUsedRange=()=>new Range(sheet,1,1,1,3);
  assert.throws(()=>run([],0,20,{Raw:sheet}),/A1/);
});
