"""Download the verified original-image archive from its public publisher URL."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
import requests

URL = "https://data.mendeley.com/public-files/datasets/t9rns2gmr3/files/902634c0-25a2-4ac3-b9c1-f7d3775e4190/file_downloaded"
SHA256 = "6ce03e37e6a0d0d9d4a0b7a563053035b938bc2ad200126330e3b134b9b8a288"


def download(destination):
    destination = Path(destination)
    archive = destination / "source" / "originals.zip"
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        temporary = archive.with_suffix(".partial")
        with requests.get(URL, headers={"User-Agent": "MedicinalLeafResearch/0.1 (academic dataset inspection)"},
                          timeout=(20, 90), stream=True) as response:
            response.raise_for_status()
            with temporary.open("wb") as fh:
                for chunk in response.iter_content(1024 * 1024):
                    fh.write(chunk)
        if hashlib.sha256(temporary.read_bytes()).hexdigest() != SHA256:
            raise ValueError("Downloaded file checksum differs from the verified dataset version.")
        temporary.rename(archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Archive checksum mismatch")
    root = (destination / "raw").resolve()
    root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if not (root / name).resolve().is_relative_to(root):
                raise ValueError("Unsafe archive member")
        z.extractall(root)
    print(f"Verified archive and extracted images to {root}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--destination", default="data")
    download(p.parse_args().destination)
