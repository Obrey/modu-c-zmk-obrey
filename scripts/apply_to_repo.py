#!/usr/bin/env python3
"""Back up and copy this rebuilt config into an existing clone. Never commits/pushes."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys

SOURCE=Path(__file__).resolve().parents[1]
LEGACY = {
 'zephyr/module.yml': 'zmk-behavior-obrey-combo-boot',
 'zephyr/module.yaml': 'zmk-behavior-obrey-combo-boot',
 '.github/workflows/obrey-combo-boot-build.yml': 'Build Obrey direct boot combos',
 'dts/bindings/behaviors/zmk,behavior-obrey-combo-boot.yaml': 'zmk,behavior-obrey-combo-boot',
 'tools/check_obrey_combo.py': 'validate_patched',
 'tools/obrey_combo_patchlib.py': 'validate_patched',
 'modules/obrey-combo-boot/CMakeLists.txt': 'Obrey combo boot',
 'modules/obrey-combo-boot/Kconfig': 'ZMK_BEHAVIOR_OBREY_COMBO_BOOT',
 'modules/obrey-combo-boot/src/behavior_combo_boot.c': 'obrey_guard_target',
 'modules/obrey-combo-boot/src/obrey_guard.h': 'obrey_chord_guard',
}


def regular_path(path: Path, root: Path) -> None:
    for p in [path,*path.parents]:
        if p == root.parent: break
        if p.is_symlink(): raise ValueError('Refusing a symlink: '+str(p))


def plan(source: Path, target: Path) -> tuple[list[str],list[str]]:
    source,target=source.resolve(),target.resolve()
    if source==target or source in target.parents or target in source.parents:
        raise ValueError('Extract the ZIP OUTSIDE the target repository, then run the installer.')
    if not target.is_dir() or not (target/'.git').exists():
        raise ValueError('Target must be an existing Git clone containing .git.')
    writes=[];removes=[]
    for p in sorted(source.rglob('*')):
        rel=p.relative_to(source)
        if any(x in ('.git','__pycache__') for x in rel.parts) or p.suffix=='.pyc':continue
        if not p.is_file():continue
        regular_path(p,source)
        dst=target/rel
        regular_path(dst,target)
        if dst.exists() and not dst.is_file():raise ValueError('File/directory collision: '+str(dst))
        if not dst.exists() or dst.read_bytes()!=p.read_bytes(): writes.append(rel.as_posix())
    for name,marker in LEGACY.items():
        p=target/name
        regular_path(p,target)
        if p.exists():
            if not p.is_file() or marker not in p.read_text(encoding='utf-8-sig'):
                raise ValueError('Unrecognized legacy file; not deleting: '+name)
            removes.append(name)
    return writes,removes


def install(source: Path, target: Path, writes: list[str], removes: list[str]) -> Path:
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
    backup=target.parent/(target.name+'.backup-'+stamp)
    backup.mkdir()
    manifest={'target':str(target),'created':[],'replaced':[],'removed':removes,
              'status':'preparing'}
    for rel in sorted(set(writes+removes)):
        p=target/rel
        if p.is_file():
            dest=backup/'files'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
            if rel in writes:manifest['replaced'].append(rel)
        elif rel in writes:manifest['created'].append(rel)
    def save(): (backup/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    save()
    try:
        for rel in writes:
            p=target/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/rel,p)
        for rel in removes:(target/rel).unlink()
        manifest['status']='copied';save()
    except Exception:
        for rel in manifest['created']:
            if (target/rel).is_file():(target/rel).unlink()
        for rel in manifest['replaced']+removes:
            p=target/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(backup/'files'/rel,p)
        manifest['status']='rolled-back';save();raise
    return backup


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target',type=Path)
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--yes',action='store_true')
    args=parser.parse_args()
    if args.target is None:
        default=r'D:\Dev\projects\modu-c-zmk-obrey'
        print('Existing repository path. Press Enter for: '+default)
        target=Path(input('> ').strip().strip('"') or default)
    else: target=args.target
    target=target.expanduser().resolve()
    writes,removes=plan(SOURCE,target)
    print('\nTarget:',target)
    for rel in writes:print('WRITE ',rel)
    for rel in removes:print('REMOVE obsolete generated file:',rel)
    if not writes and not removes:
        print('Already up to date. No files changed.');return
    if args.dry_run:print('Dry run only; no changes.');return
    for script in ('scripts/validate.py','scripts/check_combo_boot.py'):
        subprocess.run([sys.executable,str(SOURCE/script)],cwd=SOURCE,check=True)
    if not args.yes and input('\nBack up and apply these changes? [y/N] ').strip().lower()!='y':
        print('Cancelled. No files changed.');return
    backup=install(SOURCE,target,writes,removes)
    print('\nBackup:',backup)
    for script in ('scripts/validate.py','scripts/check_combo_boot.py'):
        subprocess.run([sys.executable,str(target/script)],cwd=target,check=True)
    print('\nApplied. No Git history, remote, commit or push was changed.')
    print('Review with: git status --short && git diff')
    print('Then commit only these files (also records listed obsolete deletions):')
    print('git add -- '+' '.join('"'+p+'"' for p in sorted(set(writes+removes))))
    print('git commit -m "Rebuild MODU config with source-aware 135 and 680 boot combos"')
    print('git push')


if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.CalledProcessError) as exc:
        raise SystemExit('STOP: '+str(exc))
