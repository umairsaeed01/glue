from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time

def handle_job_unavailable(driver):
    """
    Handle cases where the job is no longer available.
    Detects various error indicators and provides appropriate logging.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        bool: True if job is unavailable (should stop automation), False otherwise
    """
    try:
        print("[Job Unavailable Handler] Checking for job unavailability indicators...")
        
        # Method 1: Check for the specific SEEK "no longer advertised" message
        try:
            # Look for the exact text from the HTML you provided
            unavailable_h2 = driver.find_element(By.XPATH, "//h2[contains(text(), 'This job is no longer advertised')]")
            if unavailable_h2.is_displayed():
                print("[Job Unavailable Handler] Found 'This job is no longer advertised' message")
                return True
        except NoSuchElementException:
            pass
        
        # Method 2: Check for specific error messages in page content
        error_messages = [
            "This job is no longer available",
            "This job is no longer advertised",
            "Job has been removed",
            "Position has been filled",
            "This position is no longer accepting applications",
            "Job not found",
            "Page not found",
            "404",
            "The job you're looking for doesn't exist",
            "Jobs remain on SEEK for 30 days"
        ]
        
        page_source = driver.page_source.lower()
        for message in error_messages:
            if message.lower() in page_source:
                print(f"[Job Unavailable Handler] Found error message: '{message}'")
                return True
        
        # Method 3: Check for error elements by XPath (more specific to SEEK)
        error_selectors = [
            "//h2[contains(text(), 'This job is no longer advertised')]",
            "//h2[contains(text(), 'Job not found')]",
            "//h2[contains(text(), 'Page not found')]",
            "//h2[contains(text(), '404')]",
            "//div[contains(text(), 'This job is no longer available')]",
            "//div[contains(text(), 'Job has been removed')]",
            "//div[contains(text(), 'Position has been filled')]",
            "//div[contains(text(), 'Jobs remain on SEEK for 30 days')]",
            "//div[contains(@class, 'error')]",
            "//div[contains(@class, 'not-found')]",
            "//div[contains(@class, 'unavailable')]",
            "//div[contains(@class, 'expired')]"
        ]
        
        for selector in error_selectors:
            try:
                element = driver.find_element(By.XPATH, selector)
                if element.is_displayed():
                    print(f"[Job Unavailable Handler] Found error element: {selector}")
                    return True
            except NoSuchElementException:
                continue
        
        # Method 4: Check page title for error indicators
        page_title = driver.title.lower()
        title_error_indicators = [
            "not found",
            "404",
            "error",
            "unavailable",
            "removed",
            "expired",
            "no longer advertised"
        ]
        
        for indicator in title_error_indicators:
            if indicator in page_title:
                print(f"[Job Unavailable Handler] Found error in page title: '{indicator}'")
                return True
        
        # Method 5: Check URL for error patterns
        current_url = driver.current_url.lower()
        if "error" in current_url or "404" in current_url:
            print("[Job Unavailable Handler] Found error in URL")
            return True
        
        print("[Job Unavailable Handler] Job appears to be available")
        return False
        
    except Exception as e:
        print(f"[Job Unavailable Handler] Error detecting job availability: {e}")
        return False 