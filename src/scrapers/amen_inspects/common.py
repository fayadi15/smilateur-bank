import re
import time
import unicodedata
from typing import Optional, Dict, Any, Tuple


AMEN_PRE_SALAIRE_URL = "https://www.amenbank.com.tn/fr/simulateur-pre-salaire-amenagement.html"
AMEN_AUTO_INVEST_URL = "https://www.amenbank.com.tn/fr/simulateur-auto-invest.html"
AMEN_CREDIM_URL = "https://www.amenbank.com.tn/fr/simulateur-credim-watani.html"


def norm_text(s: str) -> str:
    s = (s or "").replace("\ufeff", "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s


def parse_float_fr(s: str) -> Optional[float]:
    """Parse number formatted with spaces and decimal comma/dot."""
    if s is None:
        return None
    t = str(s).replace("\ufeff", "").strip()
    if not t:
        return None
    t = t.replace("\xa0", " ").replace(" ", "")
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


def click_calculate(page, timeout_ms: int = 30000):
    # Button: <button class="Calculate ...">Lancez le calcul</button>
    page.wait_for_selector("button.Calculate", state="attached", timeout=timeout_ms)
    page.click("button.Calculate", force=True)


def wait_results(page, timeout_ms: int = 60000):
    # results are injected into #results as a table
    page.wait_for_selector("#results", state="attached", timeout=timeout_ms)
    page.wait_for_function(
        """() => {
            const r = document.querySelector('#results');
            if(!r) return false;
            const tb = r.querySelector('table');
            if(!tb) return false;
            const rows = tb.querySelectorAll('tr');
            return rows && rows.length >= 6;
        }""",
        timeout=timeout_ms,
    )
    time.sleep(0.15)


def extract_kv_from_results(page) -> Dict[str, str]:
    """Extract key/value rows from the results table inside #results."""
    return page.evaluate(
        """() => {
            const out = {};
            const r = document.querySelector('#results');
            if(!r) return out;
            const tb = r.querySelector('table');
            if(!tb) return out;
            const rows = Array.from(tb.querySelectorAll('tr'));
            for (const tr of rows) {
              const tds = tr.querySelectorAll('td');
              if (tds.length === 2) {
                const k = (tds[0].innerText || '').trim();
                const v = (tds[1].innerText || '').trim();
                if (k) out[k] = v;
              }
            }
            return out;
        }"""
    )


def get_selected_option_text(page, selector: str) -> Optional[str]:
    try:
        return page.evaluate(
            """(sel)=>{
                const el=document.querySelector(sel);
                if(!el) return null;
                const opt = el.options[el.selectedIndex];
                return opt ? (opt.textContent||'').trim() : null;
            }""",
            selector,
        )
    except Exception:
        return None


def choose_periodicity_value(profile: Dict[str, Any]) -> str:
    """Amen periodicity values: 1=month, 3=trimestre, 6=semestre, 12=année."""
    v = profile.get("amen_periodicity")
    if v is None:
        # default to monthly to return a true monthly payment
        return "1"
    try:
        iv = int(v)
        if iv in (1, 3, 6, 12):
            return str(iv)
    except Exception:
        pass
    return "1"


def months_per_period(period_value: str) -> int:
    try:
        iv = int(period_value)
        return iv if iv in (1, 3, 6, 12) else 1
    except Exception:
        return 1


def choose_duration_years(profile: Dict[str, Any]) -> int:
    """Amen uses dfund as duration in years (based on result label)."""
    if profile.get("amen_duration_years") is not None:
        try:
            y = int(float(profile["amen_duration_years"]))
            return max(1, min(50, y))
        except Exception:
            pass

    n_months = profile.get("duree_mois")
    if n_months is None:
        # fallback
        return 5
    try:
        n = int(float(n_months))
    except Exception:
        return 5
    # ceil to ensure non-zero
    return max(1, min(50, (n + 11) // 12))


def choose_amount(profile: Dict[str, Any]) -> int:
    v = profile.get("montant_pret_demande") or profile.get("amount") or profile.get("montant")
    try:
        return max(0, int(float(v)))
    except Exception:
        return 0


def normalize_sim_name(s: str) -> str:
    return norm_text(s).replace(" ", "").replace("-", "").replace("_", "")


def get_result_fields(page, period_value: str) -> Tuple[Optional[float], Optional[float], Optional[float], Dict[str, str]]:
    """Return (echeance_periodique, monthly_equivalent, taux, kv_map)."""
    kv = extract_kv_from_results(page)

    # find keys robustly (French accents)
    taux = None
    echeance = None
    for k, v in kv.items():
        kn = norm_text(k)
        if "taux" in kn:
            taux = parse_float_fr(v)
        if "echeanc" in kn:
            echeance = parse_float_fr(v)

    monthly = None
    if echeance is not None:
        monthly = echeance / float(months_per_period(period_value))

    return echeance, monthly, taux, kv
