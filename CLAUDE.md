# CLAUDE.md — このリポジトリで作業する Claude への共通の決まり

グラディウスIII（KONAMI）の非公式改造パッチのリポジトリです。管理者は hknroms（作業用アカウント pikadrum）。
管理者本人のチャットでも、協力者のチャットでも、最初にこのファイルの内容に従ってください。返信は日本語で短く（相手はスマホのことが多い）。

## 1. 何をする会話かで手順書を選ぶ

| 頼まれたこと | 読む手順書 |
|---|---|
| テストプレイの検証（「VERIFY.md に従って…」） | [VERIFY.md](VERIFY.md) |
| 調査・実装・素材・資料（「COLLAB.md に従って…」） | [COLLAB.md](COLLAB.md) |
| 管理者の改造・修正・リリース作業 | README.md の「リリース手順」と `src/` |

作業の担当・進み具合・提出物は Issue のコメントコマンドで記録する（一覧は `.github/scripts/task-bot.js` の先頭）。まとめページ：https://hknroms.github.io/gradius3/status.html

## 2. MAME はビルドしない（ビルド済みを使う）

gradius3 だけを入れた MAME（`g3`）のビルド済みを Releases に置いてある。**自分でビルドしないこと**（数十分かかるうえ、環境によっては失敗する）。

```bash
# 準備（その会話で1回だけ・数分）
curl -fsSL -o g3-linux-x64.tar.gz \
  https://github.com/hknroms/gradius3/releases/download/mame-g3/g3-linux-x64.tar.gz \
|| { git clone -q --depth 1 -b mame-g3-bin https://github.com/hknroms/gradius3.git g3pkg \
     && cp g3pkg/g3-linux-x64.tar.gz .; }      # Releases から取れない環境では枝から取る
tar xzf g3-linux-x64.tar.gz -C "$HOME"
export G3="$HOME/g3/g3"     # SDL 同梱。ライブラリの場所はこのラッパーが自分で設定する
"$G3" -version              # 動作確認（バージョンが出れば OK）
```

- 動かし方は `src/lua/run.sh`（`G3` 環境変数を見る）と `src/lua/g3run.lua` の先頭のコメント。画面・音なしで高速に回せる。
- 上の方法で取れない・動かない場合だけ、tar.gz の中の `BUILD.md` の手順でビルドする。

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
- push が拒否された（先に誰かが push していた）ときは、**上書きしない**。最新を取り込み、`versions.json` を見直して、版番号がぶつかっていたら付け直してから、ビルド・パッチ作成をやり直す。
- 終わったら、関係する Issue に版番号を書く（例「v0.4.17 で修正」）。

## 5. 引き継ぎのまとめを作るとき

会話が長くなって引き継ぎ用のまとめ（要約ファイル）を作るときは、**まとめの1行目に必ず次の文を書く**こと。次の会話がこのファイルを読めるようにするため。

> この作業は GitHub の hknroms/gradius3 で行う。最初にこのリポジトリをつなぎ、CLAUDE.md を読んでから続けること。

## 6. エミュレータで分かること・分からないこと

確かめられるのは CPU・RAM の動きと静止画まで。色の微妙さ・音・体感速度・ちらつきは「人の目で確認が必要」として扱い、断定しない。
