---
inclusion: always
---

# 技術スタック

この文書における次の各キーワード「しなければならない (MUST)」、「してはならない (MUST NOT)」、「要求されている (REQUIRED)」、「することになる (SHALL)」、「することはない (SHALL NOT)」、「する必要がある (SHOULD)」、「しないほうがよい (SHOULD NOT)」、「推奨される (RECOMMENDED)」、「してもよい (MAY)」、「選択できる (OPTIONAL)」は、RFC 2119 で述べられているように解釈されるべきものです。

## 言語とバージョン
- Python 3.14
- 最小サポートバージョン: Python 3.9

## ビルドシステム
- ビルドバックエンド: Hatchling
- パッケージマネージャー: uv (推奨)
- 依存関係管理: `uv.lock` によるロックファイルベース

## 主要な依存関係
- **Playwright** (>=1.40.0): Webスクレイピング・ブラウザ自動化
- **Click** (>=8.1.0): CLIフレームワーク

## プロジェクト構成
- パッケージ名: `enecoq-data-fetcher`
- CLIエントリーポイント: `enecoq-fetch`

## コマンドライン引数
| 引数 | 説明 | デフォルト値 | 必須 |
|------|------|-------------|------|
| `--email` | enecoQのメールアドレス | - | ✓ |
| `--password` | enecoQのパスワード | - | ✓ |
| `--period` | データ取得期間（`today` または `month`） | `month` | |
| `--format` | 出力形式（`json` または `console`） | `json` | |
| `--output` | JSON出力先ファイルパス | - | |
| `--config` | 設定ファイルパス | `config.yaml` | |
| `--log-level` | ログレベル（`DEBUG`, `INFO`, `WARNING`, `ERROR`） | `INFO` | |

## 共通コマンド

### 環境セットアップ
```bash
# 依存関係のインストール
uv sync

# Playwrightブラウザのインストール
uv run playwright install
```

### 開発
```bash
# パッケージのインストール
uv sync

# CLIの実行
uv run enecoq-fetch --help

# 基本的な使い方
uv run enecoq-fetch --email your@email.com --password yourpassword

# 今月のデータをJSON形式で取得
uv run enecoq-fetch --email your@email.com --password yourpassword --period month --format json

# 今日のデータをコンソールに表示
uv run enecoq-fetch --email your@email.com --password yourpassword --period today --format console

# JSON出力をファイルに保存
uv run enecoq-fetch --email your@email.com --password yourpassword --output data/power_data.json

# デバッグモードで実行
uv run enecoq-fetch --email your@email.com --password yourpassword --log-level DEBUG

# 設定ファイルを使用
uv run enecoq-fetch --email your@email.com --password yourpassword --config config.yaml
```

### ビルド
```bash
# パッケージのビルド
uv build
```

### テスト
```bash
# 全テストの実行（推奨）
./tests/run_tests.sh

# 個別テストファイルの実行（PYTHONPATH を設定して実行）
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

# 特定のテスト関数を実行
PYTHONPATH=src uv run python -c "from tests.test_exporter import test_export_json_string; test_export_json_string()"
```

## テストガイドライン
- テストファイルは `tests/` ディレクトリに配置しなければならない (MUST)
- テストファイル名は `test_*.py` の形式にする必要がある (SHOULD)
- テスト実行時は `PYTHONPATH=src` を設定してパッケージをインポート可能にしなければならない (MUST)
- テストファイルからのインポートは `from enecoq_data_fetcher import module_name` の形式を使用しなければならない (MUST)
- 各テスト関数は独立して実行可能でなければならない (MUST)
- テストファイルは `if __name__ == "__main__":` ブロックで全テストを実行できるようにする必要がある (SHOULD)

### テストスイート構成
プロジェクトには93個のテストが実装されている:
- **ユニットテスト** (83テスト)
  - `test_models.py`: データモデル (12テスト)
  - `test_exceptions.py`: カスタム例外 (12テスト)
  - `test_authenticator.py`: 認証コンポーネント (12テスト)
  - `test_fetcher.py`: データ取得コンポーネント (17テスト)
  - `test_config.py`: 設定管理 (8テスト)
  - `test_exporter.py`: データエクスポート (3テスト)
  - `test_logger.py`: ログ設定 (6テスト)
  - `test_cli.py`: CLIインターフェース (13テスト)
- **統合テスト** (10テスト)
  - `test_logging_integration.py`: ログ統合 (2テスト)
  - `test_integration.py`: エンドツーエンド統合 (8テスト)

詳細は `tests/README.md` を参照すること

## 設定ファイル（オプション）
`config.yaml` ファイルを作成することで、デフォルト設定をカスタマイズできる:

```yaml
log_level: INFO
log_file: logs/enecoq.log
timeout: 30
max_retries: 3
user_agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
```

設定項目:
- `log_level`: ログレベル（DEBUG, INFO, WARNING, ERROR）
- `log_file`: ログファイルのパス
- `timeout`: リクエストタイムアウト（秒）
- `max_retries`: 最大リトライ回数
- `user_agent`: HTTPリクエストのUser-Agent文字列

## 開発ツール
- 型チェック: 型アノテーションを使用する必要がある (SHOULD)
- コーディング標準: Google Python Style Guide に従わなければならない (MUST)

## 出力ガイドライン
- JSONやコンソールへの出力（`print()` や `sys.stdout` への出力）は文字化け防止のために常に英語で記述しなければならない (MUST)
- データモデルの単位（`unit` 属性）も英語表記を使用しなければならない (MUST)
  - 例: 「円」ではなく「JPY」を使用する

## Playwright 開発ガイドライン
- Web スクレイピングのセレクターを実装する前に、実際の HTML 構造を Playwright MCP で確認しなければならない (MUST)
- CSS セレクターや要素の ID は実際のページから取得した正確な値を使用しなければならない (MUST)
- ログインが必要な場合は Authentication Credentials をチャットで尋ねなければならない (MUST)

## トラブルシューティング

### Playwrightブラウザがインストールされていない
```bash
uv run playwright install
```

### 認証エラーが発生する
- メールアドレスとパスワードが正しいか確認する
- enecoQ Web Service にブラウザから直接ログインできるか確認する

### データが取得できない
- `--log-level DEBUG` オプションを使用して詳細なログを確認する
- enecoQ Web Service が利用可能か確認する
- ログファイル `logs/enecoq.log` を確認する

## Git コミットガイドライン
- コミットメッセージには本文を付ける必要がある (SHOULD)
- 本文には変更内容の詳細、理由、影響範囲などを記述する必要がある (SHOULD)
- Conventional Commits 仕様に従わなければならない (MUST)
- コミットメッセージのスコープには以下を使用する必要がある (SHOULD)

### コアコンポーネント
- `cli`: CLIインターフェース関連 (`cli.py`)
- `controller`: メインコントローラーロジック (`controller.py`)
- `authenticator`: 認証機能 (`authenticator.py`)
- `fetcher`: データ取得機能 (`fetcher.py`)
- `exporter`: データエクスポート機能 (`exporter.py`)

### サポートコンポーネント
- `config`: 設定管理 (`config.py`)
- `models`: データモデル定義 (`models.py`)
- `exceptions`: カスタム例外定義 (`exceptions.py`)
- `logger`: ログ設定 (`logger.py`)
