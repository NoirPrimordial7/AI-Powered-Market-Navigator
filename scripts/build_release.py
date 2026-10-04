"""Build a deterministic, allowlisted release ZIP without runtime/private files."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT=Path(__file__).resolve().parents[1]
MODEL_SHA='73d8c9649771a76c1c9f3b83dba24cba140b7ea1a349055f43f9374eea4e04c1'
PATTERNS=[r'sk-or-v1-[A-Za-z0-9]{20,}',r'sk-[A-Za-z0-9]{32,}',r'gh[pousr]_[A-Za-z0-9]{30,}',r'AKIA[0-9A-Z]{16}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']

def release_paths(root):
    names=['VERSION','README.md','NOTICE.md','CHANGELOG.md','requirements.txt','Dockerfile','.dockerignore','.gitignore','.gitattributes','.streamlit/config.toml','.streamlit/secrets.example.toml','model3.h5']
    paths=[root/name for name in names]+list(root.glob('*.py'))
    for folder,patterns in {'assets':['*.css','*.svg'],'pages':['*.py'],'tests':['*.py'],'scripts':['*.py'],'data':['*.csv','*.json'],'docs':['*.md','*.json'],'evaluation':['*.csv','*.json'],'.github/workflows':['*.yml']}.items():
        for pattern in patterns:paths.extend((root/folder).glob(pattern))
    paths=sorted(set(paths),key=lambda p:p.relative_to(root).as_posix())
    for path in paths:
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f'Unsafe or missing release file: {path.name}')
    return paths

def validate_files(paths):
    for path in paths:
        raw=path.read_bytes()
        if path.name=='model3.h5':
            if hashlib.sha256(raw).hexdigest()!=MODEL_SHA:raise ValueError('Original model integrity check failed')
            continue
        text=raw.decode('utf-8-sig')
        if any(re.search(pattern,text) for pattern in PATTERNS):
            # Report only the file path, never the matching credential.
            raise ValueError(f'Potential credential in {path.name}; release stopped')
        if path.name=='secrets.example.toml':
            import tomllib
            if any(tomllib.loads(text).values()):raise ValueError('Example secrets must be empty placeholders')

def build(version,output,revision='uncommitted-worktree',root=ROOT):
    if not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+',version):raise ValueError('Expected a release tag such as v1.0.0')
    if version!='v'+(root/'VERSION').read_text(encoding='utf-8').strip():raise ValueError('Release tag does not match VERSION')
    if revision!='uncommitted-worktree' and not re.fullmatch(r'[0-9a-f]{40}',revision):raise ValueError('Expected a full source commit SHA')
    paths=release_paths(root);validate_files(paths)
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    archive=output/f'northstar-{version}.zip'
    files=[]
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as bundle:
        for path in paths:
            raw=path.read_bytes();name=path.relative_to(root).as_posix()
            info=zipfile.ZipInfo(f'northstar-{version}/{name}',date_time=(2026,10,5,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.create_system=3;info.external_attr=0o100644<<16
            bundle.writestr(info,raw)
            files.append({'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    manifest={'version':version,'repository':'NoirPrimordial7/AI-Powered-Market-Navigator','source_commit':revision,'model_sha256':MODEL_SHA,'archive':archive.name,'archive_sha256':digest,'files':files}
    (output/'release-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    (output/'SHA256SUMS.txt').write_text(f'{digest}  {archive.name}\n',encoding='utf-8',newline='\n')
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:raise ValueError('Release ZIP verification failed')
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',required=True)
    parser.add_argument('--output',default=str(ROOT/'dist'))
    parser.add_argument('--revision',default='uncommitted-worktree')
    args=parser.parse_args()
    result=build(args.version,args.output,args.revision)
    print(json.dumps({'version':result['version'],'files':len(result['files']),'archive':result['archive'],'sha256':result['archive_sha256']}))
