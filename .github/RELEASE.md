# リリース手順

このドキュメントでは、新しいバージョンをリリースする手順を説明します。

## 前提条件

GitHubリポジトリに `PYPI_API_TOKEN` シークレットを設定する必要があります。

### PyPI API トークンの設定

1. PyPI でAPIトークンを作成
   - https://pypi.org/manage/account/token/ にアクセス
   - "Add API token" をクリック
   - Token name: `github-actions`
   - Scope: "Entire account (all projects)" または "Project: enecoq-data-fetcher"
   - トークンをコピー

2. GitHubリポジトリにシークレットを追加
   - リポジトリの Settings > Secrets and variables > Actions に移動
   - "New repository secret" をクリック
   - Name: `PYPI_API_TOKEN`
   - Secret: コピーしたトークンを貼り付け
   - "Add secret" をクリック

## リリース手順（簡単な方法）

Makefileを使用して、バージョンアップからプッシュまでを自動化できます：

```bash
# パッチバージョンアップ (1.0.0 → 1.0.1)
make release-patch

# マイナーバージョンアップ (1.0.0 → 1.1.0)
make release-minor

# メジャーバージョンアップ (1.0.0 → 2.0.0)
make release-major
```

各コマンドは以下を自動実行します：
1. `src/enecoq_data_fetcher/__init__.py` のバージョンを更新
2. 変更をコミット（コミットメッセージ: `chore: bump version to X.X.X`）
3. Gitタグを作成（`vX.X.X`）
4. リモートリポジトリにプッシュ（`git push && git push --tags`）
5. GitHub Actionsが自動的にGitHub Releaseを作成し、PyPIにアップロード

## リリース手順（手動）

### 1. バージョンの更新

`src/enecoq_data_fetcher/__init__.py` の `__version__` を更新します：

```python
__version__ = "1.0.1"  # 新しいバージョン番号
```

### 2. 変更をコミット

```bash
git add src/enecoq_data_fetcher/__init__.py
git commit -m "chore: bump version to 1.0.1"
git push origin main
```

### 3. Gitタグを作成してプッシュ

```bash
# タグを作成
git tag v1.0.1

# タグをプッシュ
git push origin v1.0.1
```

### 4. 自動リリース

タグをプッシュすると、GitHub Actionsが自動的に以下を実行します：

1. パッケージのビルド
2. GitHub Releaseの作成（リリースノート自動生成）
3. PyPIへのアップロード

進行状況は以下で確認できます：
- GitHub Actions: https://github.com/rewse/enecoq-data-fetcher/actions

リリースが完了すると、以下で確認できます：
- GitHub Releases: https://github.com/rewse/enecoq-data-fetcher/releases
- PyPI: https://pypi.org/project/enecoq-data-fetcher/

## バージョン番号の規則

Semantic Versioning (SemVer) に従います：

- **MAJOR** (1.x.x): 破壊的変更
- **MINOR** (x.1.x): 後方互換性のある機能追加
- **PATCH** (x.x.1): 後方互換性のあるバグ修正

例：
- `1.0.0` → `1.0.1`: バグ修正
- `1.0.0` → `1.1.0`: 新機能追加
- `1.0.0` → `2.0.0`: 破壊的変更

## トラブルシューティング

### GitHub Actionsが失敗する

1. Actions タブでエラーログを確認
2. `PYPI_API_TOKEN` シークレットが正しく設定されているか確認
3. PyPI APIトークンが有効か確認

### 同じバージョンを再アップロードできない

PyPIは同じバージョンの再アップロードを許可しません。バージョン番号を上げて再度リリースしてください。

### タグを削除して再作成したい

```bash
# ローカルのタグを削除
git tag -d v1.0.1

# リモートのタグを削除
git push origin :refs/tags/v1.0.1

# 新しいタグを作成してプッシュ
git tag v1.0.1
git push origin v1.0.1
```

注意: PyPIに既にアップロード済みの場合は、バージョン番号を変更する必要があります。
