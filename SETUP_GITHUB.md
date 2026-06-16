# GitHub 公開 & Zenn 連携 手順

> sandbox 側は削除操作が許可されておらず git を直接動かせなかったため、ローカル準備は
> Windows 側で実行します。下の順にやれば、公開リポジトリ作成 → push → Zenn 連携まで完了します。

## 0. 前提

- `git` がインストール済み（`git --version` で確認）。
- GitHub アカウントを所有していること。
- （任意・推奨）GitHub CLI `gh` がインストール済みだと repo 作成と push がコマンド一発で済みます。

## 1. ローカル準備（cleanup + init + 初回コミット）

PowerShell で:

```powershell
cd "D:\Thought State Register"
powershell -ExecutionPolicy Bypass -File .\git_publish_setup.ps1
```

スクリプトは次をやります: sandbox が残した壊れた `.git` と `__b` / `__unlink_test` を削除 →
`git init` → `.gitignore` に従って add → 中身のサニティチェックを表示 → 初回コミット。
**push はしません。** チェック表示で、archive が `2026-06-16_v0.3-first-model-frozen` だけ、
ログ/DB/pycache が漏れていないことを目視確認してください。

## 2. GitHub リポジトリを作成して push

### 方法A: GitHub CLI（推奨・速い）

```powershell
cd "D:\Thought State Register"
gh auth login          # 未ログインなら一度だけ（アカウント: kota2461）
gh repo create vlte-bptm --public --source . --remote origin --push
```

`vlte-bptm` はリポジトリ名（任意）。これで `kota2461/vlte-bptm` の作成と push が同時に完了します。

### 方法B: Web で作成して手動 push

1. https://github.com/new で空のリポジトリを作成（README/.gitignore は **付けない**）。Public を選択。リポジトリ名は `vlte-bptm` を推奨。
2. 作成後、次を実行（リポジトリ名を変えた場合はそこだけ差し替え）:

```powershell
cd "D:\Thought State Register"
git remote add origin https://github.com/kota2461/vlte-bptm.git
git push -u origin main
```

## 3. Zenn と連携

Zenn の記事は `articles/` フォルダの markdown を GitHub から取り込む仕組みです。
本リポジトリには既に `articles/vlte-bptm-thought-state-arch.md` があります。

1. https://zenn.dev/dashboard にログイン。
2. 右上メニュー → **GitHubからのデプロイ**（Deploys）を開く。
3. **リポジトリを連携する** から、手順2で作った GitHub リポジトリを選択して連携。
4. 連携後、`main` に push するたびに `articles/` 配下が Zenn に同期されます。

### 記事の公開について

- 現在 `articles/vlte-bptm-thought-state-arch.md` の frontmatter は `published: false`（下書き）です。
- Zenn 上でプレビューを確認し、公開したくなったら `published: true` に変更して push してください。
- ファイル名 `vlte-bptm-thought-state-arch` がそのまま記事 URL の slug になります
  （Zenn の規則: 半角英小文字・数字・ハイフンで 12〜50 字 → 適合済み）。

## 4. 公開用の英語テキストについて

- `README.en.md` … GitHub 来訪者向けの英語版プロジェクト説明（仕様・正直な性能・構成）。
- リポジトリのトップに英語 README を出したい場合は、`README.md`（日本語）を残したまま
  GitHub の "About" や Pin で `README.en.md` を案内するか、英語を主にするなら
  Windows 側で `README.md` を日本語版にリネームし `README.en.md` を `README.md` にしてください
  （sandbox では削除/リネーム不可のため、ここはローカルで）。

## トラブル時

- `git push` で認証を求められたら、GitHub の Personal Access Token か `gh auth login` を使用。
- 容量が大きすぎる/不要物が入った場合は、`.gitignore` を見直して
  `git rm -r --cached <path>` → 再コミット。
