# グラディウスIII 改造ROM パッチ（純正313ベース・非公式）

- 配布ページ（パッチ当て・更新履歴）: https://hknroms.github.io/gradius3/
- このリポジトリには **ROMデータは含まれていません**。`docs/patches/` は純正ROMとの差分（BPS形式）だけです。
- お手持ちの純正ROM（MAME用 gradius3 一式＋313版メイン2本）を配布ページにドロップすると、MAMEの roms フォルダにそのまま入れられる `gradius3.zip` が作られます（処理はブラウザ内のみ）。

## 共同作業（検証・調査・実装・素材・資料）
- まとめページ（担当・進み具合・提出物・協力者一覧）: [https://hknroms.github.io/gradius3/status.html](https://hknroms.github.io/gradius3/status.html)
- 協力者の Claude 向け手順書: 検証は [`VERIFY.md`](VERIFY.md)、それ以外は [`COLLAB.md`](COLLAB.md)。共通の決まりは [`CLAUDE.md`](CLAUDE.md)
- 協力者は「hknroms/gradius3 の VERIFY.md（または COLLAB.md）に従って、未着手の作業を1件やって」と頼むだけ
- Issue コメントのコマンド（`/claim` `/check` `/submit` `/done` など）を `.github/workflows/task-bot.yml` が処理する

## 構成
| 場所 | 内容 |
|---|---|
| `docs/index.html` | パッチ当てページ（GitHub Pages） |
| `docs/status.html` | 共同作業のまとめページ |
| `docs/collaborators.json` | まとめページの協力者一覧に足す情報 |
| `docs/versions.json` | 版ごとの変更点・確認項目・パッチ情報 |
| `docs/patches/<版>/` | BPSパッチ（改造4本分）。パッチの公開は最新と1つ前の版のみ（更新履歴は全版残す） |
| `src/` | 改造のソース（68000アセンブラ＋ビルドスクリプト） |
| `tools/bps.py` / `tools/release.py` | パッチ作成・リリース作成 |

## リリース手順（開発用）
```
VERSION=<版> python3 src/mods/build_all.py <出力>   # 改造ROMをビルド（純正ROMが必要）。起動画面に版と日時が入る
python3 tools/release.py <版> <出力> <313メインのフォルダ> <gradius3.zip> notes.json
```

Gradius III は KONAMI の著作物です。本リポジトリは非公式の改造パッチで、純正ROMを所有する方の個人利用を目的としています。
