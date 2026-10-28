"""Build the Vietnamese final Word report from the recorded experiment."""
import argparse
import json
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'report';OUT.mkdir(exist_ok=True)
R=ROOT/'results/phase2'
M=json.loads((R/'evaluation/metrics.json').read_text())
C=json.loads((R/'evaluation/comparison.json').read_text())
P=argparse.ArgumentParser();P.add_argument('--repo-url',default='');a=P.parse_args()

def setup():
 d=Document();s=d.sections[0]
 s.page_width=Inches(8.5);s.page_height=Inches(11)
 s.top_margin=s.bottom_margin=Inches(.72);s.left_margin=s.right_margin=Inches(.78)
 s.header_distance=s.footer_distance=Inches(.30)
 for name,size in [('Normal',12),('Title',22),('Subtitle',13),('Heading 1',16),('Heading 2',13),('Caption',10)]:
  style=d.styles[name];style.font.name='Times New Roman';style.font.size=Pt(size);style.font.color.rgb=RGBColor(0,0,0)
  style._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Times New Roman')
  fonts=style._element.get_or_add_rPr().rFonts
  for key in list(fonts.attrib):
   if 'theme' in key.lower():del fonts.attrib[key]
  fonts.set(qn('w:cs'),'Times New Roman')
  for border in style._element.xpath('.//w:pBdr'):border.getparent().remove(border)
  style.paragraph_format.space_after=Pt(6)
 d.styles['Normal'].paragraph_format.line_spacing=1.08
 for name in ['Heading 1','Heading 2']:
  d.styles[name].paragraph_format.space_before=Pt(10);d.styles[name].paragraph_format.keep_with_next=True
 h=s.header.paragraphs[0];h.text='HUỲNH GIA HUY  |  NHẬN DIỆN CÂY DƯỢC LIỆU';h.runs[0].font.size=Pt(9)
 f=s.footer.paragraphs[0];f.alignment=WD_ALIGN_PARAGRAPH.RIGHT
 f.add_run('Thực nghiệm 27–28/10/2026  •  Trang ').font.size=Pt(9)
 fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');f._p.append(fld)
 d.core_properties.author='Huỳnh Gia Huy';d.core_properties.subject='Tối ưu SVM trên BDMediLeaves 6 loài'
 return d

def p(t,style=None):return d.add_paragraph(t,style)
def h(t):return d.add_heading(t,level=2)
def page(t):d.add_page_break();d.add_heading(t,level=1)
def eq(t):
 para=d.add_paragraph();para.alignment=WD_ALIGN_PARAGRAPH.CENTER
 math=OxmlElement('m:oMath');run=OxmlElement('m:r');txt=OxmlElement('m:t');txt.text=t;run.append(txt);math.append(run);para._p.append(math)
 return para

def table(headers,rows,widths=None):
 t=d.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
 if widths:
  for col,width in zip(t.columns,widths):col.width=Inches(width)
 for i,v in enumerate(headers):t.rows[0].cells[i].text=str(v)
 for row in rows:
  cells=t.add_row().cells
  for i,v in enumerate(row):cells[i].text=str(v)
 pr=t._tbl.tblPr;borders=OxmlElement('w:tblBorders')
 for key in ['top','left','bottom','right','insideH','insideV']:
  e=OxmlElement('w:'+key);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
 pr.append(borders)
 for ri,row in enumerate(t.rows):
  trPr=row._tr.get_or_add_trPr();no=OxmlElement('w:cantSplit');trPr.append(no)
  if ri==0:
   rep=OxmlElement('w:tblHeader');trPr.append(rep)
  for ci,cell in enumerate(row.cells):
   if widths:cell.width=Inches(widths[ci])
   cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   cp=cell._tc.get_or_add_tcPr();mar=OxmlElement('w:tcMar')
   for edge in ['top','bottom','left','right']:
    m=OxmlElement('w:'+edge);m.set(qn('w:w'),'75');m.set(qn('w:type'),'dxa');mar.append(m)
   cp.append(mar)
   if ri==0:
    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E8EEF3');cp.append(sh)
   for para in cell.paragraphs:
    para.paragraph_format.space_after=Pt(2);para.paragraph_format.line_spacing=1.0
    para.alignment=WD_ALIGN_PARAGRAPH.LEFT if ci==0 else WD_ALIGN_PARAGRAPH.CENTER
    for run in para.runs:run.font.size=Pt(10.5);run.bold=(ri==0)
 d.add_paragraph().paragraph_format.space_after=Pt(0)
 return t

def fig(name,caption,width=6.75):
 para=d.add_paragraph();para.paragraph_format.keep_with_next=True
 para.alignment=WD_ALIGN_PARAGRAPH.CENTER;para.add_run().add_picture(str(R/'figures'/name),width=Inches(width))
 p(caption,'Caption')

# 1

d=setup()
d.add_heading('Tối ưu SVM trong nhận diện cây dược liệu qua ảnh lá',0)
p('Báo cáo thực nghiệm và đánh giá trước sau tối ưu','Subtitle')
p('Sinh viên: Huỳnh Gia Huy    |    MSSV: 2474802010135\nTrường Đại học Văn Lang    |    Ngày hoàn thiện: 28/10/2026')
h('Tóm tắt kết quả')
p('Nghiên cứu xây dựng hệ thống phân loại có giám sát ảnh lá của sáu loài trong BDMediLeaves, sau đó tối ưu siêu tham số SVM bằng Random Search và Tree-structured Parzen Estimator (TPE). Trọng tâm là thiết kế bài toán tối ưu, kiểm soát rò rỉ dữ liệu và đánh giá công bằng trên cùng một tập test giữ riêng.')
p('Sau kiểm toán, 1.217 ảnh nguồn còn 972 ảnh duy nhất theo điểm ảnh. Dự án dùng 778 ảnh để phát triển mô hình và 194 ảnh để đánh giá cuối. Bộ đặc trưng 126 chiều gồm màu HSV, LBP đa tỉ lệ và GLCM được chọn trên development. Hai phương pháp HPO chạy cùng ngân sách 40 trial mỗi seed, năm seed mỗi phương pháp, tổng 400 trial.')
table(['Chỉ số trên cùng 194 ảnh test','Trước tối ưu','Sau tối ưu'],[
 ['Macro-F1','83,06%','88,71%'],['Accuracy','82,99%','88,66%'],['Số ảnh đúng','161','172']], [3.25,1.75,1.75])
p('Random Search được chọn trước khi chấm test theo trung bình best-CV qua năm seed. Mức tăng Macro-F1 là 5,65 điểm phần trăm; khoảng bootstrap ghép cặp 95% là [2,01; 9,76] điểm phần trăm. TPE đạt Macro-F1 test 89,19% nhưng chỉ là đối chứng, không được dùng để đổi lựa chọn sau khi xem test.')
h('Đóng góp và phạm vi')
p('Sản phẩm gồm mã tái lập, manifest và nhật ký từng trial, hai mô hình trước–sau tối ưu, notebook đã thực thi, biểu đồ, báo cáo và bản tóm tắt bảo vệ. Các chỉ số được tính từ dự đoán đã lưu, có kiểm tra tự động đối chiếu. Đây là nghiên cứu học máy cổ điển; học sâu được đề xuất cho giai đoạn tiếp theo, chưa có kết quả CNN trong báo cáo.')
p('Kết quả chỉ áp dụng trong điều kiện của bộ dữ liệu. Chưa kiểm chứng trên cây, phiên chụp hoặc loài mới; không dùng dự đoán để quyết định sử dụng cây làm thuốc.')

#2
page('1 Cơ sở nghiên cứu và bài toán tối ưu')
h('Vì sao chọn hướng này')
p('Nhận diện qua lá phù hợp với một bài tập có nhãn và số lớp hữu hạn. SVM cho phép bắt đầu bằng đặc trưng thủ công, dùng CPU và tách rõ quá trình học mô hình với quá trình tìm siêu tham số. Random Search là đối chứng dễ tái lập [2]; TPE dùng các kết quả trial trước để đề xuất cấu hình tiếp theo [3]. Công trình liên quan đã nghiên cứu kết hợp CNN và SVM tối ưu cho cây dược liệu [10], tạo hướng nối tiếp khi có thêm dữ liệu và tài nguyên.')
p('Không so sánh trực tiếp độ chính xác của dự án với bài báo dùng dữ liệu hoặc cách chia khác. Đặc biệt, tỉ lệ trùng ảnh ở bộ nguồn làm việc kiểm toán trở thành điều kiện cần trước khi kết luận về chất lượng phân loại.')
h('Hai tầng tối ưu')
p('Với một cặp lớp, SVM mềm tìm siêu phẳng có biên lớn và cho phép sai lệch ξ. Bài toán huấn luyện nội bộ có dạng sau; C cân bằng độ rộng biên và phạt sai lệch. SVC mở rộng đa lớp bằng các bộ phân loại cặp lớp.')
eq('min  ½‖w‖² + C Σᵢ ξᵢ')
eq('yᵢ(wᵀφ(zᵢ) + b) ≥ 1 − ξᵢ,     ξᵢ ≥ 0')
p('Ở tầng ngoài, biến quyết định x là kernel, C và gamma. Mỗi cấu hình được đánh giá bằng ba fold development cố định. Với kernel RBF, gamma điều khiển phạm vi ảnh hưởng của từng mẫu [4].')
eq('K(z, z′) = exp(−γ‖z − z′‖²)')
eq('f(x) = 1 − meanCV(x),     x* = arg min f(x)')
table(['Biến','Miền tìm kiếm','Cách lấy mẫu'],[
 ['kernel','linear hoặc rbf','Phân loại'],['C','10⁻³ đến 10³','Log uniform'],['gamma khi RBF','10⁻⁵ đến 10⁻¹','Log uniform']], [1.7,2.55,2.5])
p('Ngân sách ràng buộc là 40 lần đánh giá hàm mục tiêu cho mỗi phương pháp và seed. Đây là tối ưu hộp đen có biến rời rạc và liên tục có điều kiện; không giả định hàm Macro-F1 khả vi. Thời gian và kích thước mô hình là chỉ số phụ, không phải mục tiêu đã được tối ưu đồng thời.')

#3
page('2 Dữ liệu và kiểm toán trước huấn luyện')
p('Nguồn chính thức là BDMediLeaves bản sáu loài, Mendeley Data V1, DOI 10.17632/t9rns2gmr3.1, CC BY 4.0 [1]. Dự án sử dụng archive Non Augmented Images-.zip, dung lượng 60.027.147 byte; không dùng bản BDMediLeaves mười loài. Các tên lớp được giữ nguyên từ nhãn nguồn.')
table(['Lớp','Nguồn','Duy nhất','Dev','Test'],[
 ['Centella Asiatica',204,164,132,32],['Justicia Adhatoda',202,162,130,32],['Kalanchoe Pinnata',202,162,129,33],['Mikania Micrantha',201,160,128,32],['Phyllanthus Emblica',200,157,125,32],['Terminalia Arjuna',208,167,134,33],['Tổng',1217,972,778,194]], [2.75,1.0,1.0,1.0,1.0])
h('Phát hiện rò rỉ trong cách chia nguồn')
p('Toàn bộ ảnh đọc được, kích thước 512 × 512. So sánh hash điểm ảnh phát hiện 245 bản sao cần loại. Có 93 nhóm trùng điểm ảnh xuất hiện ở nhiều tập nguồn; riêng 31 trong 121 ảnh test gốc trùng với train gốc. Giữ nguyên cách chia này có thể làm đánh giá lạc quan. Dự án vì vậy chia lại sau khi lọc trùng.')
p('Để hạn chế ảnh gần trùng, tính pHash 63 bit dưới các phép quay và lật D4, ngưỡng khoảng cách Hamming ≤4. Một cặp ứng viên được xem trực quan và giữ cùng nhóm. Kết quả là 971 nhóm cho 972 ảnh; cặp hai ảnh nằm cùng tập test. Đây là kiểm soát heuristic, không phải chứng nhận các ảnh thuộc các cây độc lập.')
h('Phân chia cố định')
p('Dùng StratifiedGroupKFold với năm phần, seed 2026; lấy phần đầu làm test. Phần development còn lại có 778 ảnh, chia tiếp thành ba fold nhóm với seed 2027. Cùng manifest được dùng cho mọi mô hình. 194 ảnh test gồm 193 nhóm, số ảnh mỗi lớp gần cân bằng.')
p('StandardScaler nằm trong pipeline và chỉ học thống kê từ train của từng fold; validation và test không tham gia fit [5]. Các bước chọn đặc trưng và siêu tham số chỉ dùng development. Hash archive, từng tệp ảnh, manifest và mã trích đặc trưng được lưu để phát hiện thay đổi.')
p('Giới hạn nguồn: không có mã cây, lá hay phiên chụp. Một số tên tệp chứa “augmented” dù archive do nguồn đặt tên Non Augmented. Vì vậy không khẳng định toàn bộ dữ liệu là ảnh camera chưa xử lý hoặc không có ảnh tương quan chưa được phát hiện.')

#4
page('3 Chọn bộ đặc trưng trên development')
p('Năm ứng viên được xác định trước trong PHASE2_PROTOCOL.md. Mỗi ứng viên dùng cùng SVM mặc định RBF, C=1, gamma=scale và cùng ba fold. Chọn điểm Macro-F1 CV trung bình cao nhất; nếu hòa thì ưu tiên ít chiều hơn. Thử nghiệm này không dùng điểm test để quyết định.')
fig('feature_ablation.png','Hình 1  So sánh đặc trưng với cùng SVM mặc định trên development',6.55)
h('Bộ đặc trưng được chọn')
p('texture128 xử lý ảnh RGB 128 × 128. Histogram HSV gồm 16 bin mỗi kênh, tổng 48 chiều. LBP uniform dùng các cặp số điểm–bán kính (8,1), (16,2), (24,3), cho 10+18+26=54 chiều [7]. GLCM dùng 32 mức xám, khoảng cách 1 và 3, các góc 0°, 45°, 90°, 135°; lấy trung bình và độ lệch chuẩn qua góc của sáu thuộc tính, tạo 24 chiều [8]. Tổng là 126 chiều.')
p('Sáu thuộc tính GLCM là contrast, dissimilarity, homogeneity, energy, correlation và ASM. Bộ được chọn không có HOG. Các ứng viên có HOG dùng hướng cạnh [9]; crop giữa 80% chỉ là phép cắt vùng trung tâm, không phải phân đoạn lá. Nền ảnh vẫn tham gia mọi bộ mô tả.')
h('Diễn giải có giới hạn')
p('texture128 đạt CV 85,63%, cao hơn v1 75,21%. Tuy nhiên, khi mở test cuối, v1 mặc định đạt 82,96% và texture128 mặc định đạt 83,06% Macro-F1. Mức tăng khoảng 10 điểm CV không lặp lại trên test. Điều này nhắc rằng CV đã tham gia lựa chọn có thể lạc quan [6]. So sánh HPO chính vì thế giữ cùng 126 đặc trưng ở cả trước và sau tối ưu.')

#5
page('4 Giao thức tối ưu và khóa lựa chọn')
h('Baseline và ngân sách công bằng')
p('Baseline chính là StandardScaler + SVC(kernel=rbf, C=1, gamma=scale) trên texture128. Random Search và TPE dùng cùng miền tham số, cùng ảnh, nhãn, fold và thước đo. Mỗi phương pháp chạy 40 trial với năm seed {11,29,47,71,101}; tổng 400 trial tương ứng 1.200 lần fit CV, chưa tính ablation, baseline, chẩn đoán OOF và refit cuối.')
p('TPE dùng 10 trial khởi động ngẫu nhiên, không pruning. Cả hai thực hiện tuần tự với n_jobs=1; số luồng BLAS/OMP=1. Random Search lấy mẫu độc lập trong miền; TPE phân biệt vùng cấu hình tốt và còn lại để gợi ý trial tiếp theo [3]. Lưu tham số, điểm từng fold, thời gian trial và thời gian tích lũy.')
h('Thước đo và quy tắc chọn')
eq('F1(c) = 2 TP(c) / (2 TP(c) + FP(c) + FN(c))')
eq('MacroF1 = (F1(1) + ⋯ + F1(6)) / 6')
p('Macro-F1 cho mỗi lớp trọng số bằng nhau. Mục tiêu trial là trung bình Macro-F1 của ba fold, không phải F1 của toàn bộ dự đoán OOF ghép lại. Accuracy, balanced accuracy và chỉ số từng lớp được ghi để giải thích kết quả cuối.')
p('Chọn phương pháp có trung bình best-CV qua năm seed lớn nhất, có so với baseline. Sau đó chọn cấu hình best-CV trong phương pháp đó. Nếu bằng nhau, ưu tiên C nhỏ hơn, số trial nhỏ hơn, rồi seed. Quy tắc này tránh chọn phương pháp chỉ dựa vào một seed thuận lợi; năm seed vẫn dùng chung dữ liệu, nên không phải năm mẫu dữ liệu độc lập.')
h('Đóng băng và chấm test')
p('Lựa chọn được lưu trong results/phase2/final/frozen_selection.json lúc 2026-10-27T14:56:15.951979+00:00, kèm hash manifest và mã đặc trưng. Mô hình được fit trên 778 ảnh development và lưu trước khi trích đặc trưng test. Một đợt đánh giá gồm v1 mặc định, baseline 126 chiều, Random và TPE; không chọn lại theo test.')
p('Đánh giá cuối lưu dự đoán từng ảnh và chỉ số. Khoảng tin cậy dùng 2.000 lần bootstrap ghép cặp theo nhóm, phân tầng lớp, seed 2028. McNemar chính xác chỉ dùng như phân tích bổ sung của đúng/sai (accuracy). Tệp started.json ngăn chạy lại đánh giá vào thư mục kết quả cũ.')

#6
page('5 Kết quả tối ưu qua năm seed')
table(['Seed','Random best-CV','TPE best-CV'],[
 [11,'86,99%','88,33%'],[29,'87,92%','88,33%'],[47,'86,12%','88,33%'],[71,'87,09%','84,57%'],[101,'87,94%','84,68%'],['Mean ± SD','87,21 ± 0,76%','86,85 ± 2,03%']], [1.15,2.8,2.8])
fig('convergence.png','Hình 2  Best-CV tích lũy qua 40 trial  Đường trung bình và vùng ±1 SD giữa seed',6.65)
p('Random Search có trung bình cao hơn và biến thiên thấp hơn trong năm lần chạy đã định. TPE đạt cấu hình đơn tốt nhất 88,33% ở ba seed, nhưng hai seed còn lại thấp hơn. Không loại các seed kém và không chạy bổ sung để thay chúng. Kết quả này không chứng minh Random Search luôn tốt hơn TPE trên dữ liệu khác.')
p('Hai seed TPE thấp chọn kernel linear. Giả thuyết là quá trình thăm dò ban đầu ảnh hưởng cách phân bổ trial giữa kernel; đây chỉ là diễn giải sau khi xem log, chưa có thí nghiệm tách riêng để xác nhận nguyên nhân. Với ngân sách nhỏ, phương pháp thích nghi không nhất thiết thắng đối chứng ngẫu nhiên.')
p('Mô hình được chọn là Random seed 101, trial 24: RBF, C=13,28777377006487 và gamma=0,006029953818540779, CV 87,94%. Cấu hình TPE đối chứng là seed 47, trial 36, C=15,010025821956374 và gamma=0,005581064619572679. Cả hai được giữ nguyên sau khi mở test.')

#7
page('6 Đánh giá trước và sau trên test')
table(['Mô hình','CV Macro-F1','Test Macro-F1','Test accuracy'],[
 ['v1 mặc định','75,21%','82,96%','82,99%'],['Baseline 126 chiều','85,63%','83,06%','82,99%'],['Random được chọn','87,94%','88,71%','88,66%'],['TPE đối chứng','88,33%','89,19%','89,18%']], [2.25,1.5,1.5,1.5])
fig('before_after_test.png','Hình 3  Bốn mô hình trên cùng holdout  Thanh sai số là khoảng bootstrap 95%',6.65)
p('So sánh chính là baseline và Random trên cùng 126 đặc trưng: Macro-F1 tăng 5,65 điểm phần trăm, accuracy tăng 5,67 điểm. Baseline sai 33 ảnh; Random sai 22 ảnh. Trong các thay đổi, 13 ảnh từ sai thành đúng và 2 ảnh từ đúng thành sai. TPE đúng 173 ảnh, hơn Random một ảnh, nhưng không làm thay đổi quyết định đã khóa.')
p('Khoảng bootstrap 95% của Macro-F1: baseline [77,42%; 88,12%], Random [84,21%; 92,79%]. Phép bootstrap ghép cặp trực tiếp cho chênh lệch là [+2,01; +9,76] điểm phần trăm. Không suy ra ý nghĩa của chênh lệch chỉ bằng việc xem hai khoảng riêng có giao nhau hay không.')
p('McNemar chính xác có p=0,00739 cho chênh lệch đúng/sai. Đây không phải kiểm định Macro-F1. Cần thận trọng vì nhóm chỉ phản ánh ảnh trùng/gần trùng đã phát hiện, chưa có ID cây hoặc phiên chụp thật. Khoảng bootstrap và p-value đều không thay thế một kiểm thử ngoài miền độc lập.')

#8
page('7 Phân tích theo loài và lỗi còn lại')
fig('confusion_before_after.png','Hình 4  Ma trận nhầm lẫn trước và sau tối ưu  Hàng là nhãn thật và cột là dự đoán',6.7)
table(['Loài','F1 trước','F1 sau','Recall sau'],[
 [label,f'{M["baseline"]["classification_report"][label]["f1-score"]*100:.2f}%',f'{M["random"]["classification_report"][label]["f1-score"]*100:.2f}%',f'{M["random"]["classification_report"][label]["recall"]*100:.2f}%'] for label in M['random']['labels']], [2.9,1.25,1.25,1.35])
p('F1 của cả sáu lớp đều tăng trên holdout này. Justicia Adhatoda có recall 100% trên 32 ảnh, nhưng số mẫu nhỏ nên không thể khẳng định luôn nhận diện đúng. Centella Asiatica còn F1 80%, thấp nhất trong sáu lớp; đây là nhóm cần ưu tiên thu thêm dữ liệu và kiểm định nhãn ở giai đoạn tiếp theo.')
p('Sau tối ưu, bốn ảnh Centella Asiatica và bốn ảnh Terminalia Arjuna bị nhận thành Phyllanthus Emblica. Ba ảnh Kalanchoe Pinnata bị nhận thành Centella Asiatica. Các ảnh lỗi có khác biệt góc chụp, nền và tỉ lệ lá trong khung; chưa có thí nghiệm chứng minh riêng yếu tố nào gây lỗi.')
p('Hình test_failure_examples.png lưu sáu lỗi Centella đầu tiên theo thứ tự manifest để kiểm tra trực quan, không đại diện cho tần suất lỗi toàn bộ dữ liệu. Phân tích test ở đây phục vụ giải thích mô hình đã khóa; mọi chỉnh sửa theo các lỗi này cần được kiểm chứng trên một tập test mới.')

#9
page('8 Chi phí tính toán và mức độ tin cậy')
table(['Đại lượng','Baseline','Random'],[
 ['Fit trên 778 ảnh','0,0301 giây','0,0308 giây'],['Phân loại sau trích đặc trưng','0,0489 ms/ảnh','0,0444 ms/ảnh'],['Tệp mô hình nén','384.346 byte','355.153 byte'],['Support vector','660','604'],['Train Macro-F1','97,05%','100,00%'],['Test Macro-F1','83,06%','88,71%']], [3.3,1.7,1.75])
p('Thời gian phân loại là trung vị của 10 lần dự đoán theo batch, chia số ảnh; không phải độ trễ đầu cuối của một yêu cầu đơn lẻ. Trích texture128 mất khoảng 23,58 ms/ảnh trong một batch test, dùng chung cho hai mô hình. Trích đặc trưng vì vậy chi phối chi phí so với bước SVM. Không suy ra tốc độ trên điện thoại hay máy khác từ phép đo này.')
p('Random và TPE lần lượt mất trung bình 3,18 và 3,19 giây cho 40 trial khi đặc trưng đã cache. Phép đo dùng CPU, một luồng tính toán; không gồm tải dữ liệu và trích đặc trưng. Môi trường khóa phiên bản Python 3.12, scikit-learn 1.8.0, scikit-image 0.25.2 và Optuna 4.5.0. Chi tiết các gói nằm trong requirements.txt và protocol.json.')
h('Khoảng cách tổng quát hóa')
p('Random đạt train Macro-F1 100% nhưng test 88,71%, chênh 11,29 điểm phần trăm. Tối ưu cải thiện holdout song chưa loại bỏ khả năng quá khớp. Chọn đặc trưng và tham số trên cùng development cũng làm CV sau chọn có thiên lệch; báo cáo không gọi đó là đánh giá độc lập hoặc nested CV đầy đủ.')
h('Giới hạn quan trọng')
p('Thứ nhất, chỉ một bộ dữ liệu nhỏ và sáu lớp, không có mẫu ngoài miền Việt Nam. Thứ hai, không có ID cây/phiên chụp, nên kiểm toán trùng chưa loại hết phụ thuộc giữa ảnh. Thứ ba, nền và màu tham gia đặc trưng nên mô hình có thể học tín hiệu không ổn định. Thứ tư, nhãn nguồn chưa được chuyên gia kiểm định độc lập trong dự án. Cuối cùng, mô hình không có unknown và luôn đưa một nhãn trong sáu lớp, kể cả ảnh không thuộc bài toán.')
p('Vì các giới hạn này, mức tăng 5,65 điểm là bằng chứng thực nghiệm trong giao thức đã nêu, không phải cam kết an toàn hoặc hiệu quả nhận dạng cây ngoài thực địa.')

#10
page('9 Kiểm chứng tái lập và hướng phát triển')
h('Bộ hồ sơ đã bàn giao')
p('Mã nguồn có lệnh tải và kiểm tra SHA-256, audit dữ liệu, ablation, HPO và đánh giá. trials.csv/trials.jsonl có đủ 400 trial; predictions.csv lưu 194 dự đoán mỗi mô hình. models/baseline.joblib và models/optimized.joblib là hai mô hình đã học, kèm metadata và hash. Notebook đọc các kết quả này để người xem kiểm tra mà không tự huấn luyện lại.')
p('Chạy thử: python -m src.predict "anh_la.jpg" --compare. Tái lập đầy đủ: python -m src.reproduce --out results/reproduction_01. Chương trình yêu cầu thư mục mới, giữ nguyên kết quả gốc. Chạy kiểm tra: python -m unittest discover -s tests -v. README có lệnh cụ thể cho Windows và Linux.')
p('Kiểm tra tự động đối chiếu chia tập/nhóm, đặc trưng hữu hạn, cache chỉ development, hash mã và mô hình, ngân sách trial, điểm fold, metrics tính lại từ dự đoán và bảo vệ không ghi đè đánh giá test. Bản clone không chứa cache/mô hình pilot sẽ bỏ qua các kiểm tra phụ thuộc các tệp này; log riêng ghi số kiểm tra và số bỏ qua.')
p('Trong lần khôi phục phiên, JSONL thiếu sáu dòng cuối trong khi CSV đã hoàn tất 400 dòng. Đã đối chiếu 394 dòng khớp, tính lại 18 fold của sáu trial thiếu với sai số ≤10⁻¹² rồi phục hồi log. Không có trial mới hoặc thay đổi lựa chọn. Bằng chứng được ghi trong log_integrity_recovery.json.')
h('Hướng phát triển phù hợp')
p('Bước ưu tiên là dữ liệu: thu ảnh theo cây/phiên chụp, kiểm định nhãn và giữ tập ngoài miền trước các quyết định mới. Có thể thử phân đoạn lá hoặc kiểm tra ảnh ngoài tập lớp. Sau đó so sánh bộ trích CNN tiền huấn luyện + SVM với baseline hiện tại; khi đủ dữ liệu và ngân sách, fine-tune MobileNet hoặc EfficientNet. Ảnh, nhãn và cấu trúc manifest có thể tái sử dụng, nhưng test hiện tại đã mở và cần một holdout mới cho kết luận tiếp theo.')
h('Kết luận và minh bạch')
p('Chốt hướng dự án hiện tại là tối ưu siêu tham số SVM cho nhận diện cây dược liệu qua ảnh lá. Random Search đạt kết quả chính tốt hơn baseline trên holdout và được giữ theo quy tắc trước test. Học sâu là giai đoạn phát triển sau, không được trình bày như phần đã thực hiện.')
p('AI hỗ trợ tra cứu, viết mã, phân tích và soạn báo cáo. Sinh viên cần tự đọc, chạy lại và giải thích trước khi nộp. Các checkpoint thực hiện ngày 27–28/10/2026 không thay thế yêu cầu tiến độ năm tuần; không lùi ngày commit.')
p(('Kho GitHub đã xuất bản: '+a.repo_url) if a.repo_url else 'Trạng thái GitHub: chưa xuất bản ở thời điểm tạo báo cáo; bước tạo kho đang cần đăng nhập tài khoản. Bộ mã và kết quả đã sẵn sàng bàn giao.')

#11
page('10 Tài liệu tham khảo và dấu vết kết quả')
refs=[
 '[1] Islam, S. và cộng sự (2023). BDMediLeaves, Mendeley Data V1, bản sáu loài. DOI 10.17632/t9rns2gmr3.1. CC BY 4.0. https://data.mendeley.com/datasets/t9rns2gmr3/1',
 '[2] Bergstra, J., Bengio, Y. (2012). Random Search for Hyper-Parameter Optimization. JMLR 13, 281–305. https://jmlr.org/papers/v13/bergstra12a.html',
 '[3] Optuna 4.5.0. TPESampler API. https://optuna.readthedocs.io/en/v4.5.0/reference/samplers/generated/optuna.samplers.TPESampler.html',
 '[4] scikit-learn. RBF SVM parameters. https://scikit-learn.org/stable/auto_examples/svm/plot_rbf_parameters.html',
 '[5] scikit-learn. Common pitfalls and recommended practices. https://scikit-learn.org/stable/common_pitfalls.html',
 '[6] scikit-learn. Nested versus non-nested cross-validation. https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html',
 '[7] scikit-image 0.25.x. Local Binary Pattern for texture classification. https://scikit-image.org/docs/0.25.x/auto_examples/features_detection/plot_local_binary_pattern.html',
 '[8] scikit-image 0.25.x. GLCM Texture Features. https://scikit-image.org/docs/0.25.x/auto_examples/features_detection/plot_glcm.html',
 '[9] scikit-image 0.25.x. Histogram of Oriented Gradients. https://scikit-image.org/docs/0.25.x/auto_examples/features_detection/plot_hog.html',
 '[10] Diwedi và cộng sự (2024). Công trình CNN kết hợp SVM tối ưu cho nhận diện cây dược liệu. Multimedia Tools and Applications. DOI 10.1007/s11042-023-16733-8. https://link.springer.com/article/10.1007/s11042-023-16733-8'
]
for text in refs:
 q=p(text);q.paragraph_format.space_after=Pt(6)
 for run in q.runs:run.font.size=Pt(10.5)
p('Nguồn kiểm tra trong đợt nghiên cứu 27–28/10/2026. Mục [10] dùng mô tả/tóm tắt của nhà xuất bản để xác định hướng liên quan; không tái lập hoặc so trực tiếp điểm số. Ảnh minh họa từ [1], đã resize, lọc trùng và chia lại; giấy phép ảnh vẫn là CC BY 4.0.','Caption')
h('Tệp số liệu quyết định kết luận')
p('results/phase2/ablation/summary.json — lựa chọn đặc trưng\nresults/phase2/hpo/summary.json — kết quả năm seed\nresults/phase2/final/frozen_selection.json — khóa lựa chọn\nresults/phase2/evaluation/metrics.json — chỉ số từng mô hình\nresults/phase2/evaluation/comparison.json — so sánh ghép cặp\nresults/phase2/evaluation/predictions.csv — tính lại chỉ số')
q=p('SHA-256 manifest: 5a352a09cef2b6a84855fa1a23b64f5032f6c4c3e47e154600eec4e06f3b33ff')
for run in q.runs:run.font.size=Pt(10)
d.save(OUT/'Bao_cao_SVM_thao_duoc.docx')
# A separate one-page defense summary.
d=setup();d.add_heading('Tóm tắt bảo vệ đề tài SVM cây dược liệu',0)
p('Huỳnh Gia Huy  •  MSSV 2474802010135  •  28/10/2026')
h('Bài toán và ý nghĩa tối ưu')
p('Phân loại có giám sát ảnh lá vào sáu lớp BDMediLeaves. Biến tối ưu: kernel, C, gamma; mục tiêu giảm 1 − Macro-F1 CV trung bình. SVM học mô hình trong từng lần fit; Random Search/TPE tìm siêu tham số bên ngoài. Học sâu chưa được huấn luyện trong giai đoạn này.')
h('Thiết kế có thể giải thích')
p('Lọc 1.217 ảnh còn 972 ảnh duy nhất; phát hiện 31/121 ảnh test nguồn trùng train nên chia lại. Cố định 778 development, 194 test; 3 fold nhóm. Chọn HSV + LBP đa tỉ lệ + GLCM 126 chiều trên development. StandardScaler fit trong từng fold. Hai phương pháp cùng 40 trial × 5 seed, tổng 400 trial.')
table(['Cùng 194 ảnh test','Trước HPO','Random được chọn'],[['Macro-F1','83,06%','88,71%'],['Accuracy','82,99%','88,66%'],['Đúng / 194','161','172']], [2.75,1.75,2.25])
p('Tăng 5,65 điểm Macro-F1; bootstrap ghép cặp 95% [+2,01; +9,76] điểm. Random sửa 13 lỗi, thêm 2 lỗi mới. Cấu hình RBF, C≈13,2878, gamma≈0,006030; chỉ học 778 ảnh development.')
h('Ba câu hỏi cần trả lời được')
p('Vì sao giữ Random khi TPE test 89,19%? Quy tắc đã khóa trước test: mean best-CV qua năm seed của Random 87,21% cao hơn TPE 86,85%; không chọn lại theo test.')
p('Đổi đặc trưng có tăng 10 điểm test không? Không. CV tăng từ 75,21% lên 85,63%, nhưng test mặc định chỉ từ 82,96% lên 83,06%. So sánh tối ưu chính giữ nguyên 126 đặc trưng.')
p('Mô hình dùng được ngoài thực tế chưa? Chưa chứng minh. Không có ID cây/phiên chụp, không có unknown, nền vẫn tham gia và train F1=100%. Cần dữ liệu ngoài miền có nhãn kiểm định; có thể nối tiếp bằng CNN + SVM rồi fine-tune.')
p('Minh chứng: notebook, 400 trial, dự đoán test, mô hình trước–sau và kiểm tra tự động. AI hỗ trợ nghiên cứu/mã/báo cáo; sinh viên cần tự xác minh. Checkpoint hai ngày không thay thế tiến độ năm tuần.','Caption')
d.save(OUT/'Tom_tat_bao_ve_SVM.docx')
print('Created two Word documents')
