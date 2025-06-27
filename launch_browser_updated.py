import os
import time
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from page_capture import save_page_snapshot
from analyze_form import analyze_form_page
from playbook_manager import load_playbook, save_playbook
from playbook_executor import execute_playbook_actions
from llm_agent import analyze_page_with_context, generate_playbook
from openai import OpenAI
from html_processor import extract_form_sections
from dynamic_handler import handle_dynamic_questions

RESUME_PATH = os.path.abspath("./resume.pdf")
COVER_LETTER_PATH = os.path.abspath("./cover_letter.pdf")

# Global variable to store question logs
question_logs_global = ""

def debug_print(message, level="INFO"):
    """Helper function for consistent debug output"""
    print(f"[{level}] {message}")

def dispatch_special_pages(driver, job_url=None, row_number=None, csv_file_path=None):
    """Dispatch to appropriate page handler based on URL"""
    global question_logs_global
    
    url = driver.current_url

    # 1) Role Requirements page - INTERMEDIATE PAGE (continue to next step)
    if "/apply/role-requirements" in url:
        print("[Dispatcher] Detected role-requirements page, dispatching to handler")
        success, question_logs = handle_dynamic_questions(driver)
        if not success:
            raise RuntimeError("Dynamic handler failed to fill the form.")
        # Store question logs for later use
        question_logs_global = question_logs
        print("[Dispatcher] Role-requirements page handled successfully, continuing to next step")
        return False  # Continue to next step, don't exit

    # 2) Profile page - INTERMEDIATE PAGE (continue to next step)
    if "/apply/profile" in url:
        print("[Dispatcher] Detected profile page, dispatching to handler")
        from profile_handler import handle_profile_page
        if handle_profile_page(driver):
            print("[Dispatcher] Profile page handled successfully, continuing to next step")
            return False  # Continue to next step, don't exit
        else:
            print("[Dispatcher] Profile page handling failed")
            return False

    # 3) Review page - INTERMEDIATE PAGE (continue to next step)
    if "/apply/review" in url:
        print("[Dispatcher] Detected review page, dispatching to handler")
        from review_handler import handle_review_page
        if handle_review_page(driver):
            print("[Dispatcher] Review page handled successfully, continuing to next step")
            return False  # Continue to next step, don't exit
        else:
            print("[Dispatcher] Review page handling failed")
            return False

    # 4) Success page - FINAL PAGE (end process)
    # Check multiple success page patterns
    success_indicators = [
        "/apply/success" in url,
        "/success" in url,
        "success" in url.lower() and "apply" in url.lower(),
        # Also check page content for success indicators
        any(text in driver.page_source.lower() for text in [
            "application submitted",
            "application successful",
            "thank you for your application",
            "application received",
            "submitted successfully"
        ])
    ]
    
    if any(success_indicators):
        print("[Dispatcher] Detected success page, dispatching to handler")
        from success_handler import handle_success_page
        # Pass the collected question logs to the success handler
        result = handle_success_page(driver, job_url, row_number, csv_file_path=csv_file_path, questions_and_answers=question_logs_global)
        if result == 'SUCCESS_COMPLETE':
            print("[Dispatcher] Success page handled successfully - application complete")
            return 'SUCCESS_COMPLETE'  # Special return value to exit main loop
        elif result:
            print("[Dispatcher] Success page handled successfully")
            return True  # Exit main loop
        else:
            print("[Dispatcher] Success page handling failed")
            return False

    return False

def try_click_continue(driver, job_url=None, row_number=None, csv_file_path=None):
    """Try to click the continue button using multiple selectors"""
    selectors = [
        "button[data-testid='continue-button']",
        "#app > div > div.azpfys0._1fz17ik9j > div.azpfys0._1fz17ikb7._1fz17ikaw._1fz17ika3._1fz17ik9s._1fz17ikp > div > div.azpfys0._1fz17ikcr._1fz17ikt > div.azpfys0._1fz17ik5b._1fz17ikhf._1fz17ik77 > div.azpfys0._1fz17ik5b._1fz17ikh3._1fz17ikgj._1fz17ikhb > div > button",
        "//*[@id='app']/div/div[1]/div[4]/div/div[3]/div[2]/div[4]/div/button",
        "button.azpfys0.azpfys7._1fz17ik5b._1fz17ikp._1fz17ik63._1fz17ikh._1ojf5op0"
    ]
    
    for selector in selectors:
        try:
            # Wait for button to be clickable
            button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR if not selector.startswith("//") else By.XPATH, selector))
            )
            # Scroll to button
            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(1)  # Wait for scroll
            # Click button
            button.click()
            print(f"[SUCCESS] Clicked continue button using selector: {selector}")
            
            # Check if we need to dispatch to special page handler
            dispatch_result = dispatch_special_pages(driver, job_url, row_number, csv_file_path=csv_file_path)
            if dispatch_result == 'SUCCESS_COMPLETE':
                return 'SUCCESS_COMPLETE'  # Application complete, exit
            elif dispatch_result is True:  # Only exit for success pages (True), not intermediate pages (False)
                return True  # Success page handled, exit
            else:
                # Intermediate page handled (role-requirements, profile, review), continue to next step
                print("[SUCCESS] Intermediate page handled, continuing to next step")
                return True  # Button clicked successfully, continue in main loop
                
        except Exception as e:
            print(f"[DEBUG] Could not click continue button with selector {selector}: {e}")
            continue
    return False

def detect_external_redirect(driver, original_job_url, job_url=None, row_number=None, csv_file_path=None):
    """
    Detect if clicking Apply redirected to an external website instead of staying on SEEK.
    
    Args:
        driver: Selenium WebDriver instance
        original_job_url: The original SEEK job URL
        job_url: The job URL for CSV updates
        
    Returns:
        bool: True if redirected to external site (should stop automation), False otherwise
    """
    try:
        print("[External Redirect Handler] Checking for external website redirect...")
        
        # Wait a bit for any redirects to complete
        time.sleep(3)
        
        current_url = driver.current_url
        print(f"[External Redirect Handler] Current URL: {current_url}")
        
        # Check if we're still on SEEK
        if "seek.com.au" in current_url:
            print("[External Redirect Handler] Still on SEEK website - no external redirect detected")
            return False
        
        # Check if we're on a different domain (external website)
        original_domain = urlparse(original_job_url).netloc
        current_domain = urlparse(current_url).netloc
        
        if original_domain != current_domain:
            print(f"[External Redirect Handler] ⚠️ Redirected to external website: {current_domain}")
            print(f"[External Redirect Handler] Original domain: {original_domain}")
            print(f"[External Redirect Handler] Current domain: {current_domain}")
            
            # Update CSV with external redirect status
            if job_url:
                from external_redirect_handler import update_csv_with_external_redirect
                if update_csv_with_external_redirect(job_url, row_number=row_number, csv_file_path=csv_file_path):
                    print("[External Redirect Handler] ✅ CSV updated with 'External Redirect' status")
                else:
                    print("[External Redirect Handler] ⚠️ Failed to update CSV")
            
            return True
        
        print("[External Redirect Handler] No external redirect detected")
        return False
        
    except Exception as e:
        print(f"[External Redirect Handler] Error detecting external redirect: {e}")
        return False

def main(job_url=None, resume_path=None, cover_letter_path=None, row_number=None, csv_file_path=None):
    profile_path = "/Users/umairsaeed/Library/Application Support/Firefox/Profiles/4219wmga.default-release"

    options = FirefoxOptions()
    options.set_preference("dom.webnotifications.enabled", False)
    options.add_argument("--width=1280")
    options.add_argument("--height=900")
    options.profile = profile_path

    debug_print("Initializing Firefox Service...")
    service = FirefoxService()
    debug_print("Firefox Service initialized.")

    debug_print("Launching Firefox with personal profile...")
    driver = webdriver.Firefox(service=service, options=options)
    debug_print("Firefox WebDriver initialized successfully.")

    driver.implicitly_wait(10)
    job_id = "seek_application"
    job_title = "N-A"
    step_counter = 0
    max_steps = 10

    # Initialize upload states
    upload_states = {
        'resume': False,
        'cover_letter': False
    }

    # Track if CSV has been updated by handlers
    csv_updated_by_handler = False
    final_status = 'UNKNOWN_ERROR'

    # Initialize OpenAI client
    client = OpenAI()

    try:
        # Use provided job_url or default
        if job_url is None:
            job_url = "https://www.seek.com.au/job/84528630"
        debug_print(f"Opening job page: {job_url}")
        driver.get(job_url)

        debug_print("Waiting for Apply button...")
        try:
            apply_button = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(., 'Apply') or contains(., 'apply')]"))
            )
            step_counter += 1

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            job_title_element = soup.select_one('h1')
            job_title = job_title_element.get_text(strip=True) if job_title_element else 'N-A'

            save_page_snapshot(driver, job_id, job_title, f"nav_{step_counter}")

            debug_print("Clicking Apply...")
            apply_button.click()
            time.sleep(5)
            step_counter += 1

            # Check if clicking Apply redirected to an external website
            if detect_external_redirect(driver, job_url, job_url, row_number, csv_file_path):
                debug_print("Job redirected to external website. This type of job requires manual application.", "WARNING")
                debug_print("Closing browser and marking job as 'External Redirect' in CSV.", "INFO")
                csv_updated_by_handler = True  # External redirect handler updated CSV
                final_status = 'EXTERNAL_REDIRECT'
                return final_status

        except TimeoutException:
            debug_print("Apply button not found. Checking if job is unavailable.", "WARNING")
            from job_unavailable_handler import handle_job_unavailable
            if handle_job_unavailable(driver, job_url, row_number):
                debug_print("Job is confirmed to be no longer available. Closing browser.", "ERROR")
                csv_updated_by_handler = True  # Job unavailable handler updated CSV
                final_status = 'JOB_UNAVAILABLE'
                return final_status
            else:
                debug_print("Job seems to be available, but the Apply button was not found. This might be an unexpected page layout or other issue.", "ERROR")
                final_status = 'APPLY_BUTTON_NOT_FOUND'
                return final_status
        
        except Exception as e:
            debug_print(f"An unexpected error occurred: {e}", "ERROR")
            final_status = 'UNEXPECTED_ERROR'
            return final_status

        visited_states = set()
        executed_action_keys = set()
        consecutive_same_states = 0
        last_state = None

        while step_counter < max_steps:
            debug_print(f"\n=== Processing Step {step_counter + 1} ===", "INFO")

            # Check if both uploads are complete
            if upload_states['resume'] and upload_states['cover_letter']:
                debug_print("Both resume and cover letter uploaded successfully", "SUCCESS")
                # Add a 10-second delay before trying to click continue
                debug_print("Waiting 10 seconds before clicking continue button...", "INFO")
                time.sleep(10)
                # Try to click continue button after uploads
                continue_result = try_click_continue(driver, job_url, row_number, csv_file_path=csv_file_path)
                if continue_result == 'SUCCESS_COMPLETE':
                    debug_print("Application completed successfully, exiting main loop", "SUCCESS")
                    csv_updated_by_handler = True  # Success handler updated CSV
                    final_status = 'SUCCESS_COMPLETE'
                    return final_status
                elif continue_result:
                    debug_print("Successfully clicked continue button after uploads", "SUCCESS")
                    # Check if we need to dispatch to special page handler
                    dispatch_result = dispatch_special_pages(driver, job_url, row_number, csv_file_path=csv_file_path)
                    if dispatch_result == 'SUCCESS_COMPLETE':
                        debug_print("Application completed successfully, exiting main loop", "SUCCESS")
                        csv_updated_by_handler = True  # Success handler updated CSV
                        final_status = 'SUCCESS_COMPLETE'
                        return final_status
                    elif dispatch_result is True:  # Only exit for success pages (True), not intermediate pages (False)
                        debug_print("Handed off to special page handler, exiting main loop", "SUCCESS")
                        csv_updated_by_handler = True  # Handler updated CSV
                        final_status = 'HANDLER_SUCCESS'
                        return final_status
                    # If dispatch_result is False, continue to next step (intermediate pages handled)
                else:
                    debug_print("Could not find continue button, continuing with normal flow", "WARNING")

            current_url = driver.current_url
            domain = urlparse(current_url).netloc
            debug_print(f"Current URL: {current_url}", "INFO")

            # Check if we need to dispatch to special page handler
            dispatch_result = dispatch_special_pages(driver, job_url, row_number, csv_file_path=csv_file_path)
            if dispatch_result == 'SUCCESS_COMPLETE':
                debug_print("Application completed successfully, exiting main loop", "SUCCESS")
                csv_updated_by_handler = True  # Success handler updated CSV
                final_status = 'SUCCESS_COMPLETE'
                return final_status
            elif dispatch_result is True:  # Only exit for success pages (True), not intermediate pages (False)
                debug_print("Handed off to special page handler, exiting main loop", "SUCCESS")
                csv_updated_by_handler = True  # Handler updated CSV
                final_status = 'HANDLER_SUCCESS'
                return final_status

            # Additional success page check - in case the dispatcher missed it
            success_indicators = [
                "/apply/success" in current_url,
                "/success" in current_url,
                "success" in current_url.lower() and "apply" in current_url.lower(),
                any(text in driver.page_source.lower() for text in [
                    "application submitted",
                    "application successful", 
                    "thank you for your application",
                    "application received",
                    "submitted successfully"
                ])
            ]
            
            if any(success_indicators):
                debug_print("Detected success page in main loop, dispatching to handler", "SUCCESS")
                from success_handler import handle_success_page
                result = handle_success_page(driver, job_url, row_number, csv_file_path=csv_file_path)
                if result == 'SUCCESS_COMPLETE' or result:
                    debug_print("Application completed successfully, exiting main loop", "SUCCESS")
                    csv_updated_by_handler = True  # Success handler updated CSV
                    final_status = 'SUCCESS_COMPLETE'
                    return final_status

            # Improved state detection
            current_state = hash(current_url + "_" + str(len(driver.page_source)))
            if current_state == last_state:
                consecutive_same_states += 1
                debug_print(f"Same state detected {consecutive_same_states} times", "DEBUG")
                if consecutive_same_states >= 3:
                    debug_print("Detected multiple consecutive same states. Ending automation.", "WARNING")
                    # Update CSV with "Can't Find Resume Element" status
                    if row_number:
                        from resume_element_handler import update_csv_with_resume_element_error
                        if update_csv_with_resume_element_error(row_number, csv_file_path=csv_file_path):
                            debug_print("Updated CSV with 'Can't Find Resume Element' status", "INFO")
                            csv_updated_by_handler = True  # Resume element handler updated CSV
                    final_status = 'RESUME_ELEMENT_ERROR'
                    return final_status
            else:
                consecutive_same_states = 0
                last_state = current_state
                debug_print("New state detected", "DEBUG")

            visited_states.add(current_state)

            html_path, screenshot_path = save_page_snapshot(driver, job_id, job_title, f"step_{step_counter + 1}")
            current_html = open(html_path, encoding="utf-8").read()

            playbook = load_playbook(domain)
            actions_to_execute = []

            if not playbook or 'actions' not in playbook:
                debug_print("No playbook found. Generating new actions...", "INFO")
                current_sections = extract_form_sections(current_html)
                new_actions = generate_playbook(client, current_sections, screenshot_path)
                if new_actions and "actions" in new_actions:
                    playbook = {"actions": new_actions.get("actions", [])}
                    save_playbook(domain, playbook)
                    actions_to_execute = playbook["actions"]
                    debug_print(f"Generated {len(actions_to_execute)} new actions", "INFO")
                else:
                    debug_print("LLM failed to generate actions.", "ERROR")
                    final_status = 'LLM_GENERATION_FAILED'
                    return final_status
            else:
                debug_print(f"Loaded existing playbook for {domain}", "INFO")
                for action in playbook['actions']:
                    key = f"{action['action']}|{action['selector']}|{action.get('value', '')}"
                    if key not in executed_action_keys:
                        actions_to_execute.append(action)
                debug_print(f"Found {len(actions_to_execute)} actions to execute", "INFO")

            for idx, action in enumerate(actions_to_execute):
                field = action.get("field", "Unknown").lower()
                debug_print(f"Executing action {idx+1}: {action['action']} - {field}", "INFO")

                # Skip if already handled
                if "resume" in field and upload_states['resume']:
                    debug_print("Skipping resume upload - already completed", "INFO")
                    continue
                if "cover letter" in field and upload_states['cover_letter']:
                    debug_print("Skipping cover letter upload - already completed", "INFO")
                    continue

                success = execute_playbook_actions(driver, [action], resume_path if resume_path else RESUME_PATH, cover_letter_path if cover_letter_path else COVER_LETTER_PATH)
                executed_action_keys.add(f"{action['action']}|{action['selector']}|{action.get('value', '')}")

                # Check if we need to dispatch to special page handler after each action
                dispatch_result = dispatch_special_pages(driver, job_url, row_number, csv_file_path=csv_file_path)
                if dispatch_result == 'SUCCESS_COMPLETE':
                    debug_print("Application completed successfully, exiting action loop", "SUCCESS")
                    csv_updated_by_handler = True  # Success handler updated CSV
                    final_status = 'SUCCESS_COMPLETE'
                    return final_status
                elif dispatch_result is True:  # Only exit for success pages (True), not intermediate pages (False)
                    debug_print("Handed off to special page handler, exiting action loop", "SUCCESS")
                    csv_updated_by_handler = True  # Handler updated CSV
                    final_status = 'HANDLER_SUCCESS'
                    return final_status

            # Handle any remaining special pages in sequence (role-requirements → profile → review)
            while True:
                dispatch_result = dispatch_special_pages(driver, job_url, row_number, csv_file_path=csv_file_path)
                if dispatch_result == 'SUCCESS_COMPLETE':
                    debug_print("Application completed successfully, exiting main loop", "SUCCESS")
                    csv_updated_by_handler = True  # Success handler updated CSV
                    final_status = 'SUCCESS_COMPLETE'
                    return final_status
                elif not dispatch_result:
                    break

            step_counter += 1

        # If we reach here, we've exhausted all steps
        final_status = 'MAX_STEPS_REACHED'
        return final_status

    except Exception as e:
        debug_print(f"Unexpected exception: {e}", "ERROR")
        final_status = 'UNEXPECTED_EXCEPTION'
        return final_status
    finally:
        driver.quit()
        debug_print("Browser closed.", "INFO")

if __name__ == "__main__":
    main()
