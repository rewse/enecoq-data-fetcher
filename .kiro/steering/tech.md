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

## 主要な依存関係
- **Playwright** (>=1.40.0): Webスクレイピング・ブラウザ自動化
- **Click** (>=8.1.0): CLIフレームワーク

## プロジェクト構成
- パッケージ名: `enecoq-data-fetcher`
- CLIエントリーポイント: `enecoq-fetch`

## 共通コマンド

### 環境セットアップ
```bash
# 仮想環境の作成と有効化
uv venv
source .venv/bin/activate  # macOS/Linux

# 依存関係のインストール
uv pip install -e .

# Playwrightブラウザのインストール
playwright install
```

### 開発
```bash
# パッケージのインストール（開発モード）
uv pip install -e .

# CLIの実行
enecoq-fetch --help
```

### ビルド
```bash
# パッケージのビルド
uv build
```

### テスト
```bash
# テストの実行（PYTHONPATH を設定して実行）
PYTHONPATH=src python3 tests/test_exporter.py

# 特定のテスト関数を実行
PYTHONPATH=src python3 -c "from tests.test_exporter import test_export_json_string; test_export_json_string()"
```

## テストガイドライン
- テストファイルは `tests/` ディレクトリに配置しなければならない (MUST)
- テストファイル名は `test_*.py` の形式にする必要がある (SHOULD)
- テスト実行時は `PYTHONPATH=src` を設定してパッケージをインポート可能にしなければならない (MUST)
- テストファイルからのインポートは `from enecoq_data_fetcher import module_name` の形式を使用しなければならない (MUST)
- 各テスト関数は独立して実行可能でなければならない (MUST)
- テストファイルは `if __name__ == "__main__":` ブロックで全テストを実行できるようにする必要がある (SHOULD)

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

## Conventional Commits スコープ
コミットメッセージのスコープには以下を使用する必要がある (SHOULD):

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
