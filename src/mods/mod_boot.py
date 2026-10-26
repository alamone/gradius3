"""起動時の RAM ROM CHECK 画面に、版とビルド日時の行を加える(改造ROMだとすぐ分かるように)。
文字列表(0x4c2 のポインタ → 0x52e)を、ROM合計調整域 0x3ffc0〜 に置いた新しい文字列に差し替える。
文字列の形式: [位置.w] 文字... '/'=次の[位置.w]へ '#'=終わり   (文字=タイル+0x30, '@'=空白)

表示する行: 「0 4 17  26 10 23 11:13」= 版（数字を空白区切り）・空白2つ・年(下2桁) 月 日 時:分（日本時間）
  - 版は環境変数 VERSION（例 0.4.17 / v0.4.17）。リリース用のビルドでは必ず指定する（tools/release.py が一致を確かめる）
  - 使う文字は数字・空白・コロンだけ（起動画面のフォントで確実に出るもの）
  - 0x3ffc0〜0x3fff0 の48バイトに収め、残りは ROM 合計の微調整に回す（行は25文字以内）
  - 古い版は「BUILD 2026 10 23 11:13:59」の形（tools/release.py は両方読める）"""
import struct, os, re, sys, datetime
BASE = 0x3ffc0
LIMIT = 0x3fff0
def version_digits(v=None):
    v = (v if v is not None else os.environ.get('VERSION', '')).strip().lstrip('vV')
    if not v:
        print('注意: VERSION が指定されていません（開発用ビルドとして 0 0 0 を書きます。リリースには使えません）', file=sys.stderr)
        return '0 0 0'
    if not re.fullmatch(r'\d+(\.\d+)*', v): raise SystemExit('VERSION は 0.4.17 のような数字と点だけで指定してください: %r' % v)
    return ' '.join(v.split('.'))
def text(version=None):
    t = os.environ.get('BUILDTIME')     # 例 "26 10 23 11:13"（指定するときはこの形）
    if not t:
        t = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%y %m %d %H:%M')
    return version_digits(version) + '  ' + t
def enc(s): return s.replace(' ', '@').replace(':', '>').encode()   # 起動画面のフォントでは '>' の位置にコロンがある
def blob(s=None):
    s = s or text()
    if not re.fullmatch(r'[0-9A-Z :]+', s): raise SystemExit('起動画面に出せない文字があります: %r' % s)
    b = struct.pack('>H', 0x081c) + enc('RAM ROM CHECK') + b'/'      # 純正と同じ位置(列26・行16)
    line = enc(s)
    col = 14 - (len(s) - 13) // 2                                    # RAM ROM CHECK の中央に合わせる
    b += struct.pack('>H', 0x0900 + 2 * col)                       # 2行下
    b += line + b'#'
    if len(b) % 2: b = b[:-1] + b'@#'
    if BASE + len(b) > LIMIT: raise SystemExit('起動画面の文字列が長すぎます（%dバイト、上限%d）: %r' % (len(b), LIMIT - BASE, s))
    return b
def apply(rom, s=None):
    b = blob(s)
    rom.put('main', BASE, b, 'bootstr')
    rom.put('main', 0x4c2, struct.pack('>I', BASE), 'bootptr', expect=struct.pack('>I', 0x52e))
    return BASE + len(b)
def read(main):
    """インターリーブ済みのメインROM（bytes）から、起動画面の行を読む。
    戻り値: {'version': '0.4.17' か None, 'build': '2026-10-23 11:13' など, 'raw': 表示どおりの文字列}。見つからなければ None"""
    k = main.find(enc('RAM ROM CHECK') + b'/')
    if k < 0: return None
    k += len('RAM ROM CHECK') + 1 + 2
    raw = main[k:main.index(b'#', k)].decode('latin-1').replace('@', ' ').replace('>', ':').strip()
    t = raw.split()
    if t and t[0] == 'BUILD' and len(t) >= 5:                        # 古い形: BUILD 2026 10 23 11:13:59
        return {'version': None, 'build': '%s-%s-%s %s' % (t[1], t[2], t[3], t[4]), 'raw': raw}
    m = re.fullmatch(r'([\d ]+?)  (\d\d) (\d\d) (\d\d) (\d\d:\d\d)', raw)
    if not m: return {'version': None, 'build': None, 'raw': raw}
    return {'version': '.'.join(m.group(1).split()), 'build': '20%s-%s-%s %s' % m.group(2, 3, 4, 5), 'raw': raw}

if __name__ == '__main__':   # 確認用: python3 mod_boot.py [版]  → 表示とバイト数
    s = text(sys.argv[1] if len(sys.argv) > 1 else None)
    b = blob(s)
    print(repr(s), len(s), '文字', len(b), 'バイト', '残り', LIMIT - BASE - len(b))
