from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from playwright.sync_api import Playwright, Browser, Page
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class BaseBankScraper(ABC):
    """
    Abstract base class for bank simulators scrapers.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.base_url: str = "" # To be defined in subclasses

    def start_browser(self, playwright: Playwright):
        """Starts the browser session."""
        self.browser = playwright.chromium.launch(headless=self.headless)
        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            locale="fr-FR"
        )
        self.page = context.new_page()

    def close_browser(self):
        """Closes the browser session."""
        if self.browser:
            self.browser.close()

    @abstractmethod
    def navigate(self):
        """Navigates to the simulator URL."""
        pass

    @abstractmethod
    def fill_form(self, profile: Dict[str, Any]):
        """Fills the simulator form with profile data."""
        pass

    @abstractmethod
    def submit_and_wait(self):
        """Submits the form and waits for results."""
        pass

    @abstractmethod
    def extract_result(self) -> Dict[str, Any]:
        """Exctracts the result from the page."""
        pass

    def run(self, playwright: Playwright, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution flow for a single profile.
        """
        try:
            if not self.page:
                self.start_browser(playwright)
            
            self.navigate()
            self.fill_form(profile)
            self.submit_and_wait()
            result = self.extract_result()
            
            # Combine result with base info
            result['processed'] = True
            return result

        except Exception as e:
            logger.error(f"Scraping failed for profile {profile.get('id')}: {e}")
            # Capture screenshot on failure for debugging
            if self.page:
                try:
                    self.page.screenshot(path=f"data/error_{profile.get('id')}.png")
                except:
                    pass
            
            return {
                "result_status": "ERROR",
                "error_message": str(e),
                "processed": False
            }
        finally:
             # In a real high-volume scenario, we might keep the browser open. 
             # For now, we'll keep it open but the caller manages the playwright context usually. 
             # But here we initialized it inside run if not present. 
             # To be efficient, the main loop should pass the playwright instance or manage the browser lifecycle.
             # Refined approach: The class manages its own browser instance, but we might want to reuse it.
             # For simplicity phase 1, we wont close it here to allow reuse if the object persists.
             pass
