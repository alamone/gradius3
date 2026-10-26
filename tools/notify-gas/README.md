# ログイン申請のメール通知（Google Apps Script）

配布ページの Google ログイン（Firebase Authentication、プロジェクト `gradius3-login-41798`）の申請を、メールで知らせる。

- 申請（Firestore の `users/{uid}` に `status: "pending"` ができる）→ **管理者に**「新しい申請があります」
- 管理者が Firebase の管理画面で `status` を `approved` に変える → **本人に**「見られるようになりました」
- 5分ごとに確認する。Firebase は Spark（無料）のままでよい。Firestore の読み取りは無料の範囲（1日5万回）に収まる（申請者が百数十人までなら余裕）。
- Firestore のルールは `docs/dev/firebase/firestore.rules`（クライアントは pending の作成だけ。承認は管理画面から）。

## 設定（1回だけ・パソコン推奨・10分）

Firebase のプロジェクトを作った **Google アカウント**で行う。

1. https://script.google.com を開き、「新しいプロジェクト」。名前を付ける（例「gradius3 申請通知」）。
2. 最初からある `コード.gs`（Code.gs）の中身を全部消し、このフォルダの [Code.gs](Code.gs) の中身を貼り付けて保存。
   - 先頭の「設定」の `PAGE_URL`（承認した人に案内するページ）が正しいか確かめる。
3. 左の歯車「プロジェクトの設定」→「『appsscript.json』マニフェスト ファイルをエディタで表示する」にチェック → エディタに戻り、`appsscript.json` の中身を [appsscript.json](appsscript.json) で置き換えて保存。
4. 上の関数の選択で **`setup`** を選んで「実行」。許可を求められたら、Firebase を作ったアカウントを選ぶ →「このアプリは Google で確認されていません」と出たら「詳細」→「（プロジェクト名）に移動」→「許可」。
   - 承認待ちの申請があれば、その一覧が1通届く。
5. 関数 **`testMail`** を実行して、テストのメールが届くことを確かめる。

## うまくいかないとき

- 「Firestore を読めませんでした（403）」で、`has not been used in project` などと出る:
  歯車「プロジェクトの設定」→「Google Cloud Platform（GCP）プロジェクト」→「プロジェクトを変更」→ プロジェクト番号 **570590177142**（Firebase の `messagingSenderId` と同じ番号）を入れて「プロジェクトを設定」。その後もう一度 `setup`。
- 通知先を変えたい: Code.gs の `ADMIN_EMAIL` にアドレスを書く（空なら、このスクリプトを動かしているアカウント）。
- 止めたい: 左の時計「トリガー」で `check` を削除。
- 「却下」も知らせたい・文面を変えたい: Code.gs の `mailApproved_` / `mailPending_` を直す（直したらこのフォルダにも反映する）。
