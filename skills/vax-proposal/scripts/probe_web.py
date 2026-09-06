#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_web.py — 발주처와 과업 열쇳말을 넣으면 웹에서 재료를 긁어 「발상 자극 카드」를 만든다 (P3.5 첫 동작).
한준 2026-09-06 "발상이 저절로 나올 수 있도록 웹검색·웹데이터·웹 자료 추가". 기법 일곱(writing.md §3)은 질문일 뿐이라
답이 될 재료를 기계가 먼저 모아 둔다. 결과는 초안이 아니라 **재료**다 — 사실 확인·인용은 사람과 Claude가 원 페이지를 열어 한다.

사용:
  python3 probe_web.py --org "국립순천대학교" --kw "애니메이션 순천캠퍼스 VR 콘텐츠" --prev "2025 순천캠퍼스 VR 콘텐츠 제작" \
      --type 대학 --out bids/순천캠퍼스VR/03a_raw.md [--max 5] [--fetch] [--news]
  python3 probe_web.py --selftest              (오프라인 — 검색어 생성·숫자 문장 추출·서식)
  --type: 대학 | 공공기관 | 지자체 | 학교 | 공기업 | 기업 | 기타  (공식 데이터 사이트 링크가 달라진다)
  --fetch: 상위 결과 페이지를 열어 숫자가 든 문장을 뽑는다(한 페이지 10초 · 최대 12쪽). 없으면 검색 요약만.

의존성: ddgs(무료 DuckDuckGo) · requests · beautifulsoup4 — scripts/requirements.txt. 키 없음. 결과에 개인 이름이 있어도 옮기지 않는다(writing.md §2-7).
산출: 마크다운 하나. ① 출처 유형 일곱별 검색 결과 ② 공식 데이터 사이트 바로가기 ③ 숫자 후보(문장 · 출처) ④ 발상 기법 일곱별 자극 카드(관련 결과 + 빈 「→ 후보」 줄).
"""
import argparse, datetime, io, json, os, re, sys, time

UA = "Mozilla/5.0 (vax-proposal-kit probe_web; +https://github.com/vaxport123/vax-proposal-kit)"
UNIT = r"(명|개|억|만|천|%|퍼센트|년|회|대|곳|시간|분|초|km|㎡|m²|평|편|종|건|층|호|위|배|점|원|주|일)"
NUM_SENT = re.compile(r"[^.。!?\n]*\d[\d,\.]*\s*" + UNIT + r"[^.。!?\n]*[.。!?]?")
# 잡음: 공지·수강·장학·전화번호 같은 운영 문장은 숫자가 있어도 재료가 아니다. 소셜·위키·메인 페이지는 열지 않는다.
NOISE = re.compile(r"쿠키|저작권|copyright|로그인|배너|광고|공지|안내|신청|모집|수강|장학|접속|바로가기|폐강|입금|납부|메뉴|음소거|검색결과|위키백과, 우리|나무위키|\d{2,3}-\d{3,4}-\d{4}|서무|회계", re.I)
SKIP_URL = re.compile(r"instagram\.com|facebook\.com|youtube\.com|namu\.wiki|/main\.do|login|search\.do|selectOrganizList", re.I)
KW_GLOBAL = []


def relevance(text, kw=None):
    kw = kw if kw is not None else (KW_GLOBAL[0] if KW_GLOBAL else "")
    toks = [t for t in re.split(r"\s+", kw) if len(t) >= 2]
    return sum(1 for t in toks if t in text)

# 출처 유형 일곱(writing.md §2) → 검색어 틀. {org} 기관 · {kw} 과업 열쇳말 · {prev} 전년도 사업명 · {y} 올해 · {y1} 작년
SOURCE_QUERIES = {
    "홈페이지·조직": ["{org} 조직도", "{org} {kw} 담당 부서", "{org} 비전 발전계획", "{org} 정보공개 사업 안내"],
    "보도자료·SNS": ["{org} {kw}", "{org} 보도자료 {y}", "{org} {kw} 개소 OR 출범 OR 선정"],
    "전년도 같은 사업": ["{prev}", "{org} {kw} 용역 개찰", "{org} {kw} {y1}", "{kw} 나라장터 {org}"],
    "감사·평가·회의록": ["{org} 감사 결과", "{org} 경영평가 지적", "{org} 회의록 {kw}", "{org} 국정감사 OR 행정사무감사"],
    "상위 계획": ["{org} 중장기 발전계획 {kw}", "{kw} 정부 계획 {y}", "{org} 예산 {kw}"],
    "이용자 목소리": ["{org} {kw} 학생 OR 시민 인터뷰", "{org} {kw} 후기", "{org} 커뮤니티 {kw}"],
    "경쟁사 표준 답": ["{kw} 제안서 사례", "{kw} 구축 사례 업체", "{kw} 용역 수행 결과", "{kw} 도입 효과"],
}
# 발상 기법 일곱(writing.md §3) ← 어느 출처 유형의 결과를 자극으로 쓰나
TECH_SOURCES = [
    ("① 과업 다시 정의 — RFP 낱말을 발주처 목적으로 바꿔 읽으면 이 과업은 무엇인가", ["상위 계획", "홈페이지·조직", "보도자료·SNS"]),
    ("② 하루 시나리오 — 담당자·이용자의 하루 어디가 막히나", ["홈페이지·조직", "이용자 목소리"]),
    ("③ 경쟁사 표준 답 예측 — 뻔한 답을 적고 다른 축을 고른다", ["경쟁사 표준 답", "전년도 같은 사업"]),
    ("④ 우리 실물을 현장에 — 스튜디오·장비·실적을 이 현장에 놓으면 생기는 장면 (재료: assets/photos · 03b 카드)", []),
    ("⑤ 숫자 하나로 약속 — 사업 전체를 말하는 숫자 (아래 숫자 후보에서)", ["__numbers__"]),
    ("⑥ 반대 의견 뒤집기 — 심사위원의 의심을 이름으로 (지적·민원·감사에서 의심을 읽는다)", ["감사·평가·회의록", "이용자 목소리"]),
    ("⑦ 없는 것 찾기 — RFP엔 없고 감사·회의록·전년도엔 있는 것", ["감사·평가·회의록", "전년도 같은 사업", "상위 계획"]),
]
# 기관 유형별 공식 데이터(키 없이 브라우저로 여는 곳) — 출처 있는 숫자의 1차 공급원
OFFICIAL = {
    "대학": [("대학알리미 — 재학생·유학생·취업률·교원·예산", "https://www.academyinfo.go.kr/search/search.do?kwd={orgq}"),
             ("학술정보통계·대학 재정알리미", "https://uniapply.uwayapply.com/"), ("나라장터 발주 검색", "https://www.g2b.go.kr/")],
    "공공기관": [("알리오 ALIO — 경영공시·경영평가·감사", "https://www.alio.go.kr/search/search.do?searchKeyword={orgq}"),
               ("공공기관 경영평가 보고서(기재부)", "https://www.alio.go.kr/"), ("나라장터 발주 검색", "https://www.g2b.go.kr/")],
    "지자체": [("지방재정365 — 예산·사업별 세출", "https://www.lofin365.go.kr/"), ("지방의회 회의록 — 해당 의회 사이트 「회의록 검색」", "https://www.google.com/search?q={orgq}+의회+회의록"),
             ("나라장터 발주 검색", "https://www.g2b.go.kr/")],
    "학교": [("학교알리미 — 학생 수·시설·예산", "https://www.schoolinfo.go.kr/"), ("교육청 공고", "https://www.google.com/search?q={orgq}+교육청+공고")],
    "공기업": [("클린아이 — 지방공기업 경영공시", "https://www.cleaneye.go.kr/"), ("나라장터 발주 검색", "https://www.g2b.go.kr/")],
    "기업": [("DART 전자공시 — 사업보고서", "https://dart.fss.or.kr/"), ("기업 뉴스룸·보도자료", "https://www.google.com/search?q={orgq}+뉴스룸")],
    "기타": [("나라장터 발주 검색", "https://www.g2b.go.kr/"), ("정보공개포털", "https://www.open.go.kr/")],
}
COMMON = [("나라장터 개찰결과·전년도 낙찰 업체", "https://www.g2b.go.kr/"), ("국회 회의록 검색", "https://likms.assembly.go.kr/record/"),
          ("감사원 감사결과 공개", "https://www.bai.go.kr/bai/result/branch/list"), ("정보공개포털(정보공개 청구·공개 자료)", "https://www.open.go.kr/")]


def build_queries(org, kw, prev=""):
    y = datetime.date.today().year
    ctx = {"org": org, "kw": kw, "prev": prev or (org + " " + kw + " " + str(y - 1)), "y": y, "y1": y - 1}
    out = {}
    for src, tpls in SOURCE_QUERIES.items():
        qs = []
        for t in tpls:
            q = t.format(**ctx).strip()
            if q and q not in qs:
                qs.append(q)
        out[src] = qs
    return out


def number_sentences(text, limit=15):
    seen, out = set(), []
    for m in NUM_SENT.finditer(text):
        s = re.sub(r"\s+", " ", m.group(0)).strip()
        if 12 <= len(s) <= 160 and s not in seen and not NOISE.search(s):
            seen.add(s); out.append(s)
            if len(out) >= limit:
                break
    return out


def strip_person_names(s):
    # 개인 이름은 옮기지 않는다(writing.md §2-7). 「홍길동 기자」「김OO 교수」 같은 꼴을 지운다 — 완전하지 않으니 사람이 한 번 더 본다.
    return re.sub(r"[가-힣]{2,4}\s?(기자|교수|팀장|과장|대표|학생|씨|담당자|주무관|국장|처장|총장)", "○○ \\1", s)


def search(queries, max_results=5, news=False, region="kr-kr", sleep=0.6):
    try:
        from ddgs import DDGS
    except ImportError:
        sys.exit("ddgs 없음 — pip install -r scripts/requirements.txt")
    hits, seen = {}, set()
    d = DDGS()
    for src, qs in queries.items():
        hits[src] = []
        for q in qs:
            try:
                rs = d.text(q, max_results=max_results, region=region)
            except Exception as e:
                rs = []; hits[src].append({"q": q, "error": str(e)[:80]})
            for r in rs or []:
                u = r.get("href") or r.get("url") or ""
                if not u or u in seen:
                    continue
                seen.add(u)
                hits[src].append({"q": q, "title": strip_person_names(r.get("title", "")), "url": u, "snippet": strip_person_names(r.get("body", ""))[:220]})
            time.sleep(sleep)
    if news:
        hits["뉴스(최근)"] = []
        for q in [f"{queries.get('_org','')}"] if False else [list(queries.values())[1][0]]:
            try:
                rs = d.news(q, max_results=max_results * 2, region=region)
            except Exception as e:
                rs = []
            for r in rs or []:
                u = r.get("url", "")
                if u and u not in seen:
                    seen.add(u); hits["뉴스(최근)"].append({"q": q, "title": strip_person_names(r.get("title", "")), "url": u, "snippet": strip_person_names(r.get("body", ""))[:220], "date": (r.get("date") or "")[:10]})
    for src in hits:
        hits[src].sort(key=lambda h: -relevance(h.get("title", "") + " " + h.get("snippet", "")))
    return hits


def fetch_numbers(hits, max_pages=12, timeout=10):
    import requests
    from bs4 import BeautifulSoup
    urls = []
    for src, lst in hits.items():
        for h in lst:
            u = h.get("url", "")
            if u.startswith("http") and not re.search(r"\.(pdf|hwp|hwpx|zip|xlsx?|pptx?)($|\?)", u, re.I) and not SKIP_URL.search(u):
                urls.append((src, h["title"], u))
    numbers = []
    for src, title, u in urls[:max_pages]:
        try:
            r = requests.get(u, headers={"User-Agent": UA}, timeout=timeout)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            for t in soup(["script", "style", "nav", "footer", "header", "aside"]):
                t.decompose()
            text = soup.get_text(" ")
            for s in number_sentences(text):
                numbers.append({"sent": strip_person_names(s), "url": u, "title": title, "src": src})
        except Exception:
            continue
        time.sleep(0.4)
    # 열쇳말이 든 문장을 앞에, 같은 문장 중복 제거
    seen = set(); uniq = []
    for n in numbers:
        if n["sent"] not in seen:
            seen.add(n["sent"]); uniq.append(n)
    uniq.sort(key=lambda n: -relevance(n["sent"]))
    return uniq


def render(org, kw, prev, otype, queries, hits, numbers, fetched):
    today = datetime.date.today().isoformat()
    L = [f"# 03a_raw — 웹 재료 자동 수집 · {org} · {kw}", "",
         f"수집 {today} · `probe_web.py` · 검색어 {sum(len(v) for v in queries.values())}개 · 결과 {sum(len([h for h in v if 'url' in h]) for v in hits.values())}건 · 페이지 열어 숫자 뽑기: {'했음' if fetched else '안 함(--fetch)'}",
         "**이 파일은 재료다.** 여기 문장을 그대로 본문에 옮기지 않는다. 원 페이지를 열어 확인한 사실만 `03a_페인포인트.md`에 「RFP 문장 ↔ 사실(출처·날짜) ↔ 숨은 필요」로 옮긴다. 개인 이름은 옮기지 않는다.", ""]
    L += ["## 0. 공식 데이터 바로가기 (출처 있는 숫자의 1차 공급원 — 열어서 재학생·예산·평가 결과를 적는다)"]
    orgq = org.replace(" ", "+")
    for name, url in OFFICIAL.get(otype, OFFICIAL["기타"]) + COMMON:
        L.append(f"- {name}: {url.format(orgq=orgq)}")
    L.append("")
    L += ["## 1. 출처 유형별 검색 결과 (writing.md §2 일곱 유형)"]
    for src, lst in hits.items():
        L.append(f"### {src}")
        qs = queries.get(src, [])
        if qs:
            L.append("검색어: " + " · ".join(f"「{q}」" for q in qs))
        good = [h for h in lst if "url" in h]
        if not good:
            L.append("- (결과 없음 — 검색어를 바꿔 다시)")
        for h in good[:10]:
            d = f" ({h['date']})" if h.get("date") else ""
            L.append(f"- [{h['title'][:70]}]({h['url']}){d} — {h['snippet']}")
        L.append("")
    L += ["## 2. 숫자 후보 (페이지에서 뽑은 문장 — 원 페이지에서 확인한 뒤에만 쓴다)", "| 문장 | 출처 |", "|---|---|"]
    if numbers:
        for n in numbers[:40]:
            L.append(f"| {n['sent'][:140]} | [{n['title'][:40]}]({n['url']}) |")
    else:
        L.append("| (없음 — `--fetch` 로 다시, 또는 §0 공식 데이터에서 직접) | |")
    L.append("")
    L += ["## 3. 발상 자극 카드 — 기법 일곱 (writing.md §3) · 각 줄의 「→ 후보」를 채운다"]
    for name, srcs in TECH_SOURCES:
        L.append(f"### {name}")
        if "__numbers__" in srcs:
            for n in numbers[:8]:
                L.append(f"- {n['sent'][:120]} — {n['url']}")
            if not numbers:
                L.append("- (숫자 후보 없음 — §0 공식 데이터에서 직접 적는다)")
        else:
            cnt = 0
            for s2 in srcs:
                for h in [h for h in hits.get(s2, []) if "url" in h][:3]:
                    L.append(f"- [{s2}] {h['title'][:60]} — {h['snippet'][:120]} ({h['url']})"); cnt += 1
            if cnt == 0 and srcs:
                L.append("- (관련 결과 없음)")
            if not srcs:
                L.append("- (웹이 아니라 우리 재료: `assets/photos/MANIFEST.md` · `03b` 카드에서)")
        L.append("→ 후보 1: ")
        L.append("→ 후보 2: ")
        L.append("")
    L += ["## 4. 다음", "- §1·§2에서 사실 5~8개를 골라 원 페이지를 열어 확인하고 `03a_페인포인트.md`에 옮긴다(출처·날짜 필수).",
          "- §3의 「→ 후보」를 채우고 `03b_방향전략.md` 「기법별 후보」 표로 옮긴다. 후보 셋 → 이름 후보 셋 → 하나.",
          "- 결과가 빈약하면 `--prev`(전년도 사업명 정확히)와 `--kw`(RFP 배경 문단의 고유명사)를 바꿔 다시 돌린다."]
    return "\n".join(L) + "\n"


def selftest():
    fails = []
    q = build_queries("예시대학교", "실감콘텐츠 전시관", "2025 예시 전시관 콘텐츠 제작")
    if sum(len(v) for v in q.values()) < 20: fails.append("검색어 수")
    if any("{" in x for v in q.values() for x in v): fails.append("치환 안 됨")
    ns = number_sentences("전시관 첫해 관람객은 목표의 60%였다. 담당 직원은 2명이다. 로그인 후 이용 가능합니다 3회. 예산은 1억 2천만 원으로 편성됐다.")
    if len(ns) < 2 or any("로그인" in s for s in ns): fails.append("숫자 문장 추출 " + str(ns))
    if "○○ 기자" not in strip_person_names("홍길동 기자가 썼다"): fails.append("이름 가림")
    hits = {"홈페이지·조직": [{"q": "a", "title": "t", "url": "https://x", "snippet": "s"}]}
    md = render("예시대학교", "실감콘텐츠", "", "대학", q, hits, [{"sent": "관람객 60%", "url": "https://x", "title": "t", "src": "홈페이지·조직"}], False)
    for must in ["## 0.", "## 3.", "⑤ 숫자", "→ 후보 1", "대학알리미"]:
        if must not in md: fails.append("서식 " + must)
    print(("selftest 실패 " + " | ".join(fails)) if fails else "selftest OK — 검색어 %d개 · 숫자 문장 %d · 서식 · 이름 가림" % (sum(len(v) for v in q.values()), len(ns)))
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--org"); ap.add_argument("--kw"); ap.add_argument("--prev", default="")
    ap.add_argument("--type", default="기타", choices=list(OFFICIAL.keys())); ap.add_argument("--out"); ap.add_argument("--max", type=int, default=5)
    ap.add_argument("--fetch", action="store_true"); ap.add_argument("--news", action="store_true"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not (a.org and a.kw and a.out):
        ap.error("--org --kw --out 이 필요하다 (또는 --selftest)")
    queries = build_queries(a.org, a.kw, a.prev)
    print("검색어 %d개 …" % sum(len(v) for v in queries.values()), file=sys.stderr)
    KW_GLOBAL.append(a.kw)
    hits = search(queries, max_results=a.max, news=a.news)
    numbers = fetch_numbers(hits) if a.fetch else []
    md = render(a.org, a.kw, a.prev, a.type, queries, hits, numbers, a.fetch)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with io.open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    raw = os.path.splitext(a.out)[0] + ".json"
    with io.open(raw, "w", encoding="utf-8") as f:
        json.dump({"org": a.org, "kw": a.kw, "queries": queries, "hits": hits, "numbers": numbers}, f, ensure_ascii=False, indent=1)
    print("→ %s (결과 %d건 · 숫자 후보 %d)" % (a.out, sum(len([h for h in v if 'url' in h]) for v in hits.values()), len(numbers)), file=sys.stderr)


if __name__ == "__main__":
    main()
