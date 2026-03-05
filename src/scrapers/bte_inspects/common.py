import re
import time
import unicodedata
from typing import Optional, Dict, Any, List, Tuple


BTE_URL = "https://www.bte.com.tn/fr/nos-simulateurs/simulateur-de-credit"


def norm_text(s: str) -> str:
    s = (s or "").replace("\ufeff", "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s


def parse_float_fr(s: str) -> Optional[float]:
    """Parse a Tunisian/French formatted number.

    Examples:
      "1 213,297" -> 1213.297
      "0,000" -> 0.0
    """
    if s is None:
        return None
    t = str(s).replace("\ufeff", "").strip()
    if not t:
        return None
    # remove NBSP and spaces
    t = t.replace("\xa0", " ").replace(" ", "")
    # French decimal comma
    t = t.replace(",", ".")
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
    # trigger change/input to satisfy JS validation
    page.evaluate(
        """(sel)=>{
            const el=document.querySelector(sel);
            if(!el) return;
            el.dispatchEvent(new Event('input',{bubbles:true}));
            el.dispatchEvent(new Event('change',{bubbles:true}));
        }""",
        selector,
    )


def select_option(page, selector: str, value: str, timeout_ms: int = 30000):
    page.wait_for_selector(selector, state="visible", timeout=timeout_ms)
    page.select_option(selector, value)


def click_submit(page, timeout_ms: int = 30000):
    # the form uses <input type="submit" ... value="Valider">
    page.wait_for_selector("form#myForm input[type='submit']", state="attached", timeout=timeout_ms)
    page.click("form#myForm input[type='submit']", force=True)


def wait_result_table(page, timeout_ms: int = 60000):
    # results appear as table#tbcr
    page.wait_for_selector("#tbcr", state="attached", timeout=timeout_ms)
    page.wait_for_function(
        """() => {
            const tb = document.querySelector('#tbcr');
            if(!tb) return false;
            const rows = tb.querySelectorAll('tbody tr');
            return rows && rows.length >= 2;
        }""",
        timeout=timeout_ms,
    )
    time.sleep(0.15)


RATE_BY_LOAN_TYPE = {
    "AUTO": 10.5,
    "IMMO": 8.5,
    "CONSO": 12.0,
    "VOYAGE": 12.0,
}


def choose_interest_rate_percent(profile: Dict[str, Any]) -> float:
    """BTE simulator requires the rate as an input.

    We use, in priority:
      - profile['bte_interest_rate'] (if user provided)
      - mapping by loan_type
      - fallback 10.0
    """
    v = profile.get("bte_interest_rate")
    try:
        if v is not None:
            return float(v)
    except Exception:
        pass

    loan_type = (profile.get("loan_type") or "").upper()
    return float(RATE_BY_LOAN_TYPE.get(loan_type, 10.0))


def months_to_years_months(total_months: int) -> Tuple[int, int]:
    if total_months is None:
        return 0, 0
    try:
        m = int(total_months)
    except Exception:
        return 0, 0
    if m < 0:
        m = 0
    return m // 12, m % 12


def get_input_value_float(page, selector: str) -> Optional[float]:
    page.wait_for_selector(selector, state="attached", timeout=20000)
    val = page.eval_on_selector(selector, "el => el.value")
    return parse_float_fr(val)


def extract_schedule_and_totals(page) -> Tuple[List[Dict[str, Any]], Dict[str, Optional[float]]]:
    """Extract schedule rows and totals from the #tbcr table."""
    wait_result_table(page)

    rows = page.evaluate(
        """() => {
            const tb = document.querySelector('#tbcr');
            if(!tb) return {rows: [], total: null};
            const trs = Array.from(tb.querySelectorAll('tbody tr'));
            const out = [];
            let totalRow = null;

            for(const tr of trs){
                const tds = Array.from(tr.querySelectorAll('td'));
                // Total row has colspan=2 in first cell and only 4 other cells
                if(tds.length >= 4 && tds[0].getAttribute('colspan') === '2'){
                    totalRow = tds.map(td => (td.textContent || '').trim());
                    continue;
                }
                if(tds.length < 6) continue;
                out.push(tds.map(td => (td.textContent || '').trim()));
            }
            return {rows: out, total: totalRow};
        }"""
    )

    schedule: List[Dict[str, Any]] = []
    for r in rows.get("rows", []) or []:
        # columns: N°, Echéance, Principal, Val.Rés., Intérêts, Mensualité
        num = parse_float_fr(r[0])
        schedule.append(
            {
                "num": int(num) if num is not None else None,
                "echeance": (r[1] or "").replace("\xa0", " ").strip(),
                "principal": parse_float_fr(r[2]),
                "val_res": parse_float_fr(r[3]),
                "interets": parse_float_fr(r[4]),
                "mensualite": parse_float_fr(r[5]),
            }
        )

    totals: Dict[str, Optional[float]] = {}
    totalRow = rows.get("total")
    if totalRow:
        # totalRow looks like: ["Total", "100 000,000", "", "46 253,174", "146 253,174"]
        # indexes: 0 label, 1 principal total, 2 empty, 3 interests, 4 payments
        totals = {
            "total_principal": parse_float_fr(totalRow[1]) if len(totalRow) > 1 else None,
            "total_interest": parse_float_fr(totalRow[3]) if len(totalRow) > 3 else None,
            "total_payment": parse_float_fr(totalRow[4]) if len(totalRow) > 4 else None,
        }

    return schedule, totals


def pick_regular_payment(schedule: List[Dict[str, Any]]) -> Optional[float]:
    """Pick a representative periodic payment.

    The first row can be an interest-only line (principal=0). We take the most frequent
    mensualite among rows excluding the first one.
    """
    if not schedule:
        return None

    payments: List[float] = []
    for r in schedule:
        m = r.get("mensualite")
        if m is None:
            continue
        num = r.get("num")
        # skip the first line if it looks like interest-only
        if num == 1 and (r.get("principal") in (None, 0.0)):
            continue
        payments.append(float(m))

    if not payments:
        payments = [float(r["mensualite"]) for r in schedule if r.get("mensualite") is not None]

    if not payments:
        return None

    # mode by rounding to 3 decimals (table uses 3 decimals)
    buckets: Dict[float, int] = {}
    for p in payments:
        k = round(p, 3)
        buckets[k] = buckets.get(k, 0) + 1
    best = sorted(buckets.items(), key=lambda kv: (-kv[1], -kv[0]))[0][0]
    return float(best)
