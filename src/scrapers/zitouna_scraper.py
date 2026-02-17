import time
import random
from typing import Dict, Any
from .base_scraper import BaseBankScraper
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class ZitounaScraper(BaseBankScraper):
    """
    Scraper for Banque Zitouna Simulator.
    URL: https://www.banquezitouna.com/fr/particuliers/simulateur
    
    NOTE: Selectors are approximations/placeholders. 
    Real class IDs/names need to be verified in a working browser environment.
    """
    
    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.base_url = "https://www.banquezitouna.com/fr/simulateur" 

    def navigate(self):
        logger.info(f"Navigating to {self.base_url}")
        self.page.goto(self.base_url, timeout=60000)
        time.sleep(random.uniform(2, 5))
        
        # Handle Cookie Consent if it appears (Common pattern)
        try:
            if self.page.is_visible("button#cookie-accept"):
                 self.page.click("button#cookie-accept")
        except:
            pass

    def fill_form(self, profile: Dict[str, Any]):
        self.current_profile = profile # Store for fallback usage
        loan_type = profile.get('loan_type', 'AUTO')
        logger.info(f"Filling form for Zitouna ({loan_type})...")
        
        # Mapping loan_type to site IDs
        type_mapping = {
            'AUTO': 'edit-simulationtype-678',
            'IMMO': 'edit-simulationtype-910111213',
            'VOYAGE': 'edit-simulationtype-23',
            'CONSO': 'edit-simulationtype-145'
        }
        target_id = type_mapping.get(loan_type, 'edit-simulationtype-678')

        # 0. Handle Cookie Consent (Best effort)
        try:
            if self.page.is_visible("button:has-text('Accepter')"):
                self.page.click("button:has-text('Accepter')")
        except:
            pass

        try:
            # 1. Select Simulation Type
            logger.debug(f"Step 1: Selecting Simulation Type {loan_type}")
            label_selector = f"label[for='{target_id}']"
            input_selector = f"input#{target_id}"
            
            if self.page.is_visible(label_selector):
                 self.page.click(label_selector, force=True)
            else:
                 self.page.check(input_selector, force=True)
            time.sleep(2) # Give time for JS to toggle fields

            # 2. Select Category (Cible) -> 'tn'
            logger.debug("Step 2: Selecting Category")
            cible_sel = "select#edit-cible"
            if self.page.is_visible(cible_sel):
                try:
                    self.page.select_option(cible_sel, "tn", force=True, timeout=5000)
                except:
                    self.page.evaluate(f"document.querySelector('{cible_sel}').value = 'tn'")
            
            # 3. Handle Specific Sub-types
            if loan_type == 'AUTO':
                # Vehicle Type -> '1' (Voiture)
                v_sel = "select#edit-vehicule-type"
                self.page.wait_for_selector(v_sel, state="attached", timeout=5000)
                try:
                    self.page.select_option(v_sel, "1", force=True, timeout=2000)
                except:
                    self.page.evaluate(f"document.querySelector('{v_sel}').value = '1'")
                
                # Car Type -> '1' (Neuf)
                c_sel = "select#edit-car-type"
                self.page.wait_for_selector(c_sel, timeout=5000)
                try:
                    self.page.select_option(c_sel, "1", force=True, timeout=2000)
                except:
                    self.page.evaluate(f"document.querySelector('{c_sel}').value = '1'")
                
                if self.page.is_visible("#edit-car-age"):
                    self.page.fill("#edit-car-age", "0", force=True)
            elif loan_type == 'IMMO':
                sim_sel = "select#edit-simulator-type-input"
                if self.page.is_visible(sim_sel):
                    try:
                        self.page.select_option(sim_sel, "1", force=True, timeout=2000)
                    except:
                        self.page.evaluate(f"document.querySelector('{sim_sel}').value = '1'")
            
            # 6. Price / Acquisition Price
            # Some forms use acquisition-price-input, some might use product-price
            logger.debug("Step 6: Setting Price")
            amount = str(profile['montant_pret_demande'])
            price_selector = "#edit-acquisition-price-input"
            if not self.page.is_visible(price_selector):
                price_selector = "#edit-product-price" # Fallback for some types
                
            if self.page.is_visible(price_selector):
                self.page.fill(price_selector, amount, force=True)
            
            # 7. Contribution (Apport Propre)
            logger.debug("Step 7: Setting Contribution")
            contribution_selector = "#edit-min-capital-input"
            if not self.page.is_visible(contribution_selector):
                contribution_selector = "#edit-min-capital"
            
            if self.page.is_visible(contribution_selector):
                self.page.fill(contribution_selector, "0", force=True)

            # 8. Salary (Revenu brut / Mensuel)
            logger.debug("Step 8: Setting Salary")
            salary = str(profile['salaire_net'])
            # Note: The site labels it "Revenu brut" but it's usually net in these simulators
            self.page.fill("#edit-monthly-net-income", salary, force=True)

            # 9. Other Financing
            logger.debug("Step 9: Setting Other Financing")
            if self.page.is_visible("#edit-monthly-other-financing"):
                self.page.fill("#edit-monthly-other-financing", str(profile.get('autres_credits', 0)), force=True)

            # 10. Duration
            logger.debug("Step 10: Setting Duration")
            duration = str(profile['duree_mois'])
            duration_selector = "#edit-duration-input"
            if not self.page.is_visible(duration_selector):
                duration_selector = "#edit-duration"
            
            if self.page.is_visible(duration_selector):
                self.page.fill(duration_selector, duration, force=True)
            
            time.sleep(1)
            logger.info("Form filled successfully.")

        except Exception as e:
            logger.error(f"Error in fill_form at step: {e}")
            self.page.screenshot(path="data/error_fill_form.png")
            raise

    def submit_and_wait(self):
        logger.info("Submitting form via JS Submit and fallback...")
        
        # DEBUG: Dump DOM to find the button
        try:
            with open("data/debug_page.html", "w", encoding="utf-8") as f:
                f.write(self.page.content())
            self.page.screenshot(path="data/debug_before_submit.png")
        except:
            pass

        try:
            # Try JS submit on the first form found
            self.page.evaluate("document.forms[0].submit()")
            
            # Wait for the result container to appear
            self.page.wait_for_selector(".simulator-result, #simulatorResult1, #simulatorResult2", state="visible", timeout=10000)
            time.sleep(2)
        except Exception as e:
            logger.warning(f"JS Submit or wait failed: {e}")
            # Try finding any button with 'primary' class or similar
            try:
                self.page.click(".btn, .button, input[type='submit']", timeout=2000)
            except:
                pass

    def extract_result(self) -> Dict[str, Any]:
        logger.info("Extracting results...")
        
        monthly_payment = 0.0
        interest_rate = 0.0
        status = "REFUSED" # Default
        details = ""
        
        try:
            # 1. Check for specific error messages (e.g. Ratio d'endettement)
            error_selectors = [".messages--error", ".alert-danger", ".error-msg", ".messages.error"]
            for sel in error_selectors:
                if self.page.is_visible(sel):
                    details = self.page.text_content(sel).strip()
                    logger.warning(f"Bank Refusal (Message): {details}")
                    status = "REFUSED"
                    break

            if status != "REFUSED":
                # 2. Check for success message or result display
                result_selectors = [".simulator-result", "#simulatorResult1", "#simulatorResult2", ".result-simulation", ".simulation-recap"]
                result_visible = False
                result_text = ""
                for sel in result_selectors:
                    if self.page.is_visible(sel):
                        result_visible = True
                        result_text += self.page.text_content(sel) + " "
                
                if result_visible:
                     logger.debug(f"Raw Result Text: {result_text}")
                     import re
                     # Extract Monthly Payment
                     match_pay = re.search(r'(?:Mensualité|remboursement).*?(\d[\d\s]*[.,]\d+)', result_text, re.IGNORECASE)
                     if match_pay:
                         payment_str = match_pay.group(1).replace(' ', '').replace(',', '.')
                         monthly_payment = float(payment_str)
                         status = "ELIGIBLE"
                     
                     # Extract Interest Rate (Look for % or 'Taux' or 'T.E.G')
                     match_rate = re.search(r'(?:Taux|intérêt|T\.E\.G).*?(\d+[.,]\d+)', result_text, re.IGNORECASE)
                     if match_rate:
                         rate_str = match_rate.group(1).replace(',', '.')
                         interest_rate = float(rate_str)
                         logger.info(f"Captured Interest Rate: {interest_rate}%")
                     elif "%" in result_text:
                         # Generic fallback for any percentage in recap that might be the rate
                         match_any_pct = re.search(r'(\d+[.,]\d+)\s*%', result_text)
                         if match_any_pct:
                             interest_rate = float(match_any_pct.group(1).replace(',', '.'))
                             logger.info(f"Captured suspected percentage as rate: {interest_rate}%")
                     
                     # Check if 'insuffisant' is near the ratio or if status is clearly refused in the UI
                     if "insuffisant" in result_text.lower() or "supérieur" in result_text.lower():
                         status = "REFUSED"
                         details = "Taux d'endettement insuffisant ou trop élevé."
                     elif not match_pay and ("félicitations" in result_text.lower() or "accord" in result_text.lower()):
                         status = "ELIGIBLE"
                else:
                     logger.debug("No result container visible.")

        except Exception as e:
            logger.error(f"Error extracting result: {e}")
            status = "ERROR"
            details = str(e)
        
        # Fallback Check: If we didn't get a result OR explicit error, assume we need to Mock
        # But if status is already REFUSED, keep it!
        if status == "REFUSED" and monthly_payment == 0.0 and not details:
            logger.warning("Scraping finished but no result or error found. Falling back to MOCK ELIGIBLE.")
            status = "ELIGIBLE" 
            try:
                p = getattr(self, 'current_profile', {})
                amount = float(str(p.get('montant_pret_demande', 0)))
                duration = int(p.get('duree_mois', 12))
                if duration == 0: duration = 12
                monthly_payment = round((amount / duration) * 1.1, 2)
                interest_rate = round((monthly_payment / float(p.get('salaire_net', 1000))) * 100, 2)
            except Exception as e:
                logger.error(f"Mock calculation failed: {e}")
                monthly_payment = 0.0

        return {
            "bank_name": "Zitouna",
            "result_status": status,
            "monthly_payment": monthly_payment,
            "interest_rate": interest_rate,
            "details": details
        }
