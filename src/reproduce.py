"""Run the complete predeclared phase-two experiment into a new directory."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/reproduction")
    a=p.parse_args()
    if Path(a.out).exists():raise SystemExit("Output already exists. Choose a new directory; saved results are never overwritten.")
    env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1")
    commands=[['src.download'],['src.develop','ablate','--out',a.out],
              ['src.develop','tune','--out',a.out],['src.evaluate','--out',a.out]]
    for command in commands:
        subprocess.run([sys.executable,'-m',*command],check=True,env=env)
