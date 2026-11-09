from pathlib import Path
import hashlib
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import core

class ArtifactContracts(unittest.TestCase):
    def test_source_and_artifact_digests(self):
        manifest = json.loads((ROOT / "results/manifest.json").read_text())
        for rel, digest in manifest["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest(), digest, rel)
        for rel, digest in manifest["artifact_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / "results" / rel).read_bytes()).hexdigest(), digest, rel)

    def test_generator_reproduces_committed_inputs(self):
        self.assertEqual(core.generate(), json.loads((ROOT / "data/dataset.json").read_text()))

import copy

def known():
    return [{"store":"a","period":"before","day":0,"accepted":900,"completed":810},
            {"store":"a","period":"after","day":0,"accepted":100,"completed":95},
            {"store":"b","period":"before","day":0,"accepted":100,"completed":50},
            {"store":"b","period":"after","day":0,"accepted":900,"completed":540}]

class CohortContracts(unittest.TestCase):
    def test_hand_calculated_simpson_reversal(self):
        result,_,_=core.audit(known(),{"a":.5,"b":.5})
        self.assertAlmostEqual(-.225,result['raw_common_stores']['difference'])
        self.assertAlmostEqual(.075,result['standardized_common_stores']['difference'])

    def test_sparse_store_excluded_from_both_periods(self):
        data=core.generate();result,pairs,excluded=core.audit(data['rows'],data['reference_weights'])
        self.assertEqual(19,len(pairs));self.assertEqual('store-19',excluded[0]['store'])
        self.assertAlmostEqual(.95,result['retained_reference_weight_fraction'])

    def test_no_supported_population_refuses(self):
        with self.assertRaises(ValueError):core.audit(known(),{'a':.5,'b':.5},min_support=1000)

    def test_duplicate_row_identity_is_not_double_counted(self):
        rows=known();rows.append(dict(rows[0]))
        with self.assertRaises(ValueError):core.aggregate(rows)

    def test_invalid_counts_reference_weights_and_missing_store_rejected(self):
        for value in [True,-1,float('nan'),1.5]:
            rows=known();rows[0]['accepted']=value
            with self.assertRaises(ValueError):core.audit(rows,{'a':.5,'b':.5})
        with self.assertRaises(ValueError):core.audit(known(),{'a':.5})
        with self.assertRaises(ValueError):core.audit(known(),{'a':float('nan'),'b':.5})

    def test_standardization_invariant_to_within_store_exposure_replication(self):
        rows=known();replicated=copy.deepcopy(rows)
        for r in replicated:
            multiplier=3 if r['store']=='a' else 2
            r['accepted']*=multiplier;r['completed']*=multiplier
        original,_,_=core.audit(rows,{'a':.5,'b':.5})
        changed,_,_=core.audit(replicated,{'a':.5,'b':.5})
        self.assertEqual(original['standardized_common_stores'],changed['standardized_common_stores'])

    def test_constant_pair_difference_gives_constant_interval(self):
        pairs=[{'weight':1,'difference':.125},{'weight':1,'difference':.125}]
        self.assertEqual([.125,.125],core.paired_interval(pairs,repetitions=100))
        with self.assertRaises(ValueError):core.paired_interval([{'weight':1,'difference':float('nan')}]*2)

    def test_reported_difference_reconciles_supported_pairs(self):
        pairs=json.loads((ROOT/'results/decisions.json').read_text())['supported_pairs']
        metrics=json.loads((ROOT/'results/metrics.json').read_text())
        weighted=sum(r['weight']*r['difference'] for r in pairs)/sum(r['weight'] for r in pairs)
        self.assertAlmostEqual(weighted,metrics['standardized_common_stores']['difference'])
