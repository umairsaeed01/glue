import json
import re
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)
from openai import OpenAI
from resume_summarizer import RÉSUMÉ_SUMMARY

def analyze_page_structure(driver):
    """Analyze the page structure and print detailed information about form elements"""
    print("\n[Dynamic] === Page Structure Analysis ===")
    
    # Get the page source and create BeautifulSoup object
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Find all form elements
    form = soup.find('form')
    if not form:
        print("[Dynamic] No form found on the page!")
        return None
        
    print("\n[Dynamic] Form Structure:")
    print("------------------------")
    
    # Analyze select elements
    selects = form.find_all('select')
    print(f"\n[Dynamic] Found {len(selects)} select elements:")
    for sel in selects:
        name = sel.get('name', 'No name')
        id_attr = sel.get('id', 'No ID')
        class_attr = sel.get('class', [])
        print(f"\nSelect Element:")
        print(f"  Name: {name}")
        print(f"  ID: {id_attr}")
        print(f"  Classes: {class_attr}")
        
        # Find the question text (usually in a preceding strong or label)
        question = None
        prev = sel.find_previous(['strong', 'label'])
        if prev:
            question = prev.get_text(strip=True)
            print(f"  Question: {question}")
            
        # Get options
        options = []
        for opt in sel.find_all('option'):
            if opt.get('value'):
                options.append({
                    'text': opt.get_text(strip=True),
                    'value': opt.get('value')
                })
        print(f"  Options: {json.dumps(options, indent=2)}")
    
    # Analyze checkbox groups
    print(f"\n[Dynamic] Analyzing checkbox groups...")
    checkbox_groups = []
    
    # Find all divs that might contain checkbox groups
    for div in form.find_all('div', class_=True):
        checkboxes = div.find_all('input', type='checkbox')
        if checkboxes:
            group = {
                'container': div.get('class', []),
                'question': None,
                'checkboxes': []
            }
            
            # Try to find the question
            strong = div.find('strong')
            if strong:
                group['question'] = strong.get_text(strip=True)
            
            # Get checkbox details
            for cb in checkboxes:
                cb_id = cb.get('id')
                if cb_id:
                    label = div.find('label', attrs={'for': cb_id})
                    if label:
                        group['checkboxes'].append({
                            'id': cb_id,
                            'label': label.get_text(strip=True)
                        })
            
            if group['question'] and group['checkboxes']:
                checkbox_groups.append(group)
    
    print(f"\n[Dynamic] Found {len(checkbox_groups)} checkbox groups:")
    for group in checkbox_groups:
        print(f"\nCheckbox Group:")
        print(f"  Question: {group['question']}")
        print(f"  Container Classes: {group['container']}")
        print(f"  Checkboxes: {json.dumps(group['checkboxes'], indent=2)}")
    
    # Find any iframes that might contain form elements
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    if iframes:
        print(f"\n[Dynamic] Found {len(iframes)} iframes:")
        for idx, iframe in enumerate(iframes):
            print(f"\nIframe {idx + 1}:")
            print(f"  ID: {iframe.get_attribute('id')}")
            print(f"  Name: {iframe.get_attribute('name')}")
            print(f"  Classes: {iframe.get_attribute('class')}")
    
    print("\n[Dynamic] === End of Page Analysis ===\n")
    return {
        'selects': selects,
        'checkbox_groups': checkbox_groups,
        'iframes': len(iframes) > 0
    }

def debug_print(message, level="INFO"):
    """Helper function for consistent debug output"""
    print(f"[{level}] {message}")

def normalize_text(text):
    """Normalize text for comparison by removing extra whitespace and converting to lowercase"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.lower().strip())

def handle_dynamic_questions(driver):
    """Handle dynamic questions on the role requirements page"""
    try:
        # Wait for form to be present with multiple possible selectors
        debug_print("Waiting for page to be fully loaded...")
        form_selectors = [
            (By.TAG_NAME, "form"),
            (By.CSS_SELECTOR, "form"),
            (By.CSS_SELECTOR, "div[role='form']"),
            (By.CSS_SELECTOR, "div[class*='form']"),
            (By.XPATH, "//form | //div[@role='form'] | //div[contains(@class, 'form')]")
        ]
        
        form = None
        for selector in form_selectors:
            try:
                form = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(selector)
                )
                debug_print(f"Found form using selector: {selector}")
                break
            except TimeoutException:
                continue
                
        if not form:
            debug_print("Form not found in main document, checking iframes...")
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            debug_print(f"Found {len(iframes)} iframes")
            
            for iframe in iframes:
                try:
                    iframe_id = iframe.get_attribute('id') or 'unnamed'
                    debug_print(f"Attempting to switch to iframe: {iframe_id}")
                    driver.switch_to.frame(iframe)
                    debug_print(f"Switched to iframe: {iframe_id}")
                    
                    for selector in form_selectors:
                        try:
                            form = WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located(selector)
                            )
                            debug_print(f"Found form in iframe using selector: {selector}")
                            break
                        except TimeoutException:
                            continue
                            
                    if form:
                        break
                    else:
                        driver.switch_to.default_content()
                        
                except Exception as e:
                    debug_print(f"Error switching to iframe: {str(e)}")
                    driver.switch_to.default_content()
                    continue
            
            if not form:
                debug_print("No form found in any iframe")
                return False

        # Find all question containers
        debug_print("Looking for question containers...")
        question_containers = []
        
        # Try multiple strategies to find question containers
        container_selectors = [
            "div[class*='question']",
            "div[class*='field']",
            "div[class*='form-group']",
            "div[class*='_1fz17ikhf']",
            "div[class*='container']"
        ]
        
        for selector in container_selectors:
            try:
                containers = form.find_elements(By.CSS_SELECTOR, selector)
                if containers:
                    question_containers.extend(containers)
                    debug_print(f"Found {len(containers)} containers using selector: {selector}")
            except Exception as e:
                debug_print(f"Error with selector {selector}: {str(e)}")
                continue
                
        if not question_containers:
            debug_print("No question containers found")
            return False
            
        debug_print(f"Found total of {len(question_containers)} question containers")
        
        # Process each question container
        fields = []
        for idx, container in enumerate(question_containers):
            try:
                # Find the question text
                question_text = None
                question_selectors = [
                    "strong",
                    "label",
                    "div[class*='question']",
                    "div[class*='label']"
                ]
                
                for selector in question_selectors:
                    try:
                        question_elem = container.find_element(By.CSS_SELECTOR, selector)
                        question_text = question_elem.text.strip()
                        if question_text:
                            break
                    except:
                        continue
                        
                if not question_text:
                    debug_print(f"No question text found in container {idx + 1}")
                    continue
                    
                debug_print(f"\nProcessing question {idx + 1}: {question_text}")
                
                # Find all options/checkboxes for this question
                options = []
                option_selectors = [
                    "input[type='checkbox']",
                    "input[type='radio']",
                    "div[class*='option']",
                    "div[class*='choice']"
                ]
                
                for selector in option_selectors:
                    try:
                        option_elements = container.find_elements(By.CSS_SELECTOR, selector)
                        for option in option_elements:
                            try:
                                # Get the full HTML element details
                                option_html = option.get_attribute('outerHTML')
                                option_id = option.get_attribute("id")
                                option_name = option.get_attribute("name")
                                option_class = option.get_attribute("class")
                                option_type = option.get_attribute("type")
                                option_value = option.get_attribute("value")
                                option_checked = option.get_attribute("aria-checked")
                                option_testid = option.get_attribute("data-testid")
                                
                                if not option_id:
                                    continue
                                    
                                # Try multiple strategies to find the label
                                label = None
                                label_strategies = [
                                    lambda: container.find_element(By.CSS_SELECTOR, f"label[for='{option_id}']").text,
                                    lambda: option.find_element(By.XPATH, "./following-sibling::label").text,
                                    lambda: option.find_element(By.XPATH, "./parent::div//label").text,
                                    lambda: option.find_element(By.XPATH, "./ancestor::div//label").text
                                ]
                                
                                for strategy in label_strategies:
                                    try:
                                        label = strategy()
                                        if label:
                                            break
                                    except:
                                        continue
                                        
                                if not label:
                                    debug_print(f"Could not find label for option: {option_id}")
                                    continue
                                    
                                option_details = {
                                    "id": option_id,
                                    "label": label.strip(),
                                    "element_details": {
                                        "html": option_html,
                                        "name": option_name,
                                        "class": option_class,
                                        "type": option_type,
                                        "value": option_value,
                                        "checked": option_checked,
                                        "testid": option_testid
                                    }
                                }
                                
                                debug_print(f"\nFound option for '{question_text}':")
                                debug_print(f"  Label: {label.strip()}")
                                debug_print(f"  ID: {option_id}")
                                debug_print(f"  Element HTML: {option_html}")
                                
                                options.append(option_details)
                                
                            except Exception as e:
                                debug_print(f"Error processing option: {str(e)}")
                                continue
                                
                    except Exception as e:
                        debug_print(f"Error with selector {selector}: {str(e)}")
                        continue
                        
                if options:
                    fields.append({
                        "question": question_text,
                        "options": options
                    })
                    debug_print(f"Found {len(options)} options for question: {question_text}")
                    
            except Exception as e:
                debug_print(f"Error processing container {idx + 1}: {str(e)}")
                continue
                
        if not fields:
            debug_print("No valid questions and options found")
            return False
            
        debug_print(f"\nFound {len(fields)} questions with options")
        debug_print(f"Fields: {json.dumps(fields, indent=2)}")
        
        # Get answers from LLM
        debug_print("Getting answers from LLM...")
        client = OpenAI()
        system_message = """You are an AI assistant helping to fill out a job application form. 
        You will be given a list of questions with their possible answers.
        For each question:
        1. Select the most appropriate answer based on the resume
        2. If no direct match exists, choose the closest option
        3. For work rights questions, if the resume shows Australian education or work, select appropriate visa status
        4. For experience level questions, count years of relevant experience and choose the appropriate range
        5. Always provide reasoning for your selection
        
        Return a JSON object with an 'answers' array containing objects with:
        - question: The exact question text
        - id: The exact ID of the option to select
        - choice: The exact label text of the choice to select
        - reasoning: Your reasoning for the selection"""
        
        user_message = f"""Here are all the questions with their possible answers:

{json.dumps(fields, indent=2)}

Please provide answers in the specified JSON format."""
        
        debug_print("Sending request to LLM...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1
        )
        
        debug_print("Got response from LLM")
        try:
            answers = json.loads(response.choices[0].message.content)
            debug_print(f"LLM raw response:\n {response.choices[0].message.content}")
            
            if not isinstance(answers, dict) or 'answers' not in answers:
                debug_print("Invalid response format from LLM")
                return False
                
            # Process each answer
            debug_print("Processing LLM answers...")
            for answer in answers['answers']:
                question = answer['question']
                field_id = answer['id']
                choice = answer['choice']
                reasoning = answer.get('reasoning', '')
                
                debug_print(f"\n[Dynamic] Answer for '{question}':")
                debug_print(f"  Selected: {choice}")
                debug_print(f"  Reasoning: {reasoning}")
                
                # Find the matching option details
                option_details = None
                for field in fields:
                    if field['question'] == question:
                        for option in field['options']:
                            if option['id'] == field_id:
                                option_details = option
                                break
                        if option_details:
                            break
                            
                if not option_details:
                    debug_print(f"Could not find option details for ID: {field_id}")
                    continue
                    
                debug_print(f"  Option details: {json.dumps(option_details, indent=2)}")
                
                # Try to click the checkbox
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        debug_print(f"Attempt {attempt + 1} to click checkbox...")
                        # Find the checkbox by ID
                        checkbox = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.ID, field_id))
                        )
                        debug_print("Found checkbox element")
                        
                        # Scroll to the checkbox
                        debug_print("Scrolling to checkbox...")
                        driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                        time.sleep(0.5)
                        
                        # Click the checkbox
                        debug_print("Clicking checkbox...")
                        checkbox.click()
                        debug_print(f"Successfully clicked checkbox for: {choice}")
                        time.sleep(0.5)  # Wait for click to register
                        break
                        
                    except (StaleElementReferenceException, ElementClickInterceptedException) as e:
                        debug_print(f"Error clicking checkbox (attempt {attempt + 1}): {str(e)}")
                        if attempt == max_retries - 1:
                            debug_print("Failed to click checkbox after all retries")
                            return False
                        time.sleep(1)
                    except Exception as e:
                        debug_print(f"Unexpected error: {str(e)}")
                        return False
            
            # Click continue button
            debug_print("Looking for continue button...")
            try:
                continue_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='continue-button']"))
                )
                debug_print("Found continue button, clicking...")
                continue_button.click()
                debug_print("Successfully clicked continue button")
                return True
            except Exception as e:
                debug_print(f"Error clicking continue button: {str(e)}")
                return False
                
        except json.JSONDecodeError as e:
            debug_print(f"Error parsing LLM response: {str(e)}")
            return False
        except Exception as e:
            debug_print(f"Unexpected error: {str(e)}")
            return False
            
    except Exception as e:
        debug_print(f"Unexpected error: {str(e)}")
        return False
    finally:
        # Always switch back to default content
        try:
            driver.switch_to.default_content()
        except:
            pass 