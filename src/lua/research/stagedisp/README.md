# STAGE DISP（#30）の確かめ方

`../dig/menu_start.sh` でメニューから始め、ポーズ（START 長押し）→ 下4回で STAGE DISP → 右で ON → START で再開。
スナップの上の段（y 0〜23）の右側に `L1 S3 AH SP0` が出て、HI は残る。

```bash
R=<リポジトリ>/src/lua/research/dig
ON="2400:START:70,2500:D:8,2520:D:8,2540:D:8,2560:D:8,2600:R:8,2650:START:6"
OFF="3000:START:70,3100:D:8,3120:D:8,3140:D:8,3160:D:8,3200:R:8,3250:START:6"
NOFIRE=1 HOLDX="$ON,$OFF" $R/menu_start.sh <romフォルダ> off 3 8 0 3500 2900:3500:300      # ON → OFF で 2P のスコアが戻る
NOFIRE=1 HOLDX="$ON,2800:B1:6" XP=",1700:103f09:3" $R/menu_start.sh <romフォルダ> lp 5 3 0 3000 2700:3000:300   # L3 S5 AC → SP1
NOINV=1 HOLDX="$ON" $R/menu_start.sh <romフォルダ> die 3 8 0 6000 2700:6000:150           # 死んで再開しても AH のまま
NOFIRE=1 HOLDX="$ON" $R/menu_start.sh <romフォルダ> st4 4 1 0 6000 2700:6000:500          # 4面で出る・5面に変わると S5 AA
```

- 対照: 同じ入力で STAGE DISP を ON にしないとき（`HOLDX` の R を抜く）は `2P 0` のまま。
- 通常プレイ（メニューを出さずに START）は v0.4.17 と画面が1ピクセルも変わらない（1面・900〜7500フレームの100フレームごと67枚で比較）。
