/**
 * 配布ページのログイン申請をメールで知らせる（Google Apps Script・無料）
 *
 * Firestore の users/{uid}（status: pending → approved）を5分ごとに見て、
 *   - 新しい pending  → 管理者に「申請がありました」
 *   - approved になった → 本人に「見られるようになりました」
 * をメールで送る。Firebase は Spark（無料）のままでよい（Cloud Functions を使わない）。
 * スクリプトを動かす Google アカウントが Firebase プロジェクトの持ち主なので、Firestore のルールに関係なく読める。
 *
 * 使い方は tools/notify-gas/README.md。最初に setup() を1回実行する。
 */

// ── 設定 ──────────────────────────────────────────
const PROJECT_ID = 'gradius3-login-41798';
const PAGE_URL = 'https://hknroms.github.io/gradius3/';      // 承認された人に知らせるページ
const SITE_NAME = 'グラディウスIII 改造ROM';
const ADMIN_EMAIL = '';            // 空なら、このスクリプトを動かしている Google アカウントのアドレスに送る
const APPROVED = ['approved'];     // 「承認」とみなす status の値
const CHECK_MINUTES = 5;           // 何分ごとに見るか（1, 5, 10, 15, 30 のどれか）
// ────────────────────────────────────────────────

const CONSOLE_URL = 'https://console.firebase.google.com/project/' + PROJECT_ID + '/firestore/databases/-default-/data/~2Fusers';

/** 最初に1回だけ実行: 定期実行を設定し、今の状態を覚える（今ある申請は管理者に1通でまとめて知らせる） */
function setup() {
  ScriptApp.getProjectTriggers().forEach(t => { if (t.getHandlerFunction() === 'check') ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('check').timeBased().everyMinutes(CHECK_MINUTES).create();
  PropertiesService.getScriptProperties().deleteAllProperties();
  check();
  Logger.log('設定しました。' + CHECK_MINUTES + '分ごとに確認します。通知先: ' + adminEmail_());
}

/** 試しに管理者へテストメールを送る */
function testMail() {
  MailApp.sendEmail({ to: adminEmail_(), subject: '【' + SITE_NAME + '】通知のテスト', name: SITE_NAME,
    body: 'ログイン申請の通知の設定ができています。\n\n申請の一覧（Firebase の管理画面）:\n' + CONSOLE_URL });
  Logger.log('送りました: ' + adminEmail_());
}

/** 定期実行の本体 */
function check() {
  const props = PropertiesService.getScriptProperties();
  const first = !props.getProperty('initialized');
  const seen = JSON.parse(props.getProperty('seen') || '{}');
  const users = listUsers_();
  const newPending = [];

  users.forEach(u => {
    if (seen[u.uid] === u.status) return;
    if (u.status === 'pending') newPending.push(u);
    else if (!first && APPROVED.indexOf(u.status) >= 0 && u.email) mailApproved_(u);
    seen[u.uid] = u.status;
  });
  if (newPending.length) mailPending_(newPending, first);

  props.setProperty('seen', JSON.stringify(seen));
  props.setProperty('initialized', '1');
}

function adminEmail_() { return ADMIN_EMAIL || Session.getEffectiveUser().getEmail(); }

function mailPending_(list, first) {
  const lines = list.map(u => '・' + (u.name || '(名前なし)') + ' <' + (u.email || '?') + '>' + (u.createdAt ? '  ' + fmt_(u.createdAt) : ''));
  MailApp.sendEmail({
    to: adminEmail_(),
    subject: '【' + SITE_NAME + '】' + (first ? '承認待ちの申請が ' : '新しい申請が ') + list.length + ' 件あります',
    name: SITE_NAME,
    body: (first ? '通知を設定した時点で承認待ちの申請です。\n\n' : 'ログインの許可の申請がありました。\n\n') + lines.join('\n') +
      '\n\n承認するときは、Firebase の管理画面で users の該当する人の status を「approved」に変えてください。' +
      '\n変えると、数分以内に本人へ「見られるようになりました」のメールが自動で届きます。\n\n' + CONSOLE_URL
  });
}

function mailApproved_(u) {
  MailApp.sendEmail({
    to: u.email,
    subject: '【' + SITE_NAME + '】ページを見られるようになりました',
    name: SITE_NAME,
    body: (u.name ? u.name + ' さん\n\n' : '') +
      '申請していただいたページへのログインを許可しました。\n次のページを開き、申請したときと同じ Google アカウントでログインしてください。\n\n' + PAGE_URL +
      '\n\n※ このメールは自動で送っています。'
  });
}

/** Firestore の users をすべて読む（REST API・持ち主の権限） */
function listUsers_() {
  const out = [];
  let token = '';
  do {
    const url = 'https://firestore.googleapis.com/v1/projects/' + PROJECT_ID + '/databases/(default)/documents/users?pageSize=300' +
      (token ? '&pageToken=' + encodeURIComponent(token) : '');
    const res = UrlFetchApp.fetch(url, { headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() }, muteHttpExceptions: true });
    if (res.getResponseCode() !== 200) throw new Error('Firestore を読めませんでした（' + res.getResponseCode() + '）: ' + res.getContentText().slice(0, 500));
    const data = JSON.parse(res.getContentText());
    (data.documents || []).forEach(d => {
      const f = d.fields || {};
      const v = k => f[k] ? (f[k].stringValue || f[k].timestampValue || '') : '';
      out.push({ uid: v('uid') || d.name.split('/').pop(), name: v('name'), email: v('email'), status: v('status'), createdAt: v('createdAt') });
    });
    token = data.nextPageToken || '';
  } while (token);
  return out;
}

function fmt_(iso) { return Utilities.formatDate(new Date(iso), 'Asia/Tokyo', 'yyyy-MM-dd HH:mm'); }
