import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException, TimeoutException
from page_capture import save_page_snapshot
from llm_agent import analyze_page_with_context
import html_processor
 
# Helper function to delete the first resume in the dropdown
def delete_oldest_resume(driver):
    try:
        # First, make sure we're on the "Select a resumé" option
        select_resume_radio = driver.find_element(By.CSS_SELECTOR, "input[name='resume-method'][value='change']")
        if not select_resume_radio.is_selected():
            select_resume_radio.click()
            time.sleep(1)
        
        # Wait for the select dropdown to be visible and interactable
        select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='select-input']"))
        )
        
        # Get current options count
        options = select.find_elements(By.TAG_NAME, "option")
        initial_count = len(options)
        
        if initial_count <= 1:  # Only placeholder
            print("[Resume Delete] No resumes to delete")
            return False
            
        # Try to use JavaScript to select the first resume and trigger delete
        try:
            # Use JavaScript to select the first resume (skip placeholder)
            driver.execute_script("""
                var select = document.querySelector('[data-testid="select-input"]');
                if (select && select.options.length > 1) {
                    select.selectedIndex = 1;  // Select first actual resume
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """)
            time.sleep(1)
            
            # Wait for and click the delete button using JavaScript
            delete_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='deleteButton']"))
            )
            
            # Use JavaScript to click the delete button
            driver.execute_script("arguments[0].click();", delete_btn)
            time.sleep(2)
            
            # Now wait for and click the confirmation dialog's "Delete" button
            try:
                confirm_delete_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='delete-confirmation']"))
                )
                print("[Resume Delete] Found confirmation dialog, clicking Delete...")
                driver.execute_script("arguments[0].click();", confirm_delete_btn)
                time.sleep(2)
            except Exception as confirm_error:
                print(f"[Resume Delete] Could not find confirmation dialog: {confirm_error}")
                # Try alternative selectors for confirmation
                try:
                    confirm_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Delete')]"))
                    )
                    driver.execute_script("arguments[0].click();", confirm_btn)
                    time.sleep(2)
                except:
                    print("[Resume Delete] No confirmation dialog found, continuing...")
            
            # Wait for the option to disappear
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_element(By.CSS_SELECTOR, "[data-testid='select-input']").find_elements(By.TAG_NAME, "option")) < initial_count
            )
            time.sleep(1)
            print("[Resume Delete] Successfully deleted one resume")
            return True
            
        except Exception as js_error:
            print(f"[Resume Delete] JavaScript approach failed: {js_error}")
            # Fallback to manual approach
            try:
                # Scroll the select into view
                driver.execute_script("arguments[0].scrollIntoView(true);", select)
                time.sleep(1)
                
                # Click to open dropdown
                select.click()
                time.sleep(0.5)
                
                # Select the first resume (skip placeholder)
                options = select.find_elements(By.TAG_NAME, "option")
                if len(options) > 1:
                    options[1].click()  # First actual resume
                    time.sleep(0.5)
                    
                    # Wait for and click the delete button
                    delete_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='deleteButton']"))
                    )
                    delete_btn.click()
                    time.sleep(2)
                    
                    # Handle confirmation dialog
                    try:
                        confirm_delete_btn = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='delete-confirmation']"))
                        )
                        print("[Resume Delete] Found confirmation dialog, clicking Delete...")
                        confirm_delete_btn.click()
                        time.sleep(2)
                    except Exception as confirm_error:
                        print(f"[Resume Delete] Could not find confirmation dialog: {confirm_error}")
                        # Try alternative selectors for confirmation
                        try:
                            confirm_btn = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Delete')]"))
                            )
                            confirm_btn.click()
                            time.sleep(2)
                        except:
                            print("[Resume Delete] No confirmation dialog found, continuing...")
                    
                    # Wait for the option to disappear
                    WebDriverWait(driver, 10).until(
                        lambda d: len(d.find_element(By.CSS_SELECTOR, "[data-testid='select-input']").find_elements(By.TAG_NAME, "option")) < initial_count
                    )
                    time.sleep(1)
                    print("[Resume Delete] Successfully deleted one resume (manual approach)")
                    return True
            except Exception as manual_error:
                print(f"[Resume Delete] Manual approach also failed: {manual_error}")
                
    except Exception as e:
        print(f"[Resume Delete] Error deleting resume: {e}")
    return False

def execute_playbook_actions(driver, actions, resume_path, cover_letter_path):
    resume_uploaded = False
    cover_letter_uploaded = False
 
    for idx, action in enumerate(actions):
        action_type = action.get("action")
        selector = action.get("selector")
        field = action.get("field", "Unknown field")
        value = action.get("value", "")
 
        print(f"\nExecuting action {idx+1}: {action_type} - {field}")
 
        try:
            # Determine how to find the element
            if action.get("field") == "resume file":
                # BEFORE uploading, check and delete if needed
                try:
                    select = driver.find_element(By.CSS_SELECTOR, "[data-testid='select-input']")
                    options = select.find_elements(By.TAG_NAME, "option")
                    resume_count = len(options) - 1  # Exclude placeholder
                    if resume_count > 10:
                        print(f"[Resume Delete] Found {resume_count} resumes, deleting 2 before upload...")
                        delete_oldest_resume(driver)
                        delete_oldest_resume(driver)
                        # Refresh the page after deletion as suggested
                        print("[Resume Delete] Refreshing page after deletion...")
                        driver.refresh()
                        time.sleep(3)  # Wait for page to reload
                except Exception as e:
                    print(f"[Resume Delete] Could not check/delete resumes: {e}")
                element = driver.find_element(By.ID, "resume-fileFile")
            elif action.get("field") == "cover letter file":
                # Wait for the cover letter file input to be present and interactable
                try:
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "coverLetter-fileFile"))
                    )
                except TimeoutException:
                    print("Cover letter file input not found, trying alternative selector...")
                    element = driver.find_element(By.CSS_SELECTOR, "input[type='file'][data-testid='cover-letter-upload']")
            else:
                element = driver.find_element(By.XPATH, selector) if action.get("use_xpath") else driver.find_element(By.CSS_SELECTOR, selector)
 
            if action_type == "click":
                try:
                    element.click()
                except ElementNotInteractableException:
                    print(f"Element not interactable for clicking '{field}'. Scrolling into view and retrying.")
                    driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)
                    element.click()
                print(f"Clicked: {field}")
 
            elif action_type == "upload":
                upload_path = resume_path if value == "[RESUME_PATH]" else cover_letter_path
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(1)
                element.send_keys(upload_path)
                print(f"Uploaded file for: {field} (Path: {upload_path})")
                if value == "[RESUME_PATH]":
                    resume_uploaded = True
                elif value == "[COVER_LETTER_PATH]":
                    cover_letter_uploaded = True
 
            time.sleep(3 if action_type == "upload" else 1.5)
 
            # Save snapshot
            snapshot_name = f"steppost_action_{idx+1}_{field.replace(' ', '_')}"
            html_path, screenshot_path = save_page_snapshot(driver, "seek_application", "PostAction", snapshot_name)
 
            # Get current HTML
            with open(html_path, "r", encoding="utf-8") as f:
                current_html = f.read()
 
            # Analyze step via LLM
            try:
                print("Analyzing effect of last action with LLM...")
                # Extract sections from the current HTML
                current_sections = html_processor.extract_form_sections(current_html)
                result = analyze_page_with_context(driver, {
                    "sections": current_sections,
                    "current_step": idx + 1
                })

                if isinstance(result, dict):
                    print(f"🖼️ Screenshot summary: {result.get('screenshot_summary', 'N/A')}")
                    print(f"🧾 HTML summary: {result.get('html_summary', 'N/A')}")
                    print(f"🔮 LLM-suggested next action: {result.get('suggested_action', 'N/A')}")
                    # Check for completion based on LLM analysis
                    if "no more form fields" in result.get('html_summary', '').lower() or "application complete" in result.get('screenshot_summary', '').lower():
                         print("✅ LLM analysis indicates form is completed.")
                         return True
                else:
                    print(f"❌ LLM analysis failed or returned unexpected format: {result}")
                    pass
 
            except Exception as llm_error:
                print(f"❌ LLM Error during analysis: {llm_error}")
                pass
 
        except NoSuchElementException:
            print(f"[Error] Element not found for action '{action_type}' with selector: {selector}")
            return False
        except Exception as e:
            print(f"[Error] Unexpected error during action '{field}': {e}")
            return False
 
    return True