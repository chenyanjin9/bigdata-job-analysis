# -*- coding: utf-8 -*-
"""
大数据招聘岗位数据分析 —— 合规采集框架 (requests + bs4)
==================================================================
适用对象：政府公共招聘渠道 / 公开数据集（如中国公共招聘网、各地公共就业网、川渝公共就业服务平台）
重要边界：不建议、也不在本框架默认配置中爬取 BOSS直聘 / 智联 / 前程无忧 / 拉勾 等商业平台。
          原因：① 这些站点 robots.txt 普遍禁止抓取、存在反爬与登录墙；
                ② 批量抓取违反其用户协议，国内已有数据抓取不正当竞争判例；
                ③ 简历项目应体现数据合规意识。
本文件提供"可运行骨架 + 合规护栏"，把 START_URLS 换成合规公开源、按真实 DOM 调整选择器即可上线。
"""
import csv
import time
import random
import logging
from pathlib import Path
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("collector")

# ========================== 配置区 ==========================
# 1) 待采集的"合规公开列表页"。请替换为真实可用的政府/公共招聘频道 URL。
START_URLS = [
    # 示例（需替换为实际可达地址，例如中国公共招聘网对应频道、四川省/重庆市公共就业网职位列表）：
    # "https://job.mohrss.gov.cn/front/joblist.html",
    # "https://www.sc91.org.cn/xxx",
]

# 2) 采集节奏（合规核心参数）
BASE_DELAY = 2.0     # 两次请求最小间隔（秒）
JITTER = 1.5         # 额外随机抖动上限（秒），避免固定频率被识别为机器人
TIMEOUT = 15          # 单请求超时（秒）
MAX_RETRIES = 3       # 失败重试次数

# 3) 输出字段（与 jobs_sample.csv 表头一致）
FIELDS = [
    "job_id",          # 职位唯一标识
    "job_title",       # 职位名称
    "company_name",    # 公司/单位名称
    "city",            # 城市
    "district",        # 区县（可选）
    "salary_text",     # 原始薪资文本（如 "10-15K"）
    "salary_min",      # 最低月薪（K，归一化后）
    "salary_max",      # 最高月薪（K，归一化后）
    "experience_req",  # 经验要求
    "education_req",   # 学历要求
    "company_size",    # 公司规模
    "industry",        # 所属行业
    "skill_tags",      # 技能标签（分号分隔）
    "job_description", # 岗位职责
    "publish_date",    # 发布时间
    "source",          # 数据来源站点
    "crawl_time",      # 采集时间
]

# 4) User-Agent 池（适度轮换，仍保持低频）
UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
]

OUT_CSV = Path(__file__).parent / "jobs_raw.csv"
# ===========================================================


class RateLimiter:
    """简单的限速器：保证请求间隔 >= base + 随机抖动。"""
    def __init__(self, base: float, jitter: float):
        self.base = base
        self.jitter = jitter
        self.last = 0.0

    def wait(self):
        gap = self.base + random.uniform(0, self.jitter)
        elapsed = time.time() - self.last
        if elapsed < gap:
            time.sleep(gap - elapsed)
        self.last = time.time()


class CompliantSpider:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Accept-Language": "zh-CN,zh;q=0.9"})
        self.rate = RateLimiter(BASE_DELAY, JITTER)
        self.robots_cache: dict = {}
        self.seen = set()

    # ---------- 合规护栏 ----------
    def can_fetch(self, url: str) -> bool:
        """读取并遵守目标站 robots.txt。"""
        p = urlparse(url)
        base = f"{p.scheme}://{p.netloc}"
        rp = self.robots_cache.get(base)
        if rp is None:
            rp = RobotFileParser()
            rp.set_url(base + "/robots.txt")
            try:
                rp.read()
            except Exception as e:
                log.warning("无法读取 robots.txt(%s)：%s，默认放行但请人工确认", base, e)
                rp = None
            self.robots_cache[base] = rp
        if rp is None:
            return True
        return rp.can_fetch(self.session.headers.get("User-Agent"), url)

    def fetch(self, url: str) -> str | None:
        """带限速、重试、429 处理的页面抓取。"""
        if not self.can_fetch(url):
            log.warning("robots 禁止抓取，已跳过：%s", url)
            return None
        for attempt in range(MAX_RETRIES):
            self.rate.wait()
            ua = random.choice(UA_POOL)
            try:
                r = self.session.get(url, timeout=TIMEOUT, headers={"User-Agent": ua})
                if r.status_code == 429:
                    wait = int(r.headers.get("Retry-After", 30))
                    log.warning("收到 429，按 Retry-After 等待 %s 秒", wait)
                    time.sleep(wait)
                    continue
                r.raise_for_status()
                r.encoding = r.apparent_encoding or "utf-8"
                return r.text
            except Exception as e:
                log.error("请求失败(第%d次) %s：%s", attempt + 1, url, e)
                time.sleep(5)
        return None

    # ---------- 解析层（需按目标站真实 DOM 调整选择器） ----------
    def parse_list(self, html: str, base_url: str) -> list[dict]:
        """解析列表页，抽取每条职位的概要 + 详情页链接。
        TODO: 把下面的 'TODO ...' 选择器替换成目标站真实的 CSS 选择器。
        """
        soup = BeautifulSoup(html, "html.parser")
        items = []
        # 例：for card in soup.select("div.job-card"):
        for card in soup.select("TODO .job-card"):
            a = card.select_one("a")
            title = card.select_one("TODO .job-title")
            company = card.select_one("TODO .company")
            items.append({
                "job_title": title.get_text(strip=True) if title else "",
                "company_name": company.get_text(strip=True) if company else "",
                "url": urljoin(base_url, a.get("href", "")) if a else "",
            })
        return items

    def parse_detail(self, html: str) -> dict:
        """解析详情页：薪资 / 经验 / 学历 / 技能 / 职责。
        TODO: 按目标站详情页 DOM 调整。下面给出常见字段的抽取骨架。
        """
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)
        # 这里仅做占位，真实实现请用 select_one 定位各字段节点
        return {
            "salary_text": "",
            "salary_min": "",
            "salary_max": "",
            "experience_req": "",
            "education_req": "",
            "company_size": "",
            "industry": "",
            "skill_tags": "",
            "job_description": text[:500],
            "publish_date": "",
        }

    # ---------- 调度与落盘 ----------
    def crawl(self) -> list[dict]:
        rows = []
        for url in START_URLS:
            html = self.fetch(url)
            if not html:
                continue
            items = self.parse_list(html, url)
            log.info("列表页 %s 解析到 %d 条", url, len(items))
            for it in items:
                detail_html = self.fetch(it.get("url", ""))
                if not detail_html:
                    continue
                detail = self.parse_detail(detail_html)
                row = {**it, **detail}
                row["source"] = urlparse(url).netloc
                row["crawl_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                # 简单去重
                key = row.get("job_title", "") + "|" + row.get("company_name", "")
                if key in self.seen:
                    continue
                self.seen.add(key)
                rows.append(row)
        self.save(rows)
        return rows

    @staticmethod
    def save(rows: list[dict]):
        with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in FIELDS})
        log.info("已保存 %d 条记录 -> %s", len(rows), OUT_CSV)


if __name__ == "__main__":
    if not START_URLS:
        log.warning(
            "尚未配置 START_URLS。请：\n"
            "  1) 在文件顶部填入合规的公开招聘列表页 URL；\n"
            "  2) 按目标站 DOM 调整 parse_list / parse_detail 中的选择器；\n"
            "  3) 再次运行 `python collector.py`。\n"
            "本框架默认不爬取任何商业招聘平台。"
        )
    else:
        CompliantSpider().crawl()
