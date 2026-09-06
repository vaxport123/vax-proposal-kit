#!/usr/bin/env python3
"""proposal_material.py — 「도전」 공고 → 「📦 제안 재료 팩」 (LLM 0콜 · 결정론적 조립).

한준 2026-09-04 결정: 서버는 도전 공고에 대해 HTML·문서를 자동 생성하지 않는다. 대신 **서버가 이미
갖고 있는 것**(RFP 읽기 캐시·자격 캐시·채점 결과·회사 팩트·인증·실적·학습 DB·위키 레퍼런스 색인)을
정해진 목차로 모아 위키(Notion)의 그 공고 페이지 밑에 자식 페이지로 쓴다. 판단·전략·서술은
개인 Claude의 `vax-proposal` 스킬이 이 재료 팩을 읽어 사람과 함께 한다.

목차(H2 열 개, 0~9)는 `skills/vax-proposal/references/material-pack.md`가 계약이다 — 한쪽만 바꾸지 않는다.

지키는 것
  · LLM을 부르지 않는다. 캐시가 없으면 그 절을 `⚠️ 확인필요`로 비워 두고 §8에 적는다(조용히 메우지 않는다).
  · 이미 팩이 있고 판본 도장이 같으면 다시 쓰지 않는다(`--force`가 아니면).
  · 쓰기 전 공개 금지 검사(서버 주소·포트·모델명·채널 ID·서버 경로·토큰)를 통과해야 쓴다.
  · 기본은 dry(stdout에 마크다운). 위키 쓰기는 `--commit` 또는 env `BID_MATERIAL_COMMIT=1`.
  · 숫자에는 표본·출처를 붙인다. 상수(전 공고 공통)는 상수라고 적는다.

사용 (서버 pipeline 폴더에서)
  proposal_material.py --selftest
  proposal_material.py --list                    # 게이트(도전·우리담당·마감전) 통과 목록
  proposal_material.py --no R26EX00000001        # 한 건, stdout
  proposal_material.py --no R26EX00000001 --out /tmp/pack   # 마크다운 파일로도 저장
  proposal_material.py --no R26EX00000001 --commit          # 위키에 쓴다
  proposal_material.py --commit                  # 도전 전건(이미 같은 판본이 있으면 건너뜀)

배포 순서는 server/README.md 「배포 순서」를 따른다(재료가 먼저 나와야 초안 자동 생성을 끊어도 팀이 비지 않는다).
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VERSION = "2026-09-04-v5"
NEED = "⚠️ 확인필요"
PACK_TITLE = "📦 제안 재료 팩"
RFP_TITLE = "📄 RFP 원문(추출)"
STAMP_HEAD = "판본: "

EVAL_DIR = os.environ.get("BID_EVAL_DIR", "/var/lib/vax/eval")
READ_CACHE = os.environ.get("BID_RFP_READ", os.path.join(EVAL_DIR, "rfp_read.json"))
SCOPE_CACHE = os.environ.get("BID_SCOPE_CACHE", os.path.join(EVAL_DIR, "bid_scope.json"))
REQ_CACHE = os.environ.get("GONOGO_REQ_CACHE", os.path.join(EVAL_DIR, "gonogo_req.json"))
RESEARCH_CACHE = os.environ.get("BID_RESEARCH_CACHE", os.path.join(EVAL_DIR, "bid_research.json"))
QUALS_PATH = os.environ.get("BID_QUALS", "/var/lib/vax/bid_quals.json")
DUMP = os.environ.get("NOTION_DUMP_DIR", "/var/lib/vax/notion-dump")
# 위키 「레퍼런스 색인 — 실적 ↔ 기술요소 ↔ 재활용 문구」(01.WIKI_AI / Company). 이 페이지가 정본이다.
REF_INDEX_PAGE = os.environ.get("BID_REF_INDEX_PAGE", "3d16394f-4c99-81b4-93e3-d4b5dc7884a9")
REF_INDEX_URL = "https://app.notion.com/p/" + REF_INDEX_PAGE.replace("-", "")

DUMP_FILES = {
    "facts": "회사 팩트.jsonl",
    "certs": "Certifications.jsonl",
    "projects": "Projects.jsonl",
    "archive": "00.ERP_입찰결과아카이브.jsonl",
}

# 공개 금지 — ops/render_md_page.py FORBIDDEN 의 사본(같아야 한다). 재료 팩은 사내 위키에 남지만
# 스킬이 그대로 초안에 옮기므로 애초에 넣지 않는다.
FORBIDDEN = (
    (r"\b100\.\d+\.\d+\.\d+\b", "사설망 IP"),
    (r":8787\b", "내부 포트"),
    (r"\b(gemini|gpt-4|claude-[a-z]+-\d)", "모델명"),
    (r"\bC0[A-Z0-9]{8,}\b", "슬랙 채널·유저 ID"),
    (r"/opt/vax|/var/lib/vax|/var/www", "서버 경로"),
    (r"xox[bp]-|xapp-", "토큰"),
)

# material-pack.md 계약 — 이름·순서 고정
SECTIONS = (
    "0. 공고 기본", "1. 과업 요구 (RFP 추출)", "2. 평가배점표", "3. 발주처 지정 목차·분량",
    "4. 참가자격·필수 서류", "5. 우리 자격·실적·인증 (이 공고용으로 고른 것)", "6. 정량 지표",
    "7. 유사 과거 입찰", "8. 메꿔야 할 빈칸", "9. 부속 파일",
)

COMMIT = os.environ.get("BID_MATERIAL_COMMIT") == "1"
STOP = set(("의 및 등 을 를 이 가 은 는 에 와 과 로 으로 위한 통한 대한 사업 용역 제작 개발 구축 운영 콘텐츠 년 제 차 "
            "기획 관리 문서 제출 데이터 완료일 개최 이내 착수계 계약체결 중간보고회 최종보고회 착수보고회 전까지 납품 보고 보고서 "
            "회의록 시안 제안 제안서 시스템 설계 서비스 지원 방안 계획 수행 추진 결과 성과품 산출물 자료 내용 관련 기타 일체 "
            "이상 이하 기준 사항 경우 포함 통해 대상 활동 업무 진행 작성 반영 협의 검수 납기 기간 일정 사업자 발주기관 발주처 "
            "계약 계약상대자 상대자 공고 입찰 참가 자격 확인 확인서 소지 등록 업체 업종 코드 품명 세부 형식 파일 용량").split())
ONDEMAND_DOCS = ("입찰참가자격등록증", "경쟁입찰참가자격등록증", "납세증명", "완납증명", "법인인감증명", "사업자등록증", "등기사항")
DOC_WORDS = ("증명", "확인서", "등록증", "서약서", "사업자", "등기", "증", "현황", "제안서", "신고", "신용")


# ── 속성 읽기 (Notion page.properties) ─────────────────────────────────────────
def _pv(p, k):
    return (p.get(k, {}) or {})


def _txt(p, k):
    v = _pv(p, k)
    arr = v.get("rich_text") if v.get("type") == "rich_text" or "rich_text" in v else v.get("title", [])
    return "".join(x.get("plain_text", "") for x in (arr or [])).strip()


def _links(p, k):
    """rich_text 조각 중 href 있는 것 → [(글자, url)]."""
    out = []
    for x in (_pv(p, k).get("rich_text") or []):
        if x.get("href"):
            out.append((x.get("plain_text", "").strip() or x["href"], x["href"]))
    return out


def _sel(p, k):
    return ((_pv(p, k).get("select") or {}).get("name") or "").strip()


def _multi(p, k):
    return [x.get("name", "") for x in (_pv(p, k).get("multi_select") or [])]


def _num(p, k):
    return _pv(p, k).get("number")


def _date(p, k):
    return ((_pv(p, k).get("date") or {}).get("start") or "")


def _url(p, k):
    return _pv(p, k).get("url") or ""


def _check(p, k):
    return bool(_pv(p, k).get("checkbox"))


def _people(p, k):
    return [(x.get("name") or x.get("id", "")) for x in (_pv(p, k).get("people") or [])]


def _formula(p, k):
    f = _pv(p, k).get("formula") or {}
    return str(f.get(f.get("type"), "") or "")


def won(v):
    try:
        return f"{int(v):,}원"
    except (TypeError, ValueError):
        return ""


# ── 게이트 (proposal_build._gate_reason 과 같은 판정 — 순수 함수) ───────────────────
def gate_reason(props, today):
    """레이더 행 → 재료 팩을 만들지 않을 사유 | ""(적격). 도전 + 우리담당 + 마감 전."""
    state = _sel(props, "진행상태")
    if state != "도전":
        return f"진행상태가 「{state or '미정'}」(도전 아님)"
    if not (_pv(props, "우리담당").get("people")):
        return "우리담당 미지정"
    due = _date(props, "입찰마감일")
    if due:
        try:
            if dt.date.fromisoformat(due[:10]) < today:
                return f"입찰마감({due[:10]}) 지남"
        except ValueError:
            pass
    return ""


# ── 캐시 ────────────────────────────────────────────────────────────────────────
def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f) or {}
    except (OSError, ValueError):
        return {}


def ingest_stamp(scope_entry):
    """bid_doc_ingest 산출의 판본 도장(bid_proposal_plan.ingest_stamp 와 같은 형식) — 없으면 '||0'."""
    d = scope_entry or {}
    return f"{d.get('src') or ''}|{d.get('at') or ''}|{len(d.get('scope') or [])}"


def pick_rfp(cache, no, stamp):
    """rfp_read.json 에서 이 공고의 항목을 고른다 → (key, entry, note).

    키는 `공고번호` · `공고번호#도장` · `공고번호#도장#읽기버전` 세 형태가 섞여 있고 옛 키가 정리되지
    않는다. 도장이 지금 판본과 같은 것을 우선, 그다음 읽기버전이 늦은 것, 그다음 내용이 많은 것."""
    cands = []
    for k, v in cache.items():
        if k == no or k.startswith(no + "#"):
            parts = k.split("#")
            k_stamp = parts[1] if len(parts) > 1 else ""
            ver = parts[2] if len(parts) > 2 else ""
            rich = len(v.get("tasks") or []) + len(v.get("eval_items") or []) + len(v.get("toc2") or [])
            cands.append(((k_stamp == stamp), ver, rich, k, v))
    if not cands:
        return None, {}, "RFP 읽기 캐시 없음"
    cands.sort(key=lambda c: (c[0], c[1], c[2]), reverse=True)
    same, ver, rich, k, v = cands[0]
    note = "" if same else f"판본 불일치 — 캐시 도장 {k.split('#')[1] if '#' in k else '(없음)'} ≠ 현재 {stamp}"
    return k, v, note


# ── 덤프 (notion-dump) ──────────────────────────────────────────────────────────
def dump_rows(name):
    """datasources/<name>.jsonl → [properties(+_id)]. 파일이 없으면 []."""
    path = os.path.join(DUMP, "datasources", DUMP_FILES[name])
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for ln in f:
                try:
                    d = json.loads(ln)
                except ValueError:
                    continue
                if d.get("archived") or d.get("in_trash"):
                    continue
                pr = d.get("properties") or {}
                pr["_id"] = d.get("id", "")
                pr["_url"] = d.get("url", "")
                out.append(pr)
    except OSError:
        pass
    return out


def dump_time():
    try:
        return (json.load(open(os.path.join(DUMP, "MANIFEST.json"), encoding="utf-8")) or {}).get("dumped_at", "")[:16]
    except (OSError, ValueError):
        return ""


def prop_str(p, k):
    """덤프 행의 어떤 타입이든 사람 글자로."""
    v = _pv(p, k)
    t = v.get("type")
    if t in ("rich_text", "title"):
        return "".join(x.get("plain_text", "") for x in (v.get(t) or [])).strip()
    if t == "select":
        return (v.get("select") or {}).get("name", "") or ""
    if t == "multi_select":
        return ", ".join(x.get("name", "") for x in (v.get("multi_select") or []))
    if t == "number":
        return "" if v.get("number") is None else str(v.get("number"))
    if t == "date":
        return (v.get("date") or {}).get("start", "") or ""
    if t == "checkbox":
        return "예" if v.get("checkbox") else "아니오"
    if t == "url":
        return v.get("url") or ""
    if t == "formula":
        return _formula(p, k)
    if t == "people":
        return ", ".join(_people(p, k))
    return ""


# ── 낱말 유사도 (LLM 없이 실적·과거 입찰을 고르는 기준) ─────────────────────────────
def grams(s):
    s = re.sub(r"[^0-9A-Za-z가-힣]", "", s or "")
    return {s[i:i + 2] for i in range(len(s) - 1)}


def sim(a, b):
    ga, gb = grams(a), grams(b)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / len(ga | gb)


def words(text):
    """한글·영문 낱말(2자 이상, 조사·범용어 제외)."""
    out = []
    for w in re.findall(r"[A-Za-z가-힣][A-Za-z가-힣0-9]+", text or ""):
        if w not in STOP:
            out.append(w)
    return out


def overlap(keys, text):
    """공고 열쇳말 중 본문에 실제로 있는 것 → 겹친 낱말 목록."""
    t = text or ""
    return [k for k in keys if k in t]


# ── 마크다운 → Notion 블록 ──────────────────────────────────────────────────────
def _rich(text, limit=1900):
    """굵게(**x**)·코드(`x`)·링크([t](u))만 인식. 조각마다 1900자 절단."""
    out, i = [], 0
    pat = re.compile(r"\*\*([^*]+)\*\*|`([^`]+)`|\[([^\]]+)\]\((https?://[^)\s]+)\)")
    for m in pat.finditer(text):
        if m.start() > i:
            out.append({"type": "text", "text": {"content": text[i:m.start()][:limit]}})
        if m.group(1):
            out.append({"type": "text", "text": {"content": m.group(1)[:limit]}, "annotations": {"bold": True}})
        elif m.group(2):
            out.append({"type": "text", "text": {"content": m.group(2)[:limit]}, "annotations": {"code": True}})
        else:
            out.append({"type": "text", "text": {"content": m.group(3)[:limit], "link": {"url": m.group(4)}}})
        i = m.end()
    if i < len(text):
        out.append({"type": "text", "text": {"content": text[i:][:limit]}})
    return out or [{"type": "text", "text": {"content": ""}}]


def _blk(t, text):
    return {"object": "block", "type": t, t: {"rich_text": _rich(text)}}


def _table_block(rows):
    rows = [r for r in rows if not re.match(r"^\s*\|[\s\-\|:]+\|\s*$", r)]
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    if not cells:
        return None
    w = min(max(len(r) for r in cells), 20)
    kids = [{"object": "block", "type": "table_row",
             "table_row": {"cells": [_rich((r[i] if i < len(r) else "")[:1900]) for i in range(w)]}}
            for r in cells[:100]]
    return {"object": "block", "type": "table",
            "table": {"table_width": w, "has_column_header": True, "has_row_header": False, "children": kids}}


def md_to_blocks(md):
    lines, out, i = (md or "").split("\n"), [], 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|"):
            tbl = []
            while i < len(lines) and lines[i].startswith("|"):
                tbl.append(lines[i]); i += 1
            b = _table_block(tbl)
            if b:
                out.append(b)
            continue
        if ln.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            out.append({"object": "block", "type": "code",
                        "code": {"language": "plain text", "rich_text": [{"type": "text", "text": {"content": "\n".join(buf)[:1900]}}]}})
            continue
        if ln.startswith("### "):
            out.append(_blk("heading_3", ln[4:]))
        elif ln.startswith("## "):
            out.append(_blk("heading_2", ln[3:]))
        elif ln.startswith("# "):
            out.append(_blk("heading_1", ln[2:]))
        elif ln.strip() in ("---", "***"):
            out.append({"object": "block", "type": "divider", "divider": {}})
        elif ln.startswith("> "):
            out.append(_blk("quote", ln[2:]))
        elif re.match(r"^\d+\. ", ln):
            out.append(_blk("numbered_list_item", re.sub(r"^\d+\. ", "", ln)))
        elif ln.startswith("- "):
            out.append(_blk("bulleted_list_item", ln[2:]))
        elif ln.strip():
            out.append(_blk("paragraph", ln))
        i += 1
    return out


def _bsize(o):
    return len(json.dumps(o, ensure_ascii=False).encode("utf-8"))


def batches(blocks, max_n=50, max_bytes=400_000):
    out, cur, sz = [], [], 0
    for b in blocks:
        s = _bsize(b)
        if cur and (len(cur) >= max_n or sz + s > max_bytes):
            out.append(cur); cur, sz = [], 0
        cur.append(b); sz += s
    if cur:
        out.append(cur)
    return out


def forbidden(md):
    return [why for pat, why in FORBIDDEN if re.search(pat, md, re.I)]


# ── Notion 읽기·쓰기 (bid_radar 헬퍼 경유 — 토큰을 읽는 곳은 한 군데) ─────────────────
def _B():
    import bid_radar as B  # noqa: WPS433 — 지연 import(selftest는 네트워크 없이 돈다)
    return B


def challenge_pages():
    """레이더의 진행상태=도전 행을 끝까지 읽어 **페이지 전체**(id 포함)를 준다.
    proposal_sweep._live_pages 는 properties만 흘려 자식 페이지를 붙일 parent id가 없다."""
    B = _B()
    url = f"https://api.notion.com/v1/data_sources/{B.BID_NOTION_DS}/query"
    body = {"filter": {"property": "진행상태", "select": {"equals": "도전"}}, "page_size": 100}
    cur = None
    while True:
        if cur:
            body["start_cursor"] = cur
        r = B.notion(url, body)
        for pg in r.get("results", []):
            yield pg
        if not r.get("has_more"):
            break
        cur = r.get("next_cursor")


def radar_row(no):
    B = _B()
    body = {"filter": {"property": "공고번호", "rich_text": {"equals": no}}, "page_size": 1}
    rows = B.notion(f"https://api.notion.com/v1/data_sources/{B.BID_NOTION_DS}/query", body).get("results") or []
    return rows[0] if rows else None


def children(block_id):
    B = _B()
    out, cur = [], None
    while True:
        url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100" + (f"&start_cursor={cur}" if cur else "")
        r = B.notion(url, None)
        out += r.get("results", [])
        if not r.get("has_more"):
            break
        cur = r.get("next_cursor")
    return out


def _plain(rt):
    return "".join(x.get("plain_text", "") for x in (rt or []))


def find_pack(parent_id, title_prefix=PACK_TITLE, kids=None):
    """공고 페이지 밑의 자식 페이지(제목 접두 일치) → (page_id, 판본 도장) | (None, "")."""
    for b in (kids if kids is not None else children(parent_id)):
        if b.get("archived") or b.get("in_trash"):
            continue  # 보관된 옛 팩은 없는 것으로 본다(다시 보관하려 하면 400 — 2026-09-04 실측)
        if b.get("type") == "child_page" and (b["child_page"].get("title") or "").startswith(title_prefix):
            stamp = ""
            for c in children(b["id"])[:3]:
                t = c.get("type")
                s = _plain((c.get(t) or {}).get("rich_text"))
                if s.startswith(STAMP_HEAD):
                    stamp = s[len(STAMP_HEAD):].strip()
                    break
            return b["id"], stamp
    return None, ""


def read_ref_index():
    """위키 「레퍼런스 색인」 → [{"title","rows":[[셀…]],"notes":[줄…]}] (H2 군집 단위).
    표는 table 블록, 재활용 문구는 quote, 보유 자산은 paragraph. 실패하면 []."""
    try:
        blocks = children(REF_INDEX_PAGE)
    except Exception as e:  # noqa: BLE001
        print(f"  [warn] 레퍼런스 색인 읽기 실패: {str(e)[:80]}")
        return []
    secs, cur = [], None
    for b in blocks:
        t = b.get("type")
        if t == "heading_2":
            cur = {"title": _plain(b["heading_2"].get("rich_text")), "rows": [], "notes": []}
            secs.append(cur)
        elif cur is None:
            continue
        elif t == "table":
            try:
                for r in children(b["id"]):
                    if r.get("type") == "table_row":
                        cur["rows"].append([_plain(c) for c in r["table_row"].get("cells", [])])
            except Exception as e:  # noqa: BLE001
                cur["notes"].append(f"{NEED} — 표 읽기 실패({str(e)[:40]})")
        elif t in ("quote", "paragraph", "callout", "bulleted_list_item"):
            s = _plain((b.get(t) or {}).get("rich_text"))
            if s.strip():
                cur["notes"].append(s.strip())
    return secs


def write_pack(parent_id, title, md, old_id=None):
    """자식 페이지 생성(첫 배치 포함) → 나머지 블록 append. 옛 팩은 보관(archived) 처리."""
    B = _B()
    blocks = md_to_blocks(md)
    bs = batches(blocks)
    body = {"parent": {"type": "page_id", "page_id": parent_id},
            "properties": {"title": {"title": [{"type": "text", "text": {"content": title[:200]}}]}},
            "children": bs[0] if bs else []}
    pg = B.notion("https://api.notion.com/v1/pages", body)
    pid = pg.get("id")
    for batch in bs[1:]:
        B.notion_patch(f"https://api.notion.com/v1/blocks/{pid}/children", {"children": batch})
    if old_id:
        try:
            B.notion_patch(f"https://api.notion.com/v1/pages/{old_id}", {"archived": True})
        except Exception as e:  # noqa: BLE001 — 이미 보관된 페이지면 400. 새 팩은 이미 썼으니 경고만
            print(f"  [warn] 옛 팩 보관 처리 실패({str(e)[:60]}) — 새 팩은 정상")
    return pid, pg.get("url", "")


# ── 절 만들기 ───────────────────────────────────────────────────────────────────
def h2(n):
    return f"## {SECTIONS[n]}"


def table(head, rows):
    if not rows:
        return []
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows:
        out.append("| " + " | ".join(str(c or "").replace("|", "／").replace("\n", " ") for c in r) + " |")
    return out


def _quote(q, n=110):
    q = re.sub(r"\s+", " ", q or "").strip()
    return (q[:n] + "…") if len(q) > n else q


def sec0(p, ctx):
    o = [h2(0), ""]
    who = ", ".join(_people(p, "우리담당")) or f"{NEED} — 우리담당 미지정"
    rows = [
        ("공고번호", ctx["no"]), ("공고명", ctx["title"]), ("공고기관", _txt(p, "공고기관")), ("수요기관", _txt(p, "수요기관")),
        ("사업 유형", " · ".join(x for x in (_sel(p, "용역구분"), _sel(p, "계약방법"), _sel(p, "낙찰방법"), _sel(p, "조달분류")) if x)),
        ("추정가격", won(_num(p, "추정가격(원)")) or f"{NEED}"), ("배정예산", won(_num(p, "배정예산(원)")) or "(없음)"),
        ("입찰마감", _txt(p, "입찰마감") or _date(p, "입찰마감일") or f"{NEED}"),
        ("제안서 제출 마감", (_txt(p, "입찰마감") or _date(p, "입찰마감일") or NEED) + " (입찰마감과 같은 것으로 본다 — 공고문에 별도 일시가 있으면 그것이 우선)"),
        ("사업기간·납품기한", ctx["req"].get("schedule") or f"{NEED} — 공고문 확인"),
        ("자격등록마감", _txt(p, "자격등록마감") or "(없음)"),
        ("우리담당", who), ("진행상태", _sel(p, "진행상태")), ("사업등급", _sel(p, "사업등급") or "(미채점)"),
        ("원문 링크", _url(p, "공고URL") or "(없음)"), ("과업지시서", _url(p, "과업지시서") or "(없음)"),
    ]
    o += table(("항목", "값"), rows)
    if not _pv(p, "우리담당").get("people"):
        ctx["gaps"].append("우리담당이 비어 있다 — 레이더에서 담당자를 지정해야 업무요청이 나간다")
    if _num(p, "추정가격(원)") is None:
        ctx["gaps"].append("추정가격이 레이더에 없다 — 공고문에서 확인(방향 1단계 「돈」의 입력)")
    return o


def sec1(rfp, scope, req, ctx):
    o = [h2(1), ""]
    tasks = [(t.get("req") or "", t.get("quote") or "") for t in (rfp.get("tasks") or []) if t.get("req")]
    if tasks:
        o.append(f"RFP 읽기 캐시에서 {len(tasks)}건. 요약하지 않은 원문 근거를 옆에 둔다.")
        o += table(("#", "과업(발주처가 시키는 일)", "원문 근거"), [(i + 1, r, _quote(q)) for i, (r, q) in enumerate(tasks)])
    elif scope.get("scope"):
        o.append(f"담당자가 올린 제안요청서에서 뽑은 과업 범위 {len(scope['scope'])}건(출처 문서: {scope.get('src') or '(미상)'}).")
        o += [f"- {s}" for s in scope["scope"]]
        ctx["gaps"].append("RFP 읽기 캐시에 과업 항목이 없다 — 과업 범위(bid_doc_ingest)로 대신함. 배점 대응 전에 원문 대조")
    else:
        o.append(f"{NEED} — 과업 추출이 없다. 제안요청서를 담당자 스레드에 올리면 서버가 읽는다.")
        ctx["gaps"].append("과업 요구(§1)가 비어 있다 — 제안요청서 미수집 또는 읽기 실패")
    dropped = rfp.get("_dropped_proc") or []
    if dropped:
        o += ["", f"절차 조항이라 과업에서 뺀 것 {len(dropped)}건(참고): " + " · ".join(_quote(d.get("req") or "", 40) for d in dropped[:8])]
    if req.get("deliverables"):
        o += ["", "**제출물·산출물(자격 캐시)**"] + [f"- {d}" for d in req["deliverables"][:20]]
    return o


def _pct(s):
    """배점 문자열 → 숫자. "90%"·"20점"·"20" 모두 읽는다. 문장이면(숫자 뒤에 글자가 더 있으면) None."""
    t = (s or "").strip()
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(%|점)?", t)
    return float(m.group(1)) if m else None


def tech_price_from_body(body):
    """원문에서 기술:가격 비율과 협상적격 기준을 찾는다 → (tech, price, 적격%). 없으면 None."""
    b = body or ""
    tech = price = cut = None
    # 숫자가 앞에 오는 표현("90%의 기술평가")을 먼저, 뒤에 오는 표현("기술평가점수(90점)")을 다음에.
    # "기술평가와 10%의 가격평가"처럼 뒤 항목 숫자를 잡는 실수를 막는다(실측 R26EX00000001: 10:10 오판).
    for pat in (r"(\d{2,3})\s*%\s*의\s*기술", r"기술(?:능력)?\s*평가\s*점수\s*\(?\s*(\d{2,3})\s*점", r"기술(?:능력)?\s*평가\s*\(?\s*(\d{2,3})\s*(?:%|점)"):
        m = re.search(pat, b)
        if m:
            tech = float(m.group(1)); break
    for pat in (r"(\d{1,3})\s*%\s*의\s*가격", r"가격\s*평가\s*점수\s*\(?\s*(\d{1,3})\s*점", r"가격\s*평가\s*\(?\s*(\d{1,3})\s*(?:%|점)"):
        m = re.search(pat, b)
        if m:
            price = float(m.group(1)); break
    m = re.search(r"배점한도의\s*(\d{2,3})\s*%", b)
    if m:
        cut = float(m.group(1))
    return tech, price, cut


SCORE_WORDS = ("평점", "배점", "평가기준", "평가 기준", "평가항목", "평 가 항 목")


def score_tables_from_body(body, limit=8):
    """원문 마크다운 표 중 배점·평점·평가기준이 든 표만 그대로 뽑는다(한준 2026-09-04 "정량 세부표는 RFP에 있다")."""
    out, cur = [], []
    for ln in (body or "").splitlines() + [""]:
        if ln.lstrip().startswith("|"):
            cur.append(ln.strip())
            continue
        if cur:
            head = " ".join(cur[:3])
            if any(w in head for w in SCORE_WORDS) and len(cur) >= 3:
                out.append(cur)
            cur = []
        if len(out) >= limit:
            break
    return out


def sec2(rfp, req, ctx):
    o = [h2(2), ""]
    body = rfp.get("_body") or ""
    items = rfp.get("eval_items") or []
    if not items and req.get("evaluation"):
        items = [{"item": e.get("item"), "points": e.get("points"), "factor": "", "quote": e.get("quote")} for e in req["evaluation"]]
        o.append("RFP 읽기 캐시에 배점표가 없어 자격 캐시(go/no-go 추출)의 평가 항목을 썼다.")
    if not items:
        o.append(f"{NEED} — 평가배점표 추출이 없다.")
        ctx["gaps"].append("평가배점표(§2)가 비어 있다 — P1 검산 불가. 제안요청서 배점표를 사람이 옮겨야 한다")
        return o
    rows, price, total_top, total_all = [], None, 0.0, 0.0
    tech = None
    for e in items:
        pts = e.get("points") or ""
        q = e.get("quote") or ""
        v = _pct(pts)
        name = e.get("item") or ""
        sub = bool(re.search(r"배점\s*한도|세부|소항목", q)) and "가격" not in name
        if "가격" in name and v is not None:
            price = v
        m = re.search(r"기술(?:능력)?\s*평가\s*(\d+(?:\.\d+)?)\s*(?:%|점)", q)
        if m and tech is None:
            tech = float(m.group(1))
        if v is not None:
            total_all += v
            if not sub:
                total_top += v
        rows.append((name, pts, e.get("factor") or "", _quote(q), "세부" if sub else ""))
    o += table(("평가항목", "배점", "세부기준", "근거", "구분"), rows)
    o.append("")
    bt, bp, cut = tech_price_from_body(body)
    if tech is None and bt is not None:
        tech = bt
    if price is None and bp is not None:
        price = bp
    if tech is None and price is not None and abs(total_top - 100) < 0.01:
        tech = 100 - price
    if tech is not None and price is not None:
        o.append(f"기술 : 가격 = **{tech:g} : {price:g}** (원문 기준)")
    else:
        o.append(f"기술:가격 비율 — {NEED} (원문에서 자동으로 못 읽음)")
    if cut is not None and tech is not None:
        o.append(f"협상적격 기준: 기술 배점한도의 {cut:g}% 이상 = **{tech * cut / 100:g}점** (원문 「배점한도의 {cut:g}%」)")
    o.append(f"배점 합계(자동 합산, 참고): 상위 항목 {total_top:g} · 세부 포함 {total_all:g}. "
             "「세부」 표시는 원문에 배점한도·소항목 표현이 있는 것(기계 판정). 정성·정량 구분은 P1에서 사람이 한다.")
    tech_only = tech is not None and price is not None and abs(total_top - tech) < 0.01
    if total_top and not tech_only and abs(total_top - 100) > 0.01 and total_top < 200:
        ctx["gaps"].append(f"상위 배점 합계가 {total_top:g}(100 아님) — 항목 누락 또는 상위·세부 중복. P1에서 원문 대조")
    tables = score_tables_from_body(body)
    if tables:
        o += ["", f"**정량·정성 세부 배점표 — 원문 표 {len(tables)}개 그대로(신용등급 평점·실적 건수 단계·세부 항목 배점). P2 실점 계산은 이 표로 한다.**"]
        for t in tables:
            o += [""] + t
    elif body:
        ctx["gaps"].append("원문에서 배점·평점 표를 찾지 못했다 — 정량 세부 기준(신용등급·실적 건수)은 제안요청서를 직접 본다")
    return o


def sec3(rfp, scope, req, ctx):
    o = [h2(3), ""]
    toc2 = rfp.get("toc2") or []
    toc = rfp.get("toc") or scope.get("outline") or []
    if toc2:
        o.append("**발주처 지정 목차(대·세)**")
        for d in toc2:
            o.append(f"- {d.get('대') or ''}")
            for s in (d.get("세") or [])[:12]:
                how = (s.get("작성방법") or "").strip()
                o.append(f"   - {s.get('제목') or ''}" + (f" — {_quote(how, 80)}" if how else ""))
    elif toc:
        o.append("**발주처 지정 목차**")
        o += [f"{i + 1}. {t}" for i, t in enumerate(toc)]
    else:
        o.append(f"지정 목차 없음 또는 미추출 — {NEED}. 없으면 정성평가 항목 1개 = 챕터 1개로 간다(SKILL P4).")
    lim = rfp.get("limits") or {}
    o += ["", "**분량·형식 제한**"]
    o += table(("항목", "값"), [
        ("쪽수", lim.get("pages") or "(명시 없음)"), ("글꼴", lim.get("font") or "(명시 없음)"),
        ("여백", lim.get("margin") or "(명시 없음)"), ("제출 형식", lim.get("format") or "(명시 없음)"),
    ])
    wr = rfp.get("writing_rules") or {}
    rules = list(scope.get("writing_rules") or [])
    if wr.get("forbidden"):
        rules += [f"금지: {x}" for x in wr["forbidden"]]
    if wr.get("abbr_explain"):
        rules.append("약어는 처음 나올 때 풀어 쓴다(발주처 요구)")
    if wr.get("anonymize"):
        rules.append("업체명·로고를 노출하지 않는 익명 제안서(발주처 요구)")
    if rules:
        o += ["", "**작성 요령(발주처)**"] + [f"- {r}" for r in rules[:20]]
    if scope.get("deliverables") or scope.get("quantities"):
        o += ["", "**부속·제출 서류(제안요청서)**"] + [f"- {d}" for d in (scope.get("deliverables") or [])[:15]]
        o += [f"- 수량·규격: {q}" for q in (scope.get("quantities") or [])[:10]]
    if not (toc2 or toc):
        ctx["gaps"].append("발주처 지정 목차(§3)를 못 읽었다 — 제안요청서 「제안서 작성 요령」 확인")
    return o


def sec4(p, req, certs, quals, facts, ctx):
    o = [h2(4), ""]
    codes = _multi(p, "요구업종코드")
    have = set(quals.get("industry") or []) | set(quals.get("product") or [])
    if codes:
        rows = [(c, "보유" if c in have else f"미보유 {NEED}") for c in codes]
        o += ["**요구 업종코드 ↔ 우리 등록**"] + table(("업종코드", "우리"), rows) + [""]
        for c in codes:
            if c not in have:
                ctx["gaps"].append(f"요구 업종코드 {c} 미등록 — 자격등록마감 전 등록 가능 여부 확인(회복가능 실점 후보)")
    rgn = [r for r in _multi(p, "참가제한지역") if r not in ("제한없음", "전국", "없음")]
    if rgn:
        hq = facts.get("본점", "")
        ok = any(r[:2] in hq for r in rgn)
        o.append(f"**참가제한지역**: {', '.join(rgn)} — 본점({hq or '미상'}) 기준 {'해당' if ok else '⚠️ 비해당 가능'}")
        if not ok:
            ctx["gaps"].append(f"참가제한지역 {', '.join(rgn)} — 본점·지점 소재지로 충족되는지 확인")
        o.append("")
    quals_txt = [(q.get("req") or "", q.get("quote") or "") for q in (req.get("qualifications") or [])]
    if quals_txt:
        o += ["**참가자격 조건(RFP·공고문)**"] + table(("조건", "원문 근거"), [(r, _quote(q)) for r, q in quals_txt]) + [""]
    mand = [(m.get("req") or "", m.get("quote") or "") for m in (req.get("mandatory") or [])]
    if mand:
        o += ["**필수·무효 조건**"] + table(("조건", "원문 근거"), [(r, _quote(q)) for r, q in mand[:15]]) + [""]
    docs = [d for d in (req.get("deliverables") or []) if any(w in d for w in DOC_WORDS)]
    if docs:
        rows = []
        for d in docs:
            hit = best_cert(d, certs)
            if hit:
                st = prop_str(hit, "상태") or "상태 미기재"
                rows.append((d, f"보유 — {prop_str(hit, '명칭')} ({st}{', 만료 ' + prop_str(hit, '만료일') if prop_str(hit, '만료일') else ''})"))
                if st == "만료" and not any(w in prop_str(hit, "명칭") for w in ONDEMAND_DOCS):
                    ctx["gaps"].append(f"서류 「{prop_str(hit, '명칭')}」 상태 만료 — 재발급 필요")
            else:
                rows.append((d, f"{NEED} — 인증 DB에 대응 항목 없음(온디맨드 발급 서류일 수 있음)"))
        o += ["**제출 서류 ↔ 우리 보유(인증 DB 대조)**"] + table(("서류", "우리"), rows)
    if not (codes or quals_txt or mand):
        o.append(f"{NEED} — 참가자격 추출이 없다.")
        ctx["gaps"].append("참가자격(§4)이 비어 있다 — 공고문 참가자격 조항 확인")
    return o


def best_cert(doc, certs):
    """서류 이름과 가장 닮은 인증 행(2-gram 유사도 ≥ 0.25)."""
    best, bs = None, 0.0
    for c in certs:
        s = sim(doc, prop_str(c, "명칭"))
        if s > bs:
            best, bs = c, s
    return best if bs >= 0.25 else None


FACT_KEYS = ("회사명", "대표자", "설립일", "사업자등록번호", "법인등록번호", "본점", "서울 연구소(지점)", "업태·종목",
             "직원 수", "자본금", "홈페이지", "대표전화", "대표 이메일", "입찰참가제한·부정당·영업정지 이력", "회사 소개")


def facts_map(rows):
    m = {}
    for r in rows:
        k, v = prop_str(r, "항목"), prop_str(r, "값")
        if k:
            m[k] = v
            m[k + "|비고"] = prop_str(r, "비고")
    return m


def sec5(strong, weak, facts, certs, projects, refidx, ctx, today):
    keys = strong + weak
    o = [h2(5), ""]
    o.append(f"회사 팩트·인증·실적은 위키 정본(덤프 {ctx['dump_at'] or '시각 미상'} 기준)에서, 실적 군집·인력·공백은 [레퍼런스 색인]({REF_INDEX_URL})에서 골랐다.")
    o.append("")
    # 5-① 회사 팩트
    rows = []
    for k in FACT_KEYS:
        v = facts.get(k, "")
        if not v:
            ctx["gaps"].append(f"회사 팩트 「{k}」 미기입 — 회사 팩트 DB 보강")
            v = f"{NEED}"
        note = facts.get(k + "|비고", "")
        rows.append((k, _quote(v, 160), _quote(note, 60)))
    o += ["### 5-① 회사 팩트(정본 그대로)"] + table(("항목", "값", "비고·갱신"), rows) + [""]
    # 5-② 인증·자격
    crow = []
    for c in certs:
        kind = prop_str(c, "구분")
        name = prop_str(c, "명칭")
        if not name or name[:1] in ("🔁", "🗑"):
            continue
        rel = overlap(keys, name) if kind in ("특허", "출원") else ["인증"]
        if not rel:
            continue
        exp = prop_str(c, "만료일") or prop_str(c, "유효기간")
        st = prop_str(c, "상태")
        flag = ""
        if exp:
            try:
                d = dt.date.fromisoformat(exp[:10])
                if d < today:
                    flag = "⚠️ 만료"
                elif (d - today).days <= 90:
                    flag = f"⚠️ 만료 임박(D-{(d - today).days})"
            except ValueError:
                pass
        if st == "만료" and not flag:
            flag = "⚠️ 만료"
        # 온디맨드 서류(입찰참가자격등록증·납세증명 등)는 제출 때마다 새로 발급받아 쓴다 — 위키의 만료 표시는 "그날 발급본"의 날짜일 뿐이다.
        # 한준 2026-09-04: "입찰참가등록증 만료 안 됐다, 매일 갱신해서 쓰고 있다". 만료 경고를 내지 않고 표시만 바꾼다.
        if any(w in name for w in ONDEMAND_DOCS):
            flag = "재발급 서류(제출 시 발급)" if flag else flag
        elif flag and kind not in ("특허", "출원"):
            ctx["gaps"].append(f"인증 「{name}」 {flag} — 갱신 필요(만료일 {exp or '미상'})")
        crow.append((name, kind, prop_str(c, "기관"), st or "", exp or "", flag))
    crow.sort(key=lambda r: (r[1] != "인증", r[0]))
    o += [f"### 5-② 인증·자격·특허 (인증 전부 + 이 공고 열쇳말과 닿는 특허) — {len(crow)}건"]
    o += table(("명칭", "구분", "기관", "상태", "만료일", "표시"), crow[:40]) + [""]
    # 5-③ 실적 — 프로젝트 DB에서 낱말이 겹치는 것
    scored = []
    for pr in projects:
        if prop_str(pr, "대외인용금지") == "예":
            continue
        org = prop_str(pr, "발주기관")
        if "자체" in org or "사내" in org:
            continue
        text = " ".join(prop_str(pr, k) for k in ("프로젝트명", "개요", "도메인", "관련 프로덕트", "수행역할"))
        sc, hit = match_score(strong, weak, text)
        if sc:
            scored.append((sc, pr, hit))
    scored.sort(key=lambda x: -x[0])
    prow = []
    for n, pr, hit in scored[:10]:
        amt = prop_str(pr, "사업비")
        prow.append((prop_str(pr, "프로젝트명"), prop_str(pr, "발주기관"), won(amt) if amt else "", _quote(prop_str(pr, "개요"), 60),
                     prop_str(pr, "수행역할"), ", ".join(hit[:4])))
    o += [f"### 5-③ 유사 실적 후보 (프로젝트 DB · 강한 열쇳말이 겹치는 것 · 대외인용금지 제외) — {len(prow)}건"]
    if prow:
        o += table(("프로젝트", "발주기관", "사업비", "개요", "역할", "겹친 낱말"), prow)
        o.append("겹친 낱말은 기계 판정이다. 「왜 유사한가」는 P3에서 사람이 논증한다(금액만 있고 유사성 논증이 없으면 감점).")
    else:
        o.append(f"{NEED} — 열쇳말이 겹치는 실적이 없다. 레퍼런스 색인 군집을 직접 본다.")
        ctx["gaps"].append("프로젝트 DB에서 열쇳말이 겹치는 실적 0건 — 레퍼런스 공백 가능. P3에서 대체 근거(R&D·특허·인력) 탐색")
    o.append("")
    # 5-④ 레퍼런스 색인 군집
    if refidx:
        ranked = []
        for s in refidx:
            t = s["title"]
            if not re.match(r"^[A-H]\.", t):
                continue
            text = t + " " + " ".join(" ".join(r) for r in s["rows"]) + " " + " ".join(s["notes"])
            ranked.append((match_score(strong, weak, text)[0], s))
        ranked.sort(key=lambda x: -x[0])
        picked = [s for n, s in ranked if n > 0][:3] or [s for n, s in ranked[:2]]
        o.append(f"### 5-④ 레퍼런스 색인 군집 (열쇳말 겹침 상위 {len(picked)}개 — 나머지 군집은 색인 원본)")
        for s in picked:
            o.append(f"**{s['title']}**")
            if s["rows"]:
                o += table(tuple(s["rows"][0]), s["rows"][1:])
            for n in s["notes"]:
                o.append(f"> {n}")
            o.append("")
        people = next((s for s in refidx if s["title"].startswith("I.")), None)
        if people and people["rows"]:
            o.append("### 5-⑤ 인력 카드 (색인 §I — 기준 문서·기준일은 색인의 §I 머리 인용문 참조)")
            o += table(tuple(people["rows"][0]), people["rows"][1:]) + [""]
            flagged = [r[0] for r in people["rows"][1:] if any("⚠️" in c for c in r)]
            if flagged:
                ctx["gaps"].append(f"인력 카드(색인 §I)에 ⚠️ 표시 인원 {len(flagged)}명({', '.join(flagged[:6])}) — 담당·이력·4대보험 확인 전에는 투입인력표에 넣지 않는다")
            ctx["gaps"].append("투입인력표는 입찰공고일 기준 재직 + 4대보험 가입 증빙이 조건 — 색인 §I의 취득일 열과 최신 가입자 명부로 확인")
        ctx["ref_gaps"] = next((s for s in refidx if s["title"].startswith("J.")), None)
    else:
        o.append(f"### 5-④ 레퍼런스 색인 — {NEED} (읽기 실패 또는 미접근). 스킬이 [색인 페이지]({REF_INDEX_URL})를 직접 읽는다.")
        ctx["gaps"].append("레퍼런스 색인을 서버가 읽지 못했다 — P3에서 Notion MCP로 직접 읽기")
    return o


def brief_sections(gonogo, heads):
    """GoNoGo 브리핑(`■ 제목`으로 나뉜 텍스트)에서 heads 절만 (bid_grade._brief_sections 와 같은 규약)."""
    if not gonogo:
        return ""
    blocks, cur = [], []
    for ln in gonogo.splitlines():
        if ln.startswith("■ "):
            if cur:
                blocks.append(cur)
            cur = [ln]
        elif cur:
            cur.append(ln)
    if cur:
        blocks.append(cur)
    out = []
    for blk in blocks:
        if any(blk[0].strip().startswith(h) for h in heads):
            body = "\n".join(x for x in blk if x.strip() and not x.strip().startswith("_추출"))
            if body.strip():
                out.append(body.strip())
    return "\n".join(out)


SIGNAL_HEADS = ("■ 가점", "■ 정량점수", "■ 내정 정황", "■ 수익률(추정)")
BLOCK_HEADS = ("■ 걸리는 것", "■ 되는 것", "■ 사업 조건")


def sec6(p, ctx, market_lines, learn_lines):
    o = [h2(6), ""]
    o.append("숫자만, 해석 없이. 판단용이다 — 제안서 본문에 그대로 옮기지 않는다(guardrails §2).")
    o.append("")
    rows = [
        ("go/no-go 판정", (_sel(p, "판정") or "(미판정)") + (" · 확정" if _check(p, "판정확정") else "")),
        ("판정메모", _quote(_txt(p, "판정메모"), 200) or "(없음)"),
        ("사업등급", _sel(p, "사업등급") or "(미채점)"),
        ("규모대비", _txt(p, "규모대비") or _formula(p, "규모대비") or "(없음)"),
        ("참가업체수(공고 기준)", str(_num(p, "참가업체수") or "") or "(없음)"),
        ("투찰권장", _txt(p, "투찰권장") or "(없음)"),
        ("기관이력", _quote(_txt(p, "기관이력"), 200) or "(없음)"),
    ]
    o += table(("지표", "값"), rows) + [""]
    why = _txt(p, "등급근거")
    if why:
        o += ["**등급근거(채점 v7 축)**"] + [f"> {ln}" for ln in why.splitlines() if ln.strip()][:12] + [""]
    gonogo = _txt(p, "GoNoGo")
    sig = brief_sections(gonogo, SIGNAL_HEADS)
    if sig:
        o += ["**go/no-go 4신호(가점·정량점수·내정 정황·수익률)**", "```", sig[:3500], "```", ""]
    blk = brief_sections(gonogo, BLOCK_HEADS)
    if blk:
        o += ["**걸리는 것·되는 것·사업 조건(go/no-go 추출)**", "```", blk[:3500], "```", ""]
    if not gonogo:
        ctx["gaps"].append("GoNoGo 브리핑이 비어 있다 — 가점·정량점수 신호 없음(P2 실점 계산에 원문 대조 필요)")
    if market_lines:
        o += ["**시장·낙찰가 참고(개찰 DB, 부가세 제외 환산)**"] + [f"- {ln}" for ln in market_lines[:14]] + [""]
    else:
        o += [f"시장·낙찰가 참고 — {NEED}(개찰 DB 조회 실패 또는 표본 없음)", ""]
    if learn_lines:
        o += ["**최근 90일 시장 신호(학습 DB)**"] + [f"- {ln}" for ln in learn_lines[:8]] + [""]
    return o


def sec7(keys, title, org, archive, ctx):
    o = [h2(7), ""]
    scored = []
    for r in archive:
        nm = prop_str(r, "공고명")
        s = sim(title, nm)
        same_org = bool(org) and (org in (prop_str(r, "수요기관") + prop_str(r, "공고기관")))
        hit = overlap(keys, nm)
        score = s + (0.25 if same_org else 0) + 0.05 * len(hit)
        if score >= 0.2:
            scored.append((score, r, same_org))
    scored.sort(key=lambda x: -x[0])
    rows = []
    for score, r, same_org in scored[:7]:
        lesson = prop_str(r, "교훈") or prop_str(r, "낙선·포기 사유")
        rows.append((prop_str(r, "공고번호"), _quote(prop_str(r, "공고명"), 50), prop_str(r, "수요기관") or prop_str(r, "공고기관"),
                     prop_str(r, "결과") or prop_str(r, "진행상태"), prop_str(r, "우리 순위"), prop_str(r, "낙찰률(%)"),
                     _quote(lesson, 90), f"{score:.2f}" + (" 같은기관" if same_org else "")))
    if rows:
        o.append(f"입찰결과 아카이브에서 공고명 유사도·같은 기관·열쇳말로 고른 {len(rows)}건(아카이브 총 {len(archive)}건).")
        o += table(("공고번호", "공고명", "기관", "결과", "우리 순위", "낙찰률", "배운 것", "유사도"), rows)
    else:
        o.append(f"유사 과거 입찰 없음(아카이브 {len(archive)}건 중 유사도 0.2 이상 0건) — {NEED}")
        ctx["gaps"].append("유사 과거 입찰 0건 — 이 유형은 처음이다. 시장·낙찰가 참고(§6)로 대신 판단")
    return o


def sec8(ctx):
    o = [h2(8), "", "스킬이 그대로 `⚠️ 확인필요` 목록으로 옮긴다. 5·6에서 드러난 부족과 회사 상수 공백."]
    seen, n = set(), 0
    for g in ctx["gaps"]:
        if g in seen:
            continue
        seen.add(g); n += 1
        o.append(f"{n}. {g}")
    rg = ctx.get("ref_gaps")
    if rg and rg["rows"]:
        o += ["", "**회사 공통 레퍼런스 공백(색인 §J — 모든 공고에 해당하는 상수, P3에서 반드시 함께 보고)**"]
        o += table(tuple(rg["rows"][0]), rg["rows"][1:])
    if n == 0:
        o.append("(자동으로 찾은 빈칸 없음 — 그래도 P1·P2에서 원문 대조는 한다)")
    return o


def forms_from_body(body):
    """원문에서 별지·서식 줄만 (LLM 없이). 최대 15개."""
    out, seen = [], set()
    for ln in (body or "").splitlines():
        s = re.sub(r"\s+", " ", ln).strip()
        if re.search(r"별지\s*제?\s*\d+\s*호|\[?서식\s*\d*\]?|별첨\s*\d+", s) and 4 <= len(s) <= 120 and s not in seen:
            seen.add(s); out.append(s)
        if len(out) >= 15:
            break
    return out


def sec9(p, rfp, scope, rfp_key, note, ctx, now):
    o = [h2(9), ""]
    srcs = rfp.get("_src") or []
    o.append(f"- RFP 원문(서버가 읽은 파일): {', '.join(srcs) if srcs else '(없음)'}")
    o.append(f"- 제안요청서 판본 도장: `{ctx['stamp']}`" + (f" — {note}" if note else ""))
    if rfp.get("_body"):
        o.append(f"- **RFP 원문(추출 마크다운, {len(rfp['_body']):,}자)**: 이 공고 페이지의 자식 페이지 「{RFP_TITLE} — {ctx['no']}」 (서버가 함께 쓴다. hwp를 열 필요 없이 이것으로 P1 검산·P4 인용)")
    else:
        o.append(f"- RFP 원문(추출) — {NEED}: 읽기 캐시에 본문이 없다. 첨부문서 링크의 hwp를 직접 본다")
    if scope.get("src"):
        o.append(f"- 담당자 스레드에서 올린 문서: {scope.get('src')} ({scope.get('at') or ''})")
    for name, url in _links(p, "첨부문서")[:10]:
        o.append(f"- 첨부문서: [{name}]({url})")
    if _url(p, "공고URL"):
        o.append(f"- 공고 원문: {_url(p, '공고URL')}")
    if _url(p, "과업지시서"):
        o.append(f"- 과업지시서: {_url(p, '과업지시서')}")
    forms = forms_from_body(rfp.get("_body"))
    if forms:
        o += ["", "**서식·별지 언급(원문 줄 그대로, 기계 추출)**"] + [f"- {f}" for f in forms]
    else:
        o += ["", f"서식·별지 — 원문에서 자동으로 못 찾음({NEED}). 제안요청서 뒤쪽 별지 목록 확인"]
    o += ["", f"- 레퍼런스 색인(정본): {REF_INDEX_URL}",
          f"- 위키 덤프 기준 시각: {ctx['dump_at'] or '미상'}",
          f"- 재료 팩 생성: {now.strftime('%Y-%m-%d %H:%M')} · proposal_material {VERSION} · LLM 호출 0회"]
    return o


# ── 조립 ────────────────────────────────────────────────────────────────────────
def keywords_of(title, rfp, req):
    """(강한 열쇳말, 약한 열쇳말). 강한 것 = RFP 읽기의 keywords + 공고명 낱말. 약한 것 = 과업·산출물 낱말.
    실적·군집 선택은 강한 열쇳말이 하나는 겹쳐야 한다 — 「기획·관리·데이터」 같은 낱말만으로 고르면 사내 문서까지 걸린다(실측)."""
    strong, weak = [], []
    for k in list(rfp.get("keywords") or []) + words(title):
        strong += words(k) if " " in k else [k]
    for t in (rfp.get("tasks") or [])[:12]:
        weak += words(t.get("req") or "")[:4]
    for d in (req.get("deliverables") or [])[:6]:
        weak += words(d)[:2]

    def uniq(xs, skip=()):
        seen, out = set(skip), []
        for k in xs:
            k = k.strip()
            if len(k) >= 2 and k not in seen and k not in STOP:
                seen.add(k); out.append(k)
        return out
    strong = uniq(strong)
    return strong[:25], uniq(weak, skip=strong)[:25]


def match_score(strong, weak, text):
    """(점수, 겹친 낱말). 강한 열쇳말 1개 = 2점, 약한 것 1개 = 1점. 강한 것이 하나도 없으면 0."""
    hs, hw = overlap(strong, text), overlap(weak, text)
    if not hs:
        return 0, []
    return 2 * len(hs) + len(hw), hs + hw


def market_for(title, org, presmt, mthd, div_text):
    """bid_market(개찰 DB)·bid_learn(시장 신호) 줄 — 실패하면 빈 목록과 [warn]."""
    m_lines, l_lines = [], []
    try:
        import bid_bidprc as PR
        import bid_market as MK
        con = PR.bidprc_db()
        all_nt = MK.notices(con)
        idf = MK.idf_of([v["nm"] for v in all_nt.values()])
        a = MK.analyse(con, title, org, presmt=presmt, mthd=mthd, idf=idf, all_nt=all_nt)
        m_lines = [str(x) for x in MK.lines(a)]
    except Exception as e:  # noqa: BLE001
        print(f"  [warn] 개찰 DB 분석 실패: {str(e)[:80]}")
    try:
        import bid_learn as L
        l_lines = [str(x) for x in L.market_lines(L.div_of(div_text), org)]
    except Exception as e:  # noqa: BLE001
        print(f"  [warn] 학습 DB 신호 실패: {str(e)[:80]}")
    return m_lines, l_lines


def build_rfp_doc(no, title, rfp, stamp):
    """RFP 원문(추출) 자식 페이지 본문. 첫 문단은 판본 도장. 서버 경로·파일명 외 내부 정보는 넣지 않는다."""
    body = rfp.get("_body") or ""
    head = [f"# {RFP_TITLE} — {no}", "", f"{STAMP_HEAD}{stamp}",
            f"공고 「{title}」의 제안요청서·공고문을 서버가 읽어 마크다운으로 바꾼 것. 읽은 파일: {', '.join(rfp.get('_src') or []) or '(미상)'}. "
            "표·번호는 원문 구조를 따르되 hwp 서식은 사라졌다 — 배점·자격·산출물 수치는 이 본문을 근거로 인용한다.", "", "---", ""]
    return "\n".join(head) + body.strip() + "\n"


def build_pack(page, sources, today=None, now=None, use_market=True):
    """레이더 페이지 1건 + 재료 → (마크다운, 판본 도장). sources 는 selftest 가 주입한다."""
    today = today or dt.date.today()
    now = now or dt.datetime.now()
    p = page.get("properties") or {}
    no = _txt(p, "공고번호")
    title = _txt(p, "공고명")
    org = _txt(p, "수요기관") or _txt(p, "공고기관")
    scope = (sources["scope"] or {}).get(no) or {}
    stamp_in = ingest_stamp(scope)
    rfp_key, rfp, note = pick_rfp(sources["rfp"] or {}, no, stamp_in)
    req = (sources["req"] or {}).get(no) or {}
    ctx = {"no": no, "title": title, "gaps": [], "req": req, "dump_at": sources.get("dump_at", ""),
           "stamp": (f"{rfp_key}#{VERSION}" if rfp_key else f"{no}#{stamp_in}#norfp#{VERSION}")}
    if note:
        ctx["gaps"].append(f"RFP 읽기 캐시 {note} — 최신 제안요청서로 다시 읽혔는지 확인")
    if not rfp:
        ctx["gaps"].append("RFP 읽기 캐시가 없다 — §1·§2·§3이 비어 있다. 제안요청서 수집 후 서버 읽기 재실행")
    facts = facts_map(sources["facts"])
    strong, weak = keywords_of(title, rfp, req)
    m_lines, l_lines = ([], [])
    if use_market:
        m_lines, l_lines = market_for(title, org, _num(p, "추정가격(원)"), _sel(p, "낙찰방법"), _sel(p, "용역구분"))
    md = [f"# {PACK_TITLE} — {no}", "",
          f"{STAMP_HEAD}{ctx['stamp']}",
          f"공고 「{title}」의 제안 재료. **정량 지표와 회사 자료만** 담았다 — 전략·컨셉·서술은 `vax-proposal` 스킬(사람+Claude)이 쓴다. "
          f"열쇳말(기계 추출 · 강한 것): {', '.join(strong[:15]) or '(없음)'}", ""]
    md += sec0(p, ctx) + [""]
    md += sec1(rfp, scope, req, ctx) + [""]
    md += sec2(rfp, req, ctx) + [""]
    md += sec3(rfp, scope, req, ctx) + [""]
    md += sec4(p, req, sources["certs"], sources["quals"], facts, ctx) + [""]
    md += sec5(strong, weak, facts, sources["certs"], sources["projects"], sources["refidx"], ctx, today) + [""]
    md += sec6(p, ctx, m_lines, l_lines) + [""]
    md += sec7(strong, title, org, sources["archive"], ctx) + [""]
    md += sec8(ctx) + [""]
    md += sec9(p, rfp, scope, rfp_key, note, ctx, now)
    return "\n".join(md) + "\n", ctx["stamp"]


def load_sources(read_ref=True):
    return {
        "rfp": _load(READ_CACHE), "scope": _load(SCOPE_CACHE), "req": _load(REQ_CACHE),
        "quals": _load(QUALS_PATH), "facts": dump_rows("facts"), "certs": dump_rows("certs"),
        "projects": dump_rows("projects"), "archive": dump_rows("archive"), "dump_at": dump_time(),
        "refidx": read_ref_index() if read_ref else [],
    }


def check_sections(md):
    """계약 H2 열 개가 순서대로 다 있나 → 빠진 것 목록."""
    return [s for s in SECTIONS if f"## {s}" not in md]


def run_one(page, sources, commit, out_dir, force, today=None):
    p = page.get("properties") or {}
    no = _txt(p, "공고번호")
    print(f"== {no} · {_txt(p, '공고명')[:40]} ==")
    md, stamp = build_pack(page, sources, today=today)
    bad = forbidden(md)
    if bad:
        print(f"  ⛔ 공개 금지 정보가 있어 쓰지 않는다: {' · '.join(bad)}")
        return "blocked"
    missing = check_sections(md)
    if missing:
        print(f"  ⛔ 계약 절 누락: {missing}")
        return "blocked"
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"{no}_재료팩.md")
        tmp = f"{path}.tmp{os.getpid()}"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(md)
        os.replace(tmp, path)
        print(f"  📄 저장: {path}")
    if not commit:
        print(f"  [dry] 위키에 쓰지 않음 — {len(md)}자 · 블록 {len(md_to_blocks(md))}개 · 도장 {stamp}")
        if not out_dir:
            sys.stdout.write(md)
        return "dry"
    kids = children(page["id"])
    old_id, old_stamp = find_pack(page["id"], PACK_TITLE, kids)
    rfp_id, rfp_stamp = find_pack(page["id"], RFP_TITLE, kids)
    rfp = pick_rfp(sources["rfp"] or {}, no, ingest_stamp((sources["scope"] or {}).get(no) or {}))[1]
    need_rfp = bool(rfp.get("_body")) and (force or rfp_stamp != stamp)
    if old_id and old_stamp == stamp and not force and not need_rfp:
        print(f"  [skip] 같은 판본의 재료 팩이 이미 있다({stamp}) — --force 로 다시 쓴다")
        return "skip"
    if not (old_id and old_stamp == stamp and not force):
        title = f"{PACK_TITLE} — {no}"
        pid, url = write_pack(page["id"], title, md, old_id=old_id)
        print(f"  ✅ 위키에 썼다: {url or pid}" + (f" (옛 팩 보관 처리: {old_id})" if old_id else ""))
    if need_rfp:
        rmd = build_rfp_doc(no, _txt(p, "공고명"), rfp, stamp)
        bad = forbidden(rmd)
        if bad:
            print(f"  ⛔ RFP 원문에 공개 금지 정보: {' · '.join(bad)} — 원문 페이지는 쓰지 않음")
        else:
            rid, rurl = write_pack(page["id"], f"{RFP_TITLE} — {no}", rmd, old_id=rfp_id)
            print(f"  📄 RFP 원문 페이지: {rurl or rid} ({len(rfp['_body']):,}자)" + (f" (옛 원문 보관: {rfp_id})" if rfp_id else ""))
    return "written"


# ── selftest — 네트워크·LLM·라이브 폴더 없이 ────────────────────────────────────
def _fake_page(no="R26BK0001", state="도전", who=True, due="2099-01-01"):
    def rt(s):
        return {"type": "rich_text", "rich_text": [{"type": "text", "plain_text": s, "text": {"content": s}}]}
    props = {"공고번호": rt(no), "공고명": {"type": "title", "title": [{"plain_text": "조선왕릉 웹VR 콘텐츠 제작 용역"}]},
             "공고기관": rt("국가유산진흥원"), "수요기관": rt("국가유산진흥원"),
             "진행상태": {"type": "select", "select": {"name": state}},
             "우리담당": {"type": "people", "people": ([{"id": "u1", "name": "담당"}] if who else [])},
             "입찰마감일": {"type": "date", "date": ({"start": due} if due else None)},
             "추정가격(원)": {"type": "number", "number": 190000000},
             "요구업종코드": {"type": "multi_select", "multi_select": [{"name": "1469"}, {"name": "9999"}]},
             "GoNoGo": rt("■ 가점\n신용등급 B- 실점 2\n■ 정량점수\n예상 88\n■ 되는 것\n직생 보유\n_추출 자동"),
             "등급근거": rt("[v7]\n① 적합: 웹VR 정면 부합"), "사업등급": {"type": "select", "select": {"name": "A"}},
             "공고URL": {"type": "url", "url": "https://www.g2b.go.kr/x"}}
    return {"id": "page-1", "properties": props}


def _fake_sources():
    def row(**kv):
        pr = {}
        for k, v in kv.items():
            pr[k] = {"type": "rich_text", "rich_text": [{"plain_text": v}]}
        return pr
    cert_exp = row(명칭="벤처기업확인서", 구분="인증", 기관="벤처기업협회", 상태="만료")
    cert_od = row(명칭="경쟁입찰참가자격등록증", 구분="인증", 기관="조달청", 상태="만료")
    cert_exp["만료일"] = {"type": "date", "date": {"start": "2026-08-24"}}
    cert_ok = row(명칭="직접생산증명서(자격등록증)", 구분="인증", 기관="SMPP", 상태="유효")
    pat = row(명칭="인카메라 시각효과 조명 매칭 시스템", 구분="특허", 기관="특허청")
    proj = row(프로젝트명="무형유산 볼류메트릭 콘텐츠 제작", 발주기관="한국문화재재단", 개요="웹VR 전시 콘텐츠", 수행역할="주수행")
    proj["대외인용금지"] = {"type": "checkbox", "checkbox": False}
    proj["사업비"] = {"type": "number", "number": 297000000}
    arch = row(공고번호="R25BK0009", 공고명="조선왕릉 VR 콘텐츠 제작", 수요기관="국가유산진흥원", 결과="낙선", 교훈="가격 2위")
    return {
        "rfp": {"R26BK0001#a.hwpx|2026-07-29|2#2026-08-20-writerules":
                {"tasks": [{"req": "웹VR 콘텐츠 10종 제작", "quote": "웹VR 콘텐츠 10종을 제작한다"}],
                 "eval_items": [{"item": "기술능력평가", "points": "90%", "factor": "제안서", "quote": "기술 90"},
                                {"item": "가격평가", "points": "10%", "factor": "", "quote": "가격 10"},
                                {"item": "경영상태", "points": "5점", "factor": "", "quote": "경영상태–배점한도: 5점"}],
                 "toc": ["사업 이해", "수행 방안"], "limits": {"pages": "50쪽", "format": "PDF"},
                 "writing_rules": {"forbidden": ["업체명 노출"], "abbr_explain": True},
                 "keywords": ["웹VR", "조선왕릉"], "_src": ["a.hwpx"], "_body": "가. 제출서류\n[별지 제9호 서식] 인력 총괄표\n기술능력평가 90점 가격평가 10점 배점한도의 85% 이상\n| 평가항목 | 기업 신용평가등급 | 평점 |\n|---|---|---|\n| 경영상태 | B- | 3 |\n"},
                "R26BK0001#||0": {"tasks": [], "eval_items": []}},
        "scope": {"R26BK0001": {"src": "a.hwpx", "at": "2026-07-29", "scope": ["과업1", "과업2"], "deliverables": ["정성제안서"]}},
        "req": {"R26BK0001": {"qualifications": [{"req": "업종코드 1469 등록", "quote": "1469"}], "mandatory": [],
                               "deliverables": ["경쟁입찰참가자격등록증 1부", "정성제안서 1식"], "schedule": "2026-12-01"}},
        "quals": {"industry": ["1469"], "product": []},
        "facts": [row(항목="회사명", 값="주식회사 백스포트"), row(항목="본점", 값="경기도 고양시")],
        "certs": [cert_exp, cert_od, cert_ok, pat], "projects": [proj], "archive": [arch], "dump_at": "2026-09-04T15:52",
        "refidx": [{"title": "A. 볼류메트릭 캡처 · 무형유산 기록화", "rows": [["사업", "발주기관"], ["무형유산 볼류메트릭", "한국문화재재단"]],
                    "notes": ["재활용 문구 A — 웹VR 전시 4회 납품"]},
                   {"title": "H. AI 개발 · 데이터 가공", "rows": [["사업", "발주기관"], ["운동 코칭앱", "프로맥스"]], "notes": []},
                   {"title": "I. 인력 카드", "rows": [["성명", "역할"], ["○○○", "총괄"]], "notes": []},
                   {"title": "J. ⚠ 레퍼런스 공백", "rows": [["공백", "영향"], ["해외 실적 없음", "감점"]], "notes": []}],
    }


def selftest():
    fails, n = [], [0]

    def ok(name, cond):
        n[0] += 1
        if not cond:
            fails.append(name)

    today = dt.date(2026, 9, 4)
    ok("게이트: 도전+담당+마감전 통과", gate_reason(_fake_page()["properties"], today) == "")
    ok("게이트: 도전 아님 차단", "도전 아님" in gate_reason(_fake_page(state="검토전")["properties"], today))
    ok("게이트: 담당 없음 차단", "우리담당" in gate_reason(_fake_page(who=False)["properties"], today))
    ok("게이트: 마감 지남 차단", "지남" in gate_reason(_fake_page(due="2026-01-01")["properties"], today))
    ok("게이트: 마감일 없으면 통과", gate_reason(_fake_page(due="")["properties"], today) == "")
    ok("도장: 형식", ingest_stamp({"src": "a.hwpx", "at": "2026-07-29", "scope": [1, 2]}) == "a.hwpx|2026-07-29|2")
    ok("도장: 없으면 ||0", ingest_stamp({}) == "||0")
    src = _fake_sources()
    k, v, note = pick_rfp(src["rfp"], "R26BK0001", "a.hwpx|2026-07-29|2")
    ok("RFP 고르기: 도장 일치 우선", k.endswith("writerules") and note == "")
    k2, v2, note2 = pick_rfp(src["rfp"], "R26BK0001", "b.hwpx|2026-08-01|3")
    ok("RFP 고르기: 불일치면 표시", "판본 불일치" in note2 and k2)
    ok("RFP 고르기: 없으면 빈 dict", pick_rfp({}, "X", "||0") == (None, {}, "RFP 읽기 캐시 없음"))
    b = md_to_blocks("## 제목\n| a | b |\n|---|---|\n| 1 | **2** |\n- 목록\n> 인용\n---\n본문 `코드`\n```\ncode\n```")
    types = [x["type"] for x in b]
    ok("md→블록: 종류", types == ["heading_2", "table", "bulleted_list_item", "quote", "divider", "paragraph", "code"])
    ok("md→블록: 표 폭·굵게", b[1]["table"]["table_width"] == 2 and b[1]["table"]["children"][1]["table_row"]["cells"][1][0]["annotations"]["bold"])
    ok("md→블록: 인라인 코드", b[5]["paragraph"]["rich_text"][1]["annotations"]["code"])
    ok("배치: 50개 단위", [len(x) for x in batches([_blk("paragraph", "x")] * 120)] == [50, 50, 20])
    ok("공개 금지: IP·경로 잡음", forbidden("서버 100.79.44.59 의 /var/lib/vax") == ["사설망 IP", "서버 경로"])
    ok("공개 금지: 깨끗하면 빈 목록", forbidden("예시 웹VR 1억 9천만 원") == [])
    ok("유사도: 같은 글", sim("조선왕릉 웹VR", "조선왕릉 웹VR") == 1.0)
    ok("유사도: 다른 글", sim("조선왕릉", "육군 리더십") == 0.0)
    ok("낱말: 범용어 제외", "웹VR" in words("조선왕릉 웹VR 콘텐츠 제작 용역") and words("콘텐츠 제작 용역") == [])
    ok("GoNoGo 절: 4신호만", brief_sections("■ 가점\nA\n■ 되는 것\nB\n■ 정량점수\nC\n_추출 x", SIGNAL_HEADS) == "■ 가점\nA\n■ 정량점수\nC")
    ok("서식 추출", forms_from_body("가. 제출서류\n[별지 제9호 서식] 인력 총괄표\n나. 기타") == ["[별지 제9호 서식] 인력 총괄표"])
    md, stamp = build_pack(_fake_page(), src, today=today, now=dt.datetime(2026, 9, 4, 16, 0), use_market=False)
    ok("조립: 계약 H2 열 개 전부", check_sections(md) == [])
    ok("조립: 순서 유지", [md.index(f"## {s}") for s in SECTIONS] == sorted(md.index(f"## {s}") for s in SECTIONS))
    ok("조립: 도장 첫 문단", f"{STAMP_HEAD}R26BK0001#a.hwpx|2026-07-29|2#" in md and stamp.endswith(VERSION))
    ok("조립: 기술:가격 비율", "90 : 10" in md)
    ok("배점: 단위 없는 숫자", _pct("20") == 20 and _pct("90%") == 90 and _pct("배점한도: 5점") is None)
    ok("원문: 90%의 기술평가와 10%의 가격평가", tech_price_from_body("평가비율은 90%의 기술평가와 10%의 가격평가로 한다. 배점한도의 85% 이상") == (90.0, 10.0, 85.0))
    ok("원문: 기술평가점수(90점)", tech_price_from_body("종합평가점수(100점)는 기술평가점수(90점)과 입찰가격 평가점수(10점)")[:2] == (90.0, 10.0))
    ok("원문: 기술평가(90점)", tech_price_from_body("기술능력평가 90점 · 가격평가 10점 · 배점한도의 85% 이상인 자")[0] == 90.0)
    tb = score_tables_from_body("x\n| 평가항목 | 기업 신용평가등급 | 평점 |\n|---|---|---|\n| 경영상태 | A+ | 5 |\n\n| 연번 | 도서명 |\n|---|---|\n| 1 | USB |\n")
    ok("원문: 배점 표만 추출", len(tb) == 1 and "신용평가등급" in tb[0][0])
    rd = build_rfp_doc("R26BK0001", "제목", {"_body": "본문", "_src": ["a.hwp"]}, "S")
    ok("RFP 원문 페이지: 도장·본문", rd.startswith(f"# {RFP_TITLE} — R26BK0001") and f"{STAMP_HEAD}S" in rd and rd.rstrip().endswith("본문"))
    ok("조립: 세부 항목은 상위 합계에서 제외", "상위 항목 100 · 세부 포함 105" in md)
    ok("조립: 협상적격 76.5", "76.5점" in md)
    ok("조립: 원문 배점표 실림", "세부 배점표 — 원문 표 1개" in md and "| 경영상태 | B- | 3 |" in md)
    ok("조립: §9 원문 페이지 안내", RFP_TITLE in md.split("## 9.")[1])
    ok("열쇳말: 강한/약한 분리", keywords_of("조선왕릉 웹VR 콘텐츠 제작 용역", {"keywords": ["웹VR"], "tasks": [{"req": "기획 문서 데이터 납품"}]}, {})[0] == ["웹VR", "조선왕릉"])
    ok("일치 점수: 강한 것 없으면 0", match_score(["웹VR"], ["데이터"], "데이터 가공 사업") == (0, []))
    ok("조립: 업종코드 보유/미보유", "| 1469 | 보유 |" in md and "9999 | 미보유" in md)
    ok("조립: 만료 인증이 빈칸으로", any("벤처기업확인서" in g and "만료" in g for g in md.split("## 8.")[1].splitlines()))
    ok("조립: 온디맨드 서류는 빈칸에 안 올림", not any("경쟁입찰참가자격등록증" in g for g in md.split("## 8.")[1].splitlines()) and "재발급 서류(제출 시 발급)" in md)
    ok("조립: 미기입 팩트가 빈칸으로", "회사 팩트 「대표자」 미기입" in md)
    ok("조립: 유사 실적 겹친 낱말", "무형유산 볼류메트릭 콘텐츠 제작" in md and "웹VR" in md.split("### 5-③")[1].split("###")[0])
    ok("조립: 색인 군집 A 선택·H 제외", "A. 볼류메트릭" in md and "H. AI 개발" not in md)
    ok("조립: 색인 J 공백이 §8에", "해외 실적 없음" in md.split("## 8.")[1])
    ok("조립: 유사 과거 입찰", "R25BK0009" in md)
    ok("조립: 4신호 실림", "신용등급 B- 실점 2" in md and "_추출" not in md)
    ok("조립: 서식·별지", "별지 제9호" in md.split("## 9.")[1])
    ok("조립: 공개 금지 통과", forbidden(md) == [])
    ok("조립: 블록 변환 가능", len(md_to_blocks(md)) > 30)
    print(f"[{'FAIL' if fails else 'OK'}] proposal_material 검사 {n[0]}건" + ("\n  - " + "\n  - ".join(fails) if fails else ""))
    return 1 if fails else 0


# ── CLI ─────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="도전 공고 → 📦 제안 재료 팩 (LLM 0콜)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--list", action="store_true", help="게이트 통과 공고만 나열")
    ap.add_argument("--no", help="공고번호 한 건")
    ap.add_argument("--all", action="store_true", help="게이트를 무시하고 도전 전건(담당 미지정·마감 지남 포함)")
    ap.add_argument("--out", help="마크다운을 저장할 폴더")
    ap.add_argument("--commit", action="store_true", help="위키에 쓴다 (env BID_MATERIAL_COMMIT=1 도 같음)")
    ap.add_argument("--force", action="store_true", help="같은 판본이 있어도 다시 쓴다")
    ap.add_argument("--no-ref", action="store_true", help="레퍼런스 색인을 읽지 않는다(빠른 확인용)")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    commit = a.commit or COMMIT
    today = dt.date.today()
    if a.no:
        pg = radar_row(a.no)
        if not pg:
            print(f"⛔ 레이더에 {a.no} 가 없다")
            return 2
        pages = [pg]
    else:
        pages = list(challenge_pages())
    picked = []
    for pg in pages:
        why = gate_reason(pg.get("properties") or {}, today)
        no = _txt(pg.get("properties") or {}, "공고번호")
        if why and not (a.all or a.no):
            print(f"  [skip] {no} — {why}")
            continue
        if why:
            print(f"  ※ {no} — {why} (게이트 무시하고 진행)")
        picked.append(pg)
    print(f"# 도전 {len(pages)}건 중 대상 {len(picked)}건" + (" · commit" if commit else " · dry"))
    if a.list or not picked:
        for pg in picked:
            p = pg.get("properties") or {}
            print(f"  {_txt(p, '공고번호')} · {_txt(p, '공고명')[:40]} · 마감 {_date(p, '입찰마감일') or '-'}")
        return 0
    sources = load_sources(read_ref=not a.no_ref)
    counts = {}
    for pg in picked:
        try:
            r = run_one(pg, sources, commit, a.out, a.force, today=today)
        except Exception as e:  # noqa: BLE001
            print(f"  [건너뜀] {str(e)[:120]}")
            r = "error"
        counts[r] = counts.get(r, 0) + 1
    print("# 결과: " + " · ".join(f"{k} {v}" for k, v in counts.items()))
    return 1 if counts.get("error") else 0


if __name__ == "__main__":
    sys.exit(main())
