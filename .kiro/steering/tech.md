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

## 開発ツール
- 型チェック: 型アノテーションを使用する必要がある (SHOULD)
- コーディング標準: Google Python Style Guide に従わなければならない (MUST)

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
