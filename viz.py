# -*- coding: utf-8 -*-
"""
大数据招聘岗位数据分析 —— 可视化 (matplotlib)
读取 jobs_clean.csv，绘制 4 张面向应届生的分析图，并生成可嵌入作品集网站的
自包含 HTML 报告（图表以 base64 内嵌，离线可用）。

运行：PYTHONPATH=<pylibs目录> python viz.py
依赖：pandas, numpy, matplotlib（需本地 pylibs）
"""
import sys
from pathlib import Path
from itertools import combinations
import base64
from io import BytesIO

HERE = Path(__file__).parent
PYLIBS = HERE.parent / "pylibs"
if PYLIBS.exists():
    sys.path.insert(0, str(PYLIBS))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # 无界面后端，适合服务器端/沙箱出图
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ===================== 中文显示设置 =====================
CJK = ["SimHei", "Microsoft YaHei", "Heiti SC", "Source Han Sans SC",
       "Noto Sans CJK SC", "WenQuanYi Zen Hei", "Arial Unicode MS"]
AVAIL = {f.name for f in fm.fontManager.ttflist}
CHOSEN = next((c for c in CJK if c in AVAIL), None)
if CHOSEN:
    plt.rcParams["font.sans-serif"] = [CHOSEN]        # 设置中文字体
    print("使用中文字体：", CHOSEN)
else:
    print("⚠️ 未找到中文字体，图表中文可能显示为方框；请在自己电脑运行（Windows 自带 SimHei）。")
plt.rcParams["axes.unicode_minus"] = False             # 正常显示负号
plt.rcParams["figure.dpi"] = 110                       # 提高清晰度
# =======================================================

OUT_DIR = HERE / "imgs"
OUT_DIR.mkdir(exist_ok=True)
SRC = HERE / "jobs_clean.csv"
HTML_OUT = HERE / "visualization_report.html"

df = pd.read_csv(SRC, encoding="utf-8-sig")

# 配色
C_BAR, C_LINE = "#2b6cb0", "#2f855a"


def fig_to_b64(fig):
    """将 matplotlib 图转为 base64 字符串，便于内嵌 HTML。"""
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


charts = {}  # name -> base64

# ---------- 图1：城市岗位数 + 均薪（双轴）----------
g_city = (df.groupby("city")
            .agg(岗位数=("job_id", "count"), 均薪=("salary_avg", "mean"))
            .round(1).sort_values("岗位数", ascending=False))
fig, ax1 = plt.subplots(figsize=(6.2, 4.2))
x = np.arange(len(g_city))
ax1.bar(x, g_city["岗位数"], color=C_BAR, alpha=0.85, label="岗位数")
ax1.set_xticks(x); ax1.set_xticklabels(g_city.index)
ax1.set_ylabel("岗位数量", color=C_BAR)
ax1.set_xlabel("城市")
for i, v in enumerate(g_city["岗位数"]):
    ax1.text(i, v + 0.2, str(int(v)), ha="center", color=C_BAR)
ax2 = ax1.twinx()
ax2.plot(x, g_city["均薪"], color=C_LINE, marker="o", linewidth=2, label="均薪(K)")
ax2.set_ylabel("平均月薪 (K)", color=C_LINE)
for i, v in enumerate(g_city["均薪"]):
    ax2.text(i, v + 0.3, f"{v}", ha="center", color=C_LINE)
ax1.set_title("图1 各城市岗位需求与薪资水平")
fig.tight_layout()
charts["city"] = fig_to_b64(fig)

# ---------- 图2：经验要求岗位数 + 均薪（双轴）----------
exp_order = ["应届/在校", "1-3年", "3-5年", "5年以上"]
g_exp = (df.groupby("experience_req")
           .agg(岗位数=("job_id", "count"), 均薪=("salary_avg", "mean"))
           .round(1).reindex(exp_order))
fig, ax1 = plt.subplots(figsize=(6.2, 4.2))
x = np.arange(len(g_exp))
ax1.bar(x, g_exp["岗位数"], color=C_BAR, alpha=0.85)
ax1.set_xticks(x); ax1.set_xticklabels(g_exp.index)
ax1.set_ylabel("岗位数量", color=C_BAR); ax1.set_xlabel("经验要求")
for i, v in enumerate(g_exp["岗位数"]):
    ax1.text(i, v + 0.2, str(int(v)), ha="center", color=C_BAR)
ax2 = ax1.twinx()
ax2.plot(x, g_exp["均薪"], color=C_LINE, marker="o", linewidth=2)
ax2.set_ylabel("平均月薪 (K)", color=C_LINE)
for i, v in enumerate(g_exp["均薪"]):
    ax2.text(i, v + 0.3, f"{v}", ha="center", color=C_LINE)
ax1.set_title("图2 经验门槛分布与对应薪资")
fig.tight_layout()
charts["exp"] = fig_to_b64(fig)

# ---------- 图3：高频技能 TOP15（横向条形）----------
skills = (df["skill_tags"].dropna().str.split(";").explode().str.strip()
          .value_counts().head(15))
fig, ax = plt.subplots(figsize=(6.6, 5.2))
ax.barh(skills.index[::-1], skills.values[::-1], color=C_BAR, alpha=0.85)
ax.set_xlabel("出现频次（岗位数）")
for i, v in enumerate(skills.values[::-1]):
    ax.text(v + 0.1, i, str(int(v)), va="center", color=C_BAR)
ax.set_title("图3 企业高频技能需求 TOP15")
fig.tight_layout()
charts["skill"] = fig_to_b64(fig)

# ---------- 图4：学历要求岗位数 + 均薪（双轴）----------
edu_order = ["大专", "本科", "硕士"]
g_edu = (df.groupby("education_req")
           .agg(岗位数=("job_id", "count"), 均薪=("salary_avg", "mean"))
           .round(1).reindex(edu_order))
fig, ax1 = plt.subplots(figsize=(6.2, 4.2))
x = np.arange(len(g_edu))
ax1.bar(x, g_edu["岗位数"], color=C_BAR, alpha=0.85)
ax1.set_xticks(x); ax1.set_xticklabels(g_edu.index)
ax1.set_ylabel("岗位数量", color=C_BAR); ax1.set_xlabel("学历要求")
for i, v in enumerate(g_edu["岗位数"]):
    ax1.text(i, v + 0.2, str(int(v)), ha="center", color=C_BAR)
ax2 = ax1.twinx()
ax2.plot(x, g_edu["均薪"], color=C_LINE, marker="o", linewidth=2)
ax2.set_ylabel("平均月薪 (K)", color=C_LINE)
for i, v in enumerate(g_edu["均薪"]):
    ax2.text(i, v + 0.3, f"{v}", ha="center", color=C_LINE)
ax1.set_title("图4 学历要求与薪资/机会关系")
fig.tight_layout()
charts["edu"] = fig_to_b64(fig)

# 同时保存 PNG 供单独使用
for name, b in charts.items():
    (OUT_DIR / f"{name}.png").write_bytes(base64.b64decode(b))
print("PNG 已保存至", OUT_DIR)

# ===================== 生成自包含 HTML 报告 =====================
city_rows = "".join(f"<tr><td>{c}</td><td>{int(n)}</td><td>{s}K</td></tr>"
                    for c, n, s in zip(g_city.index, g_city["岗位数"], g_city["均薪"]))
edu_rows = "".join(f"<tr><td>{c}</td><td>{int(n)}</td><td>{s}K</td></tr>"
                   for c, n, s in zip(g_edu.index, g_edu["岗位数"], g_edu["均薪"]))
exp_total = int(g_exp["岗位数"].sum())
fresh_n = int(g_exp["岗位数"].get("应届/在校", 0))
junior_n = int(g_exp["岗位数"].get("1-3年", 0))
skill_top3 = ", ".join(skills.index[:3])
skill_top5 = ", ".join(skills.index[:5])

HTML = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>大数据招聘岗位数据分析 · 可视化报告</title>
<style>
:root{{--ink:#1f2933;--muted:#52606d;--line:#e4e7eb;--brand:#2b6cb0;--panel:#f7f9fb}}
*{{box-sizing:border-box}}body{{margin:0;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
color:var(--ink);background:#fff;line-height:1.7;font-size:15px}}
.wrap{{max-width:1080px;margin:0 auto;padding:40px 26px 60px}}
header{{border-bottom:3px solid var(--brand);padding-bottom:16px;margin-bottom:6px}}
h1{{font-size:24px;margin:0 0 4px}}h2{{font-size:19px;margin:34px 0 10px;padding-left:12px;border-left:4px solid var(--brand)}}
.muted{{color:var(--muted)}}.banner{{background:#fffaf0;border:1px solid #f6e2b3;border-radius:8px;
padding:10px 16px;margin:12px 0;font-size:13px;color:#8a6d3b}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}}
.card img{{width:100%;border-radius:6px}}table{{width:100%;border-collapse:collapse;margin:10px 0;font-size:14px}}
th,td{{border:1px solid var(--line);padding:8px 10px}}th{{background:#ebf2fa;color:var(--brand)}}
.concl{{background:#fff;border:1px solid var(--line);border-left:4px solid #2f855a;border-radius:8px;
padding:12px 16px;margin:10px 0}} .concl b{{color:#2f855a}}
footer{{margin-top:40px;border-top:1px solid var(--line);padding-top:14px;color:var(--muted);font-size:12px}}
@media(max-width:760px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><div class="wrap">
<header><h1>大数据招聘岗位数据分析 · 可视化报告</h1>
<div class="muted">求职作品集 · matplotlib 可视化 · 面向应届生视角</div></header>
<div class="banner">⚠️ 当前为<b>演示数据集（30 条，非真实采集）</b>，仅用于验证可视化流程。
真实数据替换 jobs_clean.csv 后重跑 viz.py 即可复现真实图表。</div>

<h2>一、图表总览</h2>
<div class="grid">
<div class="card"><img src="data:image/png;base64,{charts['city']}"></div>
<div class="card"><img src="data:image/png;base64,{charts['exp']}"></div>
<div class="card"><img src="data:image/png;base64,{charts['skill']}"></div>
<div class="card"><img src="data:image/png;base64,{charts['edu']}"></div>
</div>

<h2>二、各图说明（类型 / 轴 / 业务意义）</h2>
<table>
<tr><th>图</th><th>类型</th><th>X / Y 轴</th><th>业务意义</th></tr>
<tr><td>图1 城市</td><td>柱状+折线双轴</td><td>X:城市 / Y左:岗位数, Y右:均薪(K)</td>
<td>判断求职地域：成都需求密集、重庆薪资更高，辅助"去哪发展"决策</td></tr>
<tr><td>图2 经验</td><td>柱状+折线双轴</td><td>X:经验要求 / Y左:岗位数, Y右:均薪(K)</td>
<td>看清应届/初级岗位占比与薪资，定位自身竞争力档位、精准投递</td></tr>
<tr><td>图3 技能</td><td>横向条形</td><td>X:出现频次 / Y:技能名</td>
<td>明确企业最看重的硬技能栈，给应届生具体学习路线</td></tr>
<tr><td>图4 学历</td><td>柱状+折线双轴</td><td>X:学历 / Y左:岗位数, Y右:均薪(K)</td>
<td>量化"学历焦虑"：学历对机会/薪资影响有限，强调项目与实习</td></tr>
</table>

<h2>三、面向应届生的 4 条落地结论</h2>
<div class="concl"><b>① 地域：川渝是主战场，按目标取舍。</b>
本样本中成都 {int(g_city['岗位数'].get('成都',0))} 个岗位（需求更密集）、重庆 {int(g_city['岗位数'].get('重庆',0))} 个且均薪更高
（重庆 {g_city['均薪'].get('重庆',0)}K &gt; 成都 {g_city['均薪'].get('成都',0)}K）。
应届生可优先布局川渝：重"机会量"看成都，重"起薪"看重庆，两地通投扩大命中率。</div>

<div class="concl"><b>② 经验门槛：企业普遍要即战力，必须用经历补足。</b>
样本中 {exp_total} 个岗位里，"1-3年"占 {junior_n} 个（主力），而"应届/在校"仅 {fresh_n} 个。
说明企业偏好有经验的候选人——应届生不能只靠学历，需用<b>实习 + 课程项目 + 竞赛</b>把简历填成"有实战痕迹"，否则极易在初筛被刷。</div>

<div class="concl"><b>③ 技能：先打牢三件套，再追实时热点。</b>
高频技能前五是 {skill_top5}；SQL、Hive、Spark 是数仓/大数据岗的<b>刚需三件套</b>，
Flink、Kafka 反映实时计算趋势。学习路线建议：优先精通 SQL 与 Hive 数仓建模，再熟用 Spark，
有余力补 Flink/Kafka——不要一上来贪多，把核心栈讲到能上手最加分。</div>

<div class="concl"><b>④ 学历：别焦虑，把项目做扎实更关键。</b>
样本中本科 {int(g_edu['岗位数'].get('本科',0))} 个（绝对主流），大专 {int(g_edu['岗位数'].get('大专',0))} 个、硕士 {int(g_edu['岗位数'].get('硕士',0))} 个；
且本科均薪({g_edu['均薪'].get('本科',0)}K)并不低于硕士({g_edu['均薪'].get('硕士',0)}K)。
结论：学历是门槛但不是天花板，专科生完全有机会——把数仓 ETL 项目做透、能讲清技术细节与业务价值，比刷学历标签更有效。</div>

<footer>本报告由 viz.py 基于 jobs_clean.csv 自动生成，图表以 base64 内嵌，可离线直接部署到作品集网站。</footer>
</div></body></html>"""

HTML_OUT.write_text(HTML, encoding="utf-8")
print("报告已生成 ->", HTML_OUT)
print("样例结论数据：城市", dict(g_city["岗位数"]), "| 经验", dict(g_exp["岗位数"]),
      "| 学历", dict(g_edu["岗位数"]), "| 技能TOP3", skill_top3)
