import json
from pathlib import Path
import unittest

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from src.curation import initialize, validate_records
from src.develop import digest, feature_code_hash
from src.phase3 import grouped_folds, select_four

ROOT = Path(__file__).resolve().parents[1]


class SelectionAndCurationChecks(unittest.TestCase):
    def test_grouped_folds_keep_repeated_individuals_together(self):
        y = np.repeat(['a', 'b', 'c'], 30)
        groups = np.array([f'{label}{i//2}' for label in ['a', 'b', 'c'] for i in range(30)])
        folds = grouped_folds(y, groups, 3, 12)
        for fold in range(3):
            self.assertFalse(set(groups[folds == fold]) & set(groups[folds != fold]))

    def test_selection_uses_inner_scores_and_declared_tie_rule(self):
        rows = [{'search': method, 'seed': seed, 'params': {'kernel': 'rbf', 'C': 2., 'gamma': .01, 'class_weight': None},
                 'best_trial': 2, 'best_inner_macro_f1': .8}
                for method in ['random4', 'tpe4'] for seed in [11, 29]]
        self.assertEqual(select_four(rows, .8)['search'], 'baseline')
        self.assertEqual(select_four(rows, .7)['search'], 'random4')
        # Outer scores are deliberately irrelevant to the selection API.
        for row in rows: row['outer_macro_f1'] = 1. if row['search'] == 'tpe4' else 0.
        self.assertEqual(select_four(rows, .7)['search'], 'random4')

    def test_pending_candidates_cannot_become_training_data(self):
        records = initialize([{'source_file': 'data/a.jpg', 'raw_label': 'rau má', 'candidate_species_id': 'VN001'}])
        result = validate_records(records, multi_organ=True)
        self.assertTrue(result['valid'])
        self.assertFalse(result['ready_for_training'])
        self.assertEqual(result['n_train_keep'], 0)
        records[0]['age_days'] = 30
        self.assertFalse(validate_records(records)['valid'])

    def test_schema_blocks_unreviewed_train_keep(self):
        records = initialize([{'source_file': 'data/a.jpg', 'raw_label': 'rau má', 'candidate_species_id': 'VN001'}])
        records[0]['quality_decision'] = 'train_keep'
        result = validate_records(records, multi_organ=True)
        self.assertFalse(result['valid'])
        self.assertEqual(result['n_train_keep'], 0)

    def test_cross_split_plant_leakage_and_false_pairing_are_blocked(self):
        records = initialize([{'source_file': 'data/a.jpg', 'raw_label': 'rau má', 'candidate_species_id': 'VN001'},
                              {'source_file': 'data/b.jpg', 'raw_label': 'rau má', 'candidate_species_id': 'VN001'}])
        for i, record in enumerate(records):
            record.update(quality_decision='train_keep', verified_species_id='VN001', species_review_status='confirmed',
                          reviewer='test fixture', review_evidence='test fixture only', rights_review_status='research_and_web',
                          attribution='test fixture', material_state='living_plant', organs_visible=['leaf'] if i == 0 else ['stem'],
                          plant_id='same_plant', plant_id_basis='tagged_individual', observation_id='same_observation',
                          duplicate_group_id=f'd{i}', split='development' if i == 0 else 'test')
        self.assertTrue(any('leakage' in e for e in validate_records(records, True)['errors']))
        records[1].update(split='development', plant_id='different_plant')
        self.assertTrue(any('multiple plants' in e for e in validate_records(records, True)['errors']))


@unittest.skipUnless((ROOT/'results/phase3/completed.json').exists(), 'Phase 3 run not completed')
class Phase3ArtifactChecks(unittest.TestCase):
    def test_budget_and_scores_recompute(self):
        rows = [json.loads(l) for l in (ROOT/'results/phase3/trials.jsonl').read_text().splitlines()]
        self.assertEqual(len(rows), 3600)
        counts = {}
        for row in rows:
            key = row['scope'], row['search'], row['seed']
            counts[key] = counts.get(key, 0) + 1
            self.assertAlmostEqual(row['mean_inner_macro_f1'], np.mean(row['inner_fold_scores']), places=12)
            if row['search'] == 'random3': self.assertIsNone(row['params']['class_weight'])
            else: self.assertIn('class_weight', row['params'])
        self.assertEqual(len(counts), 90)
        self.assertEqual(set(counts.values()), {40})

    def test_predictions_cover_only_development_and_group_folds_are_disjoint(self):
        root = ROOT/'results/phase3'
        predictions = pd.read_csv(root/'nested_predictions.csv')
        manifest = pd.read_csv(ROOT/'data/audit/manifest.csv')
        self.assertEqual(set(predictions.path), set(manifest[manifest.split=='development'].path))
        self.assertFalse(set(predictions.path) & set(manifest[manifest.split=='test'].path))
        self.assertEqual(len(predictions), 778)
        self.assertEqual(predictions.groupby('group').outer_fold.nunique().max(), 1)
        for fold in range(5):
            inner = pd.read_csv(root/f'inner_assignments_outer{fold}.csv')
            self.assertFalse(set(inner.path) & set(predictions[predictions.outer_fold==fold].path))
            self.assertEqual(inner.groupby('group').inner_fold.nunique().max(), 1)
        evaluation = json.loads((root/'nested_evaluation.json').read_text())
        for name, metrics in evaluation['metrics'].items():
            self.assertAlmostEqual(metrics['macro_f1'], f1_score(predictions.label, predictions[name], average='macro'), places=12)

    def test_model_hash_and_freeze_match(self):
        metadata = json.loads((ROOT/'models/phase3_metadata.json').read_text())
        path = ROOT/'models'/metadata['model_file']
        bundle = joblib.load(path)
        self.assertEqual(digest(path), metadata['model_sha256'])
        self.assertEqual(bundle['feature_code_sha256'], feature_code_hash())
        self.assertEqual(bundle['frozen_selection_sha256'], digest(ROOT/'results/phase3/frozen_selection.json'))
        self.assertEqual(bundle['model'][0].n_samples_seen_, 778)
        self.assertEqual(bundle['params'], metadata['params'])
        self.assertFalse(metadata['external_validation_completed'])


class APIChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient
            from src.service import create_app
        except ImportError:
            raise unittest.SkipTest('Install requirements-api.txt')
        cls.client = TestClient(create_app())

    def test_rejects_corrupt_file_and_unsupported_organs(self):
        for data, organ in [(b'not an image', 'leaf'), (b'not an image', 'root')]:
            response = self.client.post('/predict', files={'file': ('leaf.jpg', data, 'image/jpeg')}, data={'organ': organ})
            self.assertEqual(response.status_code, 422)

    @unittest.skipUnless((ROOT/'models/phase3_optimized.joblib').exists(), 'New model not trained')
    def test_health_and_prediction_roundtrip(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['supported_organs'], ['leaf'])
        manifest = pd.read_csv(ROOT/'data/audit/manifest.csv')
        images = ROOT/'data/raw'
        paths = [images/p for p in manifest[manifest.split=='development'].path]
        path = next((p for p in paths if p.exists()), None)
        if path is None: path = ROOT/'examples/centella_development.jpg'
        response = self.client.post('/predict', files={'file': (path.name, path.read_bytes(), 'image/jpeg')})
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.json()['label'], self.client.get('/health').json()['labels'])
        self.assertFalse(response.json()['score_is_probability'])
        self.assertFalse(response.json()['unknown_species_detection'])
        from src.predict import predict
        self.assertEqual(response.json()['label'], predict(path, ROOT/'models/phase3_optimized.joblib'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
