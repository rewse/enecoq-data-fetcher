# 要件定義書

## はじめに

本文書は、enecoQのWebサービスから電力使用量、電力使用料金、CO2排出量を取得する機能の要件を定義するものです。この機能により、ユーザーは自身の電力消費データをプログラマティックに取得し、分析や可視化に活用できるようになります。

## 用語集

- **Tool**: enecoQデータ取得ツール
- **enecoQ Web Service**: 株式会社ファミリーネットジャパンが提供するCYBERHOMEサービス内の電力データ管理Webサービス
- **User**: 本システムを利用してenecoQからデータを取得する利用者
- **Authentication Credentials**: enecoQ Web Serviceへのログインに必要な認証情報（メールアドレスとパスワード）
- **Power Usage Data**: 電力使用量データ（kWh単位）
- **Power Cost Data**: 電力使用料金データ（円単位）
- **CO2 Emission Data**: CO2排出量データ（kg単位）
- **Time Period**: データ取得対象の期間（今日または今月）
- **API Response**: enecoQ Web Serviceから返却されるデータレスポンス

## 要件

### 要件 1: 認証機能

**ユーザーストーリー:** ユーザーとして、enecoQ Web Serviceに安全にログインできるようにしたい。そうすることで、自分の電力データにアクセスできるようになる。

#### 受け入れ基準

1. THE Tool SHALL Authentication Credentials をコマンドライン引数として受け取る
2. WHEN User が Authentication Credentials を提供する, THE Tool SHALL enecoQ Web Service に対して認証リクエストを送信する
3. IF 認証が成功する, THEN THE Tool SHALL セッショントークンまたはクッキーを安全に保存する
4. IF 認証が失敗する, THEN THE Tool SHALL エラーメッセージを User に返却する
5. THE Tool SHALL 保存された認証情報を暗号化して管理する
6. WHEN セッションが期限切れになる, THE Tool SHALL 自動的に再認証を試行する

### 要件 2: 電力データ取得

**ユーザーストーリー:** ユーザーとして、指定した期間の電力使用量、電力使用料金、CO2排出量を取得したい。そうすることで、自分の電力消費パターンを分析し、電気代の推移を把握し、環境への影響を理解できる。

#### 受け入れ基準

1. THE Tool SHALL Time Period をコマンドライン引数として受け取る
2. WHEN User が Time Period を指定する, THE Tool SHALL enecoQ Web Service から Power Usage Data を取得する
3. WHEN User が Time Period を指定する, THE Tool SHALL enecoQ Web Service から Power Cost Data を取得する
4. WHEN User が Time Period を指定する, THE Tool SHALL enecoQ Web Service から CO2 Emission Data を取得する
5. THE Tool SHALL 取得した Power Usage Data を kWh 単位で返却する
6. THE Tool SHALL 取得した Power Cost Data を円単位で返却する
7. THE Tool SHALL 取得した CO2 Emission Data を kg 単位で返却する
8. THE Tool SHALL データ取得時にタイムスタンプ情報を含める
9. IF 指定された Time Period にデータが存在しない, THEN THE Tool SHALL 空のデータセットを返却する

### 要件 3: エラーハンドリング

**ユーザーストーリー:** ユーザーとして、データ取得時にエラーが発生した場合、適切なエラー情報を受け取りたい。そうすることで、問題を特定して対処できる。

#### 受け入れ基準

1. IF enecoQ Web Service が利用できない, THEN THE Tool SHALL 接続エラーを返却する
2. IF API Response が不正な形式である, THEN THE Tool SHALL パースエラーを返却する
3. IF レート制限に達する, THEN THE Tool SHALL リトライ可能であることを示すエラーを返却する
4. THE Tool SHALL すべてのエラーに対して詳細なエラーメッセージとエラーコードを提供する
5. WHEN エラーが発生する, THE Tool SHALL エラー内容をログに記録する

### 要件 4: データエクスポート

**ユーザーストーリー:** ユーザーとして、取得したデータを様々な形式でエクスポートしたい。そうすることで、他のツールやアプリケーションでデータを活用できる。

#### 受け入れ基準

1. THE Tool SHALL エクスポート形式をコマンドライン引数として受け取る
2. THE Tool SHALL データを JSON 形式でエクスポートする機能を提供する
3. THE Tool SHALL データをコンソールに表示する機能を提供する
4. WHERE User が形式を指定する, THE Tool SHALL 指定された形式でデータを出力する
5. WHEN JSON 形式で出力する, THE Tool SHALL 数値データを単位なしの数字のみで出力する
6. THE Tool SHALL エクスポートされたデータに取得日時を含める
7. THE Tool SHALL 文字エンコーディングを UTF-8 で統一する
