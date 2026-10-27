"""Build and execute the result-inspection notebook in a real IPython process."""
import os
from pathlib import Path
import nbformat as nbf
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

root = Path(__file__).resolve().parent
os.chdir(root)
nb = nbf.v4.new_notebook()
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.metadata.language_info = {"name": "python", "version": "3.12"}
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
nb.cells = [
    md("# Nghiên cứu giai đoạn 1: ảnh lá dược liệu, SVM và tối ưu\n"
       "Notebook này đọc và kiểm tra **kết quả chạy thật đã lưu**. Không tự huấn luyện lại hoặc chấm tập test. "
       "Để tái lập huấn luyện, dùng lệnh ở cuối notebook.\n\n"
       "Dữ liệu: [BDMediLeaves 6 loài](https://data.mendeley.com/datasets/t9rns2gmr3/1), Islam và cộng sự (2023), CC BY 4.0."),
    code("from pathlib import Path\nimport json, hashlib\nimport numpy as np\nimport pandas as pd\nfrom IPython.display import display, Image\n"
         "candidates = [Path.cwd(), Path.cwd().parent, Path.cwd() / 'medicinal-leaf-svm']\n"
         "ROOT = next((p for p in candidates if (p / 'data/audit/manifest.csv').exists()), None)\n"
         "assert ROOT is not None, 'Mở notebook trong thư mục dự án đã giải nén'\n"
         "manifest = pd.read_csv(ROOT / 'data/audit/manifest.csv')\n"
         "audit = json.loads((ROOT / 'data/audit/audit.json').read_text())\n"
         "protocol = json.loads((ROOT / 'results/pilot/protocol.json').read_text())\n"
         "assert protocol['test_evaluated'] is False\nprint('Đã đọc manifest; tập test chưa được chấm.')"),
    md("## 1. Kiểm toán dữ liệu\nẢnh được lọc theo hash của điểm ảnh sau giải mã. pHash chỉ dùng để nhóm ứng viên gần trùng, không thay thế mã mẫu cây/lá."),
    code("print('Ảnh nguồn:', audit['source_images'])\nprint('Bản trùng loại bỏ:', audit['exact_duplicates_removed'])\n"
         "print('Ảnh giữ lại:', audit['images_kept'])\ndisplay(pd.crosstab(manifest.label, manifest.split))\n"
         "leakage = json.loads((ROOT / 'data/audit/source_split_leakage.json').read_text())\n"
         "print('Test nguồn trùng train nguồn:', leakage['original_test_images_also_in_original_train'], '/', leakage['original_test_images'])"),
    code("assert manifest.pixel_sha256.nunique() == len(manifest)\n"
         "assert manifest.groupby('group').split.nunique().max() == 1\n"
         "dev = manifest[manifest.split == 'development']\n"
         "assert dev.groupby('group').cv_fold.nunique().max() == 1\n"
         "assert hashlib.sha256((ROOT / 'data/audit/manifest.csv').read_bytes()).hexdigest() == protocol['manifest_sha256']\n"
         "print('Đạt: ảnh không trùng điểm ảnh; nhóm không vượt qua split/fold; checksum đúng.')"),
    md("## 2. Kết quả CV, chưa phải điểm test\nMỗi phương pháp chạy 20 trial ở mỗi seed; 3 seed dùng cùng 3 fold. Macro-F1 coi các lớp quan trọng như nhau."),
    code("summary = pd.DataFrame(json.loads((ROOT / 'results/pilot/summary.json').read_text()))\n"
         "display(summary[['method','seed','best_cv_macro_f1','seconds']])\n"
         "display(summary[summary.method != 'baseline'].groupby('method').best_cv_macro_f1.agg(['mean','std','min','max']))"),
    code("display(Image(filename=str(ROOT / 'results/figures/convergence.png'), width=850))"),
    md("## 3. Cấu hình được chọn và giới hạn\nChọn bằng CV trên development. Cần chốt thiết kế rồi mới chấm 194 ảnh test. "
       "Không so trực tiếp với số liệu bài báo dùng khác loài, ảnh hoặc split. Mô hình chưa nhận biết loài lạ."),
    code("selection = json.loads((ROOT / 'results/pilot/selection.json').read_text())\n"
         "print(json.dumps(selection['winner'], ensure_ascii=False, indent=2))\n"
         "print((ROOT / 'results/verification.txt').read_text())"),
    md("## 4. Tái lập bằng terminal\nChạy tại thư mục dự án (đọc README để tạo môi trường):\n\n"
       "```bash\npython -m pip install -r requirements.txt\npython -m src.download\n"
       "python -m src.audit --images data/raw --out data/audit_recheck\n"
       "python -m src.experiment --trials 20 --out results/reproduction\n"
       "python -m unittest discover -s tests -v\n```\n\n"
       "Giữ nguyên bản kê `data/audit/manifest.csv`. Lệnh thí nghiệm không chấm test. "
       "Notebook đã được chạy tuần tự bằng IPython trong cùng tiến trình; chưa kiểm tra giao diện Jupyter/VS Code."),
]
shell = InteractiveShell.instance()
count = 0
for cell in nb.cells:
    if cell.cell_type != "code":
        continue
    count += 1
    with capture_output() as captured:
        result = shell.run_cell(cell.source, store_history=True)
    if result.error_before_exec or result.error_in_exec:
        raise RuntimeError(f"Notebook code cell {count} failed: {result.error_before_exec or result.error_in_exec}")
    outputs = []
    if captured.stdout:
        outputs.append(nbf.v4.new_output("stream", name="stdout", text=captured.stdout))
    if captured.stderr:
        outputs.append(nbf.v4.new_output("stream", name="stderr", text=captured.stderr))
    for item in captured.outputs:
        outputs.append(nbf.v4.new_output("display_data", data=item.data, metadata=item.metadata))
    cell.outputs = outputs
    cell.execution_count = count
nb.metadata.execution_validation = {"mode": "IPython in-process sequential cells", "code_cells_passed": count,
                                     "test_evaluated": False, "training_results_source": "results/pilot/"}
nbf.validate(nb)
(root / "notebooks").mkdir(exist_ok=True)
path = root / "notebooks/Nghien_cuu_giai_doan_1.ipynb"
nbf.write(nb, path)
print(f"Executed and validated {count} code cells: {path}")
