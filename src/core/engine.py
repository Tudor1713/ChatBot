"""Platform independent model judgments, genuine drafts, and optional ranking.

Public API: analyze(messages, config, background='', history=None, reply_to=None)
            test_connection(config)
No Qt, OCR, file IO, environment mutation, or dependency on the desktop shell.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import math
import time

from .client import ProviderError, post_json, resolve_decision, resolve_reply
from .draft import draft_candidates, draft_bundle
from .week_context import select_week, build_week_state
from .questions import build_rank_question, build_state, judge_questions
from .model_profile import profile_for


INTENTS = {"confirm_you_care": "确认你是否在意", "vent_anger": "表达不满或委屈", "request_action": "希望你采取行动", "seek_explanation": "想了解原因", "casual_chat": "轻松聊天", "close_topic": "准备结束话题"}
NEEDS = {"apology": "真诚道歉", "action": "具体行动", "explanation": "清楚解释", "care": "被在意和理解", "nothing": "暂时无需更多回应"}
ACTIONS = {"check_history": "先核对聊天记录和事实", "apologize": "为已确认的问题道歉", "give_commitment": "给出能兑现的承诺", "explain": "说明已知事实", "acknowledge": "先表达理解", "say_less": "少说一点，给对方空间", "make_plan": "商量具体安排"}


def _number(value, low=0.0, high=1.0):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        return None
    try:
        return float(value) if low <= value <= high and math.isfinite(value) else None
    except (ValueError, OverflowError):
        return None


def _usage(raw):
    if not isinstance(raw, dict):
        return {}
    return {k: v for k, v in raw.items() if k in {"input_tokens", "output_tokens", "prompt_tokens", "completion_tokens", "total_tokens", "cost"} and _number(v, 0, 1e12) is not None}


def _answers(response: dict, questions: dict) -> tuple[dict, dict, list[str]]:
    """Read typed maps only; never interpret chat completion text as a typed judgment."""
    if not isinstance(response, dict):
        raise ProviderError("模型返回结构不正确。")
    body = response
    if "answers" not in body:
        for key in ("data", "result"):
            if isinstance(response.get(key), dict) and "answers" in response[key]:
                body = response[key]
                break
    raw = body.get("answers")
    if not isinstance(raw, dict) or not raw:
        raise ProviderError("接口没有返回 typed answers，请确认使用 decisions/systemone 协议。")
    answers, missing = {}, []
    for key, question in questions.items():
        item = raw.get(key)
        kind = question["type"]
        if not isinstance(item, dict) or item.get("type", kind) != kind:
            missing.append(key)
            continue
        parsed = {"type": kind}
        if kind == "choice":
            choice = item.get("choice")
            if not isinstance(choice, str) or choice not in question["criteria"]:
                missing.append(key)
                continue
            parsed["choice"] = choice
            parsed["confidence"] = _number(item.get("confidence"))
            probabilities = item.get("probabilities")
            parsed["probabilities"] = {k: _number(probabilities.get(k)) for k in question["criteria"]} if isinstance(probabilities, dict) else {}
        elif kind == "score":
            score = _number(item.get("score"), 0, len(question["criteria"]) - 1)
            if score is None:
                missing.append(key)
                continue
            parsed.update(score=score, confidence=_number(item.get("confidence")))
        else:
            probability = _number(item.get("noul"))
            if probability is None:
                missing.append(key)
                continue
            parsed["noul"] = probability
        answers[key] = parsed
    if not answers:
        raise ProviderError("模型返回了空白或无效判断，未生成分析。")
    return answers, _usage(body.get("usage", response.get("usage"))), missing


def _ask(route, state, questions, timeout):
    response = post_json(route, {"model": route.model, "state": state, "questions": questions}, timeout=timeout)
    return _answers(response, questions)


def _options(config):
    try:
        limit = max(3, min(int(config.get("context_limit", 10)), 200))
        maximum=120 if profile_for(config.get('model_name')) else 60
        timeout = max(1, min(float(config.get("timeout", maximum if config.get('context_days') == 7 else 20)), maximum))
        if not math.isfinite(timeout):
            raise ValueError
    except (TypeError, ValueError):
        raise ProviderError("上下文条数或超时配置不正确。") from None
    return limit, timeout


def analyze(messages, config, background="", history=None, reply_to=None, context_meta=None, previous=None):
    """previous={'answers': {...}}：对话没变、只是「换一批」时沿用上次的判断，只重写并重新排序回复。"""
    started = time.monotonic()
    decision = resolve_decision(config)
    limit, timeout = _options(config)
    if config.get('context_days') == 7:
        if context_meta is None:
            messages, context_meta=select_week(messages,time.time(),complete=False,source='collected')
        state=build_week_state(messages,config,context_meta,background,reply_to)
    else:
        state = build_state(messages, str(config.get("relationship") or "未指定关系"), keep=limit, reply_to=reply_to, background=background, history=history)
    if not state["chat"]["messages"]:
        raise ProviderError("还没有可分析的文字消息。")
    warnings = []
    try:
        reply = resolve_reply(config, decision)
    except ProviderError as exc:
        reply = None
        warnings.append("回复配置不可用：" + str(exc))
    if reply is None and not warnings:
        warnings.append("当前为模型判断模式。此接口不生成回复；请在高级设置配置回复模型、地址和密钥。")
    questions = judge_questions()
    candidates, topics, draft_usage, memory = [], {}, {}, []
    # Draft failure never prevents the seven independent judgments.
    reused = previous.get("answers") if isinstance(previous, dict) and isinstance(previous.get("answers"), dict) else None
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="chatbot-model") as pool:
        judgment = None if reused else pool.submit(_ask, decision, state, questions, timeout)
        drafting = pool.submit(draft_bundle, reply, state, config.get("style", ""), timeout) if reply else None
        answers,judge_usage,missing={}, {}, []
        judgment_error=None
        if reused:
            answers = reused
        else:
            try:
                answers, judge_usage, missing = judgment.result()
            except ProviderError as exc:
                judgment_error=exc
                warnings.append('对话判断暂不可用，回复建议仍可使用：'+str(exc))
        if drafting:
            try:
                bundle = drafting.result()
                candidates, topics, draft_usage = bundle[:3]
                memory = list(bundle[3]) if len(bundle) > 3 else []
            except ProviderError as exc:
                warnings.append("候选生成失败：" + str(exc))
    if not answers and not candidates:
        raise judgment_error or ProviderError('本次判断与回复生成均未完成，请稍后重试。')
    if missing:
        warnings.append("部分判断缺失或格式无效，界面保留为空。")
    best_index, scores, rank_usage = None, [None] * len(candidates), {}
    if len(candidates) >= 2 and answers:
        try:
            ranked, rank_usage, _ = _ask(decision, state, build_rank_question(candidates), timeout)
            answer = ranked.get("best_reply", {})
            best = answer.get("choice")
            keys = ("reply_a", "reply_b", "reply_c", "reply_d", "reply_e")[:len(candidates)]
            best_index = keys.index(best) if best in keys else None
            probabilities = answer.get("probabilities", {})
            scores = [probabilities.get(k) for k in keys]
        except ProviderError as exc:
            warnings.append("候选排序不可用：" + str(exc))
    elif len(candidates)==1:
        warnings.append("回复模型仅返回一条候选，未进行候选排序。")
    if candidates and len(candidates)<5:
        warnings.append(f'模型只返回{len(candidates)}条有效建议，可重新分析以获取5条。')
    if context_meta and not context_meta.get('complete'):
        warnings.append('当前只覆盖已读取的记录，不能视为最近7天完整聊天。')
    originals={str(m.get('id')):m for m in state['chat']['messages'] if m.get('id')}
    for group in topics.values():
        for topic in group:
            topic['evidence']=[{'id':id,'text':originals[id]['text'][:500],
                                'side':originals[id]['from']} for id in topic['evidence_ids'] if id in originals]
    intent = answers.get("true_intent", {})
    need = answers.get("she_needs", {})
    action = answers.get("best_action", {})
    risk = answers.get("danger_level", {})
    should = answers.get("should_reply_now", {}).get("noul")
    return {
        "session_id": config.get("session_id"),
        "intent": INTENTS.get(intent.get("choice")), "need": NEEDS.get(need.get("choice")),
        "action": ACTIONS.get(action.get("choice")), "risk": risk.get("score"),
        "should_reply": should >= 0.5 if should is not None else None,
        "should_reply_probability": should, "urgency": None,
        "confidence": intent.get("confidence"), "confidence_source": "true_intent",
        "candidates": [{"text": t, "score": s, "reason": "模型推荐" if i == best_index else ""} for i, (t, s) in enumerate(zip(candidates, scores))],
        "best_index": best_index, "answers": answers, "topics": topics,
        "memory_candidates": memory,
        "context_window": context_meta,
        "judgment_available":bool(answers),
        "usage": {"judge": judge_usage, "draft": _usage(draft_usage), "rank": rank_usage},
        "latency_ms": round((time.monotonic() - started) * 1000),
        "updated_at": datetime.now(timezone.utc).isoformat(), "warning": " ".join(warnings) or None,
    }


def test_connection(config):
    """Explicit user action only: tiny real typed request; no chat history sent."""
    decision = resolve_decision(config)
    _, timeout = _options(config)
    questions = {"connection": {"type": "noul", "instructions": "Does the state contain the word ready?"}}
    _ask(decision, {"status": "ready"}, questions, timeout)
    try:
        reply = resolve_reply(config, decision)
        if reply:
            state = build_state([{"side": "other", "text": "你好"}], "连接测试")
            draft_candidates(reply, state, timeout=timeout)
            return {"success": True, "message": "模型判断与回复生成均已连通。", "mode": decision.mode, "generation_available": True}
        message = "模型判断已连通。当前服务仅提供判断；在高级设置配置生成模型后可获得候选回复。"
    except ProviderError as exc:
        message = "模型判断已连通，回复生成暂不可用：" + str(exc)
    return {"success": True, "message": message, "mode": decision.mode, "generation_available": False}
