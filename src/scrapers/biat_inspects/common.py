import re
import time
from typing import Optional, Tuple


def clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def parse_int(text: str) -> Optional[int]:
    if not text:
        return None
    digits = re.sub(r"[^\d]", "", text)
    if not digits:
        return None
    try:
        return int(digits)
    except Exception:
        return None


def parse_monthly_payment(text: str) -> Optional[float]:
    """
    Ex:
      "Remboursement mensuel: 460 dinars / mois"
      "Remboursement mensuel: 467 dinars."
    """
    if not text:
        return None
    m = re.search(r"Remboursement\s+mensuel\s*:?\s*(\d[\d\s]*)", text, flags=re.I)
    if not m:
        m = re.search(r"(\d[\d\s]*)", text)
    if not m:
        return None
    return float(m.group(1).replace(" ", ""))


def fill_text(page, selector: str, value: str, timeout_ms: int = 20000):
    page.wait_for_selector(selector, state="visible", timeout=timeout_ms)
    page.fill(selector, str(value))
    page.evaluate(
        """(sel)=>{
            const el=document.querySelector(sel);
            if(el){
              el.dispatchEvent(new Event('input',{bubbles:true}));
              el.dispatchEvent(new Event('change',{bubbles:true}));
              el.dispatchEvent(new KeyboardEvent('keyup',{bubbles:true}));
            }
        }""",
        selector,
    )


def check_radio(page, selector: str, timeout_ms: int = 20000):
    page.wait_for_selector(selector, state="attached", timeout=timeout_ms)
    try:
        page.check(selector, force=True)
    except Exception:
        page.evaluate(
            """(sel)=>{
                const el=document.querySelector(sel);
                if(el){
                  el.checked=true;
                  el.dispatchEvent(new Event('input',{bubbles:true}));
                  el.dispatchEvent(new Event('change',{bubbles:true}));
                }
            }""",
            selector,
        )


def wait_non_empty_value(page, selector: str, timeout_ms: int = 15000):
    page.wait_for_function(
        """(sel)=>{
            const el=document.querySelector(sel);
            return !!el && !!(el.value||'').trim();
        }""",
        arg=selector,
        timeout=timeout_ms,
    )


def get_input_value(page, selector: str) -> str:
    try:
        return (page.input_value(selector) or "").strip()
    except Exception:
        return ""


def get_slider_range(page, slider_selector: str, fallback: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """
    Return (min, max, step) from jQuery UI slider options. Uses fallback if not available.
    """
    try:
        r = page.evaluate(
            """(sel)=>{
                const $=window.jQuery;
                if(!$) return null;
                const s=$(sel);
                if(!s.length || !s.slider) return null;
                const min=s.slider('option','min');
                const max=s.slider('option','max');
                const step=s.slider('option','step') || 1;
                return [min,max,step];
            }""",
            slider_selector,
        )
        if r and len(r) == 3:
            return int(r[0]), int(r[1]), int(r[2])
    except Exception:
        pass
    return fallback


def set_slider_and_input(page, slider_selector: str, input_selector: str, value: int):
    """
    jQuery UI slider + update readonly input + trigger events.
    """
    page.evaluate(
        """({sliderSel, inputSel, val})=>{
            const $=window.jQuery;
            if(!$) throw new Error("jQuery_not_found");
            const s=$(sliderSel);
            if(s.length && s.slider){
              s.slider('value', val);
              s.trigger('slide');
              s.trigger('change');
            }
            const inp=document.querySelector(inputSel);
            if(inp){
              inp.value=String(val);
              inp.dispatchEvent(new Event('input',{bubbles:true}));
              inp.dispatchEvent(new Event('change',{bubbles:true}));
            }
        }""",
        {"sliderSel": slider_selector, "inputSel": input_selector, "val": value},
    )


def wait_monthly_result(page, selector: str = "#remb_mensuel", timeout_ms: int = 20000):
    page.wait_for_function(
        """(sel)=>{
            const el=document.querySelector(sel);
            if(!el) return false;
            const t=(el.innerText||'').trim();
            return /\\d/.test(t);
        }""",
        arg=selector,
        timeout=timeout_ms,
    )
    time.sleep(0.15)


# ---------- taux implicite ----------
def _monthly_payment_from_rate(P: float, n: int, r_month: float) -> float:
    if n <= 0:
        return float("inf")
    if abs(r_month) < 1e-12:
        return P / n
    return P * r_month / (1.0 - (1.0 + r_month) ** (-n))


def estimate_annual_rate_percent(P: float, n: int, A: float) -> float:
    """
    Estime le taux nominal annuel (%) à partir de (principal P, mois n, mensualité A).
    """
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