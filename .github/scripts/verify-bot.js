// 検証ボット: Issue コメントのコマンドで「検証」Issue の状態・確認項目を更新する。
// .github/workflows/verify-bot.yml から actions/github-script で呼ばれる。
//
// コマンド（コメントの行頭に書く。1つのコメントに複数行書いてよい）
//   /claim                  担当する（未着手 → 担当中）
//   /check 番号 ok|ng|hold  確認項目に結果を付ける（hold = 人の目で確認が必要）
//   /done [ひとこと]        終わり。ng/hold/未チェックがあれば「要人間確認」、なければ「検証済み」
//   /human [ひとこと]       人の確認が必要なので「要人間確認」にする
//   /release                担当をやめて「未着手」に戻す
//   /items                  （管理者のみ）次の行からの箇条書きを確認項目として追加し、検証タスクにする

const L = { task: '検証', todo: '未着手', doing: '担当中', human: '要人間確認', done: '検証済み' };
const STATUS = [L.todo, L.doing, L.human, L.done];
const LABEL_DEFS = [
  { name: L.task, color: '1f6feb', description: '分担して検証する項目' },
  { name: L.todo, color: 'bfbfbf', description: '検証: まだ誰も担当していない' },
  { name: L.doing, color: 'd29922', description: '検証: 担当者が作業中' },
  { name: L.human, color: 'f85149', description: '検証: 人の目での確認が必要' },
  { name: L.done, color: '3fb950', description: '検証: 完了' },
];
const STALE_DAYS = 3;
const MARK = /<!-- verify-state (\{[^]*?\}) -->/;
const ITEM = /^(\s*)- \[( |x|X)\] (.*)$/;
const MARKS = { ok: '✅', ng: '❌', hold: '⚠️' };
const MARK_PREFIX = /^(✅|❌|⚠️) /;

function getState(body) {
  const m = (body || '').match(MARK);
  if (!m) return {};
  try { return JSON.parse(m[1]); } catch { return {}; }
}
function setState(body, st) {
  const clean = {};
  for (const [k, v] of Object.entries(st)) if (v !== undefined && v !== null) clean[k] = typeof v === 'string' ? v.replace(/--/g, '—').slice(0, 300) : v;
  const s = `<!-- verify-state ${JSON.stringify(clean)} -->`;
  body = body || '';
  return MARK.test(body) ? body.replace(MARK, s) : body.replace(/\s*$/, '') + '\n\n' + s + '\n';
}
function items(body) {
  const out = [];
  (body || '').split('\n').forEach((line, i) => {
    const m = line.match(ITEM);
    if (m) {
      const text = m[3];
      const mk = (text.match(MARK_PREFIX) || [])[1] || '';
      out.push({ line: i, checked: m[2] !== ' ', mark: mk, text: text.replace(MARK_PREFIX, '') });
    }
  });
  return out;
}
function checkItem(body, n, result) {
  const lines = body.split('\n');
  const list = items(body);
  const it = list[n - 1];
  if (!it) return null;
  const indent = lines[it.line].match(ITEM)[1];
  const box = result === 'hold' ? ' ' : 'x';
  lines[it.line] = `${indent}- [${box}] ${MARKS[result]} ${it.text}`;
  return lines.join('\n');
}
function summary(body) {
  const list = items(body);
  return {
    total: list.length,
    ok: list.filter(i => i.mark === '✅').length,
    ng: list.filter(i => i.mark === '❌').length,
    hold: list.filter(i => i.mark === '⚠️').length,
    open: list.filter(i => !i.checked && i.mark !== '⚠️').length,
  };
}
function parseCommands(text) {
  const lines = (text || '').split('\n');
  const cmds = [];
  lines.forEach((raw, i) => {
    const line = raw.trim();
    const m = line.match(/^\/(claim|check|done|human|release|items)\b\s*(.*)$/i);
    if (!m) return;
    const c = { name: m[1].toLowerCase(), arg: m[2].trim() };
    if (c.name === 'items') {
      const rest = [];
      for (let j = i + 1; j < lines.length; j++) {
        const t = lines[j].trim();
        if (t.startsWith('/')) break;
        const im = t.match(/^(?:[-*・]|\d+[.)])\s*(?:\[[ xX]\]\s*)?(.+)$/);
        if (im) rest.push(im[1].trim());
      }
      c.items = rest;
    }
    cmds.push(c);
  });
  return cmds;
}

module.exports = async ({ github, context, core }) => {
  const { owner, repo } = context.repo;
  const now = new Date().toISOString();

  async function ensureLabels() {
    for (const d of LABEL_DEFS) {
      try { await github.rest.issues.createLabel({ owner, repo, ...d }); }
      catch (e) { if (e.status === 422) { try { await github.rest.issues.updateLabel({ owner, repo, ...d }); } catch {} } else throw e; }
    }
  }
  async function setStatus(num, labels, status) {
    for (const l of STATUS) {
      if (l !== status && labels.includes(l)) {
        try { await github.rest.issues.removeLabel({ owner, repo, issue_number: num, name: l }); } catch {}
      }
    }
    const add = [status];
    if (!labels.includes(L.task)) add.push(L.task);
    await github.rest.issues.addLabels({ owner, repo, issue_number: num, labels: add });
  }
  const reply = (num, body) => github.rest.issues.createComment({ owner, repo, issue_number: num, body });
  const react = (id, content) => github.rest.reactions.createForIssueComment({ owner, repo, comment_id: id, content }).catch(() => {});

  const ev = context.eventName;

  if (ev === 'workflow_dispatch') { await ensureLabels(); core.info('labels ok'); }

  if (ev === 'schedule' || ev === 'workflow_dispatch') {
    const list = await github.paginate(github.rest.issues.listForRepo, { owner, repo, state: 'open', labels: L.doing, per_page: 100 });
    for (const is of list) {
      const st = getState(is.body);
      const last = Date.parse(st.updated_at || st.claimed_at || is.updated_at);
      if (Date.now() - last > STALE_DAYS * 86400e3) {
        const who = st.claimer;
        delete st.claimer; delete st.claimed_at; st.updated_at = now;
        await github.rest.issues.update({ owner, repo, issue_number: is.number, body: setState(is.body, st) });
        await setStatus(is.number, is.labels.map(l => l.name), L.todo);
        await reply(is.number, `${STALE_DAYS}日間報告がなかったので「未着手」に戻しました${who ? `（前の担当: @${who}）` : ''}。続ける場合はもう一度 \`/claim\` してください。`);
      }
    }
    return;
  }

  const issue = context.payload.issue;
  if (!issue || issue.pull_request) return;
  const num = issue.number;
  let labels = issue.labels.map(l => l.name);
  let body = issue.body || '';

  if (ev === 'issues') {
    // テンプレートから作られた / 「検証」ラベルが付いた → 未着手にして状態欄を用意
    if (!labels.includes(L.task)) return;
    if (!STATUS.some(s => labels.includes(s))) await setStatus(num, labels, L.todo);
    if (!MARK.test(body)) await github.rest.issues.update({ owner, repo, issue_number: num, body: setState(body, { created_at: now }) });
    return;
  }

  if (ev !== 'issue_comment') return;
  const c = context.payload.comment;
  const actor = c.user.login;
  if (c.user.type === 'Bot') return;
  const isAdmin = ['OWNER', 'MEMBER', 'COLLABORATOR'].includes(c.author_association);
  const cmds = parseCommands(c.body);
  if (!cmds.length) return;

  const st = getState(body);
  const errors = [];
  let status = STATUS.find(s => labels.includes(s)) || null;
  let changed = false;
  const canEdit = () => isAdmin || st.claimer === actor;

  for (const cmd of cmds) {
    if (cmd.name === 'items') {
      if (!isAdmin) { errors.push('`/items` は管理者だけが使えます'); continue; }
      if (!cmd.items.length) { errors.push('`/items` の次の行に「- 確認すること」の形で項目を書いてください'); continue; }
      const block = cmd.items.map(t => `- [ ] ${t}`).join('\n');
      if (/^### 確認項目\s*$/m.test(body)) {
        const ls = body.split('\n');
        let at = ls.findIndex(l => /^### 確認項目\s*$/.test(l)) + 1;
        while (at < ls.length && (ITEM.test(ls[at]) || ls[at].trim() === '')) at++;
        while (at > 0 && ls[at - 1].trim() === '') at--;
        ls.splice(at, 0, block);
        body = ls.join('\n');
      } else {
        body = body.replace(MARK, '').replace(/\s*$/, '') + `\n\n### 確認項目\n${block}\n`;
      }
      if (!status) status = L.todo;
      changed = true;
      continue;
    }
    if (!labels.includes(L.task) && status === null) { errors.push('このIssueはまだ検証タスクではありません（管理者が `/items` で項目を追加すると始められます）'); break; }

    if (cmd.name === 'claim') {
      if (status === L.doing && st.claimer && st.claimer !== actor) { errors.push(`すでに @${st.claimer} さんが担当中です。別の「未着手」を選んでください`); continue; }
      if (status === L.done) { errors.push('このIssueは「検証済み」です'); continue; }
      st.claimer = actor; st.claimed_at = now; status = L.doing; changed = true;
    } else if (cmd.name === 'check') {
      if (!canEdit()) { errors.push('`/check` は担当者（先に `/claim`）か管理者だけが使えます'); continue; }
      const m = cmd.arg.match(/^(\d+)\s+(ok|ng|hold)\b/i);
      if (!m) { errors.push(`\`/check ${cmd.arg}\` が読めません。例: \`/check 2 ok\``); continue; }
      const nb = checkItem(body, Number(m[1]), m[2].toLowerCase());
      if (nb === null) { errors.push(`確認項目 ${m[1]} 番はありません（全${items(body).length}件）`); continue; }
      body = nb; changed = true;
    } else if (cmd.name === 'done') {
      if (!canEdit()) { errors.push('`/done` は担当者か管理者だけが使えます'); continue; }
      const s = summary(body);
      status = (s.ng || s.hold || s.open) ? L.human : L.done;
      st.done_at = now; st.done_by = actor; if (cmd.arg) st.note = cmd.arg; changed = true;
    } else if (cmd.name === 'human') {
      if (!canEdit()) { errors.push('`/human` は担当者か管理者だけが使えます'); continue; }
      status = L.human; if (cmd.arg) st.note = cmd.arg; changed = true;
    } else if (cmd.name === 'release') {
      if (!canEdit()) { errors.push('`/release` は担当者か管理者だけが使えます'); continue; }
      delete st.claimer; delete st.claimed_at; status = L.todo; changed = true;
    }
  }

  if (changed) {
    st.updated_at = now;
    st.last_by = actor;
    st.last_comment = c.html_url;
    await github.rest.issues.update({ owner, repo, issue_number: num, body: setState(body, st) });
    if (status) await setStatus(num, labels, status);
  }
  if (errors.length) { await react(c.id, 'confused'); await reply(num, `@${actor} ` + errors.map(e => `- ${e}`).join('\n')); }
  else if (changed) await react(c.id, '+1');
};

module.exports._test = { getState, setState, items, checkItem, summary, parseCommands, L };
