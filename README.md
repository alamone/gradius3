# グラディウスIII 改造ROM パッチ（純正313ベース・非公式）

- 配布ページ（パッチ当て・更新履歴）: https://pikadrum.github.io/gradius3/
- このリポジトリには **ROMデータは含まれていません**。`docs/patches/` は純正ROMとの差分（BPS形式）だけです。
- お手持ちの純正ROM（MAME用 gradius3 一式＋313版メイン2本）を配布ページにドロップすると、MAMEの roms フォルダにそのまま入れられる `gradius3.zip` が作られます（処理はブラウザ内のみ）。

## 構成
| 場所 | 内容 |
|---|---|
| `docs/index.html` | パッチ当てページ（GitHub Pages） |
| `docs/versions.json` | 版ごとの変更点・確認項目・パッチ情報 |
| `docs/patches/<版>/` | BPSパッチ（改造4本分）。パッチの公開は最新と1つ前の版のみ（更新履歴は全版残す） |
| `src/` | 改造のソース（68000アセンブラ＋ビルドスクリプト） |
| `tools/bps.py` / `tools/release.py` | パッチ作成・リリース作成 |

## リリース手順（開発用）
```
python3 src/mods/build_all.py <出力>            # 改造ROMをビルド（純正ROMが必要）
python3 tools/release.py <版> <出力> <313メインのフォルダ> <gradius3.zip> notes.json
```

Gradius III は KONAMI の著作物です。本リポジトリは非公式の改造パッチで、純正ROMを所有する方の個人利用を目的としています。
