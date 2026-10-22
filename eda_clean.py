# -*- coding: utf-8 -*-
"""
大数据招聘岗位数据分析 —— 数据清洗 + EDA 探索性分析
技术栈：pandas
输入：jobs_sample.csv（演示数据；真实场景替换为 jobs_raw.csv）
输出：jobs_clean.csv（清洗后数据集）+ 控制台分析报告

说明：本脚本按"真实脏数据"标准编写，对演示数据运行时将如实报告各项清洗的命中数量；
      换成真实采集的 jobs_raw.csv 后，同样的流程即可直接复用。
"""
import pandas as pd
import numpy as np

SRC = "jobs_sample.csv"      # 原始数据
OUT = "jobs_clean.csv"        # 清洗后输出
SALARY_CAP = 200              # 月薪上限阈值(K)，超过视为异常值

print("=" * 70)
print("0. 读取原始数据")
print("=" * 70)
df = pd.read_csv(SRC, encoding="utf-8-sig")
print(f"原始数据形状：{df.shape[0]} 行 × {df.shape[1]} 列")
print("字段：", list(df.columns))

# =====================================================================
# 1. 数据清洗
# =====================================================================
print("\n" + "=" * 70)
print("1. 数据清洗流程")
print("=" * 70)

# ---- 1.1 字段类型转换（先把薪资/日期转成可计算类型）----
print("\n[1.1] 字段类型转换")
df["salary_min"] = pd.to_numeric(df["salary_min"], errors="coerce")  # 无法解析→NaN
df["salary_max"] = pd.to_numeric(df["salary_max"], errors="coerce")
df["publish_date"] = pd.to_datetime(df["publish_date"], errors="coerce")
df["crawl_time"] = pd.to_datetime(df["crawl_time"], errors="coerce")
# 派生字段：月薪均值（K），便于后续薪资分析
df["salary_avg"] = (df["salary_min"] + df["salary_max"]) / 2
print("已将 salary_min/salary_max 转为数值，publish_date/crawl_time 转为日期，并派生 salary_avg")

# ---- 1.2 缺失值处理 ----
print("\n[1.2] 缺失值检查与处理")
miss = df.isna().sum()
miss = miss[miss > 0]
if len(miss) == 0:
    print("各字段均无缺失值。")
else:
    print("缺失值分布：\n", miss)
# 关键字段（薪资）缺失 → 丢弃；分类字段缺失 → 填充"未知"
before = len(df)
df = df.dropna(subset=["salary_min", "salary_max", "job_title"])
for col in ["city", "education_req", "experience_req", "industry", "company_size"]:
    df[col] = df[col].fillna("未知")
print(f"因关键字段缺失丢弃 {before - len(df)} 行，分类字段缺失已填充'未知'")

# ---- 1.3 异常值处理（薪资逻辑 & 离群）----
print("\n[1.3] 异常值处理")
before = len(df)
# (a) 薪资必须为正且 min<=max
bad_logic = df[(df["salary_min"] <= 0) | (df["salary_max"] <= 0) |
               (df["salary_min"] > df["salary_max"])]
# (b) 超出合理上限
bad_cap = df[df["salary_max"] > SALARY_CAP]
n_bad = len(bad_logic) + len(bad_cap.drop(index=bad_logic.index))
df = df[(df["salary_min"] > 0) & (df["salary_max"] > 0) &
        (df["salary_min"] <= df["salary_max"]) & (df["salary_max"] <= SALARY_CAP)]
print(f"薪资逻辑异常（<=0 或 min>max）{len(bad_logic)} 条；超上限(>{SALARY_CAP}K) {len(bad_cap)} 条；共剔除 {before - len(df)} 行")

# ---- 1.4 去重 ----
print("\n[1.4] 去重")
before = len(df)
# 优先按 job_id 去重；job_id 缺失时退化为按"职位+公司"去重
if df["job_id"].notna().all() and (df["job_id"] != "").all():
    df = df.drop_duplicates(subset=["job_id"], keep="first")
else:
    df = df.drop_duplicates(subset=["job_title", "company_name", "city"], keep="first")
print(f"去除重复记录 {before - len(df)} 条")

df = df.reset_index(drop=True)
print(f"\n清洗完成：{df.shape[0]} 行 × {df.shape[1]} 列，已保存为 {OUT}")
df.to_csv(OUT, index=False, encoding="utf-8-sig")

# =====================================================================
# 2. 探索性分析（EDA）
# =====================================================================
print("\n" + "=" * 70)
print("2. 探索性分析 EDA")
print("=" * 70)

# ---- 2.1 描述统计 ----
print("\n[2.1] 数值字段描述统计（业务含义：把握薪资整体水位与离散度）")
desc = df[["salary_min", "salary_max", "salary_avg"]].describe()
print(desc.round(2))
print("→ 含义：均值/中位数反映市场薪资中枢；std 反映薪资差异；min/max 框定分布区间。")

# ---- 2.2 分类字段分布 ----
print("\n[2.2] 岗位/城市/学历/经验/行业分布（业务含义：看需求结构与人群门槛）")
print("\n· 职位 TOP：\n", df["job_title"].value_counts().head(10))
print("\n· 城市分布：\n", df["city"].value_counts())
print("\n· 学历要求：\n", df["education_req"].value_counts())
print("\n· 经验要求：\n", df["experience_req"].value_counts())
print("\n· 行业分布：\n", df["industry"].value_counts())

# ---- 2.3 分组统计：城市 × 薪资 ----
print("\n[2.3] 按城市分组（业务含义：识别高薪/高需求地区，指导求职地域选择）")
g_city = df.groupby("city").agg(
    岗位数=("job_id", "count"),
    薪资均值=("salary_avg", "mean"),
    薪资中位数=("salary_avg", "median"),
).round(1).sort_values("薪资均值", ascending=False)
print(g_city)

# ---- 2.4 分组统计：学历 × 薪资 ----
print("\n[2.4] 按学历分组（业务含义：量化学历对薪资/机会的影响）")
g_edu = df.groupby("education_req").agg(
    岗位数=("job_id", "count"),
    薪资均值=("salary_avg", "mean"),
).round(1).sort_values("薪资均值", ascending=False)
print(g_edu)

# ---- 2.5 分组统计：经验 × 薪资 ----
print("\n[2.5] 按经验分组（业务含义：看资历溢价，判断应届/初级竞争力）")
g_exp = df.groupby("experience_req").agg(
    岗位数=("job_id", "count"),
    薪资均值=("salary_avg", "mean"),
).round(1).sort_values("薪资均值", ascending=False)
print(g_exp)

# ---- 2.6 技能词频（业务含义：提炼企业最看重的技能栈）----
print("\n[2.6] 技能标签词频 TOP（业务含义：定位高频硬技能，指导学习路线）")
skills = df["skill_tags"].dropna().str.split(";").explode().str.strip()
print(skills.value_counts().head(15))

print("\nEDA 完成。以上结果可直接用于作品集'分析发现'章节。")
