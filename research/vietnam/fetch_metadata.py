"""Download the six small metadata files used by this audit; no image archive."""
from pathlib import Path
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json

ROOT = Path(__file__).resolve().parent
URLS = {
    "vietmedi_metadata.csv": "https://raw.githubusercontent.com/trientran/VietMediSpecies/feature/update/merged_species_with_gbif_metadata.csv",
    "vietmedi_image_statistics.json": "https://raw.githubusercontent.com/trientran/VietMediSpecies/feature/update/image_statistics.json",
    "tdtu_README.md": "https://huggingface.co/datasets/azan100an/tdtu_vqa_dataset_herb/raw/main/README.md",
    "tdtu_train.jsonl": "https://huggingface.co/datasets/azan100an/tdtu_vqa_dataset_herb/resolve/main/train_metadata.jsonl",
    "tdtu_val.jsonl": "https://huggingface.co/datasets/azan100an/tdtu_vqa_dataset_herb/resolve/main/val_metadata.jsonl",
    "tdtu_test.jsonl": "https://huggingface.co/datasets/azan100an/tdtu_vqa_dataset_herb/resolve/main/test_metadata.jsonl",
}


def download(item):
    name, url = item
    request = Request(url, headers={"User-Agent": "MedicinalLeafResearch/0.3 (academic data audit)"})
    with urlopen(request, timeout=40) as response:
        data = response.read()
    (ROOT / "sources" / name).write_bytes(data)
    return {"file": name, "url": url, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


if __name__ == "__main__":
    (ROOT / "sources").mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(download, URLS.items()))
    previous = ROOT / "results" / "source_hashes.json"
    if previous.exists():
        hashes = {r['file']: r['sha256'] for r in json.loads(previous.read_text())}
        for r in results:
            if r['file'] in hashes and r['sha256'] != hashes[r['file']]:
                print("SOURCE CHANGED; review before rerunning audit:", r['file'])
    (ROOT / "sources" / "retrieval_log.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("Downloaded", len(results), "metadata files. Original licenses apply.")
