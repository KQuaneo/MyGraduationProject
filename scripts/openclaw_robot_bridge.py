#!/usr/bin/env python3
"""File-protocol bridge from Open-LLM-VTuber to OpenClaw local agent."""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_OPENCLAW_BIN = "/home/raspberrypi/.npm-global/bin/openclaw"
DEFAULT_INPUT_FILE = "/tmp/robot_input.txt"
DEFAULT_OUTPUT_FILE = "/tmp/robot_output.json"
DEFAULT_SESSION_ID = "robot-vtuber-bridge"
DEFAULT_VTUBER_CONFIG = (
    "/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/conf.yaml"
)


ROBOT_PROMPT = """你是二次元萌宠机器人的外部联网查询工具。
你不是最终发声模型；最终回复会交给 VTuber 主模型按角色语气整理。
你的职责只包括联网搜索、查天气、查新闻、查询日期和最新实时信息。
不要处理视觉、普通聊天、角色扮演、动作控制或硬件控制，这些都由 VTuber 主模型处理。
你必须只输出一个 JSON 对象，不要输出 Markdown，不要解释。
JSON 字段：
- p: 查询到的信息，简短中文，适合直接语音播报，最多 80 个汉字
如果用户问天气、新闻、今天、现在、最新等实时信息，请联网查询后再回答。
{vtuber_context}

用户输入：{query}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-file", default=DEFAULT_INPUT_FILE)
    parser.add_argument("--output-file", default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--openclaw-bin", default=DEFAULT_OPENCLAW_BIN)
    parser.add_argument("--session-id", default=DEFAULT_SESSION_ID)
    parser.add_argument(
        "--session-mode",
        choices=("isolated", "persistent"),
        default="isolated",
        help="Use isolated one-turn OpenClaw sessions by default to avoid prompt/history bloat.",
    )
    parser.add_argument("--vtuber-config", default=DEFAULT_VTUBER_CONFIG)
    parser.add_argument("--no-sync-vtuber-prompt", action="store_true")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--poll-interval", type=float, default=0.2)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--once-wait", type=int, default=30)
    return parser.parse_args()


def read_and_delete(path: Path) -> Optional[str]:
    try:
        text = path.read_text(encoding="utf-8")
        path.unlink(missing_ok=True)
        return text.strip()
    except FileNotFoundError:
        return None


def write_json(path: Path, payload: Dict[str, str]) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp_path.replace(path)


def load_vtuber_context(config_path: str, enabled: bool) -> str:
    if not enabled:
        return ""

    path = Path(config_path)
    if not path.exists():
        return ""

    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        character = data.get("character_config") or {}
        character_name = str(character.get("character_name") or "").strip()
        persona_prompt = str(character.get("persona_prompt") or "").strip()
    except Exception:
        character_name = ""
        persona_prompt = extract_persona_prompt_fallback(path)

    if not persona_prompt:
        return ""

    if len(persona_prompt) > 1200:
        persona_prompt = persona_prompt[:1200].rstrip() + "\n..."

    name_line = f"当前 VTuber 角色名：{character_name}\n" if character_name else ""
    return (
        "\n当前 VTuber 主模型的人设/系统提示词摘要如下。"
        "你必须尊重它的语气、边界和安全要求，但不要在 p 中复述这些规则：\n"
        f"{name_line}{persona_prompt}\n"
    )


def extract_persona_prompt_fallback(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.strip() != "persona_prompt: |":
            continue
        collected = []
        for next_line in lines[index + 1 :]:
            if next_line.startswith("  ") and not next_line.startswith("    "):
                break
            if next_line.startswith("    "):
                collected.append(next_line[4:])
            elif not next_line.strip():
                collected.append("")
            else:
                break
        return "\n".join(collected).strip()
    return ""


def run_openclaw(
    openclaw_bin: str,
    session_id: str,
    session_mode: str,
    timeout: int,
    query: str,
    vtuber_context: str = "",
) -> Dict[str, str]:
    quick_result = quick_live_query(query)
    if quick_result:
        return quick_result

    prompt = ROBOT_PROMPT.format(query=query, vtuber_context=vtuber_context)
    effective_session_id = session_id
    if session_mode == "isolated":
        suffix = f"{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}"
        effective_session_id = f"{session_id}-{suffix}"

    command = [
        openclaw_bin,
        "agent",
        "--local",
        "--json",
        "--session-id",
        effective_session_id,
        "--timeout",
        str(timeout),
        "--message",
        prompt,
    ]

    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout + 15,
    )

    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "").strip()
        return {
            "p": "我联网查询失败了",
            "debug": message[-300:],
        }

    text = extract_openclaw_text(completed.stdout)
    result = extract_json_object(text) or {"p": compact_reply(text)}
    normalized = normalize_result(result)
    if normalized["p"] in {"我查到啦", "我查到了，但结果有点空"}:
        fallback = fallback_live_query(query)
        if fallback:
            return fallback
    return normalized


def extract_openclaw_text(stdout: str) -> str:
    try:
        data = json.loads(stdout)
        payloads = data.get("payloads") or []
        if payloads and isinstance(payloads[0], dict):
            return str(payloads[0].get("text", "")).strip()
    except json.JSONDecodeError:
        pass
    return stdout.strip()


def extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.I).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    candidates = [cleaned]

    match = re.search(r"\{.*\}", cleaned, flags=re.S)
    if match:
        candidates.append(match.group(0))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    return None


def compact_reply(text: str) -> str:
    reply = re.sub(r"\s+", " ", text).strip()
    if not reply:
        return "我查到了，但结果有点空"
    return reply[:80]


def fallback_live_query(query: str) -> Optional[Dict[str, str]]:
    if is_weather_query(query):
        weather = fetch_weather(query)
        if weather:
            return {"p": weather}
    if is_news_query(query):
        news = fetch_news(query)
        if news:
            return {"p": news}
    return None


def quick_live_query(query: str) -> Optional[Dict[str, str]]:
    """Answer obvious realtime queries directly to avoid slow agent startup."""
    return fallback_live_query(query)


def is_weather_query(query: str) -> bool:
    return any(word in query for word in ("天气", "气温", "下雨", "降雨", "冷不冷", "热不热"))


def is_news_query(query: str) -> bool:
    return any(word in query for word in ("新闻", "最新", "热点", "时事", "今天发生"))


def infer_weather_location(query: str) -> str:
    for location in ("广州", "深圳", "上海", "北京", "杭州", "南京", "成都", "武汉", "西安"):
        if location in query:
            return location
    return "广州"


def fetch_weather(query: str) -> Optional[str]:
    location = infer_weather_location(query)
    encoded_location = urllib.parse.quote(location)
    params = urllib.parse.urlencode(
        {"format": "%l: %c %t (体感%f), 风%w, 湿度%h"}
    )
    url = f"https://wttr.in/{encoded_location}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            text = response.read().decode("utf-8", "ignore").strip()
    except Exception:
        return None
    return re.sub(r"\s+", " ", text)[:80] if text else None


def fetch_news(query: str) -> Optional[str]:
    topic = "中国"
    if "科技" in query:
        topic = "科技"
    elif "AI" in query or "人工智能" in query:
        topic = "人工智能"
    encoded_topic = urllib.parse.quote(topic)
    urls = [
        f"https://www.bing.com/news/search?q={encoded_topic}&format=rss&cc=CN",
        f"https://news.google.com/rss/search?q={encoded_topic}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    ]

    titles = []
    for url in urls:
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                xml_text = response.read().decode("utf-8", "ignore")
            root = ET.fromstring(xml_text)
        except Exception:
            continue

        for item in root.findall(".//item"):
            title = item.findtext("title")
            if title:
                title = unescape(title)
                title = re.sub(r"<[^>]+>", "", title)
                title = re.sub(r"\s+-\s+.+$", "", title).strip()
                if title and title not in titles:
                    titles.append(title)
            if len(titles) >= 2:
                break
        if titles:
            break

    if not titles:
        return None
    return "最新新闻：" + "；".join(titles)[:70]


def normalize_result(result: Dict[str, Any]) -> Dict[str, str]:
    # Accept the old reply field during rolling restarts, but only emit p.
    p = str(result.get("p") or result.get("reply") or "").strip() or "我查到啦"
    return {"p": p[:80]}


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_file)
    output_path = Path(args.output_file)
    once_deadline = time.monotonic() + args.once_wait if args.once else None
    vtuber_context = load_vtuber_context(
        args.vtuber_config,
        enabled=not args.no_sync_vtuber_prompt,
    )

    print(
        f"[OpenClawBridge] listening: {input_path} -> {output_path}",
        flush=True,
    )
    if vtuber_context:
        print("[OpenClawBridge] synced VTuber persona prompt", flush=True)

    while True:
        query = read_and_delete(input_path)
        if query:
            print(f"[OpenClawBridge] query: {query}", flush=True)
            result = run_openclaw(
                openclaw_bin=args.openclaw_bin,
                session_id=args.session_id,
                session_mode=args.session_mode,
                timeout=args.timeout,
                query=query,
                vtuber_context=vtuber_context,
            )
            write_json(output_path, result)
            print(f"[OpenClawBridge] result: {result}", flush=True)
            if args.once:
                return 0

        if args.once and once_deadline and time.monotonic() >= once_deadline:
            print("[OpenClawBridge] timed out waiting for one input", flush=True)
            return 1
        time.sleep(args.poll_interval)


if __name__ == "__main__":
    sys.exit(main())
