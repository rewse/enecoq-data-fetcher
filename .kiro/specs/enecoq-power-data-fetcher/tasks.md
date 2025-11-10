# 実装計画

- [x] 1. プロジェクト構造とセットアップ
  - uvを使用してPythonプロジェクトを初期化する
  - 必要な依存関係（playwright、click）をpyproject.tomlに追加する
  - プロジェクトのディレクトリ構造を作成する（src/enecoq_data_fetcher/）
  - _要件: 1.1, 2.1, 4.1_

- [x] 2. データモデルの実装
  - PowerUsage、PowerCost、CO2Emissionのデータクラスを作成する
  - PowerDataデータクラスを作成し、to_dict()メソッドを実装する
  - JSON形式で出力する際に数値データを単位なしで出力するロジックを実装する
  - _要件: 2.5, 2.6, 2.7, 4.5_

- [x] 3. エラークラスの実装
  - EnecoQError基底クラスを作成する
  - AuthenticationError、FetchError、ExportErrorクラスを作成する
  - 各エラークラスに適切なエラーメッセージとエラーコードを含める
  - _要件: 1.4, 3.4_

- [x] 4. Authenticatorコンポーネントの実装
  - EnecoQAuthenticatorクラスを作成する
  - login()メソッドを実装し、CYBERHOME入居者専用ページにログインする
  - メールアドレスとパスワードを入力してPOSTリクエストを送信する
  - 認証が成功した場合、セッションクッキーを保存する
  - 認証が失敗した場合、AuthenticationErrorを発生させる
  - is_logged_in()メソッドを実装し、ログイン状態を確認する
  - _要件: 1.1, 1.2, 1.3, 1.4_

- [x] 5. Data Fetcherコンポーネントの実装
  - EnecoQDataFetcherクラスを作成する
  - fetch_today_data()メソッドを実装し、今日の電力データを取得・パースする
  - fetch_month_data()メソッドを実装し、今月の電力データを取得・パースする
  - 期間に応じてプルダウンを選択するロジックを実装する
  - Playwrightのpage.locator()を使用してデータを抽出する
  - 電力使用量、電力使用料金、CO2排出量を抽出する
  - 数値データを正規表現で抽出し、floatに変換する
  - データが見つからない場合は空のデータセットを返却する
  - PowerDataオブジェクトを作成して返却する
  - _要件: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9_

- [x] 6. Exporterコンポーネントの実装
  - DataExporterクラスを作成する
  - export_json()メソッドを実装し、データをJSON形式で出力する
  - export_console()メソッドを実装し、データをコンソールに表示する
  - エクスポートされたデータに取得日時のメタデータを含める
  - 文字エンコーディングをUTF-8で統一する
  - _要件: 4.2, 4.3, 4.6, 4.7_

- [x] 7. Main Controllerの実装
  - EnecoQControllerクラスを作成する
  - Playwrightのブラウザを起動する
  - Authenticatorを使用して認証を実行する
  - Data Fetcherを使用してデータ取得を実行する
  - Exporterを使用してデータエクスポートを実行する
  - エラーハンドリングを実装する（認証エラー、ネットワークエラー、パースエラー）
  - リトライロジックを実装する（最大3回、指数バックオフ）
  - _要件: 1.2, 1.3, 1.4, 1.6, 3.1, 3.2, 3.3_

- [x] 8. CLI Interfaceの実装
  - Clickを使用してCLIを作成する
  - コマンドライン引数を定義する（--email、--password、--period、--format、--log-level）
  - 引数のバリデーションを実装する
  - Main Controllerを呼び出す
  - 結果を表示する
  - 終了コードを返す（0: 成功、非0: エラー）
  - _要件: 1.1, 2.1, 4.1, 4.4_

- [x] 9. ログ機能の実装
  - loggingモジュールを使用してログ機能を実装する
  - ログレベル（DEBUG、INFO、WARNING、ERROR）を設定する
  - コンソールにINFOレベル以上のログを出力する
  - ファイル（~/.enecoq/logs/enecoq.log）にDEBUGレベル以上のログを出力する
  - 認証情報をログに出力しないようにする
  - エラー発生時にエラー内容をログに記録する
  - _要件: 3.5_

- [ ] 10. 設定管理の実装
  - 設定ファイル（~/.enecoq/config.json）を読み込む機能を実装する（オプション）
  - デフォルト設定を定義する（log_level、timeout、max_retries、user_agent）
  - コマンドライン引数で設定を上書きできるようにする
  - _要件: 3.3_

- [ ] 11. エントリーポイントの作成
  - pyproject.tomlにCLIのエントリーポイントを定義する
  - uvを使用してツールをインストール可能にする
  - READMEファイルを作成し、使用方法を記載する
  - _要件: 1.1, 2.1, 4.1_
