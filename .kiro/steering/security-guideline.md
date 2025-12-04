# セキュリティガイドライン

## 要求レベルについて

この文書における次の各キーワード「しなければならない (MUST)」、「してはならない (MUST NOT)」、「要求されている (REQUIRED)」、「することになる (SHALL)」、「することはない (SHALL NOT)」、「する必要がある (SHOULD)」、「しないほうがよい (SHOULD NOT)」、「推奨される (RECOMMENDED)」、「してもよい (MAY)」、「選択できる (OPTIONAL)」は、RFC 2119 で述べられているように解釈されるべきものです。

## 基本方針

このプロジェクトは、Pythonパッケージのサプライチェーン攻撃に対する多層防御を実装しなければなりません (MUST)。

## 多層防御アプローチ

### 層1: 入れない（Aikido Safe Chain）

新しすぎるパッケージや怪しいパッケージをインストールさせない対策を実装しなければなりません (MUST)。

公開から96時間（4日）以内のパッケージのインストールをブロックすることで、ゼロデイ攻撃の多くを回避できます。

このプロジェクトでは、デフォルトの24時間ではなく96時間に設定しています。これにより、より多くの攻撃を検知できる可能性が高まります。

**注意:** Aikido Safe Chainは以下のパッケージマネージャーをサポートしています：
- **npm系**: npm, npx, yarn, pnpm, pnpx, bun, bunx（最小パッケージ年齢制限 + マルウェア検知）
- **Python系**: pip, pip3, uv（マルウェア検知のみ、ベータ版）

Python系パッケージマネージャーでは、現在マルウェア検知のみが有効で、最小パッケージ年齢による制限は適用されません。

#### CI/CDでの実装

GitHub Actionsワークフローには、Aikido Safe Chainのセットアップを含めなければなりません (MUST)：

```yaml
- name: Setup Aikido Safe Chain
  run: curl -fsSL https://raw.githubusercontent.com/AikidoSec/safe-chain/main/install-scripts/install-safe-chain.sh | sh -s -- --ci --include-python

- name: Install dependencies
  env:
    SAFE_CHAIN_MINIMUM_PACKAGE_AGE_HOURS: 96
  run: uv sync
```

環境変数`SAFE_CHAIN_MINIMUM_PACKAGE_AGE_HOURS`で最小パッケージ年齢を設定しなければなりません (MUST)。このプロジェクトでは96時間（4日）に設定しています。

**注意:** 最小パッケージ年齢の制限は、現在npm系パッケージマネージャー（npm, yarn, pnpmなど）にのみ適用され、Pythonパッケージマネージャー（uv, pip, pip3）には適用されません。Pythonパッケージについては、マルウェア検知のみが有効です。

#### ローカル開発

開発者は、Aikido Safe ChainをPythonサポート付きでローカル環境にインストールする必要があります (SHOULD)。

**Unix/Linux/macOS:**

```bash
curl -fsSL https://raw.githubusercontent.com/AikidoSec/safe-chain/main/install-scripts/install-safe-chain.sh | sh -s -- --include-python
```

**Windows (PowerShell):**

```powershell
iex "& { $(iwr 'https://raw.githubusercontent.com/AikidoSec/safe-chain/main/install-scripts/install-safe-chain.ps1' -UseBasicParsing) } -includepython"
```

インストール後、ターミナルを再起動しなければなりません (MUST)。

**インストールの確認:**

```bash
# Pythonパッケージでテスト
uv pip install safe-chain-pi-test
```

このコマンドは、テスト用のマルウェアパッケージをブロックするはずです。

#### 最小パッケージ年齢の設定

ローカル開発環境で96時間の設定を使用する場合は、環境変数を設定する必要があります (SHOULD)：

```bash
# 環境変数を設定
export SAFE_CHAIN_MINIMUM_PACKAGE_AGE_HOURS=96

# Pythonパッケージのインストール（マルウェア検知のみ）
uv add package-name
uv pip3 install package-name
```

または、設定ファイル（`~/.aikido/config.json`）で永続的に設定できます (MAY)：

```json
{
  "minimumPackageAgeHours": 96
}
```

**重要:** 最小パッケージ年齢の制限は、現在npm系パッケージマネージャーにのみ適用されます。Pythonパッケージマネージャー（uv, pip, pip3）では、マルウェア検知機能のみが有効で、パッケージ年齢による制限は行われません。

詳細: [Aikido Safe Chain](https://github.com/AikidoSec/safe-chain)

### 層2: 実行させない（実行環境の制限）

マルウェアが依存関係に混入してしまった場合でも、悪意あるコードを実行させない、または被害を最小限に抑える対策を実装する必要があります (SHOULD)。

#### 最小権限の原則

アプリケーションは必要最小限の権限で実行しなければなりません (MUST)：

```bash
# Good: 一般ユーザー権限で実行
uv run enecoq-data-fetcher --email "$EMAIL" --password "$PASSWORD"

# Bad: root権限で実行（避けるべき）
sudo uv run enecoq-data-fetcher --email "$EMAIL" --password "$PASSWORD"
```

#### 仮想環境の分離

依存関係は仮想環境で分離して管理しなければなりません (MUST)：

```bash
# uvは自動的に.venvを作成・管理する
uv sync

# 仮想環境内で実行
uv run enecoq-data-fetcher
```

仮想環境を使用することで、システム全体への影響を制限できます。

### 層3: 見逃さない（脆弱性スキャン）

Googleが運営するOSV（Open Source Vulnerabilities）データベースを使用して、既知の脆弱性をスキャンすることを推奨します (RECOMMENDED)。

#### CI/CDでの実装

GitHub Actionsワークフローには、OSV-Scannerによる脆弱性スキャンを含めなければなりません (MUST)：

```yaml
osv-scan:
  uses: "google/osv-scanner-action/.github/workflows/osv-scanner-reusable.yml@v2.3.0"
```

#### ローカルでのスキャン

```bash
# インストール（macOS）
brew install osv-scanner

# スキャン実行（リポジトリ全体を再帰的にスキャン）
osv-scanner --recursive ./

# または、特定のロックファイルをスキャン
osv-scanner --lockfile=uv.lock
```

詳細: 
- [OSV-Scanner](https://google.github.io/osv-scanner/)
- [OSV-Scanner GitHub Action](https://github.com/google/osv-scanner-action)

## 依存関係の管理

### 新しい依存関係の追加

新しい依存関係を追加する際は、以下を確認しなければなりません (MUST)：

1. パッケージの公開日（最低24時間経過していること）
2. パッケージのメンテナンス状況
3. GitHubスター数やダウンロード数
4. 既知の脆弱性の有無

### 依存関係の更新

依存関係を更新する際は、以下を実行しなければなりません (MUST)：

1. 変更内容の確認（CHANGELOGやリリースノート）
2. OSV-Scannerによるスキャン
3. テストの実行

## セキュリティインシデントへの対応

### 脆弱性の発見

セキュリティ上の問題を発見した場合は、以下の手順に従わなければなりません (MUST)：

1. 公開のIssueではなく、GitHubのSecurity Advisoryを使用して報告する
2. 影響範囲を特定する
3. 修正パッチを作成する
4. セキュリティアドバイザリを公開する

#### 報告手順

1. リポジトリの「Security」タブを開く
2. 「Report a vulnerability」をクリックする
3. 詳細を記入して送信する

### 依存関係の脆弱性

依存関係に脆弱性が発見された場合は、以下の手順に従わなければなりません (MUST)：

1. 影響範囲を評価する
2. 修正版が利用可能な場合は、速やかに更新する
3. 修正版が利用できない場合は、代替パッケージを検討する
4. ユーザーに通知する

## 参考リンク

- [Aikido Safe Chain](https://github.com/AikidoSec/safe-chain)
- [OSV-Scanner](https://google.github.io/osv-scanner/)
