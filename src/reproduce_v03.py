"""Re-run phase 3 in an isolated workspace, preserving deployed weights."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

from .download import download

ROOT = Path(__file__).resolve().parents[1]


def reproduce(out):
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError('Use a new output directory')
    if not out.is_relative_to(ROOT/'results'):
        raise ValueError('Output must be a new directory under results/')
    download(ROOT/'data')
    workspace = out/'workspace'
    workspace.mkdir(parents=True)
    shutil.copytree(ROOT/'src', workspace/'src', ignore=shutil.ignore_patterns('__pycache__'))
    (workspace/'docs').mkdir()
    (workspace/'models').mkdir()
    shutil.copyfile(ROOT/'docs/PHASE3_PROTOCOL.md', workspace/'docs/PHASE3_PROTOCOL.md')
    command = [sys.executable, '-m', 'src.phase3', '--images', str(ROOT/'data/raw'),
               '--manifest', str(ROOT/'data/audit/manifest.csv'), '--out', str(out/'experiment')]
    subprocess.run(command, cwd=workspace, check=True)
    print(f'New results: {out}/experiment; new weights: {workspace}/models')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='results/reproduction_v03_01')
    reproduce(parser.parse_args().out)
