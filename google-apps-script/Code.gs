/**
 * 安心股票簿 v4.2 - 研究資料跨裝置同步＋備份狀態
 * 建議：在一份 Google Sheet 內開啟「擴充功能 > Apps Script」後貼上此檔。
 */
const SYNC_TOKEN = 'CHANGE_ME_TO_A_LONG_RANDOM_KEY';
const SHEET_NAME = 'ResearchSync';
const CHUNK_SIZE = 28000;

function doGet(e) {
  try {
    checkToken_(e);
    const action = String((e && e.parameter && e.parameter.action) || 'load');
    const namespace = cleanNs_((e && e.parameter && e.parameter.namespace) || 'default');
    if (action !== 'load') return json_({ok:false,error:'Unsupported action'});
    const row = loadNamespace_(namespace);
    return json_({ok:true, namespace:namespace, data:row.data, updatedAt:row.updatedAt, deviceId:row.deviceId, chunks:row.chunks, bytes:row.bytes});
  } catch (err) {
    return json_({ok:false,error:String(err && err.message || err)});
  }
}

function doPost(e) {
  try {
    checkToken_(e);
    const action = String((e && e.parameter && e.parameter.action) || 'save');
    const namespace = cleanNs_((e && e.parameter && e.parameter.namespace) || 'default');
    if (action !== 'save') return json_({ok:false,error:'Unsupported action'});
    const body = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    if (!body.data || typeof body.data !== 'object') throw new Error('Missing data');
    const updatedAt = new Date().toISOString();
    saveNamespace_(namespace, body.data, updatedAt, String(body.deviceId || ''));
    return json_({ok:true,namespace:namespace,updatedAt:updatedAt,deviceId:String(body.deviceId || ''),bytes:JSON.stringify(body.data).length});
  } catch (err) {
    return json_({ok:false,error:String(err && err.message || err)});
  }
}

function checkToken_(e) {
  const token = String((e && e.parameter && e.parameter.token) || '');
  if (!SYNC_TOKEN || SYNC_TOKEN.indexOf('CHANGE_ME') === 0) throw new Error('請先在 Code.gs 設定 SYNC_TOKEN');
  if (token !== SYNC_TOKEN) throw new Error('同步金鑰錯誤');
}

function cleanNs_(s) {
  s = String(s || 'default').trim().replace(/[^a-zA-Z0-9._\-\u4e00-\u9fff]/g, '_');
  return s.slice(0, 80) || 'default';
}

function sheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) throw new Error('請將 Apps Script 綁定在 Google Sheet 上');
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(SHEET_NAME);
    sh.getRange(1,1,1,7).setValues([['namespace','updatedAt','deviceId','chunkIndex','chunkCount','payload','savedAt']]);
    sh.setFrozenRows(1);
  }
  return sh;
}

function loadNamespace_(namespace) {
  const sh = sheet_();
  const last = sh.getLastRow();
  if (last < 2) return {data:null,updatedAt:'',deviceId:'',chunks:0,bytes:0};
  const values = sh.getRange(2,1,last-1,7).getValues();
  const rows = values.filter(r => String(r[0]) === namespace).sort((a,b)=>Number(a[3])-Number(b[3]));
  if (!rows.length) return {data:null,updatedAt:'',deviceId:'',chunks:0,bytes:0};
  const text = rows.map(r=>String(r[5] || '')).join('');
  return {data:text ? JSON.parse(text) : null, updatedAt:String(rows[0][1] || ''), deviceId:String(rows[0][2] || ''), chunks:rows.length, bytes:text.length};
}

function saveNamespace_(namespace, data, updatedAt, deviceId) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const sh = sheet_();
    removeNamespaceRows_(sh, namespace);
    const text = JSON.stringify(data);
    const parts = [];
    for (let i=0;i<text.length;i+=CHUNK_SIZE) parts.push(text.slice(i,i+CHUNK_SIZE));
    if (!parts.length) parts.push('{}');
    const now = new Date();
    const rows = parts.map((part,i)=>[namespace,updatedAt,deviceId,i,parts.length,part,now]);
    sh.getRange(sh.getLastRow()+1,1,rows.length,7).setValues(rows);
  } finally {
    lock.releaseLock();
  }
}

function removeNamespaceRows_(sh, namespace) {
  const last = sh.getLastRow();
  if (last < 2) return;
  const vals = sh.getRange(2,1,last-1,1).getValues();
  for (let i=vals.length-1;i>=0;i--) {
    if (String(vals[i][0]) === namespace) sh.deleteRow(i+2);
  }
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
