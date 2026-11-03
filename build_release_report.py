"""Build the release report from recorded metrics; never fit or predict."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'report'
R = ROOT/'results/phase3'
FIG = R/'figures'
FIG.mkdir(exist_ok=True)
E = json.loads((R/'nested_evaluation.json').read_text())
M = json.loads((ROOT/'models/phase3_metadata.json').read_text())
F = json.loads((R/'frozen_selection.json').read_text())
DONE = json.loads((R/'completed.json').read_text())
OLD = json.loads((ROOT/'results/phase2/evaluation/metrics.json').read_text())
PRED = pd.read_csv(R/'nested_predictions.csv')
S = json.loads((R/'search_summaries.json').read_text())
BASE, AFTER = E['metrics']['baseline'], E['metrics']['selected4']
LABELS = AFTER['labels']
SHORT = [x.split()[0] for x in LABELS]
md = []


def pct(v): return f'{v*100:.2f}%'.replace('.', ',')
def pp(v): return f'{v*100:+.2f}'.replace('.', ',')


def plots():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'figure.dpi':140})
    fig, ax = plt.subplots(figsize=(8,3.5))
    names = ['Default SVM','Random 3 HP','Random 4 HP','TPE 4 HP','Selected 4 HP policy']
    vals = [BASE['macro_f1']] + [E['search_aggregate'][k]['mean_oof_macro_f1'] for k in ['random3','random4','tpe4']] + [AFTER['macro_f1']]
    sds = [0] + [E['search_aggregate'][k]['sd_between_seeds'] for k in ['random3','random4','tpe4']] + [0]
    bars = ax.barh(names,np.array(vals)*100,xerr=np.array(sds)*100,color=['#A8B1B9','#7C9BB7','#C6A56A','#71A39A','#325F79'],capsize=4)
    ax.set_xlim(0,102);ax.set_xlabel('Nested OOF Macro-F1 (%)')
    for bar,v in zip(bars,vals):ax.text(99,bar.get_y()+bar.get_height()/2,f'{v*100:.2f}',ha='right',va='center')
    ax.invert_yaxis();ax.spines[['top','right']].set_visible(False)
    fig.tight_layout();fig.savefig(FIG/'nested_comparison.png');plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4,5))
    cm=np.array(AFTER['confusion_matrix']);im=ax.imshow(cm,cmap='Blues')
    ax.set_xticks(range(6),SHORT,rotation=35,ha='right');ax.set_yticks(range(6),SHORT)
    for i in range(6):
        for j in range(6):ax.text(j,i,str(cm[i,j]),ha='center',va='center',color='white' if cm[i,j]>cm.max()*.5 else 'black')
    ax.set_xlabel('Prediction');ax.set_ylabel('True class');fig.colorbar(im,ax=ax,shrink=.75)
    fig.tight_layout();fig.savefig(FIG/'nested_confusion.png');plt.close(fig)

    rows=[json.loads(l) for l in (R/'trials.jsonl').read_text().splitlines()]
    fig,ax=plt.subplots(figsize=(8,3.5))
    for name,color in [('random3','#7C9BB7'),('random4','#C6A56A'),('tpe4','#325F79')]:
        curves=[]
        for seed in [11,29,47,71,101]:
            vals=[x['mean_inner_macro_f1'] for x in rows if x['scope']=='full_development' and x['search']==name and x['seed']==seed]
            curves.append(np.maximum.accumulate(vals))
        curves=np.array(curves)*100;mean=curves.mean(axis=0);sd=curves.std(axis=0,ddof=1)
        ax.plot(range(1,41),mean,label=name,color=color);ax.fill_between(range(1,41),mean-sd,mean+sd,color=color,alpha=.13)
    ax.set_xlabel('Trials per seed');ax.set_ylabel('Best inner CV Macro-F1 (%)');ax.legend();ax.spines[['top','right']].set_visible(False)
    fig.tight_layout();fig.savefig(FIG/'full_dev_convergence.png');plt.close(fig)

    fig,ax=plt.subplots(figsize=(8,3.6));ys=np.arange(6)
    ax.barh(ys-.18,[BASE['classification_report'][l]['f1-score']*100 for l in LABELS],height=.35,label='Default',color='#A8B1B9')
    ax.barh(ys+.18,[AFTER['classification_report'][l]['f1-score']*100 for l in LABELS],height=.35,label='Selected4',color='#325F79')
    ax.set_yticks(ys,SHORT);ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xlabel('Nested OOF F1 (%)');ax.legend(loc='lower center',bbox_to_anchor=(.5,1.01),ncol=2)
    fig.tight_layout();fig.savefig(FIG/'per_class.png');plt.close(fig)


def setup():
    d=Document();s=d.sections[0]
    s.page_width=Inches(8.27);s.page_height=Inches(11.69)
    s.top_margin=s.bottom_margin=Inches(.70);s.left_margin=s.right_margin=Inches(.76)
    s.header_distance=s.footer_distance=Inches(.28)
    for name,size in [('Normal',11.5),('Title',21),('Subtitle',12),('Heading 1',16),('Heading 2',12.5),('Caption',9.5)]:
        style=d.styles[name];style.font.name='Times New Roman';style.font.size=Pt(size);style.font.color.rgb=RGBColor(0,0,0)
        fonts=style._element.get_or_add_rPr().rFonts
        for key in list(fonts.attrib):
            if 'theme' in key.lower():del fonts.attrib[key]
        for key in ['ascii','hAnsi','eastAsia','cs']:fonts.set(qn('w:'+key),'Times New Roman')
        for b in style._element.xpath('.//w:pBdr'):b.getparent().remove(b)
        style.paragraph_format.space_after=Pt(6)
    d.styles['Normal'].paragraph_format.line_spacing=1.10
    for name in ['Heading 1','Heading 2']:d.styles[name].paragraph_format.keep_with_next=True
    header=s.header.paragraphs[0];header.text='HUỲNH GIA HUY  |  NHẬN DIỆN CÂY DƯỢC LIỆU  |  v0.3'
    header.runs[0].font.size=Pt(8)
    foot=s.footer.paragraphs[0];foot.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    foot.add_run('03/11/2026  |  Trang ').font.size=Pt(9)
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');foot._p.append(field)
    d.core_properties.author='Huỳnh Gia Huy';d.core_properties.title='Tối ưu bốn siêu tham số SVM nhận diện cây dược liệu'
    return d


def p(text,style=None):
    d.add_paragraph(text,style);md.append(text+'\n')
def h(text):
    d.add_heading(text,2);md.append('### '+text+'\n')
def page(text):
    d.add_page_break();d.add_heading(text,1);md.append('## '+text+'\n')
def table(headers,rows,widths):
    t=d.add_table(rows=1,cols=len(headers));t.autofit=False
    for col,w in zip(t.columns,widths):col.width=Inches(w)
    for i,v in enumerate(headers):t.rows[0].cells[i].text=str(v)
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row):cells[i].text=str(v)
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        b=OxmlElement('w:'+edge);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
    t._tbl.tblPr.append(borders)
    for ri,row in enumerate(t.rows):
        tr=row._tr.get_or_add_trPr();cant=OxmlElement('w:cantSplit');tr.append(cant)
        if ri==0:tr.append(OxmlElement('w:tblHeader'))
        for ci,cell in enumerate(row.cells):
            cell.width=Inches(widths[ci]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            mar=OxmlElement('w:tcMar')
            for edge in ['top','left','bottom','right']:
                m=OxmlElement('w:'+edge);m.set(qn('w:w'),'75');m.set(qn('w:type'),'dxa');mar.append(m)
            cell._tc.get_or_add_tcPr().append(mar)
            if ri==0:
                sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E8EEF3');cell._tc.get_or_add_tcPr().append(sh)
            for para in cell.paragraphs:
                para.paragraph_format.space_after=Pt(2);para.paragraph_format.line_spacing=1.0
                para.alignment=WD_ALIGN_PARAGRAPH.LEFT if ci==0 else WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:run.font.size=Pt(10);run.bold=ri==0
    d.add_paragraph().paragraph_format.space_after=Pt(1)
    md.append('| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in rows)+'\n')
def fig(name,caption,width=6.6):
    para=d.add_paragraph();para.paragraph_format.keep_with_next=True;para.alignment=WD_ALIGN_PARAGRAPH.CENTER
    para.add_run().add_picture(str(FIG/name),width=Inches(width));p(caption,'Caption')


plots()
d=setup()
d.add_heading('Tối ưu bốn siêu tham số SVM nhận diện cây dược liệu',0)
md.append('# Tối ưu bốn siêu tham số SVM nhận diện cây dược liệu\n')
p('Báo cáo toàn bộ dự án và bản bàn giao v0.3','Subtitle')
p('Huỳnh Gia Huy  |  MSSV 2474802010135\nĐại học Văn Lang  |  Chuyên ngành Trí tuệ nhân tạo\nNgày hoàn thiện 03/11/2026')
h('Kết quả chính')
p(f'Dự án đã hoàn thành mô hình phân loại có giám sát ảnh lá của sáu loài BDMediLeaves, mở rộng miền tìm kiếm từ ba lên bốn siêu tham số và chuẩn bị nền dữ liệu cho cây dược liệu ở Việt Nam. Đánh giá bổ sung dùng nested CV theo nhóm trên 778 ảnh development cũ: Macro-F1 của SVM mặc định là {pct(BASE["macro_f1"])} và chính sách chọn cấu hình bốn tham số là {pct(AFTER["macro_f1"])}. Mức tăng là {pp(E["delta_selected4_minus_baseline"])} điểm phần trăm.')
table(['Đánh giá nested OOF trên 778 ảnh','Mặc định','Chính sách 4 tham số'],[
 ['Macro-F1',pct(BASE['macro_f1']),pct(AFTER['macro_f1'])],
 ['Accuracy',pct(BASE['accuracy']),pct(AFTER['accuracy'])],['Số ảnh đúng',BASE['correct'],AFTER['correct']]], [3.0,1.55,2.2])
p('Nested OOF là dự đoán ở vòng ngoài, khi ảnh đó không tham gia fit hoặc tìm siêu tham số của mô hình tương ứng. Kết quả này là phân tích tiếp nối có điều kiện theo biểu diễn và dữ liệu cũ; chưa phải đánh giá trên ảnh Việt Nam ngoài nguồn.')
h('Phạm vi đã hoàn thành')
p('Bản bàn giao có mô hình đã học, CLI, API ảnh lá, nhật ký 3.600 trial, dự đoán OOF, ma trận nhầm lẫn, notebook, kiểm tra tự động và hướng dẫn GitHub. Bộ tiêu chuẩn dữ liệu Việt Nam gồm 20 ứng viên, ưu tiên 12 loài. Mô hình hiện tại vẫn nhận diện sáu lớp ảnh lá; chưa huấn luyện thân, rễ hoặc mô hình học sâu.')

page('1 Bài toán và mục tiêu tối ưu')
p('Một ảnh lá có thể khó phân biệt do hình dạng tương tự giữa các loài, ánh sáng và nền chụp. Dự án bắt đầu từ đặc trưng màu và kết cấu thủ công để có mô hình nhẹ, chạy CPU và dễ kiểm chứng. Tối ưu siêu tham số là phần trọng tâm của bài tập Python; API chỉ là lớp tích hợp.')
h('Hàm mục tiêu')
p('Tìm x làm nhỏ nhất f(x) = 1 - mean inner CV Macro-F1. Macro-F1 là trung bình F1 của sáu lớp, trong đó F1 = 2TP/(2TP+FP+FN). StandardScaler được fit riêng trong mỗi tập train, sau đó biến đổi tập validation tương ứng.')
table(['Biến','Miền tìm kiếm','Ý nghĩa'],[
 ['kernel','linear hoặc rbf','Dạng kernel'],['C','log từ 0,001 đến 1.000','Mức phạt lỗi'],
 ['gamma','log từ 0,00001 đến 0,1','Chỉ hoạt động với RBF'],['class_weight','None hoặc balanced','Trọng số lớp']], [1.35,2.7,2.7])
p('Gamma là biến có điều kiện. Vì vậy miền có bốn biến khai báo nhưng nhánh linear không dùng gamma. class_weight=None là một kết quả hợp lệ của tìm kiếm, không có nghĩa chưa tìm tham số thứ tư. balanced điều chỉnh trọng số theo tần suất lớp trong tập train từng fold [2].')
h('Các đối chứng')
p('SVM mặc định dùng RBF, C=1, gamma=scale, class_weight=None. Random3 tìm kernel, C và gamma. Random4 và TPE4 thêm class_weight. Mỗi search chạy 40 trial cho mỗi seed; TPE có 10 trial khởi động ngẫu nhiên. Không dùng số seed hoặc số trial để thay thế số siêu tham số của mô hình.')
p('Không giả định bốn tham số luôn tốt hơn ba. Miền lớn hơn với cùng ngân sách mỗi search có thể phân bổ ít thử nghiệm hơn cho một vùng tốt. Kết luận phải dựa trên các đối chứng và sự biến thiên được ghi lại.')

page('2 Dữ liệu và kiểm toán')
p('Nguồn ảnh đã huấn luyện là BDMediLeaves V1 sáu loài, DOI 10.17632/t9rns2gmr3.1, công bố CC BY 4.0 [1]. Ảnh được thu thập ở Bangladesh. Có mặt một loài trong nghiên cứu không tự chứng minh bộ ảnh đại diện cho cách chụp hoặc điều kiện ở Việt Nam.')
table(['Bước kiểm toán','Số lượng'],[['Ảnh đọc được từ archive',1217],['Bản trùng pixel đã bỏ',245],['Ảnh sau lọc trùng',972],['Nhóm trùng hoặc gần trùng',971],['Development cho đợt mới',778],['Test lịch sử đã mở',194]], [4.7,2.05])
p('Cách chia nguồn có rò rỉ: 31/121 ảnh test gốc trùng ảnh train gốc. Dự án chia lại sau khi lọc trùng. pHash dưới phép quay/lật nhận diện thêm một cặp gần trùng; cặp được giữ cùng nhóm. Không có mã cây, lá hay phiên chụp thật, nên nhóm vẫn chỉ là heuristic.')
table(['Lớp nguồn','Ảnh duy nhất','Development','Test lịch sử'],[
 ['Centella asiatica',164,132,32],['Justicia adhatoda',162,130,32],['Kalanchoe pinnata',162,129,33],
 ['Mikania micrantha',160,128,32],['Phyllanthus emblica',157,125,32],['Terminalia arjuna',167,134,33]], [2.9,1.3,1.25,1.3])
p('Archive mang tên Non Augmented nhưng có tên ảnh chứa augmented; không khẳng định đây là toàn bộ ảnh camera chưa xử lý. Mã băm archive, từng file và manifest được lưu. Đợt này chỉ trích đặc trưng development, không chấm lại 194 ảnh test.')

page('3 Đặc trưng và kiến trúc mô hình')
p('Pipeline là ảnh RGB resize 128 x 128, trích HSV + LBP đa tỉ lệ + GLCM, chuẩn hóa StandardScaler và SVC. Mỗi vector có 126 chiều. Trích đặc trưng chỉ phụ thuộc một ảnh, không học thống kê từ toàn bộ dataset.')
table(['Thành phần','Thiết lập','Số chiều'],[
 ['HSV','16 bin cho mỗi kênh H S V',48],['LBP uniform','(P,R) = (8,1), (16,2), (24,3)',54],
 ['GLCM','32 mức xám; khoảng cách 1 và 3; bốn góc',24],['Tổng','texture128',126]], [1.4,4.1,1.25])
p('GLCM dùng contrast, dissimilarity, homogeneity, energy, correlation và ASM; lấy trung bình/độ lệch chuẩn qua góc. Bộ texture128 được chọn ở giai đoạn 2, không có HOG. Nền ảnh vẫn tham gia đặc trưng.')
h('Kết quả chọn đặc trưng trong lịch sử')
table(['Bộ mô tả','Số chiều','Macro-F1 CV'],[['v1 HOG HSV LBP',958,'75,21%'],['v1 bỏ màu',910,'71,50%'],['texture128',126,'85,63%'],['enhanced128 có HOG',1890,'78,04%'],['crop giữa 80 phần trăm có HOG',1890,'78,50%']], [3.9,1.2,1.65])
p('Biểu diễn texture128 đã được chọn bằng development trước đây. Do đó nested CV mới chỉ đánh giá tối ưu siêu tham số khi giữ biểu diễn này cố định; không xóa sai lệch lịch sử do chọn đặc trưng. Trong test lịch sử, v1 và texture128 mặc định đạt Macro-F1 gần nhau 82,96% và 83,06%; mức tăng CV không được suy thành mức tăng test tương ứng.')

page('4 Thiết kế thực nghiệm bổ sung')
p('Giao thức PHASE3_PROTOCOL.md và protocol.json được ghi trước trial đầu tiên, kèm hash mã, manifest và phiên bản thư viện. Outer CV gồm năm fold phân tầng theo nhóm, seed 2031; mỗi outer-train có ba inner fold theo nhóm, seed 2032 cộng số fold. Mọi nhóm được kiểm tra không giao nhau giữa train và validation [3].')
table(['Phạm vi','Search','Ngân sách HPO'],[['Mỗi outer fold','Random3 Random4 TPE4','3 x 5 seed x 40 trial'],['Năm outer fold','Tổng nested CV','3.000 trial / 9.000 CV fit'],['Toàn development','Ba search như trên','600 trial / 1.800 CV fit'],['Tổng mới','Không tính baseline và refit','3.600 trial / 10.800 CV fit']], [2.0,2.4,2.35])
p('Năm seed cố định là 11, 29, 47, 71 và 101. Chạy tuần tự với n_jobs=1 và một luồng BLAS/OMP; không pruning. Các seed dùng cùng dữ liệu, không phải năm bộ dữ liệu độc lập. Baseline có thêm 18 CV fit; các mô hình outer và mô hình cuối có 86 refit.')
h('Quy tắc chọn cấu hình')
p('Trong từng outer-train, tính mean best-inner-CV qua năm seed của Random4 và TPE4, có so baseline. Chọn phương pháp cao nhất, hòa ưu tiên baseline rồi Random4 rồi TPE4. Trong phương pháp đó chọn cấu hình cao nhất inner-CV, hòa ưu tiên C nhỏ, trial nhỏ rồi seed nhỏ. Outer-validation không được dùng để chọn.')
p('Chính sách selected4 thực hiện cùng quy tắc ở cả năm outer fold. Sau đánh giá, lựa chọn mô hình bàn giao được tính lại trên toàn development theo ba fold cố định cũ; không dùng outer-score hoặc test cũ để đổi lựa chọn.')
p('Đây là phân tích tiếp nối, không phải đăng ký nghiên cứu độc lập. Tập test cũ giữ vai trò kết quả lịch sử. Cần tập ảnh mới và mã cá thể thật để đánh giá khả năng dùng ngoài nguồn.')

page('5 Kết quả tìm kiếm và độ ổn định')
fig('nested_comparison.png','Hình 1 Macro-F1 nested OOF. Thanh sai số ở ba search là SD giữa năm seed; hai chính sách còn lại có một bộ dự đoán OOF.')
table(['Đối chứng','Mean OOF Macro-F1','SD giữa seed'],[
 [name, pct(E['search_aggregate'][key]['mean_oof_macro_f1']), f"{E['search_aggregate'][key]['sd_between_seeds']*100:.2f} điểm %".replace('.',',')]
 for name,key in [('Random3','random3'),('Random4','random4'),('TPE4','tpe4')]], [2.35,2.5,1.9])
p('Random3 có mean theo seed cao hơn cả Random4 và TPE4 trong thí nghiệm này. Random4 có độ biến thiên lớn nhất. Vì vậy chưa có bằng chứng rằng thêm class_weight làm chất lượng tăng ổn định ở cùng ngân sách mỗi search.')
p('Chính sách selected4 chọn TPE4 ở cả năm outer fold và đạt OOF cao hơn baseline. Chính sách này chọn qua năm seed và hai search bốn biến; không so trực tiếp nó với một seed Random3 như thể có cùng tổng ngân sách. Thứ hạng này không chứng minh phương pháp nào luôn tốt hơn trên dữ liệu khác.')

page('6 So sánh trước và sau tối ưu')
table(['Chỉ số nested OOF','Baseline','Selected4'],[
 ['Macro-F1',pct(BASE['macro_f1']),pct(AFTER['macro_f1'])],['Accuracy',pct(BASE['accuracy']),pct(AFTER['accuracy'])],
 ['Đúng trên 778 ảnh',BASE['correct'],AFTER['correct']],['Sai trên 778 ảnh',778-BASE['correct'],778-AFTER['correct']]], [3.1,1.8,1.85])
fig('nested_confusion.png','Hình 2 Ma trận nhầm lẫn của chính sách selected4 trên các dự đoán outer OOF',width=5.7)
p('So với baseline, selected4 sửa 34 lỗi nhưng phát sinh 19 lỗi mới, tăng ròng 15 ảnh đúng. Không chỉ báo số lỗi đã sửa mà bỏ qua lỗi mới.')
ci=E['bootstrap_diagnostic']['selected_minus_baseline_macro_f1_ci95']
p(f'Bootstrap ghép cặp theo nhóm 2.000 lần cho khoảng chẩn đoán delta Macro-F1 [{pp(ci[0])}; {pp(ci[1])}] điểm phần trăm. Các tập train outer chồng lấn, biểu diễn đã được chọn trên development và nhóm là heuristic; khoảng này không là bảo đảm độc lập cho ảnh cây mới.')

page('7 Phân tích từng loài và lỗi còn lại')
table(['Loài','F1 trước','F1 sau','Recall sau'],[[l,pct(BASE['classification_report'][l]['f1-score']),pct(AFTER['classification_report'][l]['f1-score']),pct(AFTER['classification_report'][l]['recall'])] for l in LABELS], [2.8,1.3,1.3,1.35])
fig('per_class.png','Hình 3 F1 từng lớp trên cùng các dự đoán nested OOF')
p('Kalanchoe có F1 cao nhất trong vòng đánh giá này. Justicia và Mikania còn nhiều nhầm lẫn. Terminalia không tăng F1 dù một số dự đoán thay đổi. Các cặp sai nổi bật gồm Terminalia sang Mikania 9 ảnh, Justicia sang Centella 8 ảnh, Centella sang Justicia 7 ảnh và Terminalia sang Justicia 7 ảnh.')
p('Đây là mô tả lỗi trên dữ liệu hiện tại; chưa xác minh cơ chế gây nhầm. Màu, nền và trạng thái lá là các giả thuyết cần thử bằng dữ liệu khác nguồn và thử nghiệm tách biệt, không kết luận từ ma trận nhầm lẫn đơn thuần.')

page('8 Mô hình bàn giao và kết quả lịch sử')
choice=F['selection']
p(f'Mô hình bàn giao được chọn bằng inner-CV trên toàn development: {M["selected_search"]}, seed {choice.get("seed")}, trial {choice.get("best_trial")}. Tham số cuối là kernel={M["params"]["kernel"]}, C={M["params"]["C"]:.8f}, gamma={M["params"]["gamma"]:.8f}, class_weight=None. Mô hình fit trên 778 ảnh; train Macro-F1 {pct(M["training_macro_f1"])}. Train-score cao không thay thế đánh giá ngoài mẫu.')
fig('full_dev_convergence.png','Hình 4 Best inner CV trên toàn development. Đường là mean và vùng tô là SD giữa năm seed, không phải test-score.')
table(['Đánh giá test lịch sử 194 ảnh','Macro-F1','Accuracy'],[['Baseline 126 chiều',pct(OLD['baseline']['test_macro_f1']),pct(OLD['baseline']['test_accuracy'])],['Random3 chọn ở giai đoạn 2',pct(OLD['random']['test_macro_f1']),pct(OLD['random']['test_accuracy'])],['TPE3 đối chứng',pct(OLD['tpe']['test_macro_f1']),pct(OLD['tpe']['test_accuracy'])]], [3.65,1.55,1.55])
p('Bảng test lịch sử giữ nguyên kết quả đã công bố; mô hình v0.3 chưa được chấm lại trên 194 ảnh này. Không ghép 88,71% test cũ và 88,06% nested OOF mới thành một phép so sánh tăng/giảm vì khác tập và giao thức.')
p('class_weight=None được tìm ra trong miền bốn biến. Dữ liệu sáu lớp gần cân bằng nên không kỳ vọng balanced mặc định tốt hơn. Không chứng minh riêng tác động của cân bằng lớp chỉ từ cấu hình thắng.')

page('9 Mở rộng dữ liệu cây dược liệu Việt Nam')
p('Nghiên cứu Việt Nam hiện có 20 ứng viên, ưu tiên 12 loài. Đã đọc metadata Viet Medi Species: 4.799 dòng, trong đó 4.667 thực vật; cả 20 ứng viên có dòng tên tương ứng. Thống kê repo phân biệt danh mục loài với loài có ảnh, nên không coi mọi dòng metadata là một lớp ảnh sẵn sàng [5].')
policy=json.loads((ROOT/'research/vietnam/species_policy.json').read_text())
table(['Mã','Loài ưu tiên','Tên khoa học mục tiêu'],[[s['species_id'],s['name_vi'],s['scientific_name']] for s in policy['species'] if s['priority']==1], [0.65,2.2,3.9])
p('Nhóm mở rộng là gừng, nghệ vàng, sả chanh, ổi, dâu tằm, bụp giấm, đậu biếc và chùm ngây. Ngải cứu, bạc hà, diệp hạ châu, mã đề và cà gai leo chờ xác minh danh pháp và ảnh dễ nhầm. Tên Việt không dùng làm khóa loài duy nhất.')
p('TDTU VQA có 29.151 cặp hỏi đáp nhưng chỉ 3.790 đường dẫn ảnh. Lọc tên chính xác ra 69 ứng viên. Sàng lọc 18 ảnh có chủ đích phát hiện 8 ảnh nghi không khớp nhãn và một cặp trùng byte mang hai nhãn; không suy tỷ lệ lỗi cho toàn bộ dataset. Chưa có ảnh nào hoàn thành đủ định danh và quyền sử dụng [6].')

page('10 Nhiều bộ phận và nền tảng tích hợp')
p('Mỗi quan sát tương lai phải gắn các ảnh với cùng cây/khóm và lần chụp: mặt trên lá, mặt dưới lá, thân/đốt và toàn cây. Hoa/quả bổ sung khi có. Thân rễ của gừng/nghệ phân biệt với rễ. Tuổi chỉ ghi khi có nhật ký gieo/trồng; không suy số tháng tuổi từ ảnh. Observation ID không tự chứng minh các phiên khác nhau là các cá thể khác nhau [7].')
h('Kiểm tra trước khi nhập dữ liệu')
p('Mô đun curation tạo bản ghi nhãn và kiểm tra schema, trạng thái định danh, người rà soát, giấy phép, ghi công, nhóm trùng, hash ảnh, rò rỉ theo cây/quan sát và việc ghép ảnh khác cây. Chạy trên 69 ứng viên hiện tại: cấu trúc hợp lệ nhưng ready_for_training=false, 0 train_keep và 0 quan sát nhiều bộ phận được xác minh. Đây là chặn đúng, không phải lỗi cần bỏ qua.')
h('API và CLI')
p('CLI mặc định dùng phase3_optimized.joblib. API có GET /health và POST /predict cho ảnh JPEG/PNG/WEBP, giới hạn 10 MB và 20 triệu pixel. API xác minh hash mô hình và đặc trưng, xử lý file tạm rồi xóa; không lưu ảnh tải lên. API từ chối khai báo organ khác leaf; người dùng vẫn cần gửi đúng loại ảnh vì hệ thống chưa tự phát hiện cơ quan.')
p('Đầu ra gồm nhãn trong sáu lớp và ba ứng viên kèm decision score của SVM. Điểm này chưa hiệu chỉnh, không phải xác suất đúng. Chưa có bộ phát hiện loài lạ; ảnh ngoài sáu lớp vẫn có thể bị gán vào một lớp đã biết. API hiện phù hợp demo nghiên cứu và tích hợp cục bộ [8].')
h('Website phổ cập kiến thức')
p('Kho tri thức có thể gồm tên chuẩn/tên địa phương, hình thái, giai đoạn, phân bố và cây dễ nhầm với nguồn riêng. Công dụng cần phân biệt bằng chứng truyền thống, tiền lâm sàng và lâm sàng, có rà soát chuyên môn. Không lấy nguyên QA chưa kiểm chứng để tạo hướng dẫn điều trị. Chưa phát hành website công cộng trong bản này.')

page('11 Kiểm chứng bàn giao và tài liệu tham khảo')
p('Bộ kiểm tra hiện có 25 test; 21 chạy đạt và 4 bỏ qua có lý do vì cache/trọng số thí nghiệm lịch sử không đưa vào Git. Các kiểm tra mới gồm đủ ngân sách, tính lại F1 từ OOF, tách nhóm, lựa chọn chỉ theo inner-CV, hash mô hình, chặn nhãn chưa kiểm định, chặn ghép khác cây và API với ảnh thật. CI được cấu hình để chạy sau khi người dùng push; chưa có kết quả CI từ GitHub.')
p(f'Thời gian đo lần này: trích đặc trưng development {DONE["feature_seconds"]:.2f} giây; tìm kiếm/đánh giá bổ sung {DONE["search_and_evaluation_seconds"]:.2f} giây, không gồm tải dữ liệu. Mô hình mới {M["model_bytes"]:,} byte. Các số này thuộc CPU môi trường thực nghiệm, không cam kết trên máy cá nhân.')
h('Tái lập và đưa lên GitHub')
p('Cài Python 3.12, tạo venv, cài requirements-api.txt. Chạy python -m unittest discover -s tests -v; dự đoán bằng python -m src.predict examples/centella_development.jpg --compare; mở API bằng python -m uvicorn src.service:app --host 127.0.0.1 --port 8000. Hướng dẫn tái lập nằm trong README; dùng thư mục kết quả mới để bảo toàn nhật ký.')
p('Bản ZIP có mã, trọng số, báo cáo, dữ liệu kiểm toán và lịch sử Git dạng bundle; không có raw archive hoặc môi trường ảo. Tạo repo của người dùng rồi push theo docs/GITHUB_UPLOAD.md. Commit giữ ngày thực tế; lịch sử vài ngày không thay thế yêu cầu làm bài trong năm tuần. Có hỗ trợ AI; sinh viên cần tự chạy và hiểu phương pháp trước khi nộp.')
h('Tài liệu tham khảo')
for text in [
'[1] Islam và cộng sự. BDMediLeaves V1. Mendeley Data 2023. DOI 10.17632/t9rns2gmr3.1. CC BY 4.0.',
'[2] scikit-learn. SVC API. https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html',
'[3] scikit-learn. Nested versus non-nested cross-validation. https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html',
'[4] Optuna. TPESampler 4.5.0. https://optuna.readthedocs.io/en/v4.5.0/reference/samplers/generated/optuna.samplers.TPESampler.html',
'[5] Tran và cộng sự. Viet Medi Species 2026. DOI 10.57760/sciencedb.013q9. Repo github.com/trientran/VietMediSpecies nhánh feature/update.',
'[6] azan100an. TDTU VQA Herb. huggingface.co/datasets/azan100an/tdtu_vqa_dataset_herb. CC BY-NC 4.0; quyền ảnh gốc cần kiểm tra.',
'[7] LifeCLEF 2014 Plant Task. https://www.imageclef.org/2014/lifeclef/plant',
'[8] FastAPI. Request files và Testing. https://fastapi.tiangolo.com/tutorial/',
]:p(text)
main=OUT/'Bao_cao_toan_bo_du_an_thao_duoc_v0_3.docx';d.save(main)
(OUT/'Bao_cao_toan_bo_du_an_thao_duoc_v0_3.md').write_text('\n'.join(md),encoding='utf-8')

# One-page defense brief.
d=setup();d.add_heading('Tóm tắt bảo vệ dự án nhận diện cây dược liệu',0)
p('Huỳnh Gia Huy  |  2474802010135  |  Bản v0.3 ngày 03/11/2026')
h('Bài toán và phương pháp')
p('Phân loại có giám sát ảnh lá sáu loài BDMediLeaves. HSV + LBP + GLCM tạo 126 đặc trưng, StandardScaler và SVM. Tối ưu kernel, C, gamma có điều kiện và class_weight; Random Search đối chứng TPE, 40 trial x 5 seed mỗi search.')
h('Kết quả mới cần trình bày')
table(['Nested OOF trên 778 ảnh','Baseline','Selected4'],[['Macro-F1',pct(BASE['macro_f1']),pct(AFTER['macro_f1'])],['Accuracy',pct(BASE['accuracy']),pct(AFTER['accuracy'])],['Đúng',670,685]], [3.4,1.65,1.7])
p('Tổng 3.600 trial / 10.800 CV fit. Tăng 1,89 điểm phần trăm Macro-F1; sửa 34 lỗi, phát sinh 19 lỗi. Bốn tham số đã được tìm kiếm nhưng chưa chứng minh tốt hơn ổn định so với ba tham số. Cấu hình cuối: RBF, C=6,6025932, gamma=0,00581874, class_weight=None.')
h('Giới hạn phải trả lời rõ')
p('Test lịch sử 194 ảnh đã mở, không chấm lại cho v0.3. Biểu diễn đã được chọn trên development cũ; nhóm chưa phải ID cây thật. Chưa có kiểm thử ngoài miền Việt Nam, học sâu hoặc từ chối loài lạ. Điểm SVM không phải xác suất đúng.')
h('Bàn giao và mở rộng')
p('Có mô hình, CLI, API cục bộ, notebook, báo cáo, 25 test và lịch sử Git. Bộ Việt Nam có 20 ứng viên, ưu tiên 12; 69 ảnh truy hồi chưa hoàn tất kiểm định. Bộ kiểm tra chặn ghép ảnh khác cây, nhãn chưa xác minh và rò rỉ theo nhóm. Chưa có mô hình nhiều bộ phận hoặc website công cộng.')
d.save(OUT/'Tom_tat_bao_ve_v0_3.docx')
print(main)
