# 大数据招聘岗位数据分析

> 专科 · 大数据技术专业 · 求职作品集项目｜从合规公开数据源出发，构建「采集 → 清洗 → EDA → 可视化」全链路，量化岗位供需、技能与薪酬格局。

[🌐 在线报告（GitHub Pages）](https://<你的用户名>.github.io/bigdata-job-analysis/) ｜ [📄 完整项目报告（Markdown）](index.md) ｜ [📊 交互式看板（ECharts）](analysis_report.html)

---

## 项目简介

本项目以**政府公共就业渠道与公开数据集**为对象（主动规避 BOSS直聘、智联等商业平台的合规与法律风险），独立完成一套可复现的数据分析流水线：

1. **数据采集** — `requests + BeautifulSoup`，内置 robots 校验、限速、429 退避，CSV 落盘
2. **数据清洗** — `pandas`：去重、缺失值、异常值、类型转换（脚本按真实脏数据标准编写）
3. **探索性分析** — 描述统计 + 分组统计，覆盖需求分布 / 薪酬结构 / 技能画像 / 门槛差异 / 岗位细分
4. **可视化** — `matplotlib` 静态图 + `ECharts` 交互看板

## 目录结构

```
bigdata-job-analysis/
├── index.md                 # 完整项目报告（GitHub Pages 首页）
├── README.md                # 本文件：仓库首页介绍
├── collector.py             # 合规采集器（requests + bs4）
├── 采集说明.md              # 数据源推荐、字段清单、爬虫合规规范
├── eda_clean.py             # 清洗 + EDA 脚本
├── jobs_sample.csv          # 演示数据（标注「非真实采集」）
├── jobs_clean.csv           # 清洗后数据
├── viz.py                   # matplotlib 绘图脚本
├── build_report.py          # ECharts 看板生成器
├── build_report_doc.py      # 本报告（HTML）生成器
├── analysis_report.html     # ECharts 交互看板
├── project_report.html      # 自包含 HTML 报告
├── imgs/                    # 4 张 matplotlib 图表
├── 面试口述稿.md            # 2 分钟面试讲述稿
└── 面试问答.md              # 常见面试提问与参考回答
```

## 关键发现（演示数据，N=30）

- 地域：成都岗位量大（18）、重庆起薪更高（15.58K > 12.83K）
- 经验：1-3 年占 16 个（主力），应届/在校仅 2 个
- 技能：Hive / SQL / Spark 为刚需三件套，Flink / Kafka 反映实时趋势
- 学历：本科 20 个主流，但本科均薪（14.2K）不输硕士（13.6K）

## 快速复现

```bash
pip install requests beautifulsoup4 pandas matplotlib
python collector.py        # 抓取合规公开源 → jobs_raw.csv
python eda_clean.py         # 清洗 → jobs_clean.csv
python viz.py               # 生成 4 张图 + 可视化报告
python build_report.py      # 生成 ECharts 看板
```

## 技术栈

`Python` · `requests / BeautifulSoup` · `pandas` · `matplotlib` · `ECharts` · `数据合规`

---

⚠️ 当前数据为**演示样本（已标注）**，仅用于方法验证；真实数据请于本人环境运行采集器抓取合规公开源后按相同流程复现。
