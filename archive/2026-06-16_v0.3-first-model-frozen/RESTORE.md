# 復元手順: 2026-06-16_v0.3-first-model-frozen

このアーカイブは、**v0.3 初号機(gated ハイブリッド意図モデル)を意図モデル
デプロイゲートで正式昇格した直後**のワークスペース全体スナップショットである。

## 固定状態

- v0.3 first model: gate-promoted (`build/intent_model_v1.json`)
- intent model SHA-256: `055D1708CFB605AD5A449283BC05D81FF1C6BB59415F37E362FE06E7DF84091F`
- intent model k-fold (off-campaign): `0.7328431372549019`
- intent gate decision: `pass` (schema intent-model-deployment-gate.v1)
- pattern router model SHA-256: `71470C5E3D97973467661E17A66F7A382FE206F288454A7F9D39D305397DDEAC`
- executor reasoning-budget: direction (1) wired (`semantic_routing/executor.py`)
- LM Studio end-to-end: verified (external executor; output NOT training data)
- sealed v2: 依然 closed(accuracy gate 未達)
- test suite: 276 passed
- SQLite `PRAGMA quick_check`: `ok`

全ファイルの SHA-256 と件数は `MANIFEST.json` に記録している
(file_count=322, total_bytes=5154138)。

## 推奨する完全復元(別ディレクトリへ展開)

```powershell
$source = "archive\2026-06-16_v0.3-first-model-frozen\snapshot"
$destination = "D:\Thought State Register restored 2026-06-16"
New-Item -ItemType Directory -Path $destination
Copy-Item "$source\*" $destination -Recurse
Set-Location $destination
$env:PYTHONDONTWRITEBYTECODE = "1"
python -B -m pytest -p no:cacheprovider -q
```

## 既存ワークスペースへ戻す場合

```powershell
Copy-Item "archive\2026-06-16_v0.3-first-model-frozen\snapshot\*" "." -Recurse -Force
```

## 意図モデルだけ戻す場合

```powershell
Copy-Item `
  "archive\2026-06-16_v0.3-first-model-frozen\snapshot\build\intent_model_v1.json" `
  "build\intent_model_v1.json" -Force
```

## Hash 検証

```powershell
$archive = "archive\2026-06-16_v0.3-first-model-frozen"
$manifest = Get-Content "$archive\MANIFEST.json" -Raw | ConvertFrom-Json
$failures = @()
foreach ($property in $manifest.snapshot.files.PSObject.Properties) {
  $path = Join-Path "$archive\snapshot" $property.Name
  $actual = (Get-FileHash $path -Algorithm SHA256).Hash
  if ($actual -ne $property.Value.sha256) { $failures += $property.Name }
}
if ($failures.Count) { $failures; throw "snapshot hash verification failed" }
"snapshot hash verification passed"
```
