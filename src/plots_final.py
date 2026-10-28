"""Publication figures generated entirely from frozen experiment logs."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from .features import load_rgb

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/"results/phase2"
OUT=R/"figures"
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
COLORS={"baseline":"#738193","random":"#176e52","tpe":"#4e6ab0","v1_default":"#bbb7ad"}
NAMES={"baseline":"SVM mặc định","random":"Random Search","tpe":"TPE","v1_default":"SVM giai đoạn 1"}


def save(fig,name):
    fig.tight_layout();fig.savefig(OUT/name,dpi=190,bbox_inches="tight");plt.close(fig)


def main():
    ab=pd.read_csv(R/"ablation/summary.csv")
    labels={"v1":"HOG + HSV + LBP · 958 chiều","v1_no_color":"HOG + LBP · 910 chiều",
            "texture128":"HSV + LBP đa tỉ lệ + GLCM · 126 chiều","enhanced128":"Thêm HOG 128 px · 1.890 chiều",
            "center128":"Cắt vùng giữa và thêm HOG · 1.890 chiều"}
    fig,ax=plt.subplots(figsize=(10,4))
    ax.barh([labels[x] for x in ab.feature_id],ab.mean_cv_macro_f1*100,
            color=[COLORS['random'] if x=='texture128' else '#bac8d3' for x in ab.feature_id])
    ax.set(xlim=(0,100),xlabel="Macro-F1 CV (%)",title="Chọn đặc trưng bằng cùng SVM mặc định trên development")
    for i,v in enumerate(ab.mean_cv_macro_f1):ax.text(v*100+1,i,f"{v*100:.2f}",va="center")
    ax.invert_yaxis();save(fig,"feature_ablation.png")
    trials=pd.read_csv(R/"hpo/trials.csv")
    baseline=json.loads((R/"hpo/baseline.json").read_text())["mean_cv_macro_f1"]
    summary=pd.DataFrame(json.loads((R/"hpo/summary.json").read_text()))
    fig,ax=plt.subplots(figsize=(8,4.3))
    for method in ['random','tpe']:
        curves=np.stack([df.sort_values('trial').cv_macro_f1.cummax().to_numpy() for _,df in trials[trials.method==method].groupby('seed')])
        x=np.arange(1,41);m=curves.mean(axis=0);s=curves.std(axis=0,ddof=1)
        ax.plot(x,m*100,label=NAMES[method],color=COLORS[method],lw=2)
        ax.fill_between(x,(m-s)*100,(m+s)*100,color=COLORS[method],alpha=.14)
    ax.axhline(baseline*100,ls='--',color=COLORS['baseline'],label='SVM mặc định')
    ax.set(xlabel='Số trial mỗi seed',ylabel='Best CV Macro-F1 (%)',title='Hội tụ qua 5 seed · đường trung bình và vùng ±1 SD')
    ax.legend(loc='lower right');ax.grid(alpha=.15);save(fig,'convergence.png')
    fig,axes=plt.subplots(1,2,figsize=(9.4,3.7))
    for i,method in enumerate(['random','tpe']):
        vals=summary[summary.method==method].best_cv_macro_f1.to_numpy()*100
        axes[0].scatter(i+np.linspace(-.1,.1,5),vals,color=COLORS[method],s=48)
        axes[0].plot([i-.25,i+.25],[vals.mean()]*2,color='black',lw=2)
        sec=summary[summary.method==method].seconds.to_numpy()
        axes[1].bar(i,sec.mean(),color=COLORS[method],width=.6,yerr=sec.std(ddof=1),capsize=5)
    axes[0].set(xticks=[0,1],xticklabels=['Random','TPE'],ylabel='Best CV Macro-F1 (%)',title='Biến thiên giữa các seed')
    axes[0].axhline(baseline*100,color=COLORS['baseline'],ls='--')
    axes[1].set(xticks=[0,1],xticklabels=['Random','TPE'],ylabel='Giây / 40 trial',title='Chi phí tìm kiếm · mean ± SD')
    save(fig,'stability_runtime.png')
    metrics=json.loads((R/'evaluation/metrics.json').read_text());comparison=json.loads((R/'evaluation/comparison.json').read_text())
    names=['v1_default','baseline','random','tpe'];x=np.arange(4);fig,ax=plt.subplots(figsize=(8.4,4.4))
    values=np.array([metrics[n]['test_macro_f1']*100 for n in names])
    cis=np.array([comparison['bootstrap']['macro_f1_ci95'][n] for n in names])*100
    ax.bar(x,values,color=[COLORS[n] for n in names],width=.65)
    ax.errorbar(x,values,yerr=np.vstack([values-cis[:,0],cis[:,1]-values]),fmt='none',ecolor='#303030',capsize=5)
    for i,v in enumerate(values):ax.text(i,v+1,f'{v:.2f}%',ha='center',va='bottom',fontweight='bold')
    ax.set(xticks=x,xticklabels=['Giai đoạn 1','Trước HPO','Sau Random\nđã chọn trước test','Sau TPE'],ylim=(0,103),ylabel='Macro-F1 test (%)',title='Cùng 194 ảnh test · khoảng bootstrap 95%')
    save(fig,'before_after_test.png')
    labels=metrics['baseline']['labels'];short=['Centella','Justicia','Kalanchoe','Mikania','Phyllanthus','Terminalia']
    fig,axes=plt.subplots(1,2,figsize=(10,4.8))
    for ax,name in zip(axes,['baseline','random']):
        cm=np.array(metrics[name]['confusion_matrix']);ax.imshow(cm,cmap='Greens',vmin=0,vmax=33)
        for i in range(6):
            for j in range(6):ax.text(j,i,str(cm[i,j]),ha='center',va='center',color='white' if cm[i,j]>18 else '#192e27')
        ax.set(xticks=range(6),yticks=range(6),xticklabels=short,yticklabels=short,xlabel='Nhãn dự đoán',ylabel='Nhãn thật',title=NAMES[name])
        plt.setp(ax.get_xticklabels(),rotation=45,ha='right')
    save(fig,'confusion_before_after.png')
    fig,ax=plt.subplots(figsize=(8,4.5));x=np.arange(6)
    for offset,name in [(-.18,'baseline'),(.18,'random')]:
        values=[metrics[name]['classification_report'][label]['f1-score']*100 for label in labels]
        ax.barh(x+offset,values,height=.35,label=NAMES[name],color=COLORS[name])
    ax.set(yticks=x,yticklabels=labels,xlim=(0,105),xlabel='F1 test mỗi lớp (%)',title='Thay đổi theo từng loài');ax.legend(loc='lower left');ax.invert_yaxis();save(fig,'per_class_f1.png')
    df=pd.read_csv(R/'evaluation/predictions.csv')
    failed=df[df.random!=df.label].head(6)
    fig,axes=plt.subplots(2,3,figsize=(9,6.5))
    for ax,(_,row) in zip(axes.flat,failed.iterrows()):
        ax.imshow(load_rgb(ROOT/'data/raw'/row.path));ax.axis('off')
        ax.set_title(f"Thật: {row.label}\nDự đoán: {row.random}",fontsize=9)
    fig.suptitle('Ảnh sai sau tối ưu · chỉ phân tích sau khi đã khóa mô hình',fontsize=12)
    save(fig,'test_failure_examples.png')


if __name__=='__main__':main()
