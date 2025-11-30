# テストスイート

このディレクトリには enecoQ Data Fetcher のテストが含まれています。

## テスト構成

### ユニットテスト

#### コアコンポーネント
- **test_models.py** - データモデルのテスト (12テスト)
  - PowerUsage, PowerCost, CO2Emission モデル
  - PowerData モデルとシリアライゼーション
  - カスタム単位、ゼロ値、大きな値のテスト

- **test_exceptions.py** - カスタム例外のテスト (12テスト)
  - EnecoQError 基底クラス
  - AuthenticationError, FetchError, ExportError
  - 例外の継承、キャッチング、チェイニング

- **test_authenticator.py** - 認証コンポーネントのテスト (12テスト)
  - 初期化とユーザーエージェント設定
  - ログイン成功・失敗シナリオ
  - エラーメッセージ処理
  - ログイン状態チェック

- **test_fetcher.py** - データ取得コンポーネントのテスト (17テスト)
  - データ抽出（電力使用量、コスト、CO2排出量）
  - 期間選択（今日、今月）
  - エラーハンドリング
  - 様々なフォーマットのパース

#### サポートコンポーネント
- **test_config.py** - 設定管理のテスト (8テスト)
  - デフォルト設定
  - YAMLファイルからの読み込み
  - コマンドラインオーバーライド

- **test_exporter.py** - データエクスポートのテスト (3テスト)
  - JSON文字列生成
  - JSONファイル出力
  - コンソール出力

- **test_logger.py** - ログ設定のテスト (6テスト)
  - ログレベル設定
  - ファイル出力
  - 機密データフィルタ

- **test_cli.py** - CLIインターフェースのテスト (13テスト)
  - ヘルプメッセージ
  - 引数検証
  - エラーハンドリング
  - 設定ファイル統合

### プロパティベーステスト

- **test_pbt.py** - Hypothesis を使用したプロパティベーステスト (17テスト)
  - PowerUsage/PowerCost/CO2Emission の値保持プロパティ
  - PowerData の構造とシリアライゼーションプロパティ
  - 例外クラスの継承とメッセージフォーマットプロパティ
  - JSON シリアライゼーションの不変条件

### 統合テスト

- **test_logging_integration.py** - ログ統合テスト (2テスト)
  - ファイルへのログ出力
  - 機密データ保護

- **test_integration.py** - エンドツーエンド統合テスト (8テスト)
  - JSON/コンソール出力の完全なワークフロー
  - 設定ファイル統合
  - エラーハンドリング（認証、取得）
  - リトライメカニズム
  - データモデルのシリアライゼーション

## テストの実行

### 全テストの実行

```bash
./tests/run_tests.sh
```

### 個別テストの実行

```bash
# PYTHONPATHを設定して実行
PYTHONPATH=src uv run python tests/test_models.py
PYTHONPATH=src uv run python tests/test_exceptions.py
PYTHONPATH=src uv run python tests/test_authenticator.py
PYTHONPATH=src uv run python tests/test_fetcher.py
PYTHONPATH=src uv run python tests/test_config.py
PYTHONPATH=src uv run python tests/test_exporter.py
PYTHONPATH=src uv run python tests/test_logger.py
PYTHONPATH=src uv run python tests/test_cli.py
PYTHONPATH=src uv run python tests/test_logging_integration.py
PYTHONPATH=src uv run python tests/test_integration.py

# プロパティベーステスト（hypothesis が必要）
uv sync --extra test
PYTHONPATH=src uv run python tests/test_pbt.py
```

## テスト統計

- **総テスト数**: 110テスト
- **ユニットテスト**: 81テスト
- **プロパティベーステスト**: 17テスト
- **統合テスト**: 10テスト

### カバレッジ

全ての主要コンポーネントがテストされています：

- ✓ models.py - データモデル
- ✓ exceptions.py - カスタム例外
- ✓ authenticator.py - 認証
- ✓ fetcher.py - データ取得
- ✓ config.py - 設定管理
- ✓ exporter.py - データエクスポート
- ✓ logger.py - ログ設定
- ✓ cli.py - CLIインターフェース
- ✓ controller.py - メインコントローラー（統合テストでカバー）

## テスト戦略

### ユニットテスト
- 各コンポーネントを独立してテスト
- モックを使用して外部依存を排除
- 正常系と異常系の両方をカバー

### 統合テスト
- コンポーネント間の連携をテスト
- エンドツーエンドのワークフローを検証
- 実際の使用シナリオをシミュレート

## 注意事項

- PyYAMLがインストールされていない場合、一部のYAML関連テストはスキップされます
- Hypothesis がインストールされていない場合、プロパティベーステストはスキップされます
  - インストール: `uv sync --extra test`
- テストはモックを使用しているため、実際のenecoQ Webサービスへの接続は不要です
- ログエラーメッセージは一部のテストで表示されますが、これは正常な動作です
