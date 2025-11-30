---
inclusion: always
---

# プロジェクト構造

この文書における次の各キーワード「しなければならない (MUST)」、「してはならない (MUST NOT)」、「要求されている (REQUIRED)」、「することになる (SHALL)」、「することはない (SHALL NOT)」、「する必要がある (SHOULD)」、「しないほうがよい (SHOULD NOT)」、「推奨される (RECOMMENDED)」、「してもよい (MAY)」、「選択できる (OPTIONAL)」は、RFC 2119 で述べられているように解釈されるべきものです。

## ディレクトリ構造

```
enecoq-data-fetcher/
├── .git/                       # Gitリポジトリ
├── .github/                    # GitHub設定
├── .hypothesis/                # Hypothesisテストデータ（自動生成）
├── .kiro/                      # Kiro設定
├── .venv/                      # Python仮想環境
├── scripts/                    # ユーティリティスクリプト
│   └── bump_version.sh        # バージョン更新スクリプト
├── src/
│   └── enecoq_data_fetcher/   # メインパッケージ
│       ├── __init__.py        # パッケージ初期化・バージョン定義
│       ├── cli.py             # CLIエントリーポイント
│       ├── controller.py      # メインコントローラー
│       ├── authenticator.py   # 認証コンポーネント
│       ├── fetcher.py         # データ取得コンポーネント
│       ├── exporter.py        # データエクスポートコンポーネント
│       ├── config.py          # 設定管理
│       ├── models.py          # データモデル
│       ├── exceptions.py      # カスタム例外
│       ├── logger.py          # ログ設定
│       └── py.typed           # 型情報マーカー
├── tests/                      # テストスイート
├── .gitignore                 # Git除外設定
├── .python-version            # Pythonバージョン指定
├── config.yaml.example        # 設定ファイルサンプル
├── LICENSE                    # ライセンス
├── Makefile                   # ビルド・リリースタスク
├── README.md                  # プロジェクトドキュメント
├── pyproject.toml             # プロジェクト設定
└── uv.lock                    # 依存関係ロックファイル
```

## アーキテクチャパターン

### コンポーネント分離
プロジェクトは責任ごとにモジュールを分離しなければならない (MUST):

1. **CLI層** (`cli.py`)
   - コマンドライン引数の解析
   - ユーザーインターフェース

2. **コントローラー層** (`controller.py`)
   - アプリケーションのメインロジック
   - コンポーネント間の調整

3. **認証層** (`authenticator.py`)
   - enecoQ Webサービスへの認証処理
   - セッション管理

4. **データ取得層** (`fetcher.py`)
   - Playwrightを使用したWebスクレイピング
   - データの取得ロジック

5. **エクスポート層** (`exporter.py`)
   - データの出力処理
   - フォーマット変換

6. **サポート層**
   - `config.py`: 設定管理
   - `models.py`: データモデル定義
   - `exceptions.py`: カスタム例外定義
   - `logger.py`: ログ設定

### モジュール命名規則
- ファイル名: `lower_with_under.py` 形式を使用しなければならない (MUST)
- ダッシュ (`-`) は使用してはならない (MUST NOT)

### Import規則
- パッケージとモジュールのみを import しなければならない (MUST)
- 個別のクラスや関数を直接 import してはならない (MUST NOT)
- 例外: `typing`, `collections.abc`, `typing_extensions` からの型

```python
# Good
from enecoq_data_fetcher import fetcher
result = fetcher.fetch_data()

# Bad
from enecoq_data_fetcher.fetcher import fetch_data
```

## 型情報
- `py.typed` ファイルが存在し、パッケージが型情報を提供することを示す
- 公開 API には型アノテーションを付ける必要がある (SHOULD)

## 出力とデータ
- データ出力は `data/` または `output/` ディレクトリに保存する必要がある (SHOULD)
- これらのディレクトリは `.gitignore` に含まれている
- CSV形式での出力が想定されている
