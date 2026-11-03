"""Create and execute a read-only notebook of recorded release results."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path

import nbformat as nbf
from IPython.core.interactiveshell import InteractiveShell

ROOT=Path(__file__).resolve().parent
cells=[]
def md(text): cells.append(nbf.v4.new_markdown_cell(text))
def code(text): cells.append(nbf.v4.new_code_cell(text))

md('# Kết quả dự án nhận diện cây dược liệu v0.3\nHuỳnh Gia Huy - 2474802010135 - 03/11/2026.\n\nNotebook đọc nhật ký đã lưu, tính lại chỉ số từ dự đoán OOF và kiểm tra mô hình. Run All không huấn luyện hoặc dự đoán lại test lịch sử.')
code('''from pathlib import Path
import json
import pandas as pd
from sklearn.metrics import f1_score, accuracy_score
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "results/phase3/nested_evaluation.json").exists())
R = ROOT / "results/phase3"
evaluation = json.loads((R / "nested_evaluation.json").read_text())
predictions = pd.read_csv(R / "nested_predictions.csv")
metadata = json.loads((ROOT / "models/phase3_metadata.json").read_text())
print("Số dự đoán outer OOF:", len(predictions))
print("Phạm vi:", evaluation["scope"])''')
md('## Trước và sau tối ưu\nĐây là kết quả nested CV trên development cũ. Chính sách chọn cấu hình 4 tham số được chấm ở outer-validation; mô hình refit cuối chưa có một tập test mới.')
code('''comparison = []
for model in ["baseline", "selected4"]:
    f1 = f1_score(predictions.label, predictions[model], average="macro")
    acc = accuracy_score(predictions.label, predictions[model])
    assert abs(f1 - evaluation["metrics"][model]["macro_f1"]) < 1e-12
    comparison.append({"model": model, "Macro-F1 %": 100*f1, "Accuracy %": 100*acc})
print(pd.DataFrame(comparison).to_string(index=False))''')
md('## Đối chứng 3 và 4 tham số\nMean/SD giữa seed không phải điểm của các bộ dữ liệu độc lập. Chính sách selected4 chọn qua hai phương pháp/năm seed nên có tổng ngân sách khác một search của một seed. Không kết luận bốn tham số luôn tốt hơn ba.')
code('''rows = [{"search": k, "mean OOF %": 100*v["mean_oof_macro_f1"], "SD điểm %": 100*v["sd_between_seeds"]}
        for k,v in evaluation["search_aggregate"].items()]
print(pd.DataFrame(rows).to_string(index=False))
log = [json.loads(line) for line in (R/"trials.jsonl").read_text().splitlines()]
assert len(log) == 3600
print("HPO trials:", len(log), "Inner CV fit:", 3*len(log))''')
md('## Ma trận nhầm lẫn và chỉ số từng loài')
code('''labels = evaluation["metrics"]["selected4"]["labels"]
matrix = pd.DataFrame(evaluation["metrics"]["selected4"]["confusion_matrix"], index=labels, columns=labels)
print(matrix.to_string())
print(pd.DataFrame(evaluation["metrics"]["selected4"]["classification_report"]).T.to_string())''')
md('## Cấu hình cuối và nguồn gốc\nGiữ kết quả test lịch sử riêng. Điểm 88,71% của giai đoạn 2 không so trực tiếp với điểm OOF mới. class_weight=None là giá trị được tìm ra, không phải bỏ qua tham số thứ tư.')
code('''import hashlib
model_path = ROOT / "models" / metadata["model_file"]
assert hashlib.sha256(model_path.read_bytes()).hexdigest() == metadata["model_sha256"]
print(json.dumps({k:metadata[k] for k in ["params", "selected_search", "training_images", "external_validation_completed"]}, indent=2))
old = json.loads((ROOT/"results/phase2/evaluation/metrics.json").read_text())
print("Macro-F1 test lịch sử Random3:", old["random"]["test_macro_f1"])
print("Không chấm lại test lịch sử trong notebook này.")''')
md('## Dữ liệu Việt Nam và giới hạn\nBiểu diễn texture128 đã được chọn trên development trong lịch sử. Nhóm là heuristic ảnh trùng, chưa phải ID cây. Bộ kiểm tra hiện chặn dữ liệu Việt Nam chưa xác minh; mô hình vẫn là sáu lớp ảnh lá, chưa huấn luyện nhiều bộ phận/học sâu hoặc phát hiện loài lạ.')
code('''readiness = json.loads((ROOT/"research/vietnam/readiness_v0_1.json").read_text())
assert readiness["ready_for_training"] is False
print(json.dumps(readiness, ensure_ascii=False, indent=2))''')

nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'}})
shell=InteractiveShell.instance()
count=0
for cell in nb.cells:
    if cell.cell_type!='code':continue
    count+=1
    stream=io.StringIO()
    with redirect_stdout(stream): result=shell.run_cell(cell.source,store_history=True)
    if result.error_before_exec or result.error_in_exec:raise RuntimeError(str(result.error_before_exec or result.error_in_exec))
    cell.execution_count=count
    cell.outputs=[nbf.v4.new_output('stream',name='stdout',text=stream.getvalue())]
target=ROOT/'notebooks/Ket_qua_du_an_v0_3.ipynb'
nbf.validate(nb);nbf.write(nb,target)
(ROOT/'results/phase3/notebook_verification.json').write_text(json.dumps({'file':str(target.relative_to(ROOT)),'executed_code_cells':count,'all_cells_succeeded':True,'training_rerun':False,'test_prediction_rerun':False},indent=2)+'\n')
print(target)
