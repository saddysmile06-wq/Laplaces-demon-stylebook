"""Explicitly accept intentional PNG replacements before rebuilding."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent/'assets';path=HERE/'manifest.json'
d=json.loads(path.read_text(encoding='utf-8'))
for k,v in d['assets'].items():
    v['sha256']=hashlib.sha256((HERE/v['file']).read_bytes()).hexdigest()
path.write_text(json.dumps(d,indent=2),encoding='utf-8')
print('Accepted hashes for',len(d['assets']),'assets')
