import re
import time
import unicodedata
from typing import Optional, Dict, Any, Tuple


def norm_text(s: str) -> str:
    s = (s or "").replace("\ufeff", "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s)
    return s


def clean_label(label: str) -> str:
    """Normalize BH labels so we can use them as dict keys."""
    t = norm_text(label)
    t = t.replace("(*)", "")
    t = t.replace("*", "")
    t = t.replace(":", "")
    t = t.replace("’", "'")
    t = t.strip()
    return t


def parse_float_fr(s: str) -> Optional[float]:
    """Parse Tunisian formatted numbers: '10 000,000 TND' -> 10000.0"""
    if not s:
        return None
    t = (s or "").replace("\ufeff", "").strip()
    # remove currency and words
    t = re.sub(r"(?i)\b(tnd|dt|dinar|dinars|mois|an|ans|%|/|par)\b", " ", t)
    t = t.replace(" ", "")
    t = t.replace("\u00a0", "")
    t = t.replace(",", ".")
    m = re.search(r"-?\d+(?:\.\d+)?", t)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


def fill_text(page, selector: str, value: Any, timeout_ms: int = 20000):
    page.wait_for_selector(selector, state="visible", timeout=timeout_ms)
    page.fill(selector, str(value))
    # trigger JS listeners
    page.evaluate(
        """(sel) => {
            const el = document.querySelector(sel);
            if (!el) return;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
        }""",
        selector,
    )


def select_option(page, selector: str, value: str, timeout_ms: int = 20000):
    page.wait_for_selector(selector, state="visible", timeout=timeout_ms)
    page.select_option(selector, str(value))


def check_radio(page, selector: str, timeout_ms: int = 20000):
    # radio est souvent hidden sur BH (UI custom)
    page.wait_for_selector(selector, state="attached", timeout=timeout_ms)
    try:
        page.check(selector, force=True)
    except Exception:
        # fallback: cliquer sur le label associé si existe
        sel_id = selector.replace("#", "")
        lbl = f"label[for='{sel_id}']"
        page.wait_for_selector(lbl, state="attached", timeout=timeout_ms)
        page.click(lbl, force=True)


def click_calculer(page, timeout_ms: int = 20000):
    page.wait_for_selector("#btn_simulation", state="visible", timeout=timeout_ms)
    page.click("#btn_simulation")


def wait_result(page, timeout_ms: int = 30000):
    """Wait until BH simulator renders results (any of the result containers becomes visible & non-empty)."""
    page.wait_for_function(
        """() => {
            const ids = ['#details', '#details2', '#details3', '#details4', '#result_simulateur'];
            const isVisible = (el) => {
                if (!el) return false;
                const st = window.getComputedStyle(el);
                return st && st.display !== 'none' && st.visibility !== 'hidden' && el.offsetParent !== null;
            };
            for (const sel of ids) {
                const el = document.querySelector(sel);
                if (!isVisible(el)) continue;
                const txt = (el.textContent || '').trim();
                if (txt.length > 0 && /\d/.test(txt)) return true;
            }
            // fallback: any .cadre_sim shown
            const cs = document.querySelector('.cadre_sim');
            if (isVisible(cs)) {
                const txt = (cs.textContent || '').trim();
                return txt.length > 0 && /\d/.test(txt);
            }
            return false;
        }""",
        timeout=timeout_ms,
    )
    time.sleep(0.15)


def extract_kv(page) -> Dict[str, str]:
    """Extract (label -> value) pairs from the rendered result blocks."""
    data = page.evaluate(
        """() => {
            const root = document.querySelector('#simprint') || document;
            const out = [];

            const labelEls = Array.from(root.querySelectorAll('.color_label'));
            for (const span of labelEls) {
                const label = (span.textContent || '').trim();
                const left = span.closest('.simulateur_left');
                let right = null;
                if (left) {
                    // nextElementSibling may be a border_bottom; skip those
                    let sib = left.nextElementSibling;
                    while (sib && sib.classList && sib.classList.contains('border_bottom')) {
                        sib = sib.nextElementSibling;
                    }
                    if (sib && sib.classList && sib.classList.contains('simulateur_right')) {
                        right = sib;
                    }
                }
                const value = right ? (right.textContent || '').trim() : '';
                if (label && value) out.push([label, value]);
            }

            // also pick some single-line infos that don't follow the left/right pattern (ex: refusal message)
            const details = document.querySelector('#details');
            const detailsTxt = details ? (details.textContent || '').trim() : '';

            return { pairs: out, detailsTxt };
        }"""
    )

    kv: Dict[str, str] = {}
    for label, value in (data or {}).get("pairs", []) or []:
        k = clean_label(label)
        if not k:
            continue
        # keep first occurrence, but allow later overwrite if earlier empty
        if k not in kv or not kv[k]:
            kv[k] = value

    # store raw details text (useful for refusal message)
    dt = (data or {}).get("detailsTxt") or ""
    if dt:
        kv["__details_text"] = dt

    return kv


def extract_full_text(page) -> str:
    root_sel = "#simprint"
    try:
        txt = (page.text_content(root_sel) or "").strip()
        return re.sub(r"\s+", " ", txt)
    except Exception:
        return ""


def pick_value(kv: Dict[str, str], *keys: str) -> Optional[str]:
    """Return first matching key in kv (exact key after clean_label), otherwise fuzzy contains."""
    for k in keys:
        ck = clean_label(k)
        if ck in kv and kv[ck]:
            return kv[ck]
    # fuzzy contains
    for k in keys:
        ck = clean_label(k)
        for kk, vv in kv.items():
            if kk.startswith("__"):
                continue
            if ck and ck in kk and vv:
                return vv
    return None


def safe_float(kv: Dict[str, str], *keys: str) -> Optional[float]:
    v = pick_value(kv, *keys)
    return parse_float_fr(v) if v else None


def categorize_from_profile(profile: Dict[str, Any]) -> str:
    """Map profile statut/age to BH categorie select values."""
    # Allow explicit override
    if profile.get("bh_categorie"):
        return str(profile["bh_categorie"])

    statut = norm_text(str(profile.get("statut_pro", "")))
    age = int(profile.get("age") or profile.get("age_client") or 0)

    # BH options: 80 Profession libérale, 82 Salarié, 81 Seniors, 84 TRE
    if "resident" in statut and "etranger" in statut:
        return "84"
    if "profession" in statut and "lib" in statut:
        return "80"
    if "retrait" in statut or age >= 60:
        return "81"
    return "82"


def clamp_years(years: int, min_years: int, max_years: int) -> int:
    years = int(years)
    if years < min_years:
        return min_years
    if years > max_years:
        return max_years
    return years


def months_to_years(duree_mois: Any, min_years: int, max_years: int) -> int:
    try:
        m = int(float(duree_mois))
    except Exception:
        m = min_years * 12
    y = int(round(m / 12))
    if y <= 0:
        y = min_years
    return clamp_years(y, min_years, max_years)


def infer_credit_amount_from_price(price: float, credit_ratio: float = 0.6) -> float:
    return max(0.0, float(price) * float(credit_ratio))


def price_from_credit_amount(credit_amount: float, credit_ratio: float = 0.6) -> float:
    if credit_ratio <= 0:
        return float(credit_amount)
    return float(credit_amount) / float(credit_ratio)


def cost_from_credit_amount(credit_amount: float, min_apport_ratio: float = 0.2) -> Tuple[float, float]:
    """Return (project_cost, apport) so that credit = cost - apport with apport >= ratio."""
    r = float(min_apport_ratio)
    if r < 0:
        r = 0.0
    if r >= 1:
        r = 0.2
    cost = float(credit_amount) / (1.0 - r)
    apport = cost * r
    return cost, apport

# ---------- implicit annual rate (fallback) ----------

def _monthly_payment_from_rate(P: float, n: int, r_month: float) -> float:
    if n <= 0:
        return float("inf")
    if abs(r_month) < 1e-12:
        return P / n
    return P * r_month / (1.0 - (1.0 + r_month) ** (-n))


def estimate_annual_rate_percent(P: float, n: int, A: float) -> float:
    """Binary-search monthly rate so ann_rate ~= 12*r_month."""
    if P <= 0 or n <= 0 or A <= 0:
        return 0.0
    if A <= (P / n) + 1e-6:
        return 0.0

    lo, hi = 0.0, 0.05
    while hi < 2.0 and _monthly_payment_from_rate(P, n, hi) < A:
        hi *= 2.0

    for _ in range(80):
        mid = (lo + hi) / 2.0
        if _monthly_payment_from_rate(P, n, mid) < A:
            lo = mid
        else:
            hi = mid

    r_month = (lo + hi) / 2.0
    return round(r_month * 12.0 * 100.0, 2)

def select_best_numeric_option(page, selector: str, desired: int, timeout_ms: int = 20000) -> int:
    page.wait_for_selector(selector, state="attached", timeout=timeout_ms)

    enabled_values = page.evaluate(
        """(sel) => {
            const el = document.querySelector(sel);
            if (!el) return [];
            return Array.from(el.querySelectorAll('option'))
              .filter(o => o.value && !o.disabled)
              .map(o => o.value);
        }""",
        selector,
    )

    nums = sorted({int(v) for v in enabled_values if str(v).isdigit()})
    if not nums:
        raise RuntimeError(f"No enabled options for {selector}")

    if desired in nums:
        chosen = desired
    else:
        lower = [n for n in nums if n <= desired]
        chosen = max(lower) if lower else min(nums)

    page.select_option(selector, str(chosen))
    return chosen