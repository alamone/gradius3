# CLAUDE.md — このリポジトリで作業する Claude への共通の決まり

グラディウスIII（KONAMI）の非公式改造パッチのリポジトリです。管理者は hknroms（作業用アカウント pikadrum）。
管理者本人のチャットでも、協力者のチャットでも、最初にこのファイルの内容に従ってください。返信は日本語で短く（相手はスマホのことが多い）。

## 0. ユーザー（管理者）の決まりごと

- 返事は必ず日本語で、短く。ユーザーは音声入力をよく使うので聞き間違いに注意（例:「歩いて」=「上げて」、「急ラッシュ」「石油ブラシ」=キューブラッシュ、「豆」「メーム」=MAME、「グラスリー」=gradius3）。
- **push の前にユーザーに確認するのは、配布ページ（docs/index.html・docs/versions.json・docs/patches/）に新しい版を公開するときだけ。** それ以外（ソース・手順書・まとめページ・STATUS.md など）は確認なしで commit・push してよい。
- 新しい版を公開したら、配布ページのリンク https://hknroms.github.io/gradius3/ を伝える。

## 0.5 記録はすべてこのリポジトリに置く（チャットに分散させない）

| 何を | どこに |
|---|---|
| いまの状態・次にやること・保留・決定事項 | [docs/dev/STATUS.md](docs/dev/STATUS.md) |
| メモリ番地・ROM の空き・ビルドとテストの方法 | [docs/dev/TECH.md](docs/dev/TECH.md) |
| 調べること・直すこと・頼むこと（1件ずつ） | GitHub の Issue（まとめページに出る） |
| リリースの説明文 | docs/dev/notes/<版>.json |
| 調査用スクリプト | src/lua/research/ |

- 会話を始めたら、この CLAUDE.md の次に **docs/dev/STATUS.md を読む**。
- 作業の節目（何かが分かった・決まった・終わった）ごとに STATUS.md・TECH.md を更新して push する。会話が途中で止まっても続きが分かるように、まとめて最後に書くのではなく、その都度書く。
- 引き継ぎ用のファイル（HANDOFF.md や zip）は作らない。チャットを替えるときは、新しい会話でこのリポジトリをつなぐだけでよい。

## 1. 何をする会話かで手順書を選ぶ

| 頼まれたこと | 読む手順書 |
|---|---|
| テストプレイの検証（「VERIFY.md に従って…」） | [VERIFY.md](VERIFY.md) |
| 調査・実装・素材・資料（「COLLAB.md に従って…」） | [COLLAB.md](COLLAB.md) |
| 管理者の改造・修正・リリース作業 | [docs/dev/STATUS.md](docs/dev/STATUS.md)・[docs/dev/TECH.md](docs/dev/TECH.md) と `src/` |

作業の担当・進み具合・提出物は Issue のコメントコマンドで記録する（一覧は `.github/scripts/task-bot.js` の先頭）。まとめページ：https://hknroms.github.io/gradius3/status.html

## 2. MAME はビルドしない（ビルド済みを使う）

gradius3 だけを入れた MAME（`g3`、0.289・SDL 同梱）のビルド済みを、このリポジトリの枝 **`mame-g3-bin`** に置いてある。**自分でビルドしないこと**（数十分かかるうえ、環境によっては失敗する）。

```bash
# 準備（その会話で1回だけ・数秒）
git clone -q --depth 1 -b mame-g3-bin https://github.com/hknroms/gradius3.git g3pkg
tar xzf g3pkg/g3-linux-x64.tar.gz -C "$HOME"
export G3="$HOME/g3/g3"     # ライブラリの場所と画面なしの設定はこのラッパーが自分でする
"$G3" -version              # 「0.289」と出れば OK
```

- 動かし方は `src/lua/run.sh`（`G3` 環境変数を見る）と `src/lua/g3run.lua` の先頭のコメント。画面・音なしで高速に回せる。
- 上の方法で取れない・動かない場合だけ、枝の `BUILD.md`（`tools/build_env.sh` も参考）の手順でビルドする。

## 3. ROM の扱い（必ず守る）

- ROM はこのリポジトリに**含まれていない**。作業に要る場合は、会話に添付された zip を使う（改造版は配布ページで作った `gradius3.zip`、純正は名前を変えて添付してもらう）。
- ROM の中身・ダンプ・RAM ダンプ・ステートセーブ・ROM から切り出した画像などを、**リポジトリ・フォーク・Issue・コメントなど公開の場所に置かない**。必要なら「再現するスクリプトと手順」を共有する。
- 添付ファイルは元を直接いじらず、作業用フォルダにコピーして使う。

## 4. 書き込みのルール

まず、この会話で連携している GitHub アカウントが gradius3 に書き込めるか（共同編集者か）で分かれる。

- **共同編集者（hknroms・pikadrum・招待された人）**：誰でも main に直接 push してよい。push の前に必ず `git fetch origin main` して最新に合わせる（rebase）。協力者の提出物（`/submit` のリンク先）は、取り寄せて中身を確かめてから取り込み、Issue に `/accept` か `/reject` を書く。
- **それ以外の協力者**：hknroms/gradius3 には push しない。書くのは Issue のコメントと、自分のフォーク（枝 `task-<Issue番号>`）だけ。

### リリース（パッチの公開）

- リリースできるのは **hknroms と pikadrum**（どちらの会話からでもよい）。
- 始める前に main を最新にし、`docs/versions.json` の最新の版を確かめて、その次の番号を付ける。
- **ビルドは必ず版を指定する**：`VERSION=0.4.17 python3 src/mods/build_all.py <出力>`。起動画面（RAM ROM CHECK の下）に「`0 4 17  26 10 26 10:12`」（版・年の下2桁 月 日 時:分）が入る。`tools/release.py` は ROM の版がリリースの版と違うと止まる。
- 版を書き込む前のビルド（「`BUILD 2026 10 23 11:13:59`」の形）は v0.4.16 まで。
- push が拒否された（先に誰かが push していた）ときは、**上書きしない**。最新を取り込み、`versions.json` を見直して、版番号がぶつかっていたら付け直してから、ビルド・パッチ作成をやり直す。
- 配布ページへの公開（docs/index.html・versions.json・patches の push）の前に、**ユーザーに確認する**。
- 終わったら、関係する Issue に版番号を書き（例「v0.4.17 で修正」）、STATUS.md を更新する。

## 5. チャットを替えるとき（引き継ぎ）

引き継ぎファイルは作らず、STATUS.md を最新にして push しておく（0.5 を参照）。
それでも要約を書くことになった場合（会話の自動要約など）は、**1行目に必ず次の文を書く**。

> この作業は GitHub の hknroms/gradius3 で行う。最初にこのリポジトリをつなぎ、CLAUDE.md と docs/dev/STATUS.md を読んでから続けること。

## 6. エミュレータで分かること・分からないこと

確かめられるのは CPU・RAM の動きと静止画まで。色の微妙さ・音・体感速度・ちらつきは「人の目で確認が必要」として扱い、断定しない。
