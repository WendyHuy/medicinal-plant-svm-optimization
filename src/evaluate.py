"""One frozen evaluation batch on holdout data; no selection from test scores."""
import argparse
from datetime import datetime, timezone
import json
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, classification_report, confusion_matrix
from .features_v2 import extract
from .develop import digest, feature_code_hash, dump


def f1_from_ids(y, pred, nclasses):
    matrix=np.bincount(y*nclasses+pred,minlength=nclasses*nclasses).reshape(nclasses,nclasses)
    denominator=matrix.sum(axis=0)+matrix.sum(axis=1)
    return float(np.divide(2*np.diag(matrix),denominator,out=np.zeros(nclasses,dtype=float),where=denominator>0).mean())


def paired_bootstrap(y, predictions, groups, selected, iterations=2000, seed=2028):
    """Stratified cluster bootstrap, identical sampled rows for all predictions."""
    labels=np.unique(y);to_id={label:i for i,label in enumerate(labels)}
    yi=np.array([to_id[v] for v in y]);pi={key:np.array([to_id[v] for v in val]) for key,val in predictions.items()}
    strata=[]
    for label in labels:
        group_ids=np.unique(groups[y==label])
        if any(len(np.unique(y[groups==g]))!=1 for g in group_ids):
            raise ValueError("Bootstrap needs groups nested in classes")
        strata.append([np.flatnonzero(groups==g) for g in group_ids])
    rng=np.random.default_rng(seed)
    distributions={name:[] for name in predictions}
    differences=[]
    for _ in range(iterations):
        sampled=np.concatenate([members[i] for members in strata for i in rng.integers(0,len(members),len(members))])
        scores={name:f1_from_ids(yi[sampled],pred[sampled],len(labels)) for name,pred in pi.items()}
        for name,value in scores.items():distributions[name].append(value)
        differences.append(scores[selected]-scores["baseline"])
    return {"method":"paired class-stratified group percentile bootstrap","iterations":iterations,"seed":seed,
            "macro_f1_ci95":{name:np.quantile(v,[.025,.975]).tolist() for name,v in distributions.items()},
            "selected_minus_baseline_macro_f1_ci95":np.quantile(differences,[.025,.975]).tolist(),
            "limitation":"Groups are duplicate heuristics, not verified plant/leaf/session IDs; interval is conditional on this holdout."}


def evaluate(images,manifest,root):
    root,images,manifest=Path(root),Path(images),Path(manifest)
    frozen_path=root/"final/frozen_selection.json"
    frozen=json.loads(frozen_path.read_text())
    if digest(manifest)!=frozen["manifest_sha256"] or feature_code_hash()!=frozen["feature_code_sha256"]:
        raise ValueError("Frozen data or feature code changed before test evaluation")
    out=root/"evaluation"
    if (out/"started.json").exists():
        raise FileExistsError("Test evaluation already started. Inspect saved results; do not tune against the test.")
    bundles={name:joblib.load(root/f"final/{name}.joblib") for name in frozen["models_to_evaluate"]}
    for bundle in bundles.values():
        if bundle["frozen_selection_sha256"]!=digest(frozen_path):raise ValueError("Model does not match frozen selection")
        if bundle["manifest_sha256"]!=digest(manifest):raise ValueError("Model manifest mismatch")
        if bundle["feature_code_sha256"]!=feature_code_hash():raise ValueError("Model feature code mismatch")
    df=pd.read_csv(manifest)
    test=df[df.split=="test"].reset_index(drop=True)
    if df.groupby("group").split.nunique().max()!=1:raise ValueError("Group leakage")
    # Verify files against frozen source hashes before loading image content.
    for row in test.itertuples():
        if digest(images/row.path)!=row.file_sha256:raise ValueError(f"Test file changed: {row.path}")
    out.mkdir(parents=True,exist_ok=True)
    dump(out/"started.json",{"started_utc":datetime.now(timezone.utc).isoformat(),"selection_sha256":digest(frozen_path),
                             "selected_method_before_test":frozen["selected_method"],"models":list(bundles)})
    Xs,feature_times={},{}
    for fid in dict.fromkeys(b["feature_id"] for b in bundles.values()):
        tick=time.perf_counter();Xs[fid]=np.stack([extract(images/p,fid) for p in test.path]);feature_times[fid]=time.perf_counter()-tick
    y=test.label.to_numpy(dtype=str);labels=sorted(df.label.unique())
    results,predictions={},{}
    for name,bundle in bundles.items():
        X=Xs[bundle["feature_id"]];model=bundle["model"]
        pred=model.predict(X);predictions[name]=pred
        elapsed=[]
        for _ in range(10):
            tick=time.perf_counter();model.predict(X);elapsed.append(time.perf_counter()-tick)
        train=json.loads((root/f"final/{name}_train.json").read_text())
        result={"feature_id":bundle["feature_id"],"params":bundle["params"],"n_test":len(y),
                "test_accuracy":accuracy_score(y,pred),"test_macro_f1":f1_score(y,pred,average="macro",zero_division=0),
                "test_balanced_accuracy":balanced_accuracy_score(y,pred),
                "classification_report":classification_report(y,pred,labels=labels,output_dict=True,zero_division=0),
                "confusion_matrix":confusion_matrix(y,pred,labels=labels).tolist(),"labels":labels,
                "prediction_ms_per_image_median":float(np.median(elapsed)*1000/len(y)),
                "feature_ms_per_image_single_batch":feature_times[bundle["feature_id"]]*1000/len(y),
                "model_bytes":(root/f"final/{name}.joblib").stat().st_size,**train}
        result["train_test_macro_f1_gap"]=train["train_macro_f1"]-result["test_macro_f1"]
        results[name]=result
    selected=frozen["selected_method"]
    base_correct=predictions["baseline"]==y;selected_correct=predictions[selected]==y
    improved=int((~base_correct&selected_correct).sum());worsened=int((base_correct&~selected_correct).sum())
    p_value=binomtest(improved,improved+worsened,.5,alternative="two-sided").pvalue if improved+worsened else 1.0
    comparison={"selected_before_test":selected,"selected_feature_id":frozen["feature_id"],
                "delta_test_macro_f1":results[selected]["test_macro_f1"]-results["baseline"]["test_macro_f1"],
                "delta_test_accuracy":results[selected]["test_accuracy"]-results["baseline"]["test_accuracy"],
                "corrected_errors":improved,"new_errors":worsened,"mcnemar_exact_p_accuracy":p_value,
                "test_did_not_change_selection":True,
                "bootstrap":paired_bootstrap(y,predictions,test.group.to_numpy(),selected)}
    dump(out/"metrics.json",results);dump(out/"comparison.json",comparison)
    pd.DataFrame({"path":test.path,"label":y,"group":test.group,**predictions}).to_csv(out/"predictions.csv",index=False)
    pd.DataFrame([{ "model":name,**{key:val for key,val in values.items() if isinstance(val,(int,float,str))}} for name,values in results.items()]).to_csv(out/"metrics.csv",index=False)
    dump(out/"completed.json",{"completed_utc":datetime.now(timezone.utc).isoformat(),"selection_sha256":digest(frozen_path),
                               "models":list(results),"n_test":len(y),"test_evaluated":True})
    print(json.dumps({"metrics":{name:{k:v for k,v in val.items() if k in ['test_accuracy','test_macro_f1','train_macro_f1']} for name,val in results.items()},
                      "comparison":comparison},indent=2),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--images",default="data/raw")
    p.add_argument("--manifest",default="data/audit/manifest.csv")
    p.add_argument("--out",default="results/phase2")
    a=p.parse_args();evaluate(a.images,a.manifest,a.out)
