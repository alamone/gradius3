/**
 * 配布ページのログイン申請: メール通知・ワンタップ承認・自動承認・管理画面（Google Apps Script・無料）
 *
 * Firestore
 *   users/{uid}        … 申請（本人が pending で作る。ルールは docs/dev/firebase/firestore.rules）
 *   admin_notes/{uid}  … 管理者だけのメモ（Twitter・コメント・決めた日時と方法・履歴）。ルールに無いのでページからは読めない
 *   admins/{email}     … 管理者（共同作業のまとめページを見られる人）。本人が自分の分だけ読める。管理画面で登録
 *
 * 動き
 *   - 5分ごとに users を見る（check）
 *       新しい pending → 自動承認の一覧にあれば即承認、なければ管理者に「承認する／却下する」リンク付きのメール
 *       approved になった → 本人に「見られるようになりました」
 *   - Web アプリ（自分だけが開ける）: 管理画面（申請者の一覧・承認・却下・Twitter・コメント・自動承認の一覧）と、メールのリンクの受け口
 *
 * Firebase は Spark（無料）のままでよい。使い方は tools/notify-gas/README.md。
 */

// ── 設定 ──────────────────────────────────────────
const PROJECT_ID = 'gradius3-login-41798';
const PAGE_URL = 'https://hknroms.github.io/gradius3/';      // 承認された人に知らせるページ
const SITE_NAME = 'グラディウスIII 改造ROM';
const ADMIN_EMAIL = '';            // 空なら、このスクリプトを動かしている Google アカウントのアドレスに送る
const CHECK_MINUTES = 5;           // 何分ごとに見るか（1, 5, 10, 15, 30 のどれか）
const NOTIFY_REJECTED = false;     // 却下したときに本人へ知らせるか
// ────────────────────────────────────────────────

const ST = { pending: '承認待ち', approved: '承認', rejected: '却下' };
const CONSOLE_URL = 'https://console.firebase.google.com/project/' + PROJECT_ID + '/firestore/databases/-default-/data/~2Fusers';
const DOCS = 'https://firestore.googleapis.com/v1/projects/' + PROJECT_ID + '/databases/(default)/documents/';

// ═══ 最初に1回 ═══

/** 定期実行を設定し、今の状態を覚える（今ある承認待ちは管理者に1通でまとめて知らせる） */
function setup() {
  ScriptApp.getProjectTriggers().forEach(t => { if (t.getHandlerFunction() === 'check') ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('check').timeBased().everyMinutes(CHECK_MINUTES).create();
  const p = PropertiesService.getScriptProperties();
  p.deleteProperty('seen'); p.deleteProperty('initialized');
  check();
  Logger.log('設定しました。' + CHECK_MINUTES + '分ごとに確認します。通知先: ' + adminEmail_() + ' / 管理画面: ' + (appUrl_() || '（まだデプロイしていない）'));
}

/** 試しに管理者へテストメールを送る */
function testMail() {
  MailApp.sendEmail({ to: adminEmail_(), subject: '【' + SITE_NAME + '】通知のテスト', name: SITE_NAME,
    body: '通知の設定ができています。\n\n管理画面: ' + (appUrl_() || '（Web アプリとしてデプロイすると、ここに URL が出ます）') });
  Logger.log('送りました: ' + adminEmail_());
}

// ═══ 定期実行 ═══

function check() {
  const lock = LockService.getScriptLock(); if (!lock.tryLock(20000)) return;
  try {
    const props = PropertiesService.getScriptProperties();
    const first = !props.getProperty('initialized');
    const seen = JSON.parse(props.getProperty('seen') || '{}');
    const allow = allowlist_();
    const newPending = [];
    listUsers_().forEach(u => {
      if (seen[u.uid] === u.status) return;
      const prev = seen[u.uid];
      seen[u.uid] = u.status;
      if (u.status === 'pending') {
        if (u.email && allow.indexOf(u.email.toLowerCase()) >= 0) { decide_(u, 'approved', '自動（一覧）'); seen[u.uid] = 'approved'; }
        else newPending.push(u);
      } else if (!first && prev !== undefined) {
        // 管理画面以外（Firebase の管理画面など）で変えられたもの
        noteDecision_(u.uid, u.status, '管理画面（Firebase）');
        if (u.status === 'approved') mailApproved_(u);
        if (u.status === 'rejected' && NOTIFY_REJECTED) mailRejected_(u);
      } else if (!first && prev === undefined && u.status === 'approved') {
        mailApproved_(u);
      }
    });
    if (newPending.length) mailPending_(newPending, first);
    props.setProperty('seen', JSON.stringify(seen));
    props.setProperty('initialized', '1');
  } finally { lock.releaseLock(); }
}

// ═══ Web アプリ（管理画面・メールのリンク） ═══

function doGet(e) {
  const p = (e && e.parameter) || {};
  if (p.a === 'approve' || p.a === 'reject') {
    // メールのリンクは「確かめる画面」を出すだけ（メールのリンク先を自動で開く仕組みで勝手に決まらないように、ボタンで決める）
    const u = getUser_(p.uid);
    if (!u) return page_('<div class="done">申請が見つかりませんでした。</div>');
    const verb = p.a === 'approve' ? '承認' : '却下', st = p.a === 'approve' ? 'approved' : 'rejected';
    if (u.status !== 'pending') return page_('<div class="done">' + esc_(u.name || u.email) + ' さんは、すでに「' + esc_(ST[u.status] || u.status) + '」です。</div><p><a href="' + appUrl_() + '">管理画面を開く</a></p>');
    return page_('<div class="done" id="box"><b>' + esc_(u.name || '(名前なし)') + '</b><br><span class="sub">' + esc_(u.email) + '<br>申請 ' + esc_(u.createdAt ? fmt_(u.createdAt) : '') + '</span>' +
      '<div class="row"><button class="' + (st === 'approved' ? 'ok' : 'ng') + '" id="go">' + verb + 'する</button></div></div>' +
      '<p><a href="' + appUrl_() + '">管理画面を開く</a></p>' +
      '<script>document.getElementById("go").onclick=function(){this.disabled=true;this.textContent="処理中…";' +
      'google.script.run.withSuccessHandler(function(){document.getElementById("box").innerHTML="' + verb + 'しました。' + (st === 'approved' ? '本人にメールを送りました。' : '') + '";})' +
      '.withFailureHandler(function(e){document.getElementById("box").textContent="エラー: "+e.message;}).apiDecide(' + JSON.stringify(u.uid) + ',"' + st + '");};</script>');
  }
  return page_(ADMIN_HTML);
}

/** 管理画面が読むデータ */
function apiData() {
  const users = listUsers_();
  const notes = listNotes_();
  const auth = authInfo_(users.map(u => u.uid));
  return {
    users: users.map(u => Object.assign({}, u, notes[u.uid] || {}, auth[u.uid] || {})),
    allowlist: autoList_().join('\n'),
    admins: adminList_().join('\n'),
    me: adminEmail_(), consoleUrl: CONSOLE_URL, pageUrl: PAGE_URL,
  };
}

function apiDecide(uid, status) {
  if (['approved', 'rejected', 'pending'].indexOf(status) < 0) throw new Error('status が違う');
  const u = getUser_(uid); if (!u) throw new Error('申請が見つかりません');
  if (u.status === status) return apiData();
  decide_(u, status, '管理画面（このページ）');
  return apiData();
}

function apiSaveNote(uid, twitter, comment) {
  twitter = String(twitter || '').trim().replace(/^https?:\/\/(www\.)?(twitter|x)\.com\//, '').replace(/^@/, '').replace(/[/?#].*$/, '');
  patchDoc_('admin_notes/' + uid, { twitter: twitter, comment: String(comment || '').slice(0, 5000), noteUpdatedAt: new Date() });
  return apiData();
}

function parseEmails_(text) { return Array.from(new Set(String(text || '').split(/[\s,;]+/).map(s => s.trim().toLowerCase()).filter(s => /^[^@\s]+@[^@\s]+$/.test(s)))); }

/** 管理者（まとめページを見られる人）を保存。Firestore の admins/{email} を作り直す。管理者は配布ページも自動で承認する */
function apiSaveAdmins(text) {
  const want = parseEmails_(text);
  const have = listDocs_('admins').map(d => d._id);
  want.filter(e => have.indexOf(e) < 0).forEach(e => patchDoc_('admins/' + e, { email: e, addedAt: new Date() }));
  have.filter(e => want.indexOf(e) < 0).forEach(e => req_('delete', DOCS + 'admins/' + encodeURIComponent(e)));
  PropertiesService.getScriptProperties().setProperty('admins', JSON.stringify(want));
  check();
  return apiData();
}

function apiSaveAllowlist(text) {
  const list = parseEmails_(text);
  PropertiesService.getScriptProperties().setProperty('allowlist', JSON.stringify(list));
  check();   // 一覧に入った承認待ちをすぐ通す
  return apiData();
}

// ═══ 決める・記録する・メール ═══

function decide_(u, status, method) {
  patchDoc_('users/' + u.uid, { status: status });
  noteDecision_(u.uid, status, method);
  const p = PropertiesService.getScriptProperties();
  const seen = JSON.parse(p.getProperty('seen') || '{}'); seen[u.uid] = status; p.setProperty('seen', JSON.stringify(seen));
  if (status === 'approved') mailApproved_(u);
  if (status === 'rejected' && NOTIFY_REJECTED) mailRejected_(u);
}

function noteDecision_(uid, status, method) {
  const old = getDoc_('admin_notes/' + uid) || {};
  const who = method.indexOf('自動') === 0 ? '自動' : (method.indexOf('Firebase') >= 0 ? '（Firebase の管理画面）' : adminEmail_());
  const line = fmt_(new Date()) + ' ' + (ST[status] || status) + '（' + method + '）';
  patchDoc_('admin_notes/' + uid, { decidedStatus: status, decidedAt: new Date(), decidedBy: who, decidedMethod: method,
    history: ((old.history ? old.history + '\n' : '') + line).slice(-4000) });
}

function adminEmail_() { return ADMIN_EMAIL || Session.getEffectiveUser().getEmail(); }
function appUrl_() { try { return ScriptApp.getService().getUrl() || ''; } catch (e) { return ''; } }

function mailPending_(list, first) {
  const url = appUrl_();
  const lines = list.map(u => '・' + (u.name || '(名前なし)') + ' <' + (u.email || '?') + '>' + (u.createdAt ? '  ' + fmt_(u.createdAt) : '') +
    (url ? '\n   承認する: ' + url + '?a=approve&uid=' + encodeURIComponent(u.uid) + '\n   却下する: ' + url + '?a=reject&uid=' + encodeURIComponent(u.uid) : ''));
  MailApp.sendEmail({
    to: adminEmail_(), name: SITE_NAME,
    subject: '【' + SITE_NAME + '】' + (first ? '承認待ちの申請が ' : '新しい申請が ') + list.length + ' 件あります',
    body: (first ? '通知を設定した時点で承認待ちの申請です。\n\n' : 'ログインの許可の申請がありました。\n\n') + lines.join('\n\n') +
      '\n\nリンクを開いて「承認する」（または「却下する」）を押すと決まります。承認すると本人にメールが届きます。\n' +
      (url ? '\n管理画面（一覧・Twitter・コメント）: ' + url : '\nFirebase の管理画面: ' + CONSOLE_URL)
  });
}

function mailApproved_(u) {
  if (!u.email) return;
  MailApp.sendEmail({ to: u.email, name: SITE_NAME, subject: '【' + SITE_NAME + '】ページを見られるようになりました',
    body: (u.name ? u.name + ' さん\n\n' : '') + '申請していただいたページへのログインを許可しました。\n次のページを開き、申請したときと同じ Google アカウントでログインしてください。\n\n' + PAGE_URL + '\n\n※ このメールは自動で送っています。' });
}

function mailRejected_(u) {
  if (!u.email) return;
  MailApp.sendEmail({ to: u.email, name: SITE_NAME, subject: '【' + SITE_NAME + '】申請について',
    body: (u.name ? u.name + ' さん\n\n' : '') + '申請していただいたページへのログインは、今回は見送らせていただきました。\n\n※ このメールは自動で送っています。' });
}

function autoList_() { return JSON.parse(PropertiesService.getScriptProperties().getProperty('allowlist') || '[]'); }
function adminList_() { return JSON.parse(PropertiesService.getScriptProperties().getProperty('admins') || '[]'); }
/** 自動で承認する人 = 自動承認の一覧 ＋ 管理者 */
function allowlist_() { return Array.from(new Set(autoList_().concat(adminList_()))); }

// ═══ Firestore（REST・持ち主の権限なのでルールに関係なく読み書きできる） ═══

function req_(method, url, body) {
  const o = { method: method, headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken(), 'x-goog-user-project': PROJECT_ID }, muteHttpExceptions: true, contentType: 'application/json' };
  if (body) o.payload = JSON.stringify(body);
  const r = UrlFetchApp.fetch(url, o);
  const c = r.getResponseCode();
  if (c === 404) return null;
  if (c >= 300) throw new Error('Firestore（' + c + '）: ' + r.getContentText().slice(0, 500));
  return JSON.parse(r.getContentText() || '{}');
}
function enc_(v) {
  if (v instanceof Date) return { timestampValue: v.toISOString() };
  if (typeof v === 'boolean') return { booleanValue: v };
  if (typeof v === 'number') return { integerValue: String(Math.round(v)) };
  return { stringValue: String(v == null ? '' : v) };
}
function dec_(f) {
  const o = {};
  Object.keys(f || {}).forEach(k => { const v = f[k]; o[k] = v.stringValue != null ? v.stringValue : v.timestampValue != null ? v.timestampValue : v.booleanValue != null ? v.booleanValue : v.integerValue != null ? Number(v.integerValue) : ''; });
  return o;
}
function patchDoc_(path, obj) {
  const fields = {}; Object.keys(obj).forEach(k => fields[k] = enc_(obj[k]));
  const mask = Object.keys(obj).map(k => 'updateMask.fieldPaths=' + encodeURIComponent(k)).join('&');
  return req_('patch', DOCS + path + '?' + mask, { fields: fields });
}
function getDoc_(path) { const d = req_('get', DOCS + path); return d ? dec_(d.fields) : null; }
function listDocs_(coll) {
  const out = []; let token = '';
  do {
    const d = req_('get', DOCS + coll + '?pageSize=300' + (token ? '&pageToken=' + encodeURIComponent(token) : '')) || {};
    (d.documents || []).forEach(x => out.push(Object.assign({ _id: x.name.split('/').pop() }, dec_(x.fields))));
    token = d.nextPageToken || '';
  } while (token);
  return out;
}
function listUsers_() { return listDocs_('users').map(u => ({ uid: u.uid || u._id, name: u.name || '', email: u.email || '', status: u.status || '', createdAt: u.createdAt || '' })); }
function getUser_(uid) { if (!uid) return null; const u = getDoc_('users/' + uid); return u ? { uid: u.uid || uid, name: u.name || '', email: u.email || '', status: u.status || '', createdAt: u.createdAt || '' } : null; }
function listNotes_() { const m = {}; listDocs_('admin_notes').forEach(n => { m[n._id] = n; delete n._id; }); return m; }

/** Firebase Authentication の情報（最後にログインした日時など）。読めなければ空 */
function authInfo_(uids) {
  const m = {};
  try {
    for (let i = 0; i < uids.length; i += 100) {
      const r = UrlFetchApp.fetch('https://identitytoolkit.googleapis.com/v1/projects/' + PROJECT_ID + '/accounts:lookup', {
        method: 'post', contentType: 'application/json', muteHttpExceptions: true,
        headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken(), 'x-goog-user-project': PROJECT_ID }, payload: JSON.stringify({ localId: uids.slice(i, i + 100) }) });
      if (r.getResponseCode() !== 200) break;
      (JSON.parse(r.getContentText()).users || []).forEach(a => {
        m[a.localId] = { lastLoginAt: a.lastLoginAt ? new Date(Number(a.lastLoginAt)).toISOString() : '', signedUpAt: a.createdAt ? new Date(Number(a.createdAt)).toISOString() : '',
          photoUrl: a.photoUrl || '', providers: (a.providerUserInfo || []).map(p => p.providerId).join(','), disabled: !!a.disabled };
      });
    }
  } catch (e) { /* 読めなくても管理画面は出す */ }
  return m;
}

function fmt_(iso) { return Utilities.formatDate(new Date(iso), 'Asia/Tokyo', 'yyyy-MM-dd HH:mm'); }
function esc_(s) { return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }

function page_(body) {
  return HtmlService.createHtmlOutput('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<style>' + CSS + '</style></head><body><main><h1>' + esc_(SITE_NAME) + ' — 申請の管理</h1>' + body + '</main></body></html>')
    .setTitle('申請の管理 — ' + SITE_NAME).addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

const CSS = `
:root{--bg:#0d1117;--panel:#161b22;--line:#30363d;--text:#e6edf3;--sub:#8b949e;--acc:#58a6ff;--ok:#3fb950;--ng:#f85149;--warn:#d29922}
@media (prefers-color-scheme: light){:root{--bg:#f6f8fa;--panel:#fff;--line:#d0d7de;--text:#1f2328;--sub:#59636e;--acc:#0969da;--ok:#1a7f37;--ng:#cf222e;--warn:#9a6700}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.6 system-ui,-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif}
main{max-width:860px;margin:0 auto;padding:20px 16px 60px}h1{font-size:19px;margin:0 0 10px}h2{font-size:16px;margin:22px 0 8px}
a{color:var(--acc)}.sub{color:var(--sub);font-size:13px}
.done{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px;font-size:16px}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}.tabs button{font:inherit;font-size:13.5px;padding:6px 12px;border-radius:99px;border:1px solid var(--line);background:var(--panel);color:var(--text)}
.tabs button.on{border-color:var(--acc);color:var(--acc);font-weight:600}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:10px 0}
.hd{display:flex;gap:10px;align-items:center}.hd img{width:36px;height:36px;border-radius:50%;flex:none;background:var(--line)}
.nm{font-weight:600;overflow-wrap:anywhere}.em{font-size:13px;color:var(--sub);overflow-wrap:anywhere}
.badge{display:inline-block;font-size:12px;padding:0 8px;border-radius:99px;border:1px solid currentColor;margin-left:6px}
.s-pending{color:var(--warn)}.s-approved{color:var(--ok)}.s-rejected{color:var(--ng)}
dl{display:grid;grid-template-columns:auto 1fr;gap:2px 12px;font-size:13px;margin:8px 0}dt{color:var(--sub)}dd{margin:0;overflow-wrap:anywhere}
label{display:block;font-size:12.5px;color:var(--sub);margin-top:8px}
input,textarea{font:inherit;font-size:15px;width:100%;padding:7px 9px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--text)}
textarea{min-height:70px;resize:vertical}
.row{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.row button{font:inherit;font-size:14px;padding:7px 14px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text)}
.ok{border-color:var(--ok)!important;color:var(--ok)!important}.ng{border-color:var(--ng)!important;color:var(--ng)!important}.pri{background:var(--acc)!important;border-color:var(--acc)!important;color:#fff!important}
.hist{white-space:pre-wrap;font-size:12px;color:var(--sub);margin-top:6px}
#msg{position:sticky;top:0;background:var(--acc);color:#fff;border-radius:8px;padding:6px 10px;font-size:13px;display:none}
`;

const ADMIN_HTML = `
<div id="msg"></div>
<div class="sub" id="top">読み込み中…</div>
<div class="tabs" id="tabs"></div>
<div id="list"></div>
<h2>管理者（共同作業のまとめページを見られる人）</h2>
<div class="card"><div class="sub">ここに入れた Google アカウントの人だけが「共同作業のまとめ」を開けます（1行に1つ）。管理者は配布ページも自動で承認されます。</div>
<textarea id="admins" style="min-height:90px" placeholder="example@gmail.com"></textarea>
<div class="row"><button class="pri" onclick="saveAdmins()">保存</button></div></div>
<h2>自動で承認する Google アカウント</h2>
<div class="card"><div class="sub">ここにあるアドレスの人が申請したら、すぐ承認して本人にメールします（1行に1つ）。</div>
<textarea id="allow" style="min-height:110px" placeholder="example@gmail.com"></textarea>
<div class="row"><button class="pri" onclick="saveAllow()">保存</button></div></div>
<p class="sub" id="links"></p>
<script>
const ST = {pending:'承認待ち', approved:'承認', rejected:'却下'};
let D = null, tab = 'pending';
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = s => { if (!s) return ''; const d = new Date(s); return isNaN(d) ? s : d.toLocaleString('ja-JP', {year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}); };
function msg(t){ const m=document.getElementById('msg'); m.textContent=t; m.style.display=t?'block':'none'; }
function call(fn, ...args){ msg('保存中…'); google.script.run.withSuccessHandler(d=>{ D=d; render(); msg('保存しました'); setTimeout(()=>msg(''),1500); }).withFailureHandler(e=>msg('エラー: '+e.message))[fn](...args); }
function load(){ google.script.run.withSuccessHandler(d=>{ D=d; render(); }).withFailureHandler(e=>{ document.getElementById('top').textContent='エラー: '+e.message; }).apiData(); }
function render(){
  const us = D.users.slice().sort((a,b)=>String(b.createdAt).localeCompare(String(a.createdAt)));
  const n = k => us.filter(u => k==='all' || u.status===k).length;
  document.getElementById('top').textContent = '申請 ' + us.length + ' 件（承認待ち ' + n('pending') + '）・通知先 ' + D.me;
  document.getElementById('tabs').innerHTML = [['pending','承認待ち'],['approved','承認'],['rejected','却下'],['all','すべて']].map(([k,l]) => '<button class="'+(k===tab?'on':'')+'" onclick="tab=\\''+k+'\\';render()">'+l+' '+n(k)+'</button>').join('');
  const list = us.filter(u => tab==='all' || u.status===tab);
  document.getElementById('list').innerHTML = list.length ? list.map(u => {
    const tw = u.twitter ? '<a href="https://x.com/'+encodeURIComponent(u.twitter)+'" target="_blank">@'+esc(u.twitter)+'</a>' : '';
    return '<div class="card"><div class="hd">'+(u.photoUrl?'<img src="'+esc(u.photoUrl)+'" referrerpolicy="no-referrer">':'')+
      '<div><div class="nm">'+esc(u.name||'(名前なし)')+'<span class="badge s-'+esc(u.status)+'">'+esc(ST[u.status]||u.status)+'</span></div><div class="em">'+esc(u.email)+'</div></div></div>'+
      '<dl><dt>申請</dt><dd>'+fmt(u.createdAt)+'</dd>'+
      (u.decidedAt?'<dt>決定</dt><dd>'+fmt(u.decidedAt)+'　'+esc(ST[u.decidedStatus]||u.decidedStatus||'')+'（'+esc(u.decidedMethod||'')+'・'+esc(u.decidedBy||'')+'）</dd>':'')+
      (u.lastLoginAt?'<dt>最後のログイン</dt><dd>'+fmt(u.lastLoginAt)+'</dd>':'')+
      (u.signedUpAt?'<dt>初めてのログイン</dt><dd>'+fmt(u.signedUpAt)+'</dd>':'')+
      (tw?'<dt>Twitter</dt><dd>'+tw+'</dd>':'')+
      '<dt>ID</dt><dd class="sub">'+esc(u.uid)+(u.disabled?'（無効）':'')+'</dd></dl>'+
      '<label>Twitter（X）のアカウント</label><input id="tw_'+esc(u.uid)+'" value="'+esc(u.twitter||'')+'" placeholder="@なし／URL でも可">'+
      '<label>コメント（自分だけが見られるメモ）</label><textarea id="cm_'+esc(u.uid)+'">'+esc(u.comment||'')+'</textarea>'+
      '<div class="row"><button class="pri" onclick="saveNote(\\''+esc(u.uid)+'\\')">メモを保存</button>'+
      (u.status!=='approved'?'<button class="ok" onclick="decide(\\''+esc(u.uid)+'\\',\\'approved\\')">承認する</button>':'')+
      (u.status!=='rejected'?'<button class="ng" onclick="decide(\\''+esc(u.uid)+'\\',\\'rejected\\')">却下する</button>':'')+
      (u.status!=='pending'?'<button onclick="decide(\\''+esc(u.uid)+'\\',\\'pending\\')">承認待ちに戻す</button>':'')+'</div>'+
      (u.history?'<div class="hist">'+esc(u.history)+'</div>':'')+'</div>';
  }).join('') : '<div class="sub">ありません</div>';
  const a = document.getElementById('allow'); if (document.activeElement !== a) a.value = D.allowlist;
  const ad = document.getElementById('admins'); if (document.activeElement !== ad) ad.value = D.admins;
  document.getElementById('links').innerHTML = '<a href="'+esc(D.pageUrl)+'" target="_blank">配布ページ</a>　<a href="'+esc(D.consoleUrl)+'" target="_blank">Firebase の管理画面</a>';
}
function saveNote(uid){ call('apiSaveNote', uid, document.getElementById('tw_'+uid).value, document.getElementById('cm_'+uid).value); }
function decide(uid, st){ if (st!=='pending' && !confirm((st==='approved'?'承認':'却下')+'しますか？'+(st==='approved'?'（本人にメールが届きます）':''))) return; call('apiDecide', uid, st); }
function saveAllow(){ call('apiSaveAllowlist', document.getElementById('allow').value); }
function saveAdmins(){ call('apiSaveAdmins', document.getElementById('admins').value); }
load();
</script>`;
