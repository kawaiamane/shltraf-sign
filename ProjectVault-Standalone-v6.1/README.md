# ProjectVault Standalone v6

**QuickJSなし、Node.jsなし、npmなし。** Python標準ライブラリだけで動作するPVX圧縮・展開アプリです。Web UIのJavaScriptはブラウザ内で実行され、Pythonに組み込んだJavaScriptランタイムは使いません。

## 起動（Windows）
`start-windows.bat` をダブルクリック。Python 3.9以上が必要です。ブラウザが自動的に開きます。終了するにはコンソールで Ctrl+C。

## 起動（macOS / Linux）
`sh start-unix.sh`

## 1つのEXEにまとめる（Windows）
`build-windows.bat` を実行すると、PyInstallerが利用可能な環境では `dist/ProjectVault.exe` を生成します。ビルド時だけPyInstallerのインストールが必要です。配布先にはPython不要です。Windows上でビルドしてください。

## 機能
- ワンクリックでフォルダを `.pvx` に変換（Tkinterのネイティブフォルダ選択画面）
- PVX形式の展開、進捗表示、キャンセル、SHA-256整合性検査
- ファイルを1MiBチャンクに分割したストリーミング処理
- フォルダの除外設定、圧縮レベル0〜9
- ローカルHTTPサーバー（127.0.0.1:8765）

## 構造
`backend/pvx.py`: PVX形式エンジン
`backend/jobs.py`: 非同期ジョブ管理
`backend/quick.py`: フォルダ選択と出力先決定
`backend/server.py`: HTTP APIと静的UI
`frontend/index.html`, `app.js`, `style.css`: ブラウザUI
`tests/`: 自動テスト

## 注意
- PVX v1は独自コンテナですが、チャンク圧縮にはzlib/DEFLATEを利用します。
- OSネイティブダイアログはTkinterが必要です。Linuxのヘッドレス環境では表示できません。
- Windowsのダイアログ表示はこのLinux環境では未検証です。
- ローカルHTTP APIは認証を持ちません。信頼できる端末でのみ利用し、外部へ公開しないでください。
- 数十GB以上や数十万ファイルの性能・耐障害性は未検証です。
- 「1つで完結」は配布用EXEの形で実現可能ですが、EXEのビルドにはPyInstallerが必要です。


## v6.1 UI修正
CSSとJavaScriptを相対パスで参照するよう変更。画面幅によるレイアウト崩れを修正。HTMLを直接開いた場合はサーバー起動を案内します。Windowsでは start-windows.bat から起動してください。
