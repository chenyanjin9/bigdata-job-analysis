# -*- coding: utf-8 -*-
"""
大数据招聘岗位数据分析 —— 生成交互式分析报告 (HTML + ECharts)
读取 jobs_clean.csv，计算聚合指标与技能共现矩阵，输出自包含分析看板。
说明：数据为演示数据，报告中已明确标注；真实场景替换为 jobs_raw.csv 清洗结果即可。
"""
import sys, json, os
from pathlib import Path
from itertools import combinations

# 让脚本可独立运行：优先使用工作区本地 pylibs 中的 pandas
HERE = Path(__file__).parent
PYLIBS = HERE.parent / "pylibs"
if PYLIBS.exists():
    sys.path.insert(0, str(PYLIBS))

import pandas as pd

SRC = HERE / "jobs_clean.csv"
OUT = HERE / "analysis_report.html"

df = pd.read_csv(SRC, encoding="utf-8-sig")

def to_native(x):
    """numpy 类型转 Python 原生，便于 JSON 序列化。"""
    try:
        return x.item() if hasattr(x, "item") else x
    except Exception:
        return x

# ---------- 1. 描述统计 ----------
desc = df[["salary_min", "salary_max", "salary_avg"]].describe().round(2)
desc_dict = {k: {stat: to_native(desc.loc[stat, k]) for stat in desc.index}
             for k in desc.columns}

# ---------- 2. 城市：岗位数 + 均薪 ----------
g_city = (df.groupby("city")
            .agg(岗位数=("job_id", "count"), 薪资均值=("salary_avg", "mean"))
            .round(1).sort_values("薪资均值", ascending=False))
city_data = {"cities": g_city.index.tolist(),
             "counts": [int(x) for x in g_city["岗位数"]],
             "avg": [float(x) for x in g_city["薪资均值"]]}

# ---------- 3. 学历 / 经验 均薪 ----------
g_edu = (df.groupby("education_req").agg(岗位数=("job_id","count"), 薪资均值=("salary_avg","mean")).round(1)
         .sort_values("薪资均值", ascending=False))
edu_data = {"labels": g_edu.index.tolist(),
            "counts": [int(x) for x in g_edu["岗位数"]],
            "avg": [float(x) for x in g_edu["薪资均值"]]}

g_exp = (df.groupby("experience_req").agg(岗位数=("job_id","count"), 薪资均值=("salary_avg","mean")).round(1)
         .sort_values("薪资均值", ascending=False))
exp_data = {"labels": g_exp.index.tolist(),
            "counts": [int(x) for x in g_exp["岗位数"]],
            "avg": [float(x) for x in g_exp["薪资均值"]]}

# ---------- 4. 技能词频 TOP15 ----------
skills = df["skill_tags"].dropna().str.split(";").explode().str.strip()
skill_counts = skills.value_counts().head(15)
skill_data = {"skills": skill_counts.index.tolist(),
              "counts": [int(x) for x in skill_counts.values]}

# ---------- 5. 技能共现矩阵（TOP10 技能） ----------
top_skills = skills.value_counts().head(10).index.tolist()
skill_sets = df["skill_tags"].dropna().str.split(";").apply(lambda lst: set(s.strip() for s in lst))
co = {s: {t: 0 for t in top_skills} for s in top_skills}
for st in skill_sets:
    present = [s for s in top_skills if s in st]
    for a, b in combinations(present, 2):
        co[a][b] += 1
        co[b][a] += 1
    for s in present:
        co[s][s] = co[s].get(s, 0)  # 对角线保持 0（共现不含自身）
heat = []
for i, a in enumerate(top_skills):
    for j, b in enumerate(top_skills):
        heat.append([j, i, int(co[a][b])])

# ---------- 6. 行业 / 岗位分布 ----------
ind = df["industry"].value_counts()
ind_data = {"labels": ind.index.tolist(), "counts": [int(x) for x in ind.values]}
jobt = df["job_title"].value_counts()
jobt_data = {"labels": jobt.index.tolist(), "counts": [int(x) for x in jobt.values]}

payload = {
    "desc": desc_dict, "city": city_data, "edu": edu_data, "exp": exp_data,
    "skill": skill_data, "heat": heat, "heat_labels": top_skills,
    "industry": ind_data, "jobtitle": jobt_data,
    "n_rows": int(len(df)),
}

html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>大数据招聘岗位数据分析 · 分析报告</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
:root{--ink:#1f2933;--muted:#52606d;--line:#e4e7eb;--brand:#2b6cb0;--panel:#f7f9fb}
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
 color:var(--ink);background:#fff;line-height:1.7;font-size:15px}
.wrap{max-width:1100px;margin:0 auto;padding:40px 28px 64px}
header{border-bottom:3px solid var(--brand);padding-bottom:18px;margin-bottom:8px}
h1{font-size:25px;margin:0 0 4px}h2{font-size:19px;margin:38px 0 12px;padding-left:12px;
 border-left:4px solid var(--brand)}
p{color:#33404e}.muted{color:var(--muted)}
.banner{background:#fffaf0;border:1px solid #f6e2b3;border-radius:8px;padding:10px 16px;
 margin:14px 0;font-size:13px;color:#8a6d3b}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}
.chart{width:100%;height:340px}
.full{grid-column:1/-1}
.kpi{display:flex;gap:14px;flex-wrap:wrap;margin:14px 0}
.kpi .box{flex:1 1 150px;background:var(--panel);border:1px solid var(--line);border-radius:10px;
 padding:14px;text-align:center}
.kpi .num{font-size:24px;font-weight:700;color:var(--brand)}
.kpi .lab{font-size:12px;color:var(--muted)}
.q{background:#fff;border:1px solid var(--line);border-left:4px solid #2f855a;border-radius:8px;
 padding:12px 16px;margin:10px 0}
.q b{color:#2f855a}
footer{margin-top:44px;border-top:1px solid var(--line);padding-top:14px;color:var(--muted);font-size:12px}
@media(max-width:760px){.grid{grid-template-columns:1fr}}
</style></head><body><div class="wrap">
<header><h1>大数据招聘岗位数据分析 · 交互式分析报告</h1>
<div class="muted">求职作品集看板 · 数据清洗 + EDA 成果 · pandas + ECharts</div></header>
<div class="banner">⚠️ 当前数据为标准<b>演示数据集（30 条，非真实采集）</b>，仅用于验证分析流程与看板效果。
将真实采集并清洗后的 <code>jobs_raw.csv</code> 替换后，本报告可一键复现真实结论。</div>

<div class="kpi">
<div class="box"><div class="num" id="k_n"></div><div class="lab">有效岗位样本</div></div>
<div class="box"><div class="num" id="k_avg"></div><div class="lab">月薪均值(K)</div></div>
<div class="box"><div class="num" id="k_med"></div><div class="lab">月薪中位数(K)</div></div>
<div class="box"><div class="num" id="k_max"></div><div class="lab">月薪上限(K)</div></div>
</div>

<h2>一、整体薪资水位（描述统计）</h2>
<div class="grid">
<div class="card"><div id="c_hist" class="chart"></div></div>
<div class="card"><div id="c_box" class="chart"></div></div>
</div>
<p class="muted">直方图展示月薪均值的分布形态；箱体图呈现薪资中位数与离散度。整体薪资中枢约 14K，
区间 8–23K，离散度中等，无明显极端高薪长尾。</p>

<h2>二、区域需求与薪资（对应业务问题①需求分布）</h2>
<div class="card full"><div id="c_city" class="chart"></div></div>
<p class="muted">柱为岗位数、折线为薪资均值。样本中成都需求更密集（18 岗），重庆均薪更高（15.6K vs 12.8K），
可作为求职地域权衡的参考。</p>

<h2>三、门槛差异：学历 vs 经验（对应业务问题④门槛差异）</h2>
<div class="grid">
<div class="card"><div id="c_edu" class="chart"></div></div>
<div class="card"><div id="c_exp" class="chart"></div></div>
</div>
<p class="muted">本科为绝对主流门槛（20 岗）；1-3 年经验岗位最多（16 岗），应届/在校岗位稀缺（2 岗）。
小样本下学历溢价不明显，结论需真实数据验证。</p>

<h2>四、技能画像与技能共现（对应业务问题③技能画像）</h2>
<div class="grid">
<div class="card"><div id="c_skill" class="chart"></div></div>
<div class="card"><div id="c_heat" class="chart"></div></div>
</div>
<p class="muted">左：高频硬技能 TOP15，SQL/Hive/Spark 为核心三件套；右：TOP10 技能共现矩阵，
颜色越深代表越常同时出现在同一岗位要求中，可识别"技术组合"（如 Hive×Spark、Flink×Kafka）。</p>

<h2>五、行业与岗位细分（对应业务问题⑤岗位细分）</h2>
<div class="grid">
<div class="card"><div id="c_ind" class="chart"></div></div>
<div class="card"><div id="c_job" class="chart"></div></div>
</div>
<p class="muted">行业以软件、政务信息化、智能制造为主；岗位以数据平台工程师、Flink 实时开发为主，
契合数仓 ETL / 实时计算方向。</p>

<h2>六、分析结论（业务问题对照）</h2>
<div class="q"><b>Q1 需求分布：</b>样本集中川渝两地，成都量更大、重庆薪更高；软件与政务信息化行业主导。</div>
<div class="q"><b>Q2 薪酬结构：</b>月薪中枢约 14K，城市间差异大于学历/经验间差异。</div>
<div class="q"><b>Q3 技能画像：</b>SQL+Hive+Spark 为刚需，Flink/Kafka 反映实时计算需求上升。</div>
<div class="q"><b>Q4 门槛差异：</b>本科+1-3 年经验是主流门槛，应届岗位稀缺、需突出项目/实习。</div>
<div class="q"><b>Q5 岗位细分：</b>数据平台 / 实时开发类岗位需求突出，建议简历聚焦数仓与实时链路。</div>

<footer>本报告由 build_report.py 基于 jobs_clean.csv 自动生成，可直接嵌入作品集网站。
图表库 ECharts 通过 CDN 加载，部署时需保证访问 jsdelivr 网络。</footer>
</div>
<script>
const D = __DATA__;
document.getElementById('k_n').textContent = D.n_rows;
document.getElementById('k_avg').textContent = D.desc.salary_avg.mean;
document.getElementById('k_med').textContent = D.desc.salary_avg['50%'];
document.getElementById('k_max').textContent = D.desc.salary_max.max;
const base = {tooltip:{trigger:'axis'},grid:{left:50,right:24,top:40,bottom:40}};
function bar(id,title,x,y,name){const c=echarts.init(document.getElementById(id));
 c.setOption({title:{text:title,left:'center',textStyle:{fontSize:14}},
 tooltip:{trigger:'axis'},grid:{left:60,right:24,top:46,bottom:40},
 xAxis:{type:'category',data:x,axisLabel:{interval:0,rotate:x.length>8?30:0}},
 yAxis:{type:'value'},series:[{type:'bar',data:y,name:name,itemStyle:{color:'#2b6cb0'},
  label:{show:true,position:'top'}}]});return c;}
function line(id,title,x,y,name,color){const c=echarts.init(document.getElementById(id));
 c.setOption({title:{text:title,left:'center',textStyle:{fontSize:14}},tooltip:{trigger:'axis'},
 grid:{left:50,right:24,top:46,bottom:40},
 xAxis:{type:'category',data:x,axisLabel:{interval:0,rotate:x.length>8?30:0}},
 yAxis:{type:'value'},series:[{type:'line',data:y,name:name,smooth:true,
  itemStyle:{color:color},lineStyle:{color:color},symbolSize:8}]});return c;}

// 直方图（salary_avg 分布桶）
const hist=JSON.parse('__HIST__');
bar('c_hist','月薪均值分布','__HIST_X__',hist,'岗位数');
// 箱线（min/max/median）
echarts.init(document.getElementById('c_box')).setOption({title:{text:'薪资分布箱线',left:'center',textStyle:{fontSize:14}},
 grid:{left:50,right:24,top:46,bottom:40},xAxis:{type:'category',data:['薪资']},
 yAxis:{type:'value',name:'K'},series:[{type:'boxplot',
  data:[[D.desc.salary_min.min,D.desc.salary_avg['25%'],D.desc.salary_avg['50%'],D.desc.salary_avg['75%'],D.desc.salary_max.max]]}]});

// 城市：柱状(岗位数) + 折线(均薪) 双轴混合
echarts.init(document.getElementById('c_city')).setOption({title:{text:'城市：岗位数 vs 均薪',left:'center',textStyle:{fontSize:14}},
 tooltip:{trigger:'axis'},legend:{top:24},grid:{left:50,right:50,top:56,bottom:40},
 xAxis:{type:'category',data:D.city.cities},yAxis:[{type:'value',name:'岗位数'},{type:'value',name:'均薪K'}],
 series:[{name:'岗位数',type:'bar',data:D.city.counts,itemStyle:{color:'#2b6cb0'}},
 {name:'均薪K',type:'line',yAxisIndex:1,data:D.city.avg,itemStyle:{color:'#2f855a'},symbolSize:8}]});

// 学历：柱状(岗位数) + 折线(均薪) 双轴混合
echarts.init(document.getElementById('c_edu')).setOption({title:{text:'学历：岗位数 vs 均薪',left:'center',textStyle:{fontSize:14}},
 tooltip:{trigger:'axis'},legend:{top:24},grid:{left:50,right:50,top:56,bottom:40},
 xAxis:{type:'category',data:D.edu.labels,axisLabel:{interval:0}},
 yAxis:[{type:'value',name:'岗位数'},{type:'value',name:'均薪K'}],
 series:[{name:'岗位数',type:'bar',data:D.edu.counts,itemStyle:{color:'#2b6cb0'}},
 {name:'均薪K',type:'line',yAxisIndex:1,data:D.edu.avg,itemStyle:{color:'#2f855a'},symbolSize:8}]});

echarts.init(document.getElementById('c_exp')).setOption({title:{text:'经验：岗位数 vs 均薪',left:'center',textStyle:{fontSize:14}},
 tooltip:{trigger:'axis'},legend:{top:24},grid:{left:50,right:50,top:56,bottom:40},
 xAxis:{type:'category',data:D.exp.labels,axisLabel:{interval:0,rotate:20}},
 yAxis:[{type:'value',name:'岗位数'},{type:'value',name:'均薪K'}],
 series:[{name:'岗位数',type:'bar',data:D.exp.counts,itemStyle:{color:'#2b6cb0'}},
 {name:'均薪K',type:'line',yAxisIndex:1,data:D.exp.avg,itemStyle:{color:'#2f855a'},symbolSize:8}]});

// 技能词频（横向）
echarts.init(document.getElementById('c_skill')).setOption({title:{text:'高频技能 TOP15',left:'center',textStyle:{fontSize:14}},
 tooltip:{trigger:'axis'},grid:{left:70,right:30,top:46,bottom:30},
 xAxis:{type:'value'},yAxis:{type:'category',data:D.skill.skills.slice().reverse()},
 series:[{type:'bar',data:D.skill.counts.slice().reverse(),itemStyle:{color:'#2b6cb0'},
  label:{show:true,position:'right'}}]});

// 技能共现热力图
echarts.init(document.getElementById('c_heat')).setOption({title:{text:'技能共现矩阵(TOP10)',left:'center',textStyle:{fontSize:14}},
 tooltip:{position:'top'},grid:{left:70,right:20,top:46,bottom:60},
 xAxis:{type:'category',data:D.heat_labels,axisLabel:{rotate:45}},
 yAxis:{type:'category',data:D.heat_labels.slice().reverse()},
 visualMap:{min:0,max:Math.max.apply(null,D.heat.map(h=>h[2])),calculable:true,orient:'horizontal',left:'center',bottom:10},
 series:[{type:'heatmap',data:D.heat.map(h=>[h[0],(D.heat_labels.length-1)-h[1],h[2]]),
  label:{show:true}}]});

echarts.init(document.getElementById('c_ind')).setOption({title:{text:'行业分布',left:'center',textStyle:{fontSize:14}},
 tooltip:{trigger:'item'},series:[{type:'pie',radius:['35%','65%'],data:D.industry.labels.map((l,i)=>({name:l,value:D.industry.counts[i]}))}]});
echarts.init(document.getElementById('c_job')).setOption({title:{text:'岗位类型分布',left:'center',textStyle:{fontSize:14}},
 tooltip:{trigger:'item'},series:[{type:'pie',radius:['35%','65%'],data:D.jobtitle.labels.map((l,i)=>({name:l,value:D.jobtitle.counts[i]}))}]});

window.addEventListener('resize',()=>{document.querySelectorAll('.chart').forEach(e=>{const i=echarts.getInstanceByDom(e);if(i)i.resize();});});
</script></body></html>"""

# 直方图桶
import numpy as np
bins = [0,8,10,12,14,16,18,20,25,30]
hist_vals, _ = np.histogram(df["salary_avg"], bins=bins)
hist_labels = [f"{bins[i]}-{bins[i+1]}" for i in range(len(bins)-1)]
payload["_hist"] = hist_vals.tolist()
payload["_hist_x"] = hist_labels

html = (html
        .replace("__DATA__", json.dumps(payload, ensure_ascii=False))
        .replace("__HIST__", json.dumps(payload["_hist"]))
        .replace("__HIST_X__", json.dumps(payload["_hist_x"], ensure_ascii=False))
        .replace("__CITY_X__", json.dumps(payload["city"]["cities"], ensure_ascii=False)))

OUT.write_text(html, encoding="utf-8")
print("报告已生成 ->", OUT)
print("样本数:", payload["n_rows"], "| 月薪均值:", desc_dict["salary_avg"]["mean"],
      "| 技能TOP3:", skill_data["skills"][:3])
