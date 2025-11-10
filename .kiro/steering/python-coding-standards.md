---
inclusion: fileMatch
fileMatchPattern: ['**/*.py', '**/*.pyi']
---

# Python コーディング標準

この文書における次の各キーワード「しなければならない (MUST)」、「してはならない (MUST NOT)」、「要求されている (REQUIRED)」、「することになる (SHALL)」、「することはない (SHALL NOT)」、「する必要がある (SHOULD)」、「しないほうがよい (SHOULD NOT)」、「推奨される (RECOMMENDED)」、「してもよい (MAY)」、「選択できる (OPTIONAL)」は、RFC 2119 で述べられているように解釈されるべきものです。

## 基本方針

Google Python Style Guide に従う (MUST)。参考: [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

## 重要なルール

### Import
- パッケージとモジュールのみを import する (MUST)
- 個別のクラスや関数を直接 import してはならない (MUST NOT)
- `typing`, `collections.abc`, `typing_extensions` からの型は例外として import してもよい (MAY)

```python
# Good
from sound.effects import echo
echo.EchoFilter(input, output)

# Bad
from sound.effects.echo import EchoFilter
```

### 型アノテーション
- 公開 API には型アノテーションを付ける (SHOULD)
- `self`, `cls`, `__init__` の戻り値には不要

```python
def fetch_data(
    table: Table,
    keys: Sequence[str],
    require_all: bool = False,
) -> Mapping[str, tuple[str, ...]]:
    """Fetches rows from a table."""
```

### 例外処理
- catch-all `except:` や `Exception` のキャッチは避ける (MUST)
- `try`/`except` ブロックは最小限にする (SHOULD)
- `assert` を条件チェックに使用してはならない (MUST NOT)

### デフォルト引数
- 可変オブジェクトをデフォルト値にしてはならない (MUST NOT)

```python
# Good
def foo(a, b=None):
    if b is None:
        b = []

# Bad
def foo(a, b=[]):
    ...
```

### 文字列フォーマット
- f-string, `%` 演算子, `format()` を使用する (SHOULD)
- ログ出力には文字列リテラルを使用し、f-string は避ける (MUST)

```python
# Good
x = f'name: {name}; score: {n}'
logging.info('Version: %s', version)

# Bad
x = 'name: ' + name + '; score: ' + str(n)
logging.info(f'Version: {version}')
```

## スタイル

### 基本
- 行長: 80文字 (MUST)
- インデント: 4スペース (MUST)、タブ禁止 (MUST NOT)
- セミコロン禁止 (MUST NOT)

### 空行
- トップレベル定義間: 2行 (MUST)
- メソッド定義間: 1行 (MUST)

### Docstring
- 三重二重引用符 `"""` を使用 (MUST)
- 公開 API には必須 (MUST)
- Args, Returns, Raises セクションを含める (SHOULD)

```python
def fetch_data(table: Table, keys: Sequence[str]) -> Mapping[str, tuple]:
    """Fetches rows from a table.

    Args:
        table: An open Table instance.
        keys: Sequence of strings representing keys.

    Returns:
        Dict mapping keys to row data.

    Raises:
        IOError: Error accessing the table.
    """
```

### 命名規則
- パッケージ/モジュール: `lower_with_under`
- クラス: `CapWords`
- 関数/変数: `lower_with_under`
- 定数: `CAPS_WITH_UNDER`
- 内部/protected: 先頭に `_`
- ファイル名: `.py` 拡張子、ダッシュ禁止 (MUST NOT)

### Main 関数
```python
def main():
    ...

if __name__ == '__main__':
    main()
```

### Import の順序
1. `from __future__ import`
2. 標準ライブラリ
3. サードパーティ
4. ローカルアプリケーション

各グループ間に空行を入れ、グループ内は辞書順にソート (SHOULD)。
