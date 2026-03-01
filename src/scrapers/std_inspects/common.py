import re
import time
import unicodedata
import json
from typing import Optional, Tuple, Dict, Any

AJAX_URL = "https://www.stb.com.tn/wp-admin/admin-ajax.php"
DEFAULT_ACTION = "simulateurCredit"  # si le backend attend autre chose, on le change


def norm_text(s: str) -> str:
    s = (s or "").replace("\ufeff", "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s


def parse_float_fr(s: str) -> Optional[float]:
    if not s:
        return None
    s = s.replace("\ufeff", "").strip().replace(" ", "").replace(",", ".")
    m = re.search(r"-?\d+(\.\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


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


def select_option(page, selector: str, value: str, timeout_ms: int = 20000):
    page.wait_for_selector(selector, state="visible", timeout=timeout_ms)
    page.select_option(selector, value)


def click_simuler(page, timeout_ms: int = 20000):
    page.wait_for_selector("button.btn-simuler", state="visible", timeout=timeout_ms)
    page.click("button.btn-simuler")


def wait_result(page, timeout_ms: int = 25000):
    page.wait_for_function(
        """() => {
            const m = document.querySelector('#res-mensualite');
            const msg = document.querySelector('#res-message');
            if(!m && !msg) return false;
            const t1 = m ? (m.textContent||'').trim() : '';
            const t2 = msg ? (msg.textContent||'').trim() : '';
            return (t1.length>0 && /\\d/.test(t1)) || (t2.length>0);
        }""",
        timeout=timeout_ms,
    )
    time.sleep(0.15)


def get_result_fields(page) -> Tuple[str, str, str, str]:
    salaire = (page.text_content("#res-salaire") or "").strip()
    capacite = (page.text_content("#res-capacite") or "").strip()
    message = (page.text_content("#res-message") or "").strip()
    mensualite = (page.text_content("#res-mensualite") or "").strip()
    return salaire, capacite, message, mensualite


def _ensure_result_spans(page):
    # si on fait l'appel AJAX sans UI, on crée les spans pour l'extraction
    page.evaluate(
        """() => {
            const ids = ['res-salaire','res-capacite','res-message','res-mensualite'];
            for(const id of ids){
                if(!document.getElementById(id)){
                    const span = document.createElement('span');
                    span.id = id;
                    span.style.display = 'none';
                    document.body.appendChild(span);
                }
            }
        }"""
    )


def _extract_from_html_via_domparser(page, html: str) -> Dict[str, str]:
    return page.evaluate(
        """(html) => {
            const doc = new DOMParser().parseFromString(html, 'text/html');
            const pick = (id) => {
                const el = doc.querySelector('#' + id);
                return el ? (el.textContent || '').trim() : '';
            };
            return {
                salaire: pick('res-salaire'),
                capacite: pick('res-capacite'),
                message: pick('res-message'),
                mensualite: pick('res-mensualite'),
            };
        }""",
        html,
    )


def _try_parse_json(text: str) -> Optional[Dict[str, Any]]:
    t = (text or "").strip()
    if not t:
        return None
    if t.startswith("{") or t.startswith("["):
        try:
            return json.loads(t)
        except Exception:
            return None
    return None


def serialize_form(page, form_selector: str = "form#credit-auto-form") -> Dict[str, str]:
    page.wait_for_selector(form_selector, state="attached", timeout=20000)
    data = page.evaluate(
        """(sel) => {
            const form = document.querySelector(sel);
            const fd = new FormData(form);
            const o = {};
            for (const [k,v] of fd.entries()) o[k] = String(v);
            return o;
        }""",
        form_selector,
    )
    return {str(k): str(v) for k, v in (data or {}).items()}


def simulate_via_ajax(page, action: str = DEFAULT_ACTION, form_selector: str = "form#credit-auto-form") -> bool:
    """
    1) lit tous les champs du form (incl personal_ws)
    2) POST vers admin-ajax.php
    3) extrait res-* depuis la réponse (HTML/JSON)
    4) injecte dans #res-* pour extraction
    """
    try:
        payload = serialize_form(page, form_selector=form_selector)

        # WordPress admin-ajax requiert souvent "action"
        if "action" not in payload:
            payload["action"] = action

        resp = page.request.post(AJAX_URL, form=payload, timeout=30000)
        txt = resp.text() if resp else ""
        if not txt:
            return False

        _ensure_result_spans(page)

        # JSON ? (rare) / sinon HTML
        j = _try_parse_json(txt)
        if isinstance(j, dict):
            # essaie de mapper si backend renvoie direct
            salaire = str(j.get("salaire", "")).strip()
            capacite = str(j.get("capacite", "")).strip()
            message = str(j.get("message", "")).strip()
            mensualite = str(j.get("mensualite", "")).strip()
        else:
            out = _extract_from_html_via_domparser(page, txt)
            salaire = out.get("salaire", "")
            capacite = out.get("capacite", "")
            message = out.get("message", "")
            mensualite = out.get("mensualite", "")

        # injecter dans la page pour réutiliser get_result_fields()
        page.evaluate(
            """(r) => {
                const set = (id, v) => {
                    const el = document.getElementById(id);
                    if(el) el.textContent = v || '';
                };
                set('res-salaire', r.salaire);
                set('res-capacite', r.capacite);
                set('res-message', r.message);
                set('res-mensualite', r.mensualite);
            }""",
            {"salaire": salaire, "capacite": capacite, "message": message, "mensualite": mensualite},
        )

        # vérifier qu'on a au moins message ou mensualité
        sal, cap, msg, mens = get_result_fields(page)
        return bool(msg.strip()) or bool(mens.strip())

    except Exception:
        return False


# ---------- taux implicite ----------
def _monthly_payment_from_rate(P: float, n: int, r_month: float) -> float:
    if n <= 0:
        return float("inf")
    if abs(r_month) < 1e-12:
        return P / n
    return P * r_month / (1.0 - (1.0 + r_month) ** (-n))


def estimate_annual_rate_percent(P: float, n: int, A: float) -> float:
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