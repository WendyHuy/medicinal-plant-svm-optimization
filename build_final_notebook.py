"""Execute the final results notebook in IPython without training or rescoring test."""
import os,json
from pathlib import Path
import nbformat as nbf
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
root=Path(__file__).resolve().parent;os.chdir(root)
md,code=nbf.v4.new_markdown_cell,nbf.v4.new_code_cell
nb=nbf.v4.new_notebook();nb.metadata.kernelspec={'display_name':'Python 3','language':'python','name':'python3'}
nb.metadata.language_info={'name':'python','version':'3.12'}
nb.cells=[
md('# SVM cây dược liệu — đánh giá trước và sau tối ưu\nHuỳnh Gia Huy · 28/10/2026.\n\nNotebook đọc **kết quả đã chạy thật**; không huấn luyện hoặc chấm test lại. Dữ liệu [BDMediLeaves 6 loài](https://data.mendeley.com/datasets/t9rns2gmr3/1), Islam và cộng sự, CC BY 4.0. Học sâu chưa được thực hiện.'),
code("from pathlib import Path\nimport json, hashlib\nimport pandas as pd\nimport numpy as np\nfrom sklearn.metrics import f1_score, accuracy_score\nfrom IPython.display import display, Image\ncandidates=[Path.cwd(),Path.cwd().parent]\nROOT=next(p for p in candidates if (p/'data/audit/manifest.csv').exists())\nR=ROOT/'results/phase2'\nmanifest=pd.read_csv(ROOT/'data/audit/manifest.csv')\nfrozen=json.loads((R/'final/frozen_selection.json').read_text())\nassert hashlib.sha256((ROOT/'data/audit/manifest.csv').read_bytes()).hexdigest()==frozen['manifest_sha256']\nassert manifest.pixel_sha256.nunique()==len(manifest)\nassert manifest.groupby('group').split.nunique().max()==1\ndisplay(pd.crosstab(manifest.label,manifest.split))"),
md('## Chọn đặc trưng bằng development\nCV tham gia lựa chọn nên không phải đánh giá độc lập. Bộ 126 chiều được chọn trước test.'),
code("ablation=pd.read_csv(R/'ablation/summary.csv')\ndisplay(ablation[['feature_id','dimension','mean_cv_macro_f1']])\ndisplay(Image(filename=str(R/'figures/feature_ablation.png'),width=850))"),
md('## Hai phương pháp cùng ngân sách\n40 trial × 5 seed × 2 phương pháp = 400. Chọn phương pháp theo mean best-CV, giữ cả các seed kém.'),
code("trials=pd.read_csv(R/'hpo/trials.csv')\nassert len(trials)==400\nassert (trials.groupby(['method','seed']).size()==40).all()\nsummary=pd.DataFrame(json.loads((R/'hpo/summary.json').read_text()))\ndisplay(summary[['method','seed','best_cv_macro_f1','seconds']])\ndisplay(summary.groupby('method').best_cv_macro_f1.agg(['mean','std']))\ndisplay(Image(filename=str(R/'figures/stability_runtime.png'),width=850))"),
code("assert frozen['test_evaluated_at_freeze'] is False\nassert frozen['selected_method']=='random'\nprint('Lựa chọn trước test:',frozen['selected_method'])\nprint(json.dumps(frozen['best_by_method']['random'],indent=2))\ndisplay(Image(filename=str(R/'figures/convergence.png'),width=850))"),
md('## Tính lại chỉ số từ dự đoán đã lưu\nCùng 194 ảnh, mô hình chỉ fit trên 778 development. Không gọi fit hoặc predict trong notebook. TPE test cao hơn không thay đổi quyết định trước test.'),
code("pred=pd.read_csv(R/'evaluation/predictions.csv')\nmetrics=json.loads((R/'evaluation/metrics.json').read_text())\nrows=[]\nfor name,m in metrics.items():\n    f1=f1_score(pred.label,pred[name],average='macro')\n    acc=accuracy_score(pred.label,pred[name])\n    assert abs(f1-m['test_macro_f1'])<1e-12\n    assert abs(acc-m['test_accuracy'])<1e-12\n    rows.append({'model':name,'test_macro_f1':f1,'test_accuracy':acc,'train_macro_f1':m['train_macro_f1']})\ndisplay(pd.DataFrame(rows))\ndisplay(Image(filename=str(R/'figures/before_after_test.png'),width=850))"),
code("comparison=json.loads((R/'evaluation/comparison.json').read_text())\nassert comparison['selected_before_test']==frozen['selected_method']\nprint('Delta Macro-F1 (điểm phần trăm):',100*comparison['delta_test_macro_f1'])\nprint('Khoảng 95% ghép cặp:',[100*x for x in comparison['bootstrap']['selected_minus_baseline_macro_f1_ci95']])\nprint('Sửa lỗi:',comparison['corrected_errors'],'; lỗi mới:',comparison['new_errors'])\ndisplay(Image(filename=str(R/'figures/confusion_before_after.png'),width=850))"),
md('## Giới hạn và bước tiếp theo\nNhóm gần trùng không phải ID cây/phiên chụp. Test đã mở không còn là đánh giá kín cho thiết kế mới. Train F1=100% vẫn có nguy cơ quá khớp; chưa có unknown. Đổi đặc trưng tăng CV mạnh nhưng test mặc định chỉ 82,96% → 83,06%. Cần thu ảnh ngoài miền có nhãn kiểm định trước khi phát triển CNN + SVM hoặc fine-tune.'),
md('## Tái lập tại terminal\n```bash\npython -m pip install -r requirements.txt\npython -m src.reproduce --out results/reproduction_01\npython -m unittest discover -s tests -v\npython -m src.predict "anh_la.jpg" --compare\n```\nDùng thư mục kết quả mới. Xem README cho Windows. Notebook đã thực thi tuần tự bằng IPython cùng tiến trình; chưa kiểm thử giao diện Jupyter/VS Code.')]
shell=InteractiveShell.instance();count=0
for cell in nb.cells:
 if cell.cell_type!='code':continue
 count+=1
 with capture_output() as captured:result=shell.run_cell(cell.source,store_history=True)
 if result.error_before_exec or result.error_in_exec:raise RuntimeError(f'Cell {count}: {result.error_before_exec or result.error_in_exec}')
 outputs=[]
 for name in ['stdout','stderr']:
  value=getattr(captured,name)
  if value:outputs.append(nbf.v4.new_output('stream',name=name,text=value))
 outputs.extend(nbf.v4.new_output('display_data',data=item.data,metadata=item.metadata) for item in captured.outputs)
 cell.outputs=outputs;cell.execution_count=count
nb.metadata.execution_validation={'mode':'IPython in-process sequential','code_cells_passed':count,'trained_or_rescored_test':False}
nbf.validate(nb);nbf.write(nb,root/'notebooks/So_sanh_truoc_sau_toi_uu.ipynb')
(root/'results/phase2/notebook_verification.json').write_text(json.dumps(nb.metadata.execution_validation,indent=2))
print(f'Executed and validated {count} code cells')
