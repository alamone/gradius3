"""リリース作成: 改造ROMと純正ROMから差分パッチ(BPS)を作り、docs/versions.json に版を追加する。
usage: python3 tools/release.py <版> <改造ROMフォルダ(945_313.f15 等4本)> <純正313メインのフォルダ> <MAME用 gradius3.zip(R版)> <notes.json>
notes.json: {"title": "...", "changes": [...], "verified": [...], "known": [...]}
※ リポジトリには純正ROMの中身は一切入らない（パッチは改造部分の差分のみ）。
"""
import sys, os, json, zipfile, zlib, datetime
sys.path.insert(0, os.path.dirname(__file__))
import bps

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ver, moddir, d313, setzip, notes = sys.argv[1:6]
crc = lambda b: '%08x' % zlib.crc32(b)
with zipfile.ZipFile(setzip) as z:
    setfiles = {n: z.read(n) for n in z.namelist() if not n.endswith('/')}
g313 = {'f15': open(os.path.join(d313, '945_313.f15'), 'rb').read(), 'e15': open(os.path.join(d313, '945_312.e15'), 'rb').read()}
mod = {n: open(os.path.join(moddir, n), 'rb').read() for n in ('945_313.f15', '945_312.e15', '945_m09.r17', '945_m08.n17')}
SND = '945_r05.d9'   # サウンドROM（改造したときだけ出力フォルダにある）
if os.path.exists(os.path.join(moddir, SND)): mod[SND] = open(os.path.join(moddir, SND), 'rb').read()
# 出力ファイル名(MAME gradius3) ← (改造ROM, 元にする純正ROM)
plan = {
    '945_r13.f15': (mod['945_313.f15'], g313['f15']),
    '945_r12.e15': (mod['945_312.e15'], g313['e15']),
    '945_m09.r17': (mod['945_m09.r17'], setfiles['945_m09.r17']),
    '945_m08.n17': (mod['945_m08.n17'], setfiles['945_m08.n17']),
}
if SND in mod: plan[SND] = (mod[SND], setfiles[SND])
outdir = os.path.join(REPO, 'docs', 'patches', ver); os.makedirs(outdir, exist_ok=True)
patches = {}
for name, (tgt, src) in plan.items():
    p = bps.create(src, tgt)
    assert bps.apply(src, p) == tgt
    fn = name.replace('.', '_') + '.bps'
    open(os.path.join(outdir, fn), 'wb').write(p)
    patches[name] = {'file': 'patches/%s/%s' % (ver, fn), 'source_crc': crc(src), 'target_crc': crc(tgt), 'size': len(p)}
    print(name, 'patch', len(p), 'bytes')
vj = os.path.join(REPO, 'docs', 'versions.json')
data = json.load(open(vj)) if os.path.exists(vj) else {'versions': []}
# 出力ROMセットの構成（ファイル名・中身のCRC）。改造4本以外は利用者の純正ファイルをそのまま使う
# サウンドROMは版によって改造したりしなかったりするので一覧に残す（ページ側でパッチのあるファイルは除く）
data['set'] = {'name': 'gradius3', 'files': [{'name': n, 'crc': crc(b), 'size': len(b)} for n, b in sorted(setfiles.items()) if n not in plan or n == SND]}
data['required'] = {'313main': {'945_313.f15': crc(g313['f15']), '945_312.e15': crc(g313['e15'])}}
n = json.load(open(notes))
# ビルド日時: 改造メインROMの起動画面の文字列（BUILD 年 月 日 時:分:秒）から読む
mm = bytes(x for p in zip(mod['945_313.f15'], mod['945_312.e15']) for x in p)
k = mm.find(b'BUILD@')
build = None
if k >= 0:
    t = mm[k + 6:mm.index(b'#', k)].decode().replace('@', ' ').replace('>', ':').split()
    build = '%s-%s-%s %s' % (t[0], t[1], t[2], t[3])      # 例 2026-10-20 22:21:45 (日本時間)
entry = {'version': ver, 'date': datetime.date.today().isoformat(), **({'build': build} if build else {}), **n, 'patches': patches}
data['versions'] = [v for v in data['versions'] if v['version'] != ver]
data['versions'].insert(0, entry)
# パッチを公開するのは最新と1つ前の版だけ。それより古い版はパッチを削除（更新履歴の説明は残す）
KEEP = 2
for v in data['versions'][KEEP:]:
    d = os.path.join(REPO, 'docs', 'patches', v['version'])
    if os.path.isdir(d):
        import shutil; shutil.rmtree(d); print('removed old patches', v['version'])
    v.pop('patches', None)
json.dump(data, open(vj, 'w'), ensure_ascii=False, indent=1)
print('versions.json updated:', ver)
