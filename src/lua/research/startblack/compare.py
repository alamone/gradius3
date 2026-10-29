"""allareas.sh の出力を2つ（直す前・直した後）比べる。
usage: python3 compare.py <前> <後> [一覧の画像.png]
- START 表示（s1_2_040）: 黒くない画素の数（前・後）。エリア A（面の最初）は前と後で画面が同じか、
  ほかは後の地形・背景のパレット（$20〜$27・$30〜$37）がすべて 0 か
- プレイ（s1_5_060・300・600）: 画面が前と後で同じか（パレットRAMは、面で使わない色が前はメニューの名残り・後は 0 で
  違うことがある。純正の「死んで再開」も 0。違ったパレットの番号を参考に出す）
"""
import sys, os, glob
from PIL import Image
A, B = sys.argv[1], sys.argv[2]
def px(f): return Image.open(f).convert('RGB')
def nonblack(im): return sum(1 for p in im.getdata() if p != (0, 0, 0))
def key(d): s, a = os.path.basename(d).split('_'); return int(s), int(a)
rows = []; bad = 0
for d in sorted(glob.glob(B + '/*_*'), key=key):
    n = os.path.basename(d); o = os.path.join(A, n)
    s, a = key(d)
    st = 's1_2_040'
    if not os.path.exists(f'{d}/{st}.ppm') or not os.path.exists(f'{o}/{st}.ppm'):
        print(n, 'START の画像なし'); bad += 1; continue
    pal = open(f'{d}/{st}.pal', 'rb').read()
    if a == 1: zero = open(f'{o}/{st}.ppm', 'rb').read() == open(f'{d}/{st}.ppm', 'rb').read()
    else: zero = all(b == 0 for b in pal[0x400:0x500] + pal[0x600:0x700])
    nb_o, nb_n = nonblack(px(f'{o}/{st}.ppm')), nonblack(px(f'{d}/{st}.ppm'))
    same = []
    for t in ('060', '300', '600'):
        f1, f2 = f'{o}/s1_5_{t}', f'{d}/s1_5_{t}'
        if not os.path.exists(f2 + '.ppm'): same.append(t + ':なし'); continue
        eq = open(f1 + '.ppm', 'rb').read() == open(f2 + '.ppm', 'rb').read()
        p1, p2 = open(f1 + '.pal', 'rb').read(), open(f2 + '.pal', 'rb').read()
        pd = sorted(set(i // 32 for i in range(0, 4096, 2) if p1[i:i + 2] != p2[i:i + 2]))
        same.append(t + (':同じ' if eq else ':違う') + ('' if not pd or t != '600' else '(パレット ' + ','.join('$%x' % p for p in pd) + ')'))
        bad += not eq
    bad += not zero
    print(f'{s:2}面 エリア{a:2}  START 黒くない画素 前 {nb_o:6} → 後 {nb_n:6}  {"A:前と同じ" if a == 1 else "パレット0"}:{"OK" if zero else "NG"}  プレイ ' + ' '.join(same))
    rows.append((n, f'{o}/{st}.ppm', f'{d}/{st}.ppm'))
print('NG の数:', bad)
if len(sys.argv) > 3 and rows:
    w, h = px(rows[0][1]).size; w2, h2 = w // 2, h // 2; cols = 4
    sheet = Image.new('RGB', (cols * w2 * 2 + cols * 4, ((len(rows) + cols - 1) // cols) * h2))
    for i, (n, f1, f2) in enumerate(rows):
        x = (i % cols) * (w2 * 2 + 4); y = (i // cols) * h2
        sheet.paste(px(f1).resize((w2, h2)), (x, y)); sheet.paste(px(f2).resize((w2, h2)), (x + w2, y))
    sheet.save(sys.argv[3])
