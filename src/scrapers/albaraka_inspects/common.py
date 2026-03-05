import re
import time
import unicodedata
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple, List


def norm_text(s: str) -> str:
    s = (s or "").replace("\ufeff", "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s)
    return s


def parse_float_tn(s: str) -> Optional[float]:
    """Parse Tunisian formatted numbers.

    Supports:
      - "1 101.016" -> 1101.016
      - "100 000.000" -> 100000.0
      - "1 213,297" -> 1213.297
      - "2000.000 DT" -> 2000.0
      - "54.04%" -> 54.04
    """
    if s is None:
        return None
    t = str(s).replace("\ufeff", "").strip()
    if not t:
        return None
    t = t.replace("\xa0", " ")
    # keep digits, separators, minus
    # remove currency and percent signs
    t = t.replace("DT", "").replace("%", "")
    t = re.sub(r"[^0-9,\.\- ]", "", t)
    # remove spaces thousands separators
    t = t.replace(" ", "")
    # if both comma and dot exist, assume comma is thousands or decimal? On these pages:
    # - numbers like 1 213,297 (comma decimal)
    # - numbers like 100 000.000 (dot decimal)
    # We'll decide: if comma present and dot not present -> comma decimal
    # if both present -> remove thousands commas and keep dot
    if "," in t and "." not in t:
        t = t.replace(",", ".")
    elif "," in t and "." in t:
        # remove commas as thousands separators
        t = t.replace(",", "")
    m = re.search(r"-?\d+(?:\.\d+)?", t)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


def fill_number(page, selector: str, value: Any, timeout_ms: int = 30000):
    page.wait_for_selector(selector, state="visible", timeout=timeout_ms)
    page.fill(selector, "")
    page.fill(selector, str(value))
    # trigger input/change for Drupal/validation
    page.evaluate(
        """(sel)=>{
            const el=document.querySelector(sel);
            if(!el) return;
            el.dispatchEvent(new Event('input',{bubbles:true}));
            el.dispatchEvent(new Event('change',{bubbles:true}));
        }""",
        selector,
    )


def select_best_numeric_option(page, selector: str, desired: int, timeout_ms: int = 30000) -> int:
    page.wait_for_selector(selector, state="attached", timeout=timeout_ms)
    enabled_values = page.evaluate(
        """(sel)=>{
            const el=document.querySelector(sel);
            if(!el) return [];
            return Array.from(el.querySelectorAll('option'))
              .filter(o => o.value && o.value !== '0' && !o.disabled)
              .map(o => o.value);
        }""",
        selector,
    )
    nums = sorted({int(v) for v in enabled_values if str(v).isdigit()})
    if not nums:
        # fallback: try select anyway
        page.select_option(selector, str(desired))
        return desired

    if desired in nums:
        chosen = desired
    else:
        lower = [n for n in nums if n <= desired]
        chosen = max(lower) if lower else min(nums)

    page.select_option(selector, str(chosen))
    return chosen


def get_input_max(page, selector: str) -> Optional[float]:
    try:
        page.wait_for_selector(selector, state="attached", timeout=10000)
        m = page.eval_on_selector(selector, "el => el.getAttribute('max')")
        return parse_float_tn(m)
    except Exception:
        return None


def maybe_select_financement(page, slug: str, timeout_ms: int = 20000):
    """Select the financing type if the select exists.

    Some URLs already preselect it, but we keep it robust.
    """
    try:
        page.wait_for_selector("#type_financement", state="attached", timeout=timeout_ms)
        # only select if different / empty
        current = page.eval_on_selector("#type_financement", "el => el.value")
        if not current or current != slug:
            page.select_option("#type_financement", slug)
            time.sleep(0.15)
    except Exception:
        return


def click_calculate(page, timeout_ms: int = 30000):
    page.wait_for_selector("#calcul_simulateur", state="attached", timeout=timeout_ms)
    page.click("#calcul_simulateur", force=True)


def wait_box_recap(page, timeout_ms: int = 60000):
    page.wait_for_selector("#box-recap", state="attached", timeout=timeout_ms)
    page.wait_for_function(
        """() => {
            const box = document.querySelector('#box-recap');
            if(!box) return false;
            const li = box.querySelectorAll('ul.liste-value li');
            return li && li.length >= 3;
        }""",
        timeout=timeout_ms,
    )
    time.sleep(0.15)


@dataclass
class RecapResult:
    monthly_payment: Optional[float]
    requested_amount: Optional[float]
    duration_months: Optional[int]
    cmr_percent: Optional[float]
    cmr_ok: Optional[bool]
    fees: Optional[float]
    raw_text: str


def extract_recap(page) -> RecapResult:
    wait_box_recap(page)

    data = page.evaluate(
        """() => {
            const box = document.querySelector('#box-recap');
            if(!box) return null;

            const lis = Array.from(box.querySelectorAll('ul.liste-value li'))
              .map(li => (li.textContent || '').replace(/\s+/g,' ').trim());

            const percent = (box.querySelector('.chiffre span')?.textContent || '').replace(/\s+/g,' ').trim();

            // cmr label is inside a strong tag in the same column
            const cmrLabel = (box.querySelector('.chiffre p strong')?.textContent || '').replace(/\s+/g,' ').trim();

            // fees are in the last column .col-md-2 .chiffre span (second one)
            const spans = Array.from(box.querySelectorAll('.col-md-2 .chiffre span')).map(s => (s.textContent||'').replace(/\s+/g,' ').trim());
            const fees = spans.length ? spans[spans.length - 1] : '';

            return {lis, percent, cmrLabel, fees, raw: box.innerText || ''};
        }"""
    )

    if not data:
        return RecapResult(None, None, None, None, None, None, "")

    lis: List[str] = data.get("lis") or []
    percent_s: str = data.get("percent") or ""
    cmr_label: str = data.get("cmrLabel") or ""
    fees_s: str = data.get("fees") or ""
    raw: str = data.get("raw") or ""

    monthly = None
    requested = None
    duration_months = None

    for li in lis:
        t = norm_text(li)
        if "remboursement mensuel" in t:
            # after ':'
            parts = li.split(":", 1)
            monthly = parse_float_tn(parts[1] if len(parts) > 1 else li)
        elif "financement sollicite" in t:
            requested = parse_float_tn(li)
        elif t.startswith("duree") or "duree" in t:
            # contains "240 mois" etc.
            m = re.search(r"(\d+)\s*mois", t)
            if m:
                try:
                    duration_months = int(m.group(1))
                except Exception:
                    duration_months = None

    cmr_percent = parse_float_tn(percent_s)
    cmr_ok = None
    cmr_norm = norm_text(cmr_label)
    if "suffisante" in cmr_norm:
        cmr_ok = True
    if "insuffisante" in cmr_norm:
        cmr_ok = False

    fees = parse_float_tn(fees_s)

    return RecapResult(
        monthly_payment=monthly,
        requested_amount=requested,
        duration_months=duration_months,
        cmr_percent=cmr_percent,
        cmr_ok=cmr_ok,
        fees=fees,
        raw_text=raw,
    )
