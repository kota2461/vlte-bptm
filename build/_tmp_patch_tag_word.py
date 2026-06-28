from pathlib import Path
path=Path('semantic_routing/baseline.py')
text=path.read_text(encoding='utf-8')
old='(?:タグ名|タグ一覧|列名|料金表の列|辞書カード|ラベル|データセット|CSV|例文|小説の一文)'
new='(?:タグ名|タグ一覧|タグ|列名|料金表の列|辞書カード|ラベル|データセット|CSV|例文|小説の一文)'
if old not in text:
    raise SystemExit('ja structural alternation not found')
text=text.replace(old,new,1)
path.write_text(text, encoding='utf-8', newline='\n')