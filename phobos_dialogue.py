"""Parser and runtime selection for the supplied Phobos/VTD dialogue bank."""
from __future__ import annotations

import re
from pathlib import Path


PHOBOS_FALLBACK_REACTIONS = [
    "Ха-ха-ха!",
    "Ха! Какой удивительно серьёзный человек.",
    "Ха-ха-ха... Ты снова его вызвал?",
    "Ха. Начинаю понимать, почему ты продолжаешь это делать.",
    "Ха-ха-ха! Даже я бы не стал спорить с ним об этикете.",
    "Ха! Он всегда разговаривает так?",
    "Ха-ха-ха... У твоего мира странные заклинатели.",
    "Ха. Признаю: этого я не предусмотрел.",
]


def _quotes(text: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"(?m)^>\s*(.+?)\s*$", text)]


def _speaker_lines(text: str) -> list[str]:
    quoted = _quotes(text)
    if quoted:
        return quoted
    lines=[]
    for raw in text.splitlines():
        line=raw.strip().rstrip()
        if not line or line.startswith(("#", "**", "---", "- ", "###")):
            continue
        lines.append(line.rstrip("  "))
    return lines[:4]


def _numbered_lines(section: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"(?m)^\s*\d+\.\s+(.+?)\s*$", section)]


def load_opening_chains(path: Path) -> tuple[list[dict], list[str]]:
    """Parse the authored nine intros and the Escape-only reaction."""
    try:
        source=path.read_text(encoding="utf-8")
    except OSError:
        return [],[]
    intros=[]; escape=[]
    sections=re.split(r"(?m)(?=^#\s+INTRO-|^#\s+EVENT-ESCAPE-)",source)
    for section in sections:
        heading=section.splitlines()[0] if section.splitlines() else ""
        intro=re.search(r"INTRO-(\d+)",heading)
        lines=_numbered_lines(section.split("**ФОБОС:**",1)[-1])
        if intro and lines:
            intros.append({"id":f"opening-{intro.group(1)}","lines":lines})
        elif "EVENT-ESCAPE-" in heading and lines:
            escape=lines
    return intros,escape


def load_phobos_dialogue(path: Path, opening_path: Path | None = None) -> dict:
    """Read the authored Markdown bank without a fragile generated JSON copy."""
    result = {"intros": [], "random": [], "vtd": [], "reactions": PHOBOS_FALLBACK_REACTIONS[:]}
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return result
    sections = re.split(r"(?m)(?=^#{1,3}\s+)", source)
    for section in sections:
        heading = section.splitlines()[0] if section.splitlines() else ""
        intro = re.search(r"P-INTRO-(\d+)", heading)
        room = re.search(r"P-RANDOM-(\d+)", heading)
        vtd = re.search(r"(?:VTD-(\d+)|VTD-POOL-(\d+))", heading)
        if intro:
            lines = _speaker_lines(section.split("**ФОБОС:**", 1)[-1])
            if lines:
                result["intros"].append({"id": f"intro-{intro.group(1)}", "lines": lines})
        elif room:
            lines = _speaker_lines(section.split("**ФОБОС:**", 1)[-1])
            if lines:
                result["random"].append({"id": f"random-{room.group(1)}", "lines": lines})
        elif vtd and "**ВАЛЕНТИН:**" in section:
            valentin_part = section.split("**ВАЛЕНТИН:**", 1)[1]
            if "**ФОБОС:**" in valentin_part:
                valentin_part, phobos_part = valentin_part.split("**ФОБОС:**", 1)
            else:
                phobos_part = ""
            lines = _quotes(valentin_part)
            reply = _quotes(phobos_part)
            if lines:
                number = vtd.group(1) or vtd.group(2)
                prefix = "base" if vtd.group(1) else "pool"
                result["vtd"].append({"id": f"{prefix}-{number}", "lines": lines, "reply": reply})
    if opening_path is not None:
        intros,escape=load_opening_chains(opening_path)
        if intros: result["intros"]=intros
        if escape: result["escape"]=escape
    return result
