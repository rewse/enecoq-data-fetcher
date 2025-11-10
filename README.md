# enecoQ Data Fetcher

enecoQ Web Service から電力使用量、電力使用料金、CO2排出量を取得するCLIツールです。

## 概要

enecoQは株式会社ファミリーネットジャパンが提供するCYBERHOMEサービス内の電力データ管理Webサービスです。このツールは、enecoQから電力データをプログラマティックに取得し、JSON形式やコンソール表示で出力します。

## 主な機能

- enecoQ Web Service への安全な認証
- 電力使用量データの取得（kWh単位）
- 電力使用料金データの取得（円単位）
- CO2排出量データの取得（kg単位）
- 今日または今月のデータ取得
- JSON形式またはコンソール表示での出力
- 詳細なエラーハンドリングとログ機能

## 必要要件

- CYBERHOME（enecoQ）のアカウント
- Python 3.9以上
- uv（Pythonパッケージマネージャー）
- Playwright（ブラウザ自動化）

## インストール

### 1. uvのインストール

uvがインストールされていない場合は、以下のコマンドでインストールしてください：

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# または Homebrew (macOS/Linux)
brew install uv
```

### 2. パッケージのインストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd enecoq-data-fetcher

# 仮想環境の作成
uv venv

# 仮想環境の有効化
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# 依存関係のインストール
uv pip install -e .

# Playwrightブラウザのインストール
playwright install
```

## 使用方法

### 基本的な使い方

```bash
enecoq-fetch --email your@email.com --password yourpassword
```

### コマンドライン引数

| 引数 | 説明 | デフォルト値 | 必須 |
|------|------|-------------|------|
| `--email` | enecoQのメールアドレス | - | ✓ |
| `--password` | enecoQのパスワード | - | ✓ |
| `--period` | データ取得期間（`today` または `month`） | `month` | |
| `--format` | 出力形式（`json` または `console`） | `json` | |
| `--output` | JSON出力先ファイルパス | - | |
| `--log-level` | ログレベル（`DEBUG`, `INFO`, `WARNING`, `ERROR`） | `INFO` | |

### 使用例

#### 今月のデータをJSON形式で取得

```bash
enecoq-fetch --email your@email.com --password yourpassword --period month --format json
```

#### 今日のデータをコンソールに表示

```bash
enecoq-fetch --email your@email.com --password yourpassword --period today --format console
```

#### JSON出力をファイルに保存

```bash
enecoq-fetch --email your@email.com --password yourpassword --output data/power_data.json
```

#### デバッグモードで実行

```bash
enecoq-fetch --email your@email.com --password yourpassword --log-level DEBUG
```

## 出力形式

### JSON形式

```json
{
  "period": "month",
  "timestamp": "2024-01-15T10:30:00",
  "usage": 250.5,
  "cost": 7515.0,
  "co2": 125.25
}
```

注: JSON出力では単位情報は含まれません。単位は以下の通りです：
- `usage`: kWh（キロワット時）
- `cost`: JPY（日本円）
- `co2`: kg（キログラム）

### コンソール形式

```
==================================================
enecoQ Power Data
==================================================

Period: month
Timestamp: 2024-01-15 10:30:00

Power Usage: 250.5 kWh
Power Cost: 7515.0 JPY
CO2 Emission: 125.25 kg

==================================================
```

## ログ

ログは以下の場所に出力されます：

- **コンソール**: INFOレベル以上
- **ファイル**: `logs/enecoq.log`（DEBUGレベル以上）

ログファイルには認証情報は記録されません。

## 高度な設定（オプション）

`config.yaml` ファイルを作成することで、デフォルト設定をカスタマイズできます：

```yaml
log_level: INFO
log_file: logs/enecoq.log
timeout: 30
max_retries: 3
user_agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
```

設定ファイルを使用する場合：

```bash
enecoq-fetch --email your@email.com --password yourpassword --config config.yaml
```

## 開発

### テストの実行

```bash
# 全テストの実行
PYTHONPATH=src python3 -m pytest tests/

# 特定のテストファイルの実行
PYTHONPATH=src python3 tests/test_exporter.py
```

### パッケージのビルド

```bash
uv build
```

## トラブルシューティング

### Playwrightブラウザがインストールされていない

```bash
playwright install
```

### 認証エラーが発生する

- メールアドレスとパスワードが正しいか確認してください
- enecoQ Web Service にブラウザから直接ログインできるか確認してください

### データが取得できない

- `--log-level DEBUG` オプションを使用して詳細なログを確認してください
- enecoQ Web Service が利用可能か確認してください
