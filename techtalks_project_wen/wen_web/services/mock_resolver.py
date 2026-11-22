"""Development stand-in for the landmark resolver (lane 1 replaces this).

What it does, deliberately simply:
1. Normalises Arabic (hamza forms, taa marbuta, diacritics) and Latin/Arabizi
   spellings (ch/sh, ou/u, e/i...) the same way on both sides.
2. Fuzzy-matches word windows of the description against the gazetteer aliases.
3. Pulls two easy hints out of the text: floor and building colour.

It never claims certainty: every result carries a match quality, and the UI
shows these results as suggestions from a simulated resolver.
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

from .base import LandmarkResolver
from .gazetteer import LANDMARKS
from .types import Candidate, Landmark, Resolution

AR = "\u0621-\u063a\u0641-\u064a\u064b-\u0652\u0671-\u06d3"  # Arabic letters + harakat
ARABIC_LETTERS = re.compile(f"[{AR}]")
LATIN_LETTERS = re.compile(r"[A-Za-z]")
TOKEN = re.compile(f"[0-9A-Za-z\u00c0-\u024f\u0660-\u0669{AR}]+")
ENGLISH_ORDINAL = re.compile(r"\b\d+(?:st|nd|rd|th)\b")
TASHKEEL = re.compile("[\u064b-\u0652\u0670\u0640]")
ARABIZI_WORD = re.compile(r"\b[a-z]*[a-z][2357][a-z]*\b|\b[2357][a-z]+\b")
ARABIZI_COMMON = {
    "ba3d", "b3d", "jamb", "7ad", "7adde", "fo2", "ta7t", "abel", "2abel", "yamin", "shmel",
    "tabe2", "tabi2", "bineye", "binaye", "3al", "mn", "ta2ateh", "ma7al", "baddak", "fout",
    "lfo2", "awwal", "tene", "telit", "dekken", "ma3", "ra2em", "share3", "chare3",
}
LATIN_FOLDS = [("ch", "sh"), ("ou", "u"), ("oo", "u"), ("ee", "i"), ("ie", "i"), ("y", "i"), ("e", "i"), ("aa", "a")]
TOKEN_SYNONYMS = {"saint": "mar", "st": "mar", "sainte": "mar"}
ARABIC_INDIC = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

MIN_SCORE = 0.74
STRONG, PARTIAL = 0.93, 0.84


def _fold_latin(token: str) -> str:
    token = "".join(c for c in unicodedata.normalize("NFKD", token) if not unicodedata.combining(c))
    for a, b in LATIN_FOLDS:
        token = token.replace(a, b)
    return token


def normalize_token(token: str) -> str:
    token = unicodedata.normalize("NFKC", token).lower().translate(ARABIC_INDIC)
    if ARABIC_LETTERS.search(token):
        token = TASHKEEL.sub("", token)
        token = re.sub("[أإآٱ]", "ا", token)
        token = token.replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
        return token
    token = TOKEN_SYNONYMS.get(token, token)
    return _fold_latin(token)


def tokenize(text: str) -> list[tuple[str, int, int]]:
    """Return (normalised token, start, end) for each word in ``text``."""
    return [(normalize_token(m.group()), m.start(), m.end()) for m in TOKEN.finditer(text)]


def detect_language(text: str) -> str:
    arabic = len(ARABIC_LETTERS.findall(text))
    latin = len(LATIN_LETTERS.findall(text))
    if arabic and latin and min(arabic, latin) / max(arabic, latin) > 0.15:
        return "mixed"
    if arabic > latin:
        return "ar"
    lowered = ENGLISH_ORDINAL.sub(" ", text.lower())
    words = set(re.findall(r"[a-z0-9]+", lowered))
    if ARABIZI_WORD.search(lowered) or words & ARABIZI_COMMON:
        return "arabizi"
    return "en"


ORDINALS = {
    # English
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
    "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10, "ground": 0,
    # Arabizi
    "awwal": 1, "tene": 2, "teni": 2, "telit": 3, "talet": 3, "rebe3": 4, "khemis": 5, "ardi": 0,
    # Arabic (normalised)
    "الاول": 1, "الثاني": 2, "الثالث": 3, "الرابع": 4, "الخامس": 5, "السادس": 6,
    "السابع": 7, "الثامن": 8, "التاسع": 9, "العاشر": 10, "الارضي": 0,
}
FLOOR_PATTERNS = [
    re.compile(r"\b(\d{1,2})\s*(?:st|nd|rd|th)?\s+floor\b"),
    re.compile(r"\bfloor\s+(\d{1,2})\b"),
    re.compile(r"\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|ground)\s+floor\b"),
    re.compile(r"\b(?:tabe2|tabi2|tab2a)\s*(?:el\s*|l)?(\d{1,2}|awwal|tene|teni|telit|talet|rebe3|khemis|ardi)\b"),
    re.compile(r"\b(\d{1,2})\s*(?:tabe2|tabi2)\b"),
    re.compile(r"(?:الطابق|طابق)\s*(\d{1,2}|الاول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|الارضي)"),
]
COLOR_WORDS = {
    "green": "green", "red": "red", "white": "white", "yellow": "yellow", "blue": "blue",
    "beige": "beige", "grey": "grey", "gray": "grey", "brown": "brown", "orange": "orange",
    "pink": "pink", "black": "black",
    "akhdar": "green", "khadra": "green", "5adra": "green", "a7mar": "red", "7amra": "red",
    "abyad": "white", "bayda": "white", "asfar": "yellow", "safra": "yellow",
    "azra2": "blue", "zar2a": "blue", "rmede": "grey", "rsase": "grey", "bej": "beige",
    "اخضر": "green", "خضرا": "green", "الخضرا": "green", "احمر": "red", "حمرا": "red",
    "ابيض": "white", "بيضا": "white", "اصفر": "yellow", "صفرا": "yellow", "ازرق": "blue",
    "زرقا": "blue", "بيج": "beige", "رمادي": "grey", "رصاصي": "grey", "بني": "brown",
    "برتقالي": "orange", "زهري": "pink", "اسود": "black",
}


def extract_hints(text: str) -> dict:
    hints: dict = {}
    lowered = unicodedata.normalize("NFKC", text).lower().translate(ARABIC_INDIC)
    arabic_norm = " ".join(normalize_token(t) if ARABIC_LETTERS.search(t) else t for t in lowered.split())
    for pattern in FLOOR_PATTERNS:
        match = pattern.search(arabic_norm)
        if match:
            value = match.group(1)
            hints["floor"] = str(ORDINALS.get(value, value))
            break
    for word in re.findall(f"[0-9a-z{AR}]+", arabic_norm):
        if word in COLOR_WORDS:
            hints["building_color"] = COLOR_WORDS[word]
            break
    return hints


def _distinctive_tokens_match(alias: list[str], window: list[str]) -> bool:
    """Every longer alias word must look like some word in the window.

    Stops "Mar Elias church" from matching "Mar Charbel church" just because
    the generic words line up.
    """
    for token in alias:
        if len(token) < 4:
            continue
        if max(SequenceMatcher(None, token, w).ratio() for w in window) < 0.75:
            return False
    return True


class MockLandmarkResolver(LandmarkResolver):
    simulated = True

    def __init__(self) -> None:
        self._landmarks: dict[str, Landmark] = {}
        self._aliases: list[tuple[str, list[str]]] = []  # (landmark id, normalised alias tokens)
        for lid, name, name_ar, category, area, area_ar, lat, lng, aliases in LANDMARKS:
            self._landmarks[lid] = Landmark(lid, name, name_ar, category, area, area_ar, lat, lng)
            for alias in aliases:
                tokens = [t for t, _, _ in tokenize(alias)]
                if tokens:
                    self._aliases.append((lid, tokens))

    def get_landmark(self, landmark_id: str) -> Landmark | None:
        return self._landmarks.get(landmark_id)

    def resolve(self, text: str) -> Resolution:
        words = tokenize(text)
        best: dict[str, tuple[float, int, int, int]] = {}  # id -> (score, start, end, alias len)
        for lid, alias in self._aliases:
            n = len(alias)
            alias_str = " ".join(alias)
            short = n == 1 and len(alias_str) <= 4
            for i in range(0, len(words) - n + 1):
                window = words[i : i + n]
                window_str = " ".join(t for t, _, _ in window)
                if short:
                    score = 1.0 if window_str == alias_str else 0.0
                elif not _distinctive_tokens_match(alias, [t for t, _, _ in window]):
                    continue
                else:
                    score = SequenceMatcher(None, window_str, alias_str).ratio()
                if score < MIN_SCORE:
                    continue
                current = best.get(lid)
                candidate = (score, window[0][1], window[-1][2], n)
                if current is None or (score, n) > (current[0], current[3]):
                    best[lid] = candidate

        ranked = sorted(best.items(), key=lambda kv: (-round(kv[1][0], 1), -kv[1][3], kv[1][1]))[:3]
        candidates = [
            Candidate(
                landmark=self._landmarks[lid],
                score=score,
                quality="strong" if score >= STRONG else "partial" if score >= PARTIAL else "weak",
                matched_text=text[start:end],
            )
            for lid, (score, start, end, _) in ranked
        ]
        return Resolution(
            text=text,
            language=detect_language(text),
            candidates=candidates,
            hints=extract_hints(text),
            simulated=True,
        )
