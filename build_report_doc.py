# -*- coding: utf-8 -*-
"""生成自包含的项目完整报告 HTML（图表 base64 内嵌，可直接发布到作品集网站）。"""
import base64, pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent

df = pd.read_csv(ROOT / "jobs_clean.csv")

def b64(p):
    return base64.b64encode((ROOT / p).read_bytes()).decode()

imgs = {k: b64(f"imgs/{k}.png") for k in ["city", "exp", "skill", "edu"]}

# 关键指标（已与 jobs_clean.csv 核对）
N = len(df)
sal = df["salary_avg"]
desc = sal.describe().round(2)
city_cnt = df["city"].value_counts().to_dict()
city_avg = df.groupby("city")["salary_avg"].mean().round(2).to_dict()
edu_cnt = df["education_req"].value_counts().to_dict()
edu_avg = df.groupby("education_req")["salary_avg"].mean().round(2).to_dict()
exp_cnt = df["experience_req"].value_counts().to_dict()
exp_avg = df.groupby("experience_req")["salary_avg"].mean().round(2).to_dict()
sk = df["skill_tags"].str.split(";").explode().str.strip().value_counts()
sk_top = sk.head(8)
title_top = df["job_title"].value_counts().head(5)
ind = df["industry"].value_counts()

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>大数据招聘岗位数据分析 · 项目报告</title>
<style>
  :root{{--blue:#1f5fbf;--ink:#1f2933;--sub:#52606d;--line:#e4e7eb;--bg:#f7f9fc;--card:#fff;--accent:#2f855a;}}
  *{{box-sizing:border-box;}}
  body{{margin:0;font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
    color:var(--ink);background:var(--bg);line-height:1.75;font-size:15.5px;}}
  .wrap{{max-width:960px;margin:0 auto;padding:0 22px 70px;}}
  header.hero{{background:linear-gradient(135deg,#1f5fbf,#2f855a);color:#fff;padding:46px 22px 38px;}}
  header.hero .inner{{max-width:960px;margin:0 auto;}}
  header.hero h1{{margin:0 0 8px;font-size:30px;letter-spacing:.5px;}}
  header.hero p{{margin:4px 0;opacity:.95;font-size:15px;}}
  .tags{{margin-top:16px;}}
  .tag{{display:inline-block;background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.35);
    padding:4px 11px;border-radius:20px;font-size:13px;margin:4px 6px 0 0;}}
  h2{{font-size:21px;margin:42px 0 14px;padding-left:12px;border-left:5px solid var(--blue);}}
  h3{{font-size:16.5px;margin:24px 0 8px;color:var(--blue);}}
  p{{margin:10px 0;color:var(--sub);}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 22px;margin:16px 0;
    box-shadow:0 1px 3px rgba(0,0,0,.04);}}
  table{{width:100%;border-collapse:collapse;margin:14px 0;font-size:14px;}}
  th,td{{border:1px solid var(--line);padding:9px 12px;text-align:left;}}
  th{{background:#eef3fb;color:var(--ink);font-weight:600;}}
  td.num{{text-align:right;font-variant-numeric:tabular-nums;}}
  code{{background:#eef1f6;padding:2px 6px;border-radius:5px;font-size:13px;color:#b4316b;
    font-family:"SFMono-Regular",Consolas,monospace;}}
  pre{{background:#0f172a;color:#e2e8f0;padding:16px 18px;border-radius:10px;overflow:auto;
    font-size:13px;line-height:1.6;}}
  pre .c{{color:#7f9bb3;}}
  img.chart{{width:100%;border:1px solid var(--line);border-radius:10px;margin:10px 0;background:#fff;}}
  .kpi{{display:flex;flex-wrap:wrap;gap:14px;margin:16px 0;}}
  .kpi .box{{flex:1;min-width:140px;background:var(--card);border:1px solid var(--line);
    border-radius:12px;padding:16px;text-align:center;}}
  .kpi .n{{font-size:26px;font-weight:700;color:var(--blue);}}
  .kpi .l{{font-size:13px;color:var(--sub);margin-top:4px;}}
  .note{{background:#fff8e6;border:1px solid #ffe2a8;border-radius:10px;padding:12px 16px;
    font-size:13.5px;color:#7a5b00;margin:14px 0;}}
  .concl{{background:#eefaf2;border:1px solid #b7e4c7;border-left:5px solid var(--accent);
    border-radius:10px;padding:14px 18px;margin:14px 0;}}
  .concl b{{color:var(--accent);}}
  ol,ul{{color:var(--sub);padding-left:22px;}}
  li{{margin:7px 0;}}
  footer{{margin-top:50px;padding-top:20px;border-top:1px solid var(--line);font-size:13px;color:#9aa5b1;text-align:center;}}
  .flow{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:14px 0;}}
  .flow .step{{background:#eef3fb;border:1px solid #c7d8f5;border-radius:8px;padding:9px 13px;font-size:13.5px;}}
  .flow .arrow{{color:var(--blue);font-weight:700;}}
  .figcap{{font-size:13px;color:#9aa5b1;text-align:center;margin:-4px 0 14px;}}
</style>
</head>
<body>
<header class="hero">
  <div class="inner">
    <h1>大数据招聘岗位数据分析 · 项目报告</h1>
    <p>从公开渠道采集招聘数据，构建「采集—清洗—分析—可视化」全链路，量化岗位供需、技能与薪酬格局</p>
    <p style="opacity:.85;font-size:13.5px;">项目定位：专科·大数据技术专业·大三 · 求职作品集 / 简历项目</p>
    <div class="tags">
      <span class="tag">Python</span><span class="tag">requests / bs4</span><span class="tag">pandas</span>
      <span class="tag">matplotlib</span><span class="tag">ECharts</span><span class="tag">数据合规</span>
    </div>
  </div>
</header>

<div class="wrap">

<div class="note">
  <b>数据说明：</b>本报告基于一份<strong>演示数据集（{N} 条，已标注「非真实采集」）</strong>完成全流程验证。
  真实数据可通过项目内置采集器抓取合规公开源后，按相同流程一键复现。结论仅用于方法演示与作品集展示。
</div>

<h2>1. 项目概述</h2>
<div class="card">
<p><b>背景。</b>大数据产业持续扩张，但求职者普遍缺乏对市场供需、技能要求与薪酬水平的结构化认知，往往只能凭直觉或碎片信息做决策。与此同时，主流招聘平台（BOSS直聘、智联、前程无忧等）的批量抓取存在合规与法律风险，不宜作为学生作品的采集对象。</p>
<p><b>目标。</b>本项目以<strong>合规公开数据源</strong>为对象，构建一条完整的「数据采集 → 清洗预处理 → 探索性分析 → 可视化呈现」数据工程链路，将分散的职位文本转化为可度量的市场洞察，回答「去哪发展、学什么技能、如何定位自身竞争力」三类求职核心问题。它既是一份求职决策辅助，也是对个人大数据技术栈（爬虫、ETL、分析、可视化）的综合实践。</p>
<p><b>我的角色与产出。</b>作为项目唯一执行者，独立完成需求拆解、采集器编写、数据清洗、EDA 与可视化看板开发，形成可复现、可部署的作品集站点。</p>
</div>
<div class="kpi">
  <div class="box"><div class="n">{N}</div><div class="l">分析样本量（条）</div></div>
  <div class="box"><div class="n">18</div><div class="l">数据字段（列）</div></div>
  <div class="box"><div class="n">4</div><div class="l">核心分析图表</div></div>
  <div class="box"><div class="n">5</div><div class="l">业务问题覆盖</div></div>
</div>

<h2>2. 数据源与采集方案</h2>
<h3>2.1 数据源选择原则</h3>
<p>优先选择<strong>政府公共就业渠道与公开数据集</strong>，规避商业招聘平台的 robots 限制、反爬机制与法律判例风险；同时贴合「川渝就业情报」主线，区域样本更聚焦。推荐优先级如下：</p>
<table>
  <tr><th>优先级</th><th>数据源</th><th>说明</th></tr>
  <tr><td>★★★</td><td>中国公共招聘网 job.mohrss.gov.cn</td><td>人社部官方，合规风险最低</td></tr>
  <tr><td>★★★</td><td>四川 / 重庆公共就业服务网</td><td>区域聚焦，契合川渝主线</td></tr>
  <tr><td>★★☆</td><td>高校就业指导中心、公共数据开放平台</td><td>结构化程度较高</td></tr>
  <tr><td>★☆☆</td><td>Kaggle / 天池公开职位数据集</td><td>适合快速跑通流程验证</td></tr>
  <tr><td class="num">✕ 排除</td><td>BOSS直聘 / 智联 / 前程无忧 / 拉勾</td><td>robots 禁止、反爬、违反用户协议、有判例风险</td></tr>
</table>

<h3>2.2 采集字段清单（17 列）</h3>
<p><code>job_id, job_title, company_name, city, district, salary_text, salary_min, salary_max, experience_req, education_req, company_size, industry, skill_tags, job_description, publish_date, source, crawl_time</code></p>

<h3>2.3 采集框架与合规规范</h3>
<p>采集器以 <code>requests + BeautifulSoup</code> 为核心，内置 <code>RobotFileParser</code> 遵守 robots 协议、限速器（≥2 秒 + 随机抖动）、429 自动退避、UTF-8-BOM 落盘与去重。核心要点：</p>
<ul>
  <li><b>守协议：</b>每次采集前读取目标站 <code>robots.txt</code>，仅抓允许路径。</li>
  <li><b>控频率：</b>请求间隔 ≥ 2 秒（政府站建议 3–5 秒），附带真实 UA，避免对服务器造成压力。</li>
  <li><b>懂退避：</b>遇 429 / 503 读取 <code>Retry-After</code> 自动暂停，不强行突破。</li>
  <li><b>守边界：</b>只采集公开职位字段，不触碰个人隐私，不绕过登录/反爬。</li>
  <li><b>可溯源：</b>成果标注来源与「趋势性分析」口径，不宣称精确就业指导。</li>
</ul>

<h2>3. 数据预处理与清洗</h2>
<p>清洗使用 <code>pandas</code> 实现，覆盖四类典型问题。演示数据本身较干净，故本批命中 0 异常，但脚本按「真实脏数据」标准编写，可直接复用于真实采集结果。</p>
<table>
  <tr><th>步骤</th><th>处理动作</th><th>本批结果</th></tr>
  <tr><td>字段类型转换</td><td>薪资转数值、日期转 datetime、派生 <code>salary_avg</code></td><td>已完成，新增 1 列</td></tr>
  <tr><td>缺失值处理</td><td>关键字段（薪资/职位）缺失→丢弃；分类字段缺失→填「未知」</td><td>0 行丢弃</td></tr>
  <tr><td>异常值处理</td><td>薪资 ≤ 0、min &gt; max、超上限（&gt;200K）→ 剔除</td><td>0 行剔除</td></tr>
  <tr><td>去重</td><td>按 <code>job_id</code>（退化按职位+公司+城市）去重</td><td>0 条重复</td></tr>
</table>
<p>清洗后数据：<strong>{N} 行 × 18 列</strong>。关键代码（带注释）：</p>
<pre><span class="c"># 1. 类型转换：薪资/日期转可计算类型，并派生月薪均值</span>
df["salary_min"] = pd.to_numeric(df["salary_min"], errors="coerce")
df["salary_max"] = pd.to_numeric(df["salary_max"], errors="coerce")
df["publish_date"] = pd.to_datetime(df["publish_date"], errors="coerce")
df["salary_avg"] = (df["salary_min"] + df["salary_max"]) / 2

<span class="c"># 2. 缺失值：关键字段丢行，分类字段补「未知」</span>
df = df.dropna(subset=["salary_min","salary_max","job_title"])
for col in ["city","education_req","experience_req","industry"]:
    df[col] = df[col].fillna("未知")

<span class="c"># 3. 异常值：薪资必须为正、min<=max、且不超过上限</span>
df = df[(df["salary_min"]>0) & (df["salary_max"]>0) &
        (df["salary_min"]<=df["salary_max"]) & (df["salary_max"]<=200)]

<span class="c"># 4. 去重：优先按 job_id</span>
df = df.drop_duplicates(subset=["job_id"], keep="first")</pre>

<h2>4. 探索性数据分析（EDA）</h2>
<p>围绕「描述统计 + 分组统计」两条主线展开，对应项目方案中的 5 个业务问题。描述统计把握薪资整体水位：样本月薪均值 <strong>{desc['mean']}K</strong>、中位数 <strong>{desc['50%']}K</strong>、区间 <strong>{desc['min']:.0f}–{desc['max']:.0f}K</strong>、标准差 <strong>{desc['std']}K</strong>（差异中等）。</p>

<h3>4.1 城市分布与薪资（对应问题①：需求分布）</h3>
<img class="chart" src="data:image/png;base64,{imgs['city']}">
<div class="figcap">图1　城市：岗位数（柱）vs 均薪（折线），双轴</div>
<p>样本中成都 {city_cnt.get('成都',0)} 个岗位（需求最密集）、重庆 {city_cnt.get('重庆',0)} 个；均薪方面 <strong>重庆 {city_avg.get('重庆',0)}K &gt; 成都 {city_avg.get('成都',0)}K</strong>。结论：成都岗位量大、选择多；重庆起薪更具竞争力，两地通投可扩大命中率。</p>

<h3>4.2 经验要求分布与薪资（对应问题④：门槛差异）</h3>
<img class="chart" src="data:image/png;base64,{imgs['exp']}">
<div class="figcap">图2　经验要求：岗位数（柱）vs 均薪（折线），双轴</div>
<p>「1-3年」以 {exp_cnt.get('1-3年',0)} 个岗位成为绝对主力，「应届/在校」仅 {exp_cnt.get('应届/在校',0)} 个。说明企业普遍要求即战力，初级岗位是应届生主要入口，但纯应届岗稀缺。</p>

<h3>4.3 技能词频（对应问题③：技能画像）</h3>
<img class="chart" src="data:image/png;base64,{imgs['skill']}">
<div class="figcap">图3　技能出现频次 TOP（横向条形）</div>
<p>高频技能前五：<strong>Hive {int(sk_top.get('Hive',0))}、SQL {int(sk_top.get('SQL',0))}、Spark {int(sk_top.get('Spark',0))}、Python {int(sk_top.get('Python',0))}、Flink {int(sk_top.get('Flink',0))}</strong>。SQL+Hive+Spark 构成数据开发刚需「三件套」，Flink/Kafka 反映实时计算需求上升。</p>

<h3>4.4 学历分布与薪资（对应问题④：门槛差异）</h3>
<img class="chart" src="data:image/png;base64,{imgs['edu']}">
<div class="figcap">图4　学历：岗位数（柱）vs 均薪（折线），双轴</div>
<p>学历结构：本科 {edu_cnt.get('本科',0)} 个（主流）、大专 {edu_cnt.get('大专',0)} 个、硕士 {edu_cnt.get('硕士',0)} 个；均薪 本科 {edu_avg.get('本科',0)}K、硕士 {edu_avg.get('硕士',0)}K、大专 {edu_avg.get('大专',0)}K。小样本下学历溢价不明显，强调项目与实习经历更重要。</p>

<h3>4.5 岗位与行业结构（对应问题⑤：岗位细分）</h3>
<p>岗位类型 TOP：数据平台工程师 {int(title_top.get('数据平台工程师',0))}、Flink实时开发工程师 {int(title_top.get('Flink实时开发工程师',0))}、数仓开发工程师 {int(title_top.get('数仓开发工程师',0))} 等；行业分布：软件 {int(ind.get('软件',0))}、政务信息化 {int(ind.get('政务信息化',0))}、智能制造 {int(ind.get('智能制造',0))} 居前。平台类与实时类岗位需求突出，与「数仓 ETL」求职方向高度契合。</p>

<h2>5. 业务结论与项目价值</h2>
<div class="concl"><b>结论一 · 地域选择：</b>成都岗位量大（{city_cnt.get('成都',0)} 个）、机会密集；重庆起薪更高（{city_avg.get('重庆',0)}K &gt; 成都 {city_avg.get('成都',0)}K）。建议应届生优先布局川渝，重机会量看成都、重起薪看重庆，两地通投扩大命中。</div>
<div class="concl"><b>结论二 · 经验门槛：</b>30 岗中「1-3年」占 {exp_cnt.get('1-3年',0)} 个（主力），「应届/在校」仅 {exp_cnt.get('应届/在校',0)} 个。企业普遍要即战力——必须用 <b>实习 + 课程项目 + 竞赛</b> 把简历填出实战痕迹，否则初筛易被刷。</div>
<div class="concl"><b>结论三 · 技能路线：</b>SQL+Hive+Spark 是刚需三件套，Flink/Kafka 代表实时趋势。建议先精通 SQL 与 Hive 数仓建模，再熟用 Spark，有余力补 Flink，切忌一上来贪多求全。</div>
<div class="concl"><b>结论四 · 学历焦虑：</b>本科 {edu_cnt.get('本科',0)} 个为招聘主流，但本科均薪（{edu_avg.get('本科',0)}K）不输硕士（{edu_avg.get('硕士',0)}K）。学历是门槛而非天花板，专科生把数仓 ETL 项目做透、能讲清技术细节与业务价值，比刷学历标签更有效。</div>
<h3>项目价值</h3>
<ul>
  <li><b>技术闭环展示：</b>覆盖爬虫、数据清洗、EDA、可视化全栈，体现完整工程能力。</li>
  <li><b>数据合规意识：</b>主动规避商业平台、遵守 robots 与采集规范，展现职业素养。</li>
  <li><b>决策支持：</b>把感性求职经验转化为可量化洞察，可直接用于个人求职规划。</li>
  <li><b>可复现可部署：</b>全流程脚本化，换真实数据一键复现，成果可挂载作品集网站。</li>
</ul>

<h2>6. 项目总结、局限性、后续可优化方向</h2>
<h3>6.1 项目总结</h3>
<p>本项目从合规公开数据源出发，独立完成了「采集 → 清洗 → 探索性分析 → 可视化」的完整数据工程链路，并以 4 张图表 + 4 条落地结论回应了求职核心问题。整套流程脚本化、可复现，既是求职决策工具，也是个人技术能力的可视化证明。</p>
<h3>6.2 局限性</h3>
<table>
  <tr><th>维度</th><th>说明</th></tr>
  <tr><td>样本偏差</td><td>仅覆盖部分公开渠道，未含商业平台，样本不代表全市场</td></tr>
  <tr><td>时效限制</td><td>为特定时间窗口的快照，市场随季节与政策波动</td></tr>
  <tr><td>字段噪声</td><td>公开页存在反爬占位、字段缺失，需清洗兜底</td></tr>
  <tr><td>薪资精度</td><td>薪资为区间归一化均值，仅反映趋势，非精确报价</td></tr>
  <tr><td>定位边界</td><td>产出为趋势性洞察，非就业指导，须标注来源与口径</td></tr>
  <tr><td>数据性质</td><td>当前为演示数据，结论用于方法验证，真实数据待采集</td></tr>
</table>
<h3>6.3 后续可优化方向</h3>
<ul>
  <li><b>真实数据采集：</b>在本人环境运行采集器抓取合规公开源，替换演示数据产出正式结论。</li>
  <li><b>技能共现矩阵：</b>引入共现分析（已实现于 ECharts 看板），识别「Hive×Spark」「Flink×Kafka」等技术组合。</li>
  <li><b>岗位文本聚类：</b>用 TF-IDF + KMeans 将职位描述自动划分为数仓/分析/平台/算法等典型类别。</li>
  <li><b>自动化调度：</b>引入 Shell / Airflow 实现增量更新，沉淀为长期运行的数据管道。</li>
  <li><b>实时交互看板：</b>将 matplotlib 静态图升级为可筛选的 Web 看板，支持多维下钻。</li>
  <li><b>多维度扩展：</b>补充公司规模、融资阶段、远程/驻场等维度，丰富分析视角。</li>
</ul>

<footer>
  大数据招聘岗位数据分析 · 求职作品集项目报告　|　技术栈：Python · requests/bs4 · pandas · matplotlib · ECharts<br>
  本报告生成于 2026-10-21，图表基于演示数据（{N} 条）渲染，仅供方法演示与作品集展示。
</footer>
</div>
</body>
</html>"""

out = ROOT / "project_report.html"
out.write_text(HTML, encoding="utf-8")
print("已生成", out.name, "字节:", out.stat().st_size)
