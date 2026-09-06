from __future__ import annotations
import re
from dataclasses import dataclass

# This module is deliberately input-format agnostic: PDF, CSV cells and pasted
# text all reach the same normalized economic-clause representation.

NUMBER_WITH_UNIT = re.compile(
    r"(?:[-+]?\d+(?:[.,]\d+)?)\s*(?:%|points?|milliards?|millions?|MD\b|"
    r"[A-Z]{3}\b|dinars?|dollars?|euros?|pesos?|roupies?|couronnes?|francs?\s+CFA|"
    r"نقطة\s+مئوية|مليارات?|مليار|ملايين|مليون|دراهم?|درهم|دنانير|دينار)",
    re.I,
)

ECONOMIC_TERMS = re.compile(
    r"\b(?:PIB|croissance|inflation|prix|ch[oô]mage|dette|endettement|d[eé]ficit|"
    r"solde|exportations?|importations?|r[eé]serves?|investissements?|IDE|"
    r"recettes?|d[eé]penses?|compte courant|taux d['’]?activit[eé]|"
    r"الناتج|النمو|التضخم|البطالة|الميزانية|الصادرات|الواردات|الحساب\s+الجاري|"
    r"الاستثمارات|الفائدة|الاحتياطيات)\b", re.I,
)

# Independent discourse boundaries. Comparison markers are intentionally absent.
STRONG_BOUNDARY = re.compile(
    r"\s*;\s*|"
    r"\s+(?:tandis\s+qu(?:e|[’'])|alors\s+que|whereas|while|en revanche|par ailleurs|"
    r"بينما|في\s+حين|وفي\s+الوقت\s+نفسه)\s*",
    re.I,
)

# A coordinated clause may contain several independent indicator/value pairs:
# "recettes 4 120, dépenses 5 040 et déficit 4,8 %".
INDICATOR_HEAD = (
    r"(?:les?\s+)?(?:recettes?|d[eé]penses?|exportations?|importations?|"
    r"r[eé]serves?|investissements?\s+directs?\s+[ée]trangers?|IDE|"
    r"dette|endettement|d[eé]ficit|solde|inflation|ch[oô]mage|croissance|PIB|"
    r"compte\s+courant|taux\s+d['’]activit[eé]|الناتج\s+المحلي|النمو|التضخم|"
    r"البطالة|عجز\s+الميزانية|الصادرات|الواردات|الحساب\s+الجاري|الاستثمارات|"
    r"سعر\s+الفائدة|الاحتياطيات)"
)
COORDINATE_BOUNDARY = re.compile(
    rf"\s*(?:,\s*|\s+et\s+|\s+ainsi\s+que\s+)(?={INDICATOR_HEAD}\b)", re.I
)

# Markers that semantically couple two sides and therefore forbid a split.
COUPLERS = re.compile(
    r"\b(?:contre|compar[ée]s?\s+[àa]|compared\s+(?:with|to)|apr[eè]s|after|"
    r"avant|before|passant\s+de|from\s+.+?\s+to|respectivement|respectively|"
    r"مقابل|مقارنة|بعد|قبل|من\s+.+?\s+إلى|الفترة\s+نفسها)\b", re.I
)

@dataclass(frozen=True)
class EconomicClause:
    text: str
    index: int
    start: int
    end: int
    parent_text: str

def _has_economic_measure(text: str) -> bool:
    return bool(NUMBER_WITH_UNIT.search(text or "")) and bool(ECONOMIC_TERMS.search(text or ""))

def _candidate_cuts(raw: str) -> list[tuple[int,int]]:
    cuts=[]
    for rx in (STRONG_BOUNDARY, COORDINATE_BOUNDARY):
        cuts.extend((m.start(),m.end()) for m in rx.finditer(raw))
    return sorted(set(cuts))

def split_economic_clauses(text: str) -> list[EconomicClause]:
    """Split a sentence into independent economic propositions.

    A split is accepted only when both sides can stand as economic events.
    Comparison expressions stay intact. This is intentionally generic and is
    shared by PDF, CSV and pasted-text ingestion.
    """
    raw=(text or "").strip()
    if not raw:
        return []

    accepted=[]
    cursor=0
    candidates=[]
    for rx,kind in ((STRONG_BOUNDARY,"strong"),(COORDINATE_BOUNDARY,"coordinate")):
        candidates.extend((m.start(),m.end(),kind) for m in rx.finditer(raw))
    for start,end,kind in sorted(candidates):
        if start < cursor:
            continue
        left=raw[cursor:start].strip()
        right=raw[end:].strip()
        # Strong discourse boundaries may separate two coreferential economic
        # events ("..., tandis qu'elle ..."). The parent sentence has already
        # passed economic filtering, so two measured sides are sufficient.
        if kind == "strong":
            both_explicit = _has_economic_measure(left) and _has_economic_measure(right)
            right_coreferential = bool(re.search(
                r"^(?:(?:en|au|pour)\b.{0,45})?\s*(?:elle|il|elles|ils|ce taux|ce niveau|cette valeur)\b",
                right, re.I
            ))
            coreferential_pair = (
                NUMBER_WITH_UNIT.search(left) and NUMBER_WITH_UNIT.search(right)
                and right_coreferential and not ECONOMIC_TERMS.search(right)
            )
            if not (both_explicit or coreferential_pair):
                continue
        elif not (_has_economic_measure(left) and _has_economic_measure(right)):
            continue
        # "respectivement" needs the indicator order from the left clause.
        local=raw[max(0,start-55):min(len(raw),end+75)]
        if COUPLERS.search(local) and re.search(r"\brespectivement\b|\brespectively\b", right, re.I):
            continue
        accepted.append((start,end))
        cursor=end

    if not accepted:
        return [EconomicClause(raw,0,0,len(raw),raw)]

    clauses=[]
    last=0
    for start,end in accepted:
        piece=raw[last:start].strip(" ,;")
        if piece:
            actual=raw.find(piece,last,start)
            clauses.append(EconomicClause(piece,len(clauses),actual,actual+len(piece),raw))
        last=end
    piece=raw[last:].strip(" ,;")
    if piece:
        actual=raw.find(piece,last)
        clauses.append(EconomicClause(piece,len(clauses),actual,actual+len(piece),raw))
    return clauses or [EconomicClause(raw,0,0,len(raw),raw)]

def local_measure_window(text: str, start: int, end: int, radius: int = 100) -> str:
    left=max(text.rfind(";",0,start),0)
    left=left+1 if left>0 else 0
    right_semicolon=text.find(";",end)
    right=right_semicolon if right_semicolon>=0 else len(text)
    return text[max(left,start-radius):min(right,end+radius)]
