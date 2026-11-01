"""Keyword policy gate. The first matching rule wins. No model call."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import Settings

FACTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("expense_ratio", ("expense ratio",)),
    ("exit_load", ("exit load",)),
    ("minimum_sip", ("minimum sip", "min sip")),
    ("minimum_lumpsum", ("minimum lump sum", "minimum lumpsum", "lump sum", "lumpsum")),
    ("lock_in", ("lock-in", "lock in")),
    ("riskometer", ("riskometer", "risk-o-meter")),
    ("benchmark", ("benchmark",)),
    ("investment_objective", ("investment objective",)),
    ("category", ("sub-category", "subcategory", "category")),
    ("factsheet_link", ("scheme information document", "factsheet", "fact sheet")),
    ("fund_manager", ("fund manager", "fund managers")),
    ("holdings", ("holding", "holdings")),
    ("nav", ("nav", "net asset value")),
    ("aum", ("aum", "assets under management", "asset under management")),
    ("returns", ("return", "returns")),
    ("launch_date", ("launch date", "launched", "inception")),
    ("stamp_duty", ("stamp duty",)),
    ("isin", ("isin",)),
    ("tax_note", ("taxed", "taxation", "tax implication", "tax impact", "tax if")),
    ("base_expense_ratio", ("base expense ratio",)),
    ("portfolio_turnover", ("portfolio turnover", "turnover")),
)

FACT_LABELS = {
    "expense_ratio": "expense ratio",
    "exit_load": "exit load",
    "minimum_sip": "minimum sip",
    "minimum_lumpsum": "lump sum",
    "lock_in": "lock-in",
    "riskometer": "riskometer",
    "benchmark": "benchmark",
    "investment_objective": "investment objective",
    "category": "category",
    "factsheet_link": "scheme information document",
    "statement_download": "capital-gains statement",
    "amc_overview": "hdfc mutual fund",
}

OTHER_AMCS = (
    "parag parikh",
    "ppfas",
    "sbi mutual",
    "axis mutual",
    "icici prudential",
    "nippon",
    "kotak mutual",
    "mirae",
    "uti",
    "aditya birla",
    "motilal",
    "tata mutual",
    "franklin",
    "dsp",
    "canara robeco",
    "bandhan",
    "edelweiss",
    "invesco",
    "pgim",
    "whiteoak",
    "hsbc",
    "sundaram",
    "quantum",
    "samco",
    "bajaj finserv",
)

PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)
AADHAAR_RE = re.compile(r"\b(?:\d{4}[\s-]?){2}\d{4}\b")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?:\+91[\s-]?)?\b[6-9]\d{9}\b")
OTP_RE = re.compile(r"\b(?:otp|pan|folio|account)\b.{0,24}\b\d{4,8}\b", re.IGNORECASE)
JAILBREAK = ("ignore your rules", "ignore all rules", "developer mode", "act as an advisor", "act as an adviser")
PERFORMANCE = ("alpha", "ranking", "which is best", "which one is best", "highest", "outperform")
PORTFOLIO = ("salary", "allocation", "how much")
ADVICE = ("should i", "should we", "buy", "sell", "hold", "recommend")


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    scheme_name: str
    fact_types: tuple[str, ...]
    question_redacted: str


def redact(question: str) -> str:
    text = PAN_RE.sub("[redacted]", question)
    text = AADHAAR_RE.sub("[redacted]", text)
    text = EMAIL_RE.sub("[redacted]", text)
    text = PHONE_RE.sub("[redacted]", text)
    text = OTP_RE.sub("[redacted]", text)
    return text


def _has(text: str, phrase: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text) is not None


def _pii(text: str) -> bool:
    return any(pattern.search(text) for pattern in (PAN_RE, AADHAAR_RE, EMAIL_RE, PHONE_RE, OTP_RE))


def _schemes(question: str, settings: Settings) -> list:
    text = question.lower()
    found = []
    for scheme in settings.schemes:
        names = (scheme.scheme_name.lower(), *(alias.lower() for alias in scheme.aliases))
        if any(_has(text, name) for name in names):
            found.append(scheme)
    return found


def _facts(text: str) -> tuple[str, ...]:
    found = []
    for fact_type, phrases in FACTS:
        if any(_has(text, phrase) for phrase in phrases):
            found.append(fact_type)
    return tuple(found)


def _other_amc(text: str) -> bool:
    return any(_has(text, name) for name in OTHER_AMCS)


def classify(question: str, settings: Settings) -> Decision:
    redacted = redact(question)
    text = question.lower()
    schemes = _schemes(question, settings)
    facts = _facts(text)
    scheme_name = schemes[0].scheme_name if len(schemes) == 1 else ""

    def decision(action: str, reason: str, fact_types: tuple[str, ...] = ()) -> Decision:
        return Decision(action, reason, scheme_name if action != "narrow" else "", fact_types, redacted)

    if _pii(question):
        return decision("refuse", "pii")
    if any(phrase in text for phrase in JAILBREAK):
        return decision("refuse", "jailbreak")
    if _other_amc(text):
        return decision("refuse", "out_of_corpus")
    if any(_has(text, phrase) for phrase in PERFORMANCE):
        return decision("refuse", "performance")

    advice = any(_has(text, phrase) for phrase in ADVICE)
    portfolio = any(_has(text, phrase) for phrase in PORTFOLIO)
    if (advice or portfolio) and not facts:
        return decision("refuse", "portfolio" if portfolio and not advice else "advice")
    if (advice or portfolio) and facts and len(schemes) == 1:
        return decision("answer_with_refusal", "fact", facts)
    if (advice or portfolio) and facts:
        return decision("narrow", "narrow", facts)

    statement = "capital-gain" in text or "capital gain" in text or "tax statement" in text
    if statement and not facts:
        return decision("answer", "statement_download", ("statement_download",))
    if not facts and any(_has(text, phrase) for phrase in ("fund house", "amc", "about hdfc mutual fund")):
        return decision("answer", "amc_overview", ("amc_overview",))
    if len(schemes) > 1:
        return decision("narrow", "narrow", facts)
    if facts and len(schemes) != 1:
        return decision("narrow", "narrow", facts)
    if len(schemes) == 1:
        return decision("answer", "fact" if facts else "page", facts)
    return decision("answer", "page", ())
