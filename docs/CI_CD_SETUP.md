# CI/CD セットアップガイド

## 概要

このプロジェクトは GitHub Actions を使用した自動テスト・カバレッジ監視パイプラインを備えています。

## 📋 機能

- ✅ **自動テスト実行**: プッシュ・PR時に自動でテスト実行
- ✅ **カバレッジ監視**: 80%カバレッジ閾値を自動チェック
- ✅ **マルチPythonバージョン対応**: Python 3.11, 3.12 でテスト
- ✅ **コード品質チェック**: flake8, mypy による静的解析
- ✅ **カバレッジレポート**: HTML/XML形式でレポート生成
- ✅ **pre-commitフック**: コミット前の自動チェック

## 🚀 クイックスタート

### 1. 依存関係のインストール

```bash
make install
```

または

```bash
pip install -r requirements.txt
pip install pre-commit
```

### 2. pre-commit フックのインストール

```bash
make pre-commit-install
```

これにより、以下が自動で実行されます：
- コードフォーマット（black, isort）
- リント（flake8）
- 型チェック（mypy）
- セキュリティチェック（bandit）
- ユニットテスト（pytest）

### 3. テストの実行

```bash
# 全テスト実行
make test

# ユニットテストのみ
make test-unit

# カバレッジレポート付き
make coverage

# カバレッジレポートをブラウザで開く
make coverage-html
```

## 📁 ファイル構成

```
.
├── .github/
│   └── workflows/
│       └── test.yml          # GitHub Actions ワークフロー
├── .pre-commit-config.yaml   # pre-commit 設定
├── .coveragerc               # カバレッジ設定
├── Makefile                  # 開発用コマンド集
└── docs/
    └── CI_CD_SETUP.md        # このドキュメント
```

## 🔧 GitHub Actions ワークフロー

### トリガー条件

- `main` / `develop` ブランチへのプッシュ
- `main` / `develop` ブランチへのプルリクエスト

### ワークフローステップ

1. **コードチェックアウト**
2. **Python環境セットアップ** (3.11, 3.12)
3. **依存関係インストール**
4. **Lint チェック** (flake8)
5. **型チェック** (mypy)
6. **ユニットテスト実行** (pytest + coverage)
7. **カバレッジレポートアップロード** (Codecov)
8. **カバレッジアーティファクト保存**

### カバレッジ閾値

- **必須カバレッジ**: 80%
- 80%未満の場合、ビルドが失敗します

## 📊 カバレッジレポート

### ローカルでのレポート確認

```bash
# カバレッジレポート生成 + ブラウザで開く
make coverage-html
```

HTMLレポートは `htmlcov/index.html` に生成されます。

### GitHub Actions でのレポート

- プルリクエストにカバレッジコメントが自動投稿されます
- Artifacts からHTMLレポートをダウンロード可能
- Codecov にアップロード（設定済みの場合）

## 🛠️ Make コマンド一覧

| コマンド | 説明 |
|---------|------|
| `make help` | 利用可能なコマンド一覧を表示 |
| `make install` | 依存関係をインストール |
| `make test` | 全テストを実行 |
| `make test-unit` | ユニットテストのみ実行 |
| `make coverage` | カバレッジレポート付きテスト |
| `make coverage-html` | HTMLカバレッジレポート生成 + 表示 |
| `make lint` | コード品質チェック |
| `make format` | コード自動フォーマット |
| `make type-check` | 型チェック実行 |
| `make clean` | 生成ファイルを削除 |
| `make pre-commit-install` | pre-commitフックをインストール |
| `make ci-test` | CI パイプライン全体をローカル実行 |

## 🔐 Codecov セットアップ（オプション）

Codecov を使用する場合：

1. [Codecov](https://codecov.io) でリポジトリを登録
2. トークンを取得
3. GitHub リポジトリの Secrets に `CODECOV_TOKEN` を追加

## 🎯 カバレッジ目標

### 現在のカバレッジ: **80.21%** ✅

| モジュール | カバレッジ | 状態 |
|----------|----------|------|
| WBSService | 99% | 🟢 Excellent |
| Converter | 97% | 🟢 Excellent |
| Validators | 98% | 🟢 Excellent |
| TaskMerger | 96% | 🟢 Excellent |
| BacklogClient | 93% | 🟢 Excellent |
| MasterService | 92% | 🟢 Excellent |
| StorageManager | 90% | 🟢 Great |
| GCSClient | 83% | 🟡 Good |
| FirestoreClient | 82% | 🟡 Good |
| DocumentProcessor | 86% | 🟡 Good |

### 次のマイルストーン: **85%** 🎯

## ⚙️ カバレッジ設定（.coveragerc）

```ini
[run]
source = src
omit = */tests/*, */venv/*

[report]
precision = 2
show_missing = True
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    if __name__ == .__main__.:
```

## 🐛 トラブルシューティング

### テストが失敗する

```bash
# 詳細なログでテスト実行
pytest tests/unit/ -vv

# 特定のテストのみ実行
pytest tests/unit/test_services/test_wbs_service.py -v
```

### カバレッジが80%未満

```bash
# 未カバーの行を確認
make coverage

# HTMLレポートで詳細確認
make coverage-html
```

### pre-commit フックが動かない

```bash
# フックを再インストール
pre-commit uninstall
make pre-commit-install

# 手動で実行
pre-commit run --all-files
```

## 📝 ベストプラクティス

1. **コミット前に必ずテストを実行**
   ```bash
   make ci-test
   ```

2. **新機能追加時はテストも追加**
   - カバレッジを維持・向上させる
   - エッジケースもカバーする

3. **PRを作成する前に**
   - `make lint` でコード品質チェック
   - `make coverage` でカバレッジ確認
   - `make format` でコード整形

4. **カバレッジが下がった場合**
   - 新しいコードに対してテストを追加
   - 80%閾値を必ず維持

## 🔄 CI/CD フロー図

```
コミット/PR作成
    ↓
GitHub Actions トリガー
    ↓
├─ Python 3.11 環境
│   ├─ 依存関係インストール
│   ├─ Lint チェック
│   ├─ 型チェック
│   ├─ テスト実行
│   └─ カバレッジチェック
│
└─ Python 3.12 環境
    ├─ 依存関係インストール
    ├─ Lint チェック
    ├─ 型チェック
    ├─ テスト実行
    └─ カバレッジチェック
    ↓
カバレッジレポート生成
    ↓
Codecov アップロード
    ↓
PR コメント投稿
    ↓
成功 ✅ / 失敗 ❌
```

## 📚 関連ドキュメント

- [pytest ドキュメント](https://docs.pytest.org/)
- [coverage.py ドキュメント](https://coverage.readthedocs.io/)
- [GitHub Actions ドキュメント](https://docs.github.com/ja/actions)
- [pre-commit ドキュメント](https://pre-commit.com/)

## 🤝 貢献

CI/CD設定の改善提案は大歓迎です！

## ライセンス

このプロジェクトのライセンスに従います。
