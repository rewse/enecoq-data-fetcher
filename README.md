# enecoQ Data Fetcher

enecoQ から電力使用量、電力使用料金、CO2 排出量を取得する CLI ツールです。enecoQ は株式会社ファミリーネットジャパンが提供する CYBERHOME サービス内の電力データ管理 Web サービスで、公開 API がないため、このツールは Playwright でブラウザを操作してデータを取得します。今日または今月のデータを JSON かコンソール表示で出力します。

## 必要要件

- CYBERHOME（enecoQ）のアカウント
- Python 3.10 以上

## インストール

どの方法でも、初回に Playwright のブラウザ（Chromium）のインストールが必要です。

### uvx

インストールせずに直接実行できます。

```bash
uvx --from enecoq-data-fetcher playwright install chromium
uvx enecoq-data-fetcher --email your@email.com --password yourpassword
```

### uv tool

```bash
uv tool install --with-executables-from playwright enecoq-data-fetcher
playwright install chromium
```

`--with-executables-from playwright` を付けると、依存パッケージの `playwright` コマンドも PATH に入ります。

### pipx

```bash
pipx install --include-deps enecoq-data-fetcher
playwright install chromium
```

### pip

仮想環境を有効にした状態で実行してください。

```bash
pip install enecoq-data-fetcher
playwright install chromium
```

## 使用方法

```bash
enecoq-data-fetcher --email your@email.com --password yourpassword
```

uvx の場合は先頭を `uvx enecoq-data-fetcher` に置き換えてください。

| 引数 | 説明 | デフォルト値 | 必須 |
|------|------|--------------|------|
| `--email` | CYBERHOME（enecoQ）のメールアドレス | - | ✓ |
| `--password` | CYBERHOME（enecoQ）のパスワード | - | ✓ |
| `--period` | データ取得期間（`today` または `month`） | `month` | |
| `--format` | 出力形式（`json` または `console`） | `json` | |
| `--output` | JSON 出力先ファイルパス | - | |
| `--config` | 設定ファイルパス | `config.yaml` | |
| `--log-level` | ログレベル（`DEBUG`, `INFO`, `WARNING`, `ERROR`） | `INFO` | |
| `--log-file` | ログファイルパス | - | |

```bash
# 今日のデータをコンソールに表示
enecoq-data-fetcher --email your@email.com --password yourpassword --period today --format console

# 今月のデータを JSON ファイルに保存
enecoq-data-fetcher --email your@email.com --password yourpassword --output data/power_data.json
```

## 出力形式

### JSON

```json
{
  "period": "month",
  "timestamp": "2024-01-15T10:30:00.123456+09:00",
  "usage": 250.5,
  "cost": 7515.0,
  "co2": 125.25
}
```

JSON には単位が含まれません。`usage` は kWh、`cost` は円（JPY）、`co2` は kg です。値は期間の開始からの累計です。`timestamp` は取得した時刻で、実行環境のタイムゾーンのオフセットが付きます。

### コンソール

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

ログは標準ではコンソールにだけ出力されます。`--log-file` を指定すると、DEBUG レベル以上のログがそのファイルにも記録されます。認証情報はどちらにも記録されません。

```bash
enecoq-data-fetcher --email your@email.com --password yourpassword --log-file logs/enecoq.log
```

## 設定ファイル

カレントディレクトリの `config.yaml`（または `--config` で指定したファイル）でデフォルト設定を変更できます。項目は [config.yaml.example](config.yaml.example) を参照してください。

```yaml
log_level: INFO
log_file: logs/enecoq.log
timeout: 30
max_retries: 3
```

`max_retries` は、取得に失敗したときに最初の試行に追加でやり直す回数です（`0` でやり直しなし）。`--config` で指定したファイルが存在しない場合や、値の型が正しくない場合、知らない項目がある場合はエラーになります。

コマンドライン引数と設定ファイルの両方で指定した場合は、コマンドライン引数が優先されます。

## 他システムとの連携例

### cron での定期実行

毎時 42 分にデータを取得してファイルに保存する例です。多くの人が同じ時刻にアクセスすると enecoQ のサーバーに負荷がかかるので、42 は 1〜59 の好きな数字に変えてください。さらに 0〜59 秒のランダムな待機を入れています。`$RANDOM` は bash の機能なので、`SHELL=/bin/bash` を指定しています。

```bash
crontab -e
```

```
SHELL=/bin/bash
42 * * * * sleep $((RANDOM \% 60)) && enecoq-data-fetcher --email your@email.com --password yourpassword --output /path/to/enecoq_data.json
```

### Home Assistant

cron で保存した JSON ファイルを command_line センサーで読み込みます。スクレイピングは cron の 1 回だけで済み、3 つのセンサーは同じファイルを読みます。

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
      scan_interval: 300
  - sensor:
      name: "enecoQ Power Cost"
      command: "cat /config/data/enecoq_data.json"
      value_template: "{{ value_json.cost }}"
      unit_of_measurement: "JPY"
      device_class: monetary
      state_class: total
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

`monetary` の device class には `total` しか使えないため、料金センサーだけ `state_class` が異なります。

#### Utility Meter で期間ごとの値を出す

このツールの値は累計なので、1 時間ごとや 1 日ごとの値は Utility Meter で計算します。次の例は 1 時間ごとの電力使用量、料金、CO2 排出量のセンサー（`sensor.enecoq_power_usage_hourly` など）を作ります。

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

日ごとの値が欲しい場合は、`--period month` で取得したデータを使い、`cycle: daily` にします。

## 開発

```bash
uv sync
uv run playwright install chromium
./tests/run_tests.sh
uv build
```

1 つのテストファイルだけを実行するときは `PYTHONPATH=src uv run python tests/test_exporter.py` のように実行します。テストの詳細は [tests/README.md](tests/README.md)、コーディング規約やリリース手順は [AGENTS.md](AGENTS.md) にあります。

## トラブルシューティング

### Playwright のブラウザが見つからない

次のようなエラーが出たら、[インストール](#インストール)の手順で Chromium をインストールしてください。

```
Executable doesn't exist at /root/.cache/ms-playwright/chromium_headless_shell-1194/chrome-linux/headless_shell
```

### 認証エラーが出る

メールアドレスとパスワードが正しいか、ブラウザから enecoQ に直接ログインできるかを確認してください。

### データが取得できない

`--log-level DEBUG` を付けて実行し、詳細なログを確認してください。`--log-file` を指定すればログをファイルに残せます。enecoQ 自体が停止していないかも確認してください。
