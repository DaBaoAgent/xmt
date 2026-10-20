"""编排：链接 → 提取 → 入库 → 拆解 → 判号/选品 → 逐字稿 → 审核/同步。"""
import os
import re
import sys
import json

from . import util
from . import store
from . import sources
from . import breakdown as breakdown_mod
from . import products
from . import personas
from . import writer
from . import render
from .company_kb import CompanyKB, CompanyKBError


def _kb():
    kb = CompanyKB()
    return kb if kb.available() else None


def _douyin_id_from_url(url):
    m = re.search(r"douyin\.com/(?:video|note)/(\d{10,})", str(url or ""))
    if m:
        return m.group(1)
    m = re.search(r"[?&]modal_id=(\d{10,})", str(url or ""))
    return m.group(1) if m else None


def _cached(con, platform, url):
    ref = None
    if platform == "douyin":
        vid = _douyin_id_from_url(url)
        if vid:
            ref = store.get_reference(con, platform, vid)
    if not ref:
        ref = store.find_reference_by_url(con, platform, url)
    if not ref:
        return None
    transcript = store.get_transcript(con, platform, ref.get("video_key"))
    if not transcript or not transcript.get("text"):
        return None
    return ref, transcript


def estimate(text, max_calls=None):
    urls = util.extract_urls(text)
    cfg = util.config()
    per = int((cfg.get("redfox") or {}).get("estimated_calls_per_link") or 3)
    threshold = int(max_calls or (cfg.get("redfox") or {}).get("batch_call_threshold") or 50)
    est = len(urls) * per
    return {
        "links": urls,
        "count": len(urls),
        "estimated_calls": est,
        "threshold": threshold,
        "needs_confirmation": est > threshold,
        "message": (f"预计 {len(urls)} 条，RedFox 约 {est} 次计费调用；超过阈值 {threshold}，"
                    f"需要你确认后再跑。" if est > threshold else
                    f"预计 {len(urls)} 条，RedFox 约 {est} 次计费调用（阈值 {threshold}）。"),
    }


def add(text, account=None, product=None, force=False, yes=False,
        use_llm=True, keep_video=False, max_calls=None):
    store.init()
    est = estimate(text, max_calls=max_calls)
    if not est["links"]:
        return {"ok": False, "status": "no_links", "message": "没有识别到抖音/视频号链接。", "estimate": est}
    if est["needs_confirmation"] and not yes:
        return {"ok": False, "status": "needs_confirmation", "message": est["message"], "estimate": est}

    batch_code = "B-" + util.now_stamp() + "-" + util.short_hash(text, 4)
    con = store.connect()
    counter = sources.CallCounter()
    extractor = sources.RedFoxExtractor(counter=counter, keep_video=keep_video)
    kb = _kb()
    items, pending = [], []
    total = len(est["links"])
    try:
        for idx, url in enumerate(est["links"], 1):
            platform = util.detect_platform(url)
            if not platform:
                items.append({"index": idx, "url": url, "platform": None, "title": url,
                              "status": "失败", "error": "不支持的链接平台"})
                continue
            before = counter.billable
            try:
                cached = None if force else _cached(con, platform, url)
                if cached:
                    ref, transcript = cached
                    warnings = []
                    cached_flag = True
                else:
                    ref = extractor.extract(url, platform)
                    warnings = ref.get("warnings") or []
                    cached_flag = False
                    if not ref.get("transcript") or not (ref.get("transcript") or {}).get("text"):
                        items.append({"index": idx, "url": url, "platform": platform,
                                      "title": ref.get("title") or url,
                                      "status": "失败",
                                      "error": ref.get("error") or "未取到文案",
                                      "warnings": warnings})
                        continue
                    transcript = ref["transcript"]

                key = store.upsert_reference(con, ref)
                store.save_transcript(con, platform, key, transcript, warnings)
                ref["video_key"] = key
                con.commit()
                delta = counter.billable - before
                if delta:
                    store.log_usage(con, batch_code, platform, key, "extract", delta,
                                    ref.get("metadata_source") or "")
                    con.commit()

                # 拆解（缓存优先）
                bd_row = None if force else store.get_breakdown(con, platform, key)
                if bd_row and bd_row.get("breakdown"):
                    b = bd_row["breakdown"]
                    if not b.get("summary_md"):
                        b["summary_md"] = render.summarize_breakdown_md(b)
                else:
                    b = breakdown_mod.analyze(ref, transcript, use_llm=use_llm)
                # 账号判断
                if account:
                    acc_sel = breakdown_mod.select_account(b, forced=account)
                else:
                    acc_sel = b.get("account_selection") or breakdown_mod.select_account(b)
                b["account_selection"] = acc_sel

                # 选品
                if product:
                    prod = products.select_manual(product, kb)
                else:
                    cached_prod = b.get("product_selection") if not force else None
                    prod = cached_prod or products.match(
                        b, ref, transcript.get("text") or "", kb, use_llm=use_llm)
                b["product_selection"] = prod
                b["summary_md"] = render.summarize_breakdown_md(b)
                store.save_breakdown(con, platform, key, b, b["summary_md"])
                ref_path = store.reference_path(ref)
                store.write_text(ref_path, render.render_reference(ref, transcript, b))
                con.commit()

                acc_ok = bool(acc_sel.get("selected") and acc_sel.get("account"))
                prod_ok = prod.get("status") in ("selected", "category", "manual_unlisted")
                if product and prod.get("status") in ("selected", "category", "manual_unlisted"):
                    prod_ok = True
                elif prod.get("needs_confirmation"):
                    prod_ok = False

                if not acc_ok or not prod_ok:
                    reasons = []
                    if not acc_ok:
                        reasons.append(acc_sel.get("reason") or "账号判断不明确")
                    if not prod_ok:
                        reasons.append(prod.get("reason") or "产品匹配不明确")
                    pending_item = _pending_item(idx, url, platform, key, ref, acc_sel, prod,
                                                 "；".join(reasons))
                    pending.append(pending_item)
                    items.append(pending_item)
                    continue

                # 已有同号脚本则复用
                existing = _existing_script(con, platform, key, acc_sel.get("account"))
                target_model = prod.get("model") if prod.get("status") == "selected" else None
                if existing and not force and (existing.get("product_model") or None) == (target_model or None):
                    items.append({
                        "index": idx, "url": url, "platform": platform, "title": ref.get("title") or url,
                        "account_id": acc_sel.get("account"), "account_label": acc_sel.get("account_label"),
                        "product": prod.get("model") or prod.get("category") or "品类通用",
                        "status": "成功（复用）", "code": existing.get("code"),
                        "file_path": existing.get("file_path"),
                    })
                    continue

                persona = personas.get(acc_sel.get("account")) or {}
                out = writer.generate(acc_sel.get("account"), persona, ref, transcript, b, prod,
                                      {"use_llm": use_llm})
                code, path, docx = _save_script(con, ref, transcript, b, acc_sel, prod, out)
                items.append({
                    "index": idx, "url": url, "platform": platform, "title": ref.get("title") or url,
                    "account_id": acc_sel.get("account"), "account_label": acc_sel.get("account_label"),
                    "product": prod.get("model") or prod.get("category") or "品类通用",
                    "status": "成功", "code": code, "file_path": path, "docx_path": docx,
                    "compliance_ok": bool((out.get("compliance") or {}).get("ok")),
                    "cached": cached_flag,
                })
            except Exception as e:
                items.append({"index": idx, "url": url, "platform": platform,
                              "title": url, "status": "失败",
                              "error": f"{type(e).__name__}: {str(e)[:300]}"})
        result = _finish_batch(con, batch_code, text, items, pending, counter, total)
        result["ok"] = True
        result["message"] = (f"完成：成功 {result['succeeded']}，失败 {result['failed']}，"
                             f"待确认 {result['pending_confirmation']}；"
                             f"计费调用 {result['billable_calls']} 次。")
        return result
    finally:
        try:
            con.close()
        except Exception:
            pass


def _pending_item(idx, url, platform, key, ref, acc_sel, prod, reason):
    acc_candidates = []
    for c in acc_sel.get("candidates") or []:
        if isinstance(c, dict):
            acc_candidates.append(c.get("label") or c.get("id"))
        else:
            acc_candidates.append(str(c))
    prod_candidates = prod.get("alternatives") or []
    if not prod_candidates:
        prod_candidates = products._default_candidates(prod.get("category"))
    return {
        "index": idx, "url": url, "platform": platform, "video_key": key,
        "title": ref.get("title") or url, "author": ref.get("author"),
        "status": "待确认",
        "account_selection": acc_sel,
        "product_selection": prod,
        "account_candidates": [x for x in acc_candidates if x],
        "account_candidate_ids": [c.get("id") for c in (acc_sel.get("candidates") or []) if isinstance(c, dict)],
        "product_candidates": [x for x in prod_candidates if x],
        "reason": reason,
        "cached": bool(ref.get("video_key")),
    }


def _existing_script(con, platform, key, account_id):
    row = con.execute(
        """SELECT * FROM sg_scripts WHERE source_platform=? AND video_key=? AND account_id=?
           AND status!='已退回' ORDER BY id DESC LIMIT 1""",
        (platform, key, account_id)).fetchone()
    return store._script_row_to_dict(row) if row else None


def _save_script(con, ref, transcript, b, acc_sel, prod, out):
    data = {
        "account_id": acc_sel.get("account"),
        "account_label": acc_sel.get("account_label"),
        "presenters": out.get("presenters") or [],
        "source_platform": ref.get("platform"),
        "video_key": ref.get("video_key"),
        "benchmark_url": ref.get("url"),
        "benchmark_title": ref.get("title"),
        "product_model": prod.get("model") if prod.get("status") == "selected" else None,
        "product_doc_ids": prod.get("doc_ids") or ([prod.get("doc_id")] if prod.get("doc_id") else []),
        "title": out.get("title"),
        "body": out.get("body"),
        "body_md": out.get("body_text"),
        "shooting_tips": out.get("shooting_tips"),
        "publish": out.get("publish"),
        "compliance": out.get("compliance"),
        "facts": out.get("facts_used"),
        "word_count": out.get("word_count"),
        "estimated_seconds": out.get("estimated_seconds"),
        "target_seconds": out.get("target_seconds"),
        "status": out.get("status") or store.STATUS_PENDING,
        "notes": " | ".join(x for x in [out.get("account_reason"), out.get("product_reason")] if x),
    }
    code = store.create_script(con, data)
    con.commit()
    script = store.get_script(con, code)
    path = store.script_path({**script, "title": out.get("title")})
    store.update_script(con, code, file_path=path)
    con.commit()
    _render_script(con, code)
    store.rebuild_index(con)
    saved = store.get_script(con, code)
    return code, path, (saved.get("docx_path") if saved else None)


def _render_script(con, code):
    script = store.get_script(con, code)
    if not script:
        return None
    bd_row = store.get_breakdown(con, script.get("source_platform"), script.get("video_key"))
    script["breakdown"] = (bd_row or {}).get("breakdown") or {}
    script["versions"] = store.list_versions(con, script["id"])
    text = render.render_script(script)
    path = script.get("file_path") or store.script_path(script)
    store.write_text(path, text)
    if path != script.get("file_path"):
        store.update_script(con, code, file_path=path)
        con.commit()
    # 打印版 Word：只含标题、账号/出镜、逐字稿或对白稿
    docx = script.get("docx_path") or store.docx_path(script)
    try:
        from . import docx_export
        docx_export.export(script, docx)
        if docx != script.get("docx_path"):
            store.update_script(con, code, docx_path=docx)
            con.commit()
    except Exception as e:
        print(f"[docx] 导出失败：{type(e).__name__}: {str(e)[:200]}", file=sys.stderr)
    return path


def _finish_batch(con, batch_code, source_text, items, pending, counter, total):
    succeeded = sum(1 for x in items if str(x.get("status") or "").startswith("成功"))
    failed = sum(1 for x in items if x.get("status") == "失败")
    result = {
        "batch_code": batch_code,
        "created_at": util.now_iso(),
        "total": total,
        "succeeded": succeeded,
        "failed": failed,
        "pending_confirmation": len(pending),
        "billable_calls": counter.billable,
        "poll_calls": counter.polls,
        "items": items,
        "pending": pending,
        "api_events": counter.events,
        "report_path": store.batch_path(batch_code),
    }
    store.create_batch(con, batch_code, source_text, result)
    con.commit()
    batch = store.get_batch(con, batch_code)
    store.write_text(store.batch_path(batch_code), render.render_batch(batch))
    store.rebuild_index(con)
    return result


def resolve_batch(batch_code, choices, use_llm=True):
    store.init()
    con = store.connect()
    try:
        batch = store.get_batch(con, batch_code)
        if not batch:
            return {"ok": False, "message": f"找不到批次 {batch_code}"}
        result = batch.get("result") or {}
        pending = list(result.get("pending") or [])
        items = list(result.get("items") or [])
        by_index = {int(p.get("index")): p for p in pending}
        kb = _kb()
        done = []
        for ch in choices:
            idx = int(ch.get("index"))
            p = by_index.get(idx)
            if not p:
                done.append({"index": idx, "ok": False, "message": "该编号不在待确认列表"})
                continue
            platform, key = p.get("platform"), p.get("video_key")
            ref = store.get_reference(con, platform, key) or {}
            tr = store.get_transcript(con, platform, key) or {}
            bd_row = store.get_breakdown(con, platform, key) or {}
            b = bd_row.get("breakdown") or {}
            if not ref or not tr.get("text") or not b:
                done.append({"index": idx, "ok": False, "message": "缓存缺失，需要重新跑该链接"})
                continue
            acc_sel = b.get("account_selection") or {}
            if ch.get("account"):
                acc_sel = breakdown_mod.select_account(b, forced=ch["account"])
                b["account_selection"] = acc_sel
            prod = b.get("product_selection") or {}
            if ch.get("product"):
                prod = products.select_manual(ch["product"], kb)
                b["product_selection"] = prod
            b["account_selection"] = acc_sel
            b["product_selection"] = prod
            b["summary_md"] = render.summarize_breakdown_md(b)
            store.save_breakdown(con, platform, key, b, b["summary_md"])
            store.write_text(store.reference_path(ref), render.render_reference(ref, tr, b))
            con.commit()
            acc_ok = bool(acc_sel.get("selected") and acc_sel.get("account"))
            prod_ok = prod.get("status") in ("selected", "category", "manual_unlisted")
            if not acc_ok or not prod_ok:
                done.append({"index": idx, "ok": False,
                             "message": "仍未确定账号或产品，请指定 account/product"})
                continue
            try:
                persona = personas.get(acc_sel.get("account")) or {}
                out = writer.generate(acc_sel.get("account"), persona, ref, tr, b, prod,
                                      {"use_llm": use_llm})
                code, path, docx = _save_script(con, ref, tr, b, acc_sel, prod, out)
                item = {
                    "index": idx, "url": p.get("url"), "platform": platform,
                    "title": ref.get("title"), "account_id": acc_sel.get("account"),
                    "account_label": acc_sel.get("account_label"),
                    "product": prod.get("model") or prod.get("category") or "品类通用",
                    "status": "成功", "code": code, "file_path": path, "docx_path": docx,
                    "compliance_ok": bool((out.get("compliance") or {}).get("ok")),
                }
                for i, it in enumerate(items):
                    if int(it.get("index") or 0) == idx and it.get("status") == "待确认":
                        items[i] = item
                        break
                pending = [x for x in pending if int(x.get("index")) != idx]
                done.append({"index": idx, "ok": True, "code": code, "file_path": path,
                             "docx_path": docx})
            except Exception as e:
                done.append({"index": idx, "ok": False,
                             "message": f"{type(e).__name__}: {str(e)[:300]}"})
        result["items"] = items
        result["pending"] = pending
        result["succeeded"] = sum(1 for x in items if str(x.get("status") or "").startswith("成功"))
        result["failed"] = sum(1 for x in items if x.get("status") == "失败")
        result["pending_confirmation"] = len(pending)
        result["report_path"] = store.batch_path(batch_code)
        store.create_batch(con, batch_code, batch.get("source_text") or "", result)
        con.commit()
        batch = store.get_batch(con, batch_code)
        store.write_text(store.batch_path(batch_code), render.render_batch(batch))
        store.rebuild_index(con)
        return {"ok": True, "batch_code": batch_code, "resolved": done,
                "pending_confirmation": len(pending), "report_path": result["report_path"]}
    finally:
        con.close()


def approve(codes, reject=False, note=None, by="老板"):
    store.init()
    con = store.connect()
    out = []
    try:
        for code in codes:
            s = store.get_script(con, code)
            if not s:
                out.append({"code": code, "ok": False, "message": "找不到脚本"})
                continue
            status = store.STATUS_REJECTED if reject else store.STATUS_APPROVED
            store.update_script(con, code, status=status,
                                approved_at=util.now_iso(), approved_by=by,
                                notes=((s.get("notes") or "") + (" | " + note if note else "")).strip(" |"))
            con.commit()
            path = _render_script(con, code)
            s2 = store.get_script(con, code)
            out.append({"code": code, "ok": True, "status": status, "file_path": path,
                        "docx_path": s2.get("docx_path") if s2 else None})
        store.rebuild_index(con)
        return {"ok": True, "items": out}
    finally:
        con.close()


def revise(code, instruction, use_llm=True):
    store.init()
    con = store.connect()
    try:
        s = store.get_script(con, code)
        if not s:
            return {"ok": False, "message": "找不到脚本"}
        bd_row = store.get_breakdown(con, s.get("source_platform"), s.get("video_key"))
        b = (bd_row or {}).get("breakdown") or {}
        persona = personas.get(s.get("account_id")) or {}
        bench_dur = (b.get("pacing") or {}).get("duration_sec")
        target = s.get("target_seconds") or writer.target_duration(persona, bench_dur)
        m = re.search(r"(\d+(?:\.\d+)?)\s*秒", instruction or "")
        if m:
            target = float(m.group(1))
        prod = b.get("product_selection") or {}
        if prod.get("facts"):
            s = dict(s)
            s["facts"] = prod["facts"]
        new = writer.revise(s, instruction, use_llm=use_llm, target_seconds=target)
        version = int(s.get("version") or 1) + 1
        store.update_script(
            con, code,
            title=new.get("title") or s.get("title"),
            body=new.get("body"), body_md=new.get("body_text"),
            shooting_tips=new.get("shooting_tips"),
            publish=new.get("publish"), compliance=new.get("compliance"),
            facts=new.get("facts_used"),
            word_count=new.get("word_count"), estimated_seconds=new.get("estimated_seconds"),
            target_seconds=target,
            status=new.get("status") or store.STATUS_PENDING, version=version,
        )
        store.add_version(con, s["id"], version, instruction, new.get("body_text"),
                          new.get("publish"), new.get("compliance"))
        con.commit()
        path = _render_script(con, code)
        store.rebuild_index(con)
        s2 = store.get_script(con, code)
        return {"ok": True, "code": code, "version": version, "status": new.get("status"),
                "file_path": path, "docx_path": s2.get("docx_path") if s2 else None,
                "compliance": new.get("compliance")}
    finally:
        con.close()


def sync(codes, dry_run=False):
    store.init()
    con = store.connect()
    kb = _kb()
    out = []
    try:
        for code in codes:
            s = store.get_script(con, code)
            if not s:
                out.append({"code": code, "ok": False, "message": "找不到脚本"})
                continue
            if s.get("status") not in (store.STATUS_APPROVED, store.STATUS_SYNCED):
                out.append({"code": code, "ok": False,
                            "message": f"只有已通过的脚本才能同步（当前 {s.get('status')}）"})
                continue
            content = _kb_doc_content(con, s)
            if dry_run:
                out.append({"code": code, "ok": True, "dry_run": True, "content": content[:1200]})
                continue
            if not kb:
                out.append({"code": code, "ok": False, "message": "公司知识库不可用（COMPANY_KB_TOKEN）"})
                continue
            title = f"[{s.get('account_label')}] {s.get('title')}"
            doc_id = f"scriptgen/{code}.md"
            try:
                r = kb.write("marketing", title, content,
                             doc_id=doc_id, tags=["口播脚本", "对标的拆解", "scriptgen"])
            except Exception as e1:
                try:
                    r = kb.write("marketing", title, content,
                                 tags=["口播脚本", "对标的拆解", "scriptgen"])
                except Exception as e2:
                    out.append({"code": code, "ok": False,
                                "message": f"写入失败：{type(e2).__name__}: {str(e2)[:240]}"})
                    continue
            kb_doc = None
            if isinstance(r, dict):
                kb_doc = r.get("doc_id") or r.get("id") or (r.get("doc") or {}).get("doc_id")
            store.update_script(con, code, status=store.STATUS_SYNCED,
                                sync_status="已同步", synced_at=util.now_iso(),
                                kb_doc_id=kb_doc)
            con.commit()
            _render_script(con, code)
            out.append({"code": code, "ok": True, "kb_doc_id": kb_doc})
        store.rebuild_index(con)
        return {"ok": True, "items": out}
    finally:
        con.close()


def _kb_doc_content(con, s):
    bd_row = store.get_breakdown(con, s.get("source_platform"), s.get("video_key"))
    b = (bd_row or {}).get("breakdown") or {}
    lines = [
        f"# [{s.get('account_label')}] {s.get('title')}",
        "",
        f"- 编号：{s.get('code')}",
        f"- 日期：{(s.get('created_at') or '')[:10]}",
        f"- 账号：{s.get('account_label')}（{'、'.join(s.get('presenters') or [])}）",
        f"- 产品：{s.get('product_model') or '品类通用'}",
        f"- 对标：{s.get('benchmark_title') or '—'}",
        f"- 对标链接：{s.get('benchmark_url') or '—'}",
        f"- 状态：{s.get('status')}",
        "",
        "## 逐字稿",
        "",
        s.get("body_md") or "",
        "",
        "## 对标结构摘要",
        "",
        b.get("summary_md") or render.summarize_breakdown_md(b),
        "",
        "## 可复用方法论",
        "",
        f"- 钩子类型：{(b.get('hook') or {}).get('type') or '—'}",
        f"- 结构：{'；'.join(str(x.get('beat') or '') for x in (b.get('structure') or []))}",
        f"- 卖点顺序：{'；'.join(str(x.get('point') or '') for x in (b.get('selling_points') or []))}",
        f"- CTA 映射：{(b.get('cta') or {}).get('mapping') or '—'}",
        "",
        "## 合规自检",
        "",
        json.dumps(s.get("compliance") or {}, ensure_ascii=False, indent=2)[:2500],
        "",
        "## 发布提示",
        "",
        f"- 发布文案末尾固定追加：{(s.get('publish') or {}).get('disclaimer') or util.compliance_config().get('disclaimer')}",
        "",
        "---",
        "由 xmt scriptgen 生成；公司知识库只存审核通过版本，原始对标文案仅在本地知识库。",
        "",
    ]
    return "\n".join(lines)


def list_scripts(status=None, account=None, date=None, limit=50):
    store.init()
    con = store.connect()
    try:
        return store.list_scripts(con, status=status, account_id=account, date=date, limit=limit)
    finally:
        con.close()


def get_script(code):
    store.init()
    con = store.connect()
    try:
        s = store.get_script(con, code)
        if not s:
            return None
        bd_row = store.get_breakdown(con, s.get("source_platform"), s.get("video_key"))
        s["breakdown"] = (bd_row or {}).get("breakdown") or {}
        s["versions"] = store.list_versions(con, s["id"])
        return s
    finally:
        con.close()


def search_local(query, limit=20):
    store.init()
    con = store.connect()
    q = f"%{query}%"
    out = []
    try:
        for r in con.execute(
                """SELECT code,title,status,account_label,file_path,docx_path,created_at
                   FROM sg_scripts WHERE title LIKE ? OR body_md LIKE ? OR benchmark_title LIKE ?
                   ORDER BY created_at DESC LIMIT ?""", (q, q, q, limit)):
            d = dict(r)
            d["type"] = "脚本"
            out.append(d)
        for r in con.execute(
                """SELECT platform,video_key,title,author,url
                   FROM sg_reference_videos WHERE title LIKE ? OR description LIKE ?
                   ORDER BY last_seen DESC LIMIT ?""", (q, q, limit)):
            d = dict(r)
            d["type"] = "对标"
            d["doc_path"] = store.reference_path({**d, "video_key": d.get("video_key")})
            out.append(d)
        for r in con.execute(
                """SELECT platform,video_key,text FROM sg_transcripts WHERE text LIKE ?
                   ORDER BY updated_at DESC LIMIT ?""", (q, limit)):
            d = dict(r)
            d["type"] = "转写"
            d["snippet"] = (d.pop("text", "") or "")[:200]
            out.append(d)
        return out
    finally:
        con.close()
