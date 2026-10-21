"""起動時の RAM ROM CHECK 画面に、ビルド日時の行を加える(改造ROMだとすぐ分かるように)。
文字列表(0x4c2 のポインタ → 0x52e)を、ROM合計調整域 0x3ffc0〜 に置いた新しい文字列に差し替える。
文字列の形式: [位置.w] 文字... '/'=次の[位置.w]へ '#'=終わり   (文字=タイル+0x30, '@'=空白)"""
import struct, os, datetime
BASE = 0x3ffc0
def text():
    t = os.environ.get('BUILDTIME')
    if not t:
        t = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y %m %d %H:%M:%S')
    return 'BUILD ' + t
def enc(s): return s.replace(' ', '@').replace(':', '>').encode()   # 起動画面のフォントでは '>' の位置にコロンがある
def blob(s=None):
    s = s or text()
    b = struct.pack('>H', 0x081c) + enc('RAM ROM CHECK') + b'/'      # 純正と同じ位置(列26・行16)
    line = enc(s)
    col = 14 - (len(s) - 13) // 2                                    # RAM ROM CHECK の中央に合わせる
    b += struct.pack('>H', 0x0900 + 2 * col)                       # 2行下
    b += line + b'#'
    if len(b) % 2: b = b[:-1] + b'@#'
    return b
def apply(rom, s=None):
    b = blob(s)
    rom.put('main', BASE, b, 'bootstr')
    rom.put('main', 0x4c2, struct.pack('>I', BASE), 'bootptr', expect=struct.pack('>I', 0x52e))
    return BASE + len(b)
