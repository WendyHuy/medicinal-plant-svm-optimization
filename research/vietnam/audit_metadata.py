"""Reproduce metadata audit. Python standard library only; no image training."""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import json
import re
import unicodedata

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"
RESULTS = ROOT / "results"


def normalize(text):
    return unicodedata.normalize("NFC", text).casefold().strip().strip(".?!:; ")


PREFIXES = [
    "tên dược liệu trong ảnh là ", "dược liệu trong ảnh là ",
    "dược liệu này là ", "tên của nó là ", "đó là vị thuốc ",
    "đây là ", "trong ảnh là ",
]
IDENTITY_QUESTIONS = {
    "Tên dược liệu trong ảnh là gì?",
    "Hãy cho biết tên gọi của dược liệu trong bức ảnh này?",
    "Đây là loại dược liệu gì?",
    "Vị thuốc xuất hiện trong hình có tên là gì?",
    "Hình ảnh này hiển thị dược liệu nào?",
    "Thực thể trong hình được sử dụng làm vị thuốc gì?",
}


def extract_name(answer):
    name = normalize(answer)
    for prefix in PREFIXES:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    if name.startswith("cây "):
        name = name[4:]
    return normalize(name)


def main():
    RESULTS.mkdir(exist_ok=True)
    policy = json.loads((ROOT / "species_policy.json").read_text())
    species = policy["species"]
    assert len(species) == len({s["species_id"] for s in species}) == 20
    aliases = {normalize(a): s["species_id"] for s in species for a in s["exact_vi_aliases"]}
    for forbidden in ["rau má lông", "rau má lá rau muống", "bông ổi", "gừng gió", "nghệ trắng", "tía tô dại"]:
        assert forbidden not in aliases
    assert aliases[extract_name("Tên dược liệu trong ảnh là Rau má.")] == "VN001"
    assert extract_name("Dược liệu trong ảnh là cây Thuốc bỏng.") == "thuốc bỏng"

    with (SOURCES / "vietmedi_metadata.csv").open(encoding="utf-8-sig", newline="") as f:
        vms = list(csv.DictReader(f))
    grouped = defaultdict(list)
    for row in vms:
        grouped[row["canonicalName"]].append(row)
    stats = json.loads((SOURCES / "vietmedi_image_statistics.json").read_text())
    vms_audit = {
        "metadata_rows": len(vms), "by_kingdom": dict(Counter(r["kingdom"] for r in vms)),
        "taxonomic_status": dict(Counter(r["taxonomicStatus"] for r in vms)),
        "unique_species_keys": len({r['speciesKey'] for r in vms}),
        "author_repository_image_statistics": stats,
        "caution": "Metadata rows are not verified image-bearing classes. The repository statistics and landing-page descriptions differ; verify archive before using either as a training count.",
    }
    splits = {}
    identity_rows = defaultdict(list)
    for split in ["train", "val", "test"]:
        rows = [json.loads(l) for l in (SOURCES / f"tdtu_{split}.jsonl").read_text().splitlines() if l.strip()]
        splits[split] = rows
        for row in rows:
            if row["question"] in IDENTITY_QUESTIONS:
                identity_rows[row["file_name"]].append({**row, "source_split": split})
    sets = {k: {r['file_name'] for r in v} for k, v in splits.items()}
    all_ids = set.union(*sets.values())
    assert set(identity_rows) == all_ids
    conflict_ids = [k for k, rr in identity_rows.items() if len({extract_name(r['answer']) for r in rr}) != 1]
    proposals = []
    excluded_similar_names = []
    for filename, rows in sorted(identity_rows.items()):
        if filename in conflict_ids:
            continue
        row = rows[0]
        name = extract_name(row['answer'])
        match = aliases.get(name)
        if match:
            proposals.append({
                "source": "TDTU_VQA", "source_file": filename,
                "source_split": row['source_split'], "raw_label": name,
                "candidate_species_id": match,
                "review_status": "pending_botanical_and_rights_review",
                "species_label_verified": False,
                "plant_id": None, "observation_id": None,
                "organs_visible": None, "growth_stage": None,
                "age_days": None, "training_eligible": False,
            })
        elif any(re.search(r'(?<!\w)' + re.escape(a) + r'(?!\w)', name) for a in aliases):
            excluded_similar_names.append({"source_file": filename, "raw_label": name, "reason": "substring_is_not_species_identity"})
    counts = Counter(p['candidate_species_id'] for p in proposals)
    shortlist = []
    for sp in species:
        matches = grouped[sp['scientific_name']]
        shortlist.append({**sp,
            "vms_metadata_matches": [{k: m[k] for k in ['speciesKey','canonicalName','vietnameseName','taxonomicStatus','kingdom']} for m in matches],
            "vms_verified_image_count": None,
            "tdtu_exact_name_candidate_images": counts[sp['species_id']],
            "verified_training_images_this_audit": 0,
            "status": "candidate_pending_image_inventory",
        })
    audit = {
        "date": "2026-10-29", "scope": "metadata audit; no model training or full-image audit",
        "vietmedi": vms_audit,
        "tdtu": {
            "qa_rows": sum(len(x) for x in splits.values()),
            "unique_image_paths": len(all_ids),
            "split_counts": {s: {"qa_rows":len(rr),"unique_image_paths":len(sets[s])} for s,rr in splits.items()},
            "filename_overlap": {a+'__'+b: len(sets[a]&sets[b]) for a,b in [('train','val'),('train','test'),('val','test')]},
            "identity_conflicts": conflict_ids,
            "exact_name_candidate_images": len(proposals),
            "species_with_exact_name_candidates": len(counts),
            "ambiguous_substring_images_not_assigned": len(excluded_similar_names),
            "note": "Counts are label-based retrieval candidates, not verified botanical identifications. Disjoint paths do not establish disjoint pixels, plants, or sessions.",
        },
        "species": shortlist,
    }
    for name, value in [('metadata_audit.json',audit),('candidate_images.json',proposals),('ambiguous_names_not_assigned.json',excluded_similar_names)]:
        (RESULTS/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    hashes = [{"file":p.name,"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(SOURCES.iterdir()) if p.is_file()]
    (RESULTS/'source_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({"vms_rows":len(vms),"tdtu_rows":audit['tdtu']['qa_rows'],"tdtu_images":len(all_ids),"exact_candidates":len(proposals),"species_with_candidates":len(counts),"conflicts":len(conflict_ids)},ensure_ascii=False))
    for s in shortlist: print(s['species_id'],s['name_vi'],s['tdtu_exact_name_candidate_images'])


if __name__ == '__main__':
    main()
