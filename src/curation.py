"""Validate future Vietnam plant datasets without inventing labels or pairing."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def initialize(candidates):
    records = []
    for item in candidates:
        records.append({
            "image_id": "tdtu_" + Path(item["source_file"]).stem,
            "source": "TDTU_VQA", "source_record_id": item["source_file"],
            "source_url": "https://huggingface.co/datasets/azan100an/tdtu_vqa_dataset_herb/resolve/main/" + item["source_file"],
            "raw_species_label": item["raw_label"],
            "candidate_species_id": item["candidate_species_id"], "verified_species_id": None,
            "species_review_status": "pending", "reviewer": None, "review_evidence": None,
            "plant_id": None, "plant_id_basis": "unknown", "observation_id": None,
            "session_id": None, "capture_country": None,
            "organs_visible": [], "view_type": "unknown", "material_state": "unknown",
            "phenophases": None, "vegetative_stage": "unknown", "age_days": None, "age_evidence": None,
            "license": "CC-BY-NC-4.0 (dataset declaration; original-image rights unverified)",
            "creator": None, "attribution": None, "rights_review_status": "pending",
            "quality_decision": item.get("quality_decision", "pending"),
            "quality_reasons": [item["visual_note"]] if item.get("visual_note") else [],
            "duplicate_group_id": None, "split": "unassigned", "sha256": item.get("sha256"),
        })
    return records


def validate_records(records, multi_organ=False, images_root=None):
    schema = json.loads((ROOT / "research/vietnam/annotation_schema.json").read_text())
    validator = Draft202012Validator(schema)
    known = {r['species_id'] for r in json.loads((ROOT / "research/vietnam/species_policy.json").read_text())['species']}
    errors, warnings = [], []
    if not isinstance(records, list):
        return {"valid": False, "ready_for_training": False, "errors": ["Root must be a JSON list"]}
    seen = set()
    active = []
    for i, record in enumerate(records):
        prefix = f"row {i}"
        if not isinstance(record, dict):
            errors.append(prefix + ": expected object"); continue
        schema_errors = list(validator.iter_errors(record))
        for error in schema_errors:
            errors.append(prefix + ": " + error.message)
        if schema_errors:
            continue
        image_id = record.get('image_id')
        if image_id in seen:
            errors.append(prefix + ": duplicate image_id")
        seen.add(image_id)
        if record.get('verified_species_id') and record['verified_species_id'] not in known:
            errors.append(prefix + ": unknown verified species ID")
        if record.get('age_days') is not None and not record.get('age_evidence'):
            errors.append(prefix + ": age requires planting/sowing evidence")
        if record.get('quality_decision') != 'train_keep':
            continue
        active.append(record)
        if not record.get('organs_visible'):
            errors.append(prefix + ": no visible-organ annotation")
        if record.get('split') not in {'development', 'test', 'external_validation'}:
            errors.append(prefix + ": no assigned split")
        if not record.get('license') or not record.get('attribution'):
            errors.append(prefix + ": missing license or attribution")
        if not record.get('reviewer') or not record.get('review_evidence'):
            errors.append(prefix + ": missing botanical reviewer/evidence")
        if not record.get('duplicate_group_id'):
            errors.append(prefix + ": missing duplicate group")
        if multi_organ and (not record.get('plant_id') or not record.get('observation_id') or record.get('plant_id_basis') == 'unknown'):
            errors.append(prefix + ": multi-organ training requires proven plant and observation identity")
        if images_root is not None:
            root = Path(images_root).resolve()
            relative = record.get('image_path')
            if not relative:
                errors.append(prefix + ": missing image_path")
            else:
                path = (root / relative).resolve()
                if not path.is_relative_to(root) or not path.is_file():
                    errors.append(prefix + ": unsafe/missing local image")
                elif not record.get('sha256') or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
                    errors.append(prefix + ": image hash mismatch")
    for key in ['plant_id', 'observation_id', 'duplicate_group_id', 'sha256']:
        groups = defaultdict(list)
        for r in active:
            if r.get(key): groups[r[key]].append(r)
        for group, rows in groups.items():
            if len({r.get('split') for r in rows}) > 1:
                errors.append(f"{key} {group}: leakage across splits")
            if len({r.get('verified_species_id') for r in rows}) > 1:
                errors.append(f"{key} {group}: conflicting species")
    observations = defaultdict(list)
    for r in active:
        if r.get('observation_id'): observations[r['observation_id']].append(r)
    multi_count = 0
    for observation, rows in observations.items():
        if len({r.get('plant_id') for r in rows}) != 1:
            errors.append(f"observation {observation}: photos from multiple plants")
        if len(rows) >= 2 and len(set().union(*(set(r.get('organs_visible', [])) for r in rows))) >= 2:
            multi_count += 1
        elif multi_organ:
            errors.append(f"observation {observation}: fewer than two images/organs")
    counts = Counter(r.get('verified_species_id') for r in active)
    if not active:
        warnings.append("No images have completed botanical and rights review")
    if images_root is None:
        warnings.append("Image bytes not checked; pass --images-root before training release")
    for species, count in counts.items():
        if count < 30: warnings.append(f"{species}: only {count} images; independent-plant count must also be checked")
    return {"valid": not errors,
            "ready_for_training": not errors and bool(active) and images_root is not None and (not multi_organ or multi_count > 0),
            "n_records": len(records), "n_train_keep": len(active),
            "n_blocked": len(records) - len(active), "verified_species_counts": dict(counts),
            "multi_organ_observations": multi_count, "errors": errors, "warnings": warnings,
            "note": "Passing validation checks structure and recorded evidence, not botanical truth or sufficient statistical power."}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['init', 'validate'])
    parser.add_argument('--input', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--multi-organ', action='store_true')
    parser.add_argument('--images-root')
    args = parser.parse_args()
    records = json.loads(Path(args.input).read_text())
    result = initialize(records) if args.stage == 'init' else validate_records(records, args.multi_organ, args.images_root)
    target = Path(args.out)
    if target.exists(): raise FileExistsError("Use a fresh output path to preserve review history")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Saved {target}")
    if args.stage == 'validate':
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result['ready_for_training']: raise SystemExit(2)
