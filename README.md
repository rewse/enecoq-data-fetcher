# enecoQ Data Fetcher

enecoQ Web Service から電力使用量、電力使用料金、CO2排出量を取得するCLIツールです。

## 概要

enecoQは株式会社ファミリーネットジャパンが提供するCYBERHOMEサービス内の電力データ管理Webサービスです。このツールは、enecoQから電力データをプログラマティックに取得し、JSON形式やコンソール表示で出力します。

## 主な機能

- 電力使用量データの取得
- 電力使用料金データの取得
- CO2排出量データの取得
- 今日または今月のデータ取得
- JSON形式またはコンソール表示での出力

## 必要要件

- CYBERHOME（enecoQ）のアカウント
- Python 3.9以上

## インストール

### uvxを使用（推奨）

インストール不要で直接実行できます。初回のみブラウザのインストールが必要です：

```bash
# 初回のみ: Playwrightブラウザをインストール
uvx --from enecoq-data-fetcher playwright install chromium

# 実行
uvx enecoq-data-fetcher --email your@email.com --password yourpassword
```

### uvを使用

```bash
uv tool install enecoq-data-fetcher
playwright install chromium
```

### pipxを使用

```bash
pipx install enecoq-data-fetcher
playwright install chromium
```

### pipを使用

```bash
pip install enecoq-data-fetcher
playwright install chromium
```

## 使用方法

### 基本的な使い方

```bash
# uvxを使用（推奨）
uvx enecoq-data-fetcher --email your@email.com --password yourpassword

# uv tool / pipx / pip でインストール済みの場合
enecoq-data-fetcher --email your@email.com --password yourpassword
```

### コマンドライン引数

| 引数 | 説明 | デフォルト値 | 必須 |
|------|------|--------------|------|
| `--email` | CYBERHOME (enecoQ) のメールアドレス | - | ✓ |
| `--password` | CYBERHOME (enecoQ) のパスワード | - | ✓ |
| `--period` | データ取得期間（`today` または `month`） | `month` | |
| `--format` | 出力形式（`json` または `console`） | `json` | |
| `--output` | JSON出力先ファイルパス | - | |
| `--config` | 設定ファイルパス | `config.yaml` | |
| `--log-level` | ログレベル（`DEBUG`, `INFO`, `WARNING`, `ERROR`） | `INFO` | |
| `--log-file` | ログファイルパス（指定しない場合はファイル出力なし） | - | |

### 使用例

#### 今月のデータをJSON形式で取得

```bash
enecoq-data-fetcher --email your@email.com --password yourpassword --period month --format json
```

#### 今日のデータをコンソールに表示

```bash
enecoq-data-fetcher --email your@email.com --password yourpassword --period today --format console
```

#### JSON出力をファイルに保存

```bash
enecoq-data-fetcher --email your@email.com --password yourpassword --output data/power_data.json
```

#### デバッグモードで実行

```bash
enecoq-data-fetcher --email your@email.com --password yourpassword --log-level DEBUG
```

## 出力形式

### JSON形式

```json
{
  "period": "month",
  "timestamp": "2024-01-15T10:30:00.123456",
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
==============================
enecoQ Data
==============================

Period: month
Timestamp: 2024-01-15 10:30:00

Power Usage: 250.5 kWh
Power Cost: 7515.0 JPY
CO2 Emission: 125.25 kg

==============================
```

## ログ

デフォルトではコンソールのみにログが出力されます。

ファイルにログを出力したい場合は、`--log-file` オプションを使用してください：

```bash
enecoq-data-fetcher --email your@email.com --password yourpassword --log-file logs/enecoq.log
```

ログファイルにはDEBUGレベル以上のログが記録されます。ログファイルには認証情報は記録されません。

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
enecoq-data-fetcher --email your@email.com --password yourpassword --config config.yaml
```

注: コマンドライン引数と設定ファイルを同時に設定した場合、コマンドライン引数が優先されます。

## 他システムとの連携例

### cronでの定期実行

毎時42分にデータを取得してファイルに保存する例（負荷分散のため0〜60秒のランダム待機）：

```bash
# crontabを編集
crontab -e

# 以下を追加
42 * * * * sleep $((RANDOM \% 60)) && enecoq-data-fetcher --email your@email.com --password yourpassword --output /path/to/enecoq_data.json
```

注: 負荷分散のため、42を別の数字（59以下の任意の値）に変更することを推奨します。多くのユーザーが同じ時刻にアクセスするとサーバーに負荷がかかるため、0以外のランダムな時刻を選択してください。

### Home Assistantとの連携

cronで定期的に保存したJSONファイルを読み込む方法：

```yaml
# configuration.yaml
command_line:
  - sensor:
      name: "enecoQ Power Usage"
      command: "cat /config/data/enecoq_data.json"
      value_template: "{{ value_json.usage }}"
      unit_of_measurement: "kWh"
      device_class: energy
      state_class: total_increasing
      icon: mdi:lightning-bolt
      scan_interval: 300  # 5分ごとに更新
  - sensor:
      name: "enecoQ Power Cost"
      command: "cat /config/data/enecoq_data.json"
      value_template: "{{ value_json.cost }}"
      unit_of_measurement: "JPY"
      device_class: monetary
      state_class: total_increasing
      icon: mdi:cash
      scan_interval: 300
  - sensor:
      name: "enecoQ CO2 Emission"
      command: "cat /config/data/enecoq_data.json"
      value_template: "{{ value_json.co2 }}"
      unit_of_measurement: "kg"
      state_class: total_increasing
      icon: mdi:molecule-co2
      scan_interval: 300
```

注: cronがデータを取得して `/config/data/` に保存し、複数のセンサーがそのファイルを読むことで、スクレイピングの回数を1回で済ませます。

#### Utility Meter で差分を取得

このツールが返す値は累計値です。差分が必要な場合は、Utility Meter を使用してください。

累計値から時間ごとの使用量を計算する例：

```yaml
# configuration.yaml
utility_meter:
  enecoq_power_usage_hourly:
    source: sensor.enecoq_power_usage
    cycle: hourly
  enecoq_power_cost_hourly:
    source: sensor.enecoq_power_cost
    cycle: hourly
  enecoq_co2_emission_hourly:
    source: sensor.enecoq_co2_emission
    cycle: hourly
```

これにより、以下のセンサーが作成されます：
- `sensor.enecoq_power_usage_hourly`: 1時間あたりの電力使用量（kWh）
- `sensor.enecoq_power_cost_hourly`: 1時間あたりの電力使用料金（JPY）
- `sensor.enecoq_co2_emission_hourly`: 1時間あたりのCO2排出量（kg）

同様の方法で ``--period month`` で取得したデータから日次センサーを作ることもできます。

累計値から日付ごとの使用量を計算する例：

```yaml
# configuration.yaml
utility_meter:
  enecoq_power_usage_daily:
    source: sensor.enecoq_power_usage
    cycle: daily
  enecoq_power_cost_daily:
    source: sensor.enecoq_power_cost
    cycle: daily
  enecoq_co2_emission_daily:
    source: sensor.enecoq_co2_emission
    cycle: daily
```

これにより、以下のセンサーが作成されます：
- `sensor.enecoq_power_usage_daily`: 1日あたりの電力使用量（kWh）
- `sensor.enecoq_power_cost_daily`: 1日あたりの電力使用料金（JPY）
- `sensor.enecoq_co2_emission_daily`: 1日あたりのCO2排出量（kg）

## 開発

### テストの実行

#### 全テストの実行

```bash
# テストスクリプトを使用（推奨）
./tests/run_tests.sh
```

#### 個別テストの実行

```bash
# PYTHONPATHを設定して実行
PYTHONPATH=src uv run python tests/test_exporter.py
```

詳細なテスト情報は [tests/README.md](tests/README.md) を参照してください。

### パッケージのビルド

```bash
uv build
```

## トラブルシューティング

### Playwrightブラウザがインストールされていない

```
Executable doesn't exist at /root/.cache/ms-playwright/chromium_headless_shell-1194/chrome-linux/headless_shell
```

このエラーが表示された場合は、Playwrightブラウザをインストールしてください：

```bash
# uvxを使用している場合
uvx --from enecoq-data-fetcher playwright install chromium

# uv tool / pipx / pip でインストールしている場合
playwright install chromium
```

### 認証エラーが発生する

- メールアドレスとパスワードが正しいか確認してください
- enecoQ Web Service にブラウザから直接ログインできるか確認してください

### データが取得できない

- `--log-level DEBUG` オプションを使用して詳細なログを確認してください
- enecoQ Web Service が利用可能か確認してください
- ログファイル `logs/enecoq.log` を確認してください
