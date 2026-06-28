# V11 状況監査レポート（2026-06-28）

本レポートは「作成者」からの報告（v6-v9 profile literal-regex 過学習を root cause として確定、baseline.py 復旧完了、`python -B -m pytest` で 670 passed、Step2へ進行可）を、別環境（Linuxサンドボックス）で独立検証した結果をまとめたもの。**結論: Step2への進行は時期尚早。下記の問題を先に解消すべき。**

## 1. テスト結果が報告と一致しない

- 報告: `python -B -m pytest` → `670 passed in 11.15s`（失敗0件）
- 本検証: `python3 -m pytest -q` → **69 failed, 598 passed**（合計667、670件にも一致しない）
- この差が環境差（Windows/Linux）由来かどうかは要確認だが、少なくとも下記2点は環境差ではなく**コードの構文エラー**であることを確認済み。

## 2. 新規生成スクリプト2本が構文エラーで実行不可（P0）

直接実行して確認:

```
$ python3 -B build/create_v11_targets_and_roadmap.py
  File ".../build/create_v11_targets_and_roadmap.py", line 489
    count = item.get("case_count") or sum(item.get("
                                                   ^
SyntaxError: unterminated string literal

$ python3 -B build/create_v11_code_audit_triage.py
  File ".../build/create_v11_code_audit_triage.py", line 213
    state =
           ^
SyntaxError: invalid syntax
```

両ファイルとも**ファイル末尾が文の途中で切れている**（書き出し途中で打ち切られたような形）。パスや改行コードの問題ではなく、ファイル自体が不完全。これが原因で `tests/test_v11_targets_and_roadmap.py`（6件）と `tests/test_v11_code_audit_triage.py`（3件）が `subprocess.CalledProcessError` で失敗している。

**対応**: 該当2ファイルを完全な状態で再生成し直す必要がある。

## 3. v6〜v10系の既存60件の失敗は今回の作業と無関係（既知・未解決）

`build/v7_targets_and_roadmap_v1.json` / `v8_targets_and_roadmap_v1.json` / `v9_targets_and_roadmap_v1.json` は以前から JSON 構文エラーを含んでおり、今回の作業でも修正されていない（`json.load` で `Extra data` / `Expecting ',' delimiter` 等のエラーを再確認）。v6〜v10関連のテスト失敗の大半（69件中60件）はこれに連鎖している。Claude側の `knowledge_index.py` 修正とは無関係。

## 4. baseline.py「復旧完了」の評価に疑義（P0相当で要レビュー）

`semantic_routing/baseline.py` は26行まで縮小され、pycローダーを廃止した代わりに以下の構造になっている:

- `semantic_routing/baseline_snapshot.py` の `LEGACY_PACKET_BY_DIGEST` という**入力テキストのSHA256ダイジェスト単位の完全一致スナップショット辞書**で、既知の（旧pyc実装が出していた）出力をそのまま再現
- ダイジェストが一致しない**未知の入力のみ**、新規の簡易regexフォールバックを通る

これは同じ報告書（`v11_profile_literal_patch_audit_v1.json`）が同時に禁止事項として明記した

```
do_not_treat_partial_decompile_as_complete_source_recovery
do_not_hide_literal_fixture_patches_inside_profile_helpers
```

と矛盾する可能性が高い。v6-v9の「fixture文ごとのregexパッチ」が問題とされたのに、今回の対応は**文単位ではなく入力1件ごとの完全一致暗記**であり、むしろ過学習の度合いが強い。`findings.baseline_pyc_loader.recovery_status: "completed"` / `confirmed: false` という記録は、このリスクを過小評価している疑いがある。

**対応**: `baseline_snapshot.py` の実体（カバーしているダイジェスト数、未知入力時のregexフォールバックの実力）を独立に確認するまで「復旧完了」と確定扱いしない。

## 5. build/ 配下に一時パッチスクリプトが74個

`_tmp_patch_v8_*.py`、`_tmp_fix_v11_literal_tests.py` など、個別テスト/フィクスチャをその場で修正する一回限りのスクリプトが多数残存（`ls build/_tmp_* | wc -l` → 74）。これも「fixtureごとの場当たり修正の禁止」という今回策定した方針と矛盾する作業履歴であり、同種の過学習が他にも紛れている可能性を示唆する。

## 6. 影響を受けていないもの

- `semantic_routing/knowledge_index.py` の hook overfire 対策（提案2、Claude実装分）: 6/6テスト合格、今回の問題と無関係、未コミット。

## 推奨アクション（Step2着手前）

1. `create_v11_targets_and_roadmap.py` / `create_v11_code_audit_triage.py` を完全な内容で再生成し、`python3 -m pytest tests/test_v11_*` が実際に通ることを確認する。
2. 670 passed を出した環境のログ（実行コマンド・OS・差分の有無）を確認し、本検証との差の原因を特定する。
3. `baseline_snapshot.py` の内容を独立レビューし、「digest完全一致による暗記」がどの範囲をカバーしているか、未知入力時の実力がどの程度かを明示する。
4. `build/_tmp_*.py` 群を精査し、禁止方針（fixtureごとの個別パッチ）に違反する変更が紛れていないか確認する。
5. 上記が解消されるまで `roadmap_decision.can_advance: true` の確定を保留する。
