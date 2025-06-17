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
openai.log = "debug"
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
        # Wait for form to be present
        debug_print("Waiting for form...")
        form = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
        
        # Find question containers - using the specific class we know works
        debug_print("Finding questions...")
        question_containers = form.find_elements(By.CSS_SELECTOR, "div[class*='_1fz17ikhf']")
        
        if not question_containers:
            debug_print("No questions found")
            return False
            
        debug_print(f"Found {len(question_containers)} questions")
        
        # Process each question
        fields = []
        seen_questions = set()  # Track unique questions
        
        for container in question_containers:
            try:
                # Get question text
                question_elem = container.find_element(By.TAG_NAME, "strong")
                question_text = question_elem.text.strip()
                
                if not question_text or question_text in seen_questions:
                    continue
                    
                seen_questions.add(question_text)
                debug_print(f"\nProcessing: {question_text}")
                
                # Find checkboxes and their labels
                options = []
                checkboxes = container.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                
                for checkbox in checkboxes:
                    try:
                        option_id = checkbox.get_attribute("id")
                        if not option_id:
                            continue
                            
                        # Get label
                        label = None
                        label_elem = None
                        try:
                            label_elem = container.find_element(By.CSS_SELECTOR, f"label[for='{option_id}']")
                            label = label_elem.text
                        except:
                            try:
                                label_elem = checkbox.find_element(By.XPATH, "./following-sibling::label")
                                label = label_elem.text
                            except:
                                continue
                                
                        if not label:
                            continue
                            
                        # Get full element details - only store serializable data
                        element_details = {
                            "id": option_id,
                            "name": checkbox.get_attribute("name"),
                            "class": checkbox.get_attribute("class"),
                            "type": checkbox.get_attribute("type"),
                            "value": checkbox.get_attribute("value"),
                            "aria-checked": checkbox.get_attribute("aria-checked"),
                            "data-testid": checkbox.get_attribute("data-testid"),
                            "css_selector": f"#{option_id}",
                            "xpath": driver.execute_script("""
                                function getXPath(element) {
                                    if (element.id !== '')
                                        return `//*[@id="${element.id}"]`;
                                    if (element === document.body)
                                        return '/html/body';
                                    let ix = 0;
                                    const siblings = element.parentNode.childNodes;
                                    for (let i = 0; i < siblings.length; i++) {
                                        const sibling = siblings[i];
                                        if (sibling === element)
                                            return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                                            ix++;
                                    }
                                }
                                return getXPath(arguments[0]);
                            """, checkbox)
                        }
                        
                        # Get label element details - only store serializable data
                        if label_elem:
                            element_details["label_element"] = {
                                "text": label,
                                "class": label_elem.get_attribute("class"),
                                "css_selector": driver.execute_script("""
                                    function getCssPath(element) {
                                        if (element.id !== '')
                                            return '#' + element.id;
                                        if (element === document.body)
                                            return 'body';
                                        let path = '';
                                        while (element.parentNode) {
                                            let tag = element.tagName.toLowerCase();
                                            let siblings = Array.from(element.parentNode.children).filter(e => e.tagName === element.tagName);
                                            if (siblings.length > 1) {
                                                let index = siblings.indexOf(element) + 1;
                                                tag += ':nth-child(' + index + ')';
                                            }
                                            path = tag + (path ? ' > ' + path : '');
                                            element = element.parentNode;
                                            if (element.id) {
                                                path = '#' + element.id + ' > ' + path;
                                                break;
                                            }
                                        }
                                        return path;
                                    }
                                    return getCssPath(arguments[0]);
                                """, label_elem),
                                "xpath": driver.execute_script("""
                                    function getXPath(element) {
                                        if (element.id !== '')
                                            return `//*[@id="${element.id}"]`;
                                        if (element === document.body)
                                            return '/html/body';
                                        let ix = 0;
                                        const siblings = element.parentNode.childNodes;
                                        for (let i = 0; i < siblings.length; i++) {
                                            const sibling = siblings[i];
                                            if (sibling === element)
                                                return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                                            if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                                                ix++;
                                        }
                                    }
                                    return getXPath(arguments[0]);
                                """, label_elem)
                            }
                        
                        # Store option details - only serializable data
                        options.append({
                            "id": option_id,
                            "label": label.strip(),
                            "element_details": element_details
                        })
                        
                        debug_print(f"  Found option: {label.strip()}")
                        debug_print(f"    Element details: {json.dumps(element_details, indent=2)}")
                        
                    except Exception as e:
                        debug_print(f"Error with option: {str(e)}")
                        continue
                        
                if options:
                    fields.append({
                        "question": question_text,
                        "options": options
                    })
                    
            except Exception as e:
                debug_print(f"Error with question: {str(e)}")
                continue
                
        if not fields:
            debug_print("No valid questions found")
            return False
            
        debug_print(f"\nFound {len(fields)} questions")
        
        # Get answers from LLM
        debug_print("Getting answers from LLM...")
        client = OpenAI()
        system_message = """You are an AI assistant helping to fill out a job application form. 
        For each question, select the most appropriate answer based on the resume.
        Return a JSON object with an 'answers' array containing objects with:
        - name: The unique name attribute of the question's input element
        - answerIndex: The zero-based index of the option to select (e.g., 0 for first option, 1 for second, etc.)
        - reasoning: Your reasoning for the selection"""
        
        # Convert fields to JSON string with proper formatting
        fields_json = json.dumps(fields, indent=2, ensure_ascii=False)
        
        user_message = f"""Here are the questions with their possible answers:

{fields_json}

Please provide answers in the specified JSON format, using zero-based indices for the options."""
        
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,
            max_tokens=32768,
            response_format={ "type": "json_object" }
        )
        
        try:
            answers = json.loads(response.choices[0].message.content)
            
            if not isinstance(answers, dict) or 'answers' not in answers:
                debug_print("Invalid LLM response")
                return False

            # First, collect all checkboxes and group them by name
            debug_print("\nCollecting and grouping checkboxes...")
            all_checkboxes = form.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            groups_by_name = {}
            
            for checkbox in all_checkboxes:
                name = checkbox.get_attribute("name")
                if not name:
                    continue
                if name not in groups_by_name:
                    groups_by_name[name] = []
                groups_by_name[name].append(checkbox)
            
            debug_print(f"Found {len(groups_by_name)} checkbox groups")
            
            # For each group, find its question container and text
            question_groups = {}
            for name, checkboxes in groups_by_name.items():
                if not checkboxes:
                    continue
                    
                # Start from the first checkbox's parent
                wrapper = checkboxes[0].find_element(By.XPATH, "./ancestor::div[contains(@class,'_1fz17ikhf')]")
                if not wrapper:
                    debug_print(f"Could not find wrapper for group {name}")
                    continue
                
                # Verify this wrapper contains all checkboxes in the group
                group_checkboxes = wrapper.find_elements(By.CSS_SELECTOR, f"input[name='{name}']")
                if len(group_checkboxes) != len(checkboxes):
                    debug_print(f"Wrapper does not contain all checkboxes for group {name}")
                    continue
                
                # Get the question text and store with name as key
                try:
                    question_elem = wrapper.find_element(By.TAG_NAME, "strong")
                    question_text = question_elem.text.strip()
                    if question_text:
                        question_groups[name] = {
                            'text': question_text,
                            'checkboxes': checkboxes
                        }
                        debug_print(f"Found question: {question_text} with {len(checkboxes)} options")
                except:
                    debug_print(f"Could not find question text for group {name}")
                    continue
            
            # Process each answer
            for answer in answers['answers']:
                question_name = answer['name']
                answer_index = answer['answerIndex']
                
                # Get the question group
                question_group = question_groups.get(question_name)
                if not question_group:
                    debug_print(f"No question group found for name: {question_name}")
                    continue
                
                question_text = question_group['text']
                checkboxes = question_group['checkboxes']
                
                debug_print(f"\nProcessing question: {question_text}")
                debug_print(f"Selected answer index: {answer_index}")
                
                # Validate index
                if answer_index < 0 or answer_index >= len(checkboxes):
                    debug_print(f"Invalid answer index {answer_index} for {len(checkboxes)} options")
                    continue
                
                # Get the target checkbox
                target_checkbox = checkboxes[answer_index]
                
                # Debug print before clicking
                html = target_checkbox.get_attribute("outerHTML")
                debug_print(f"→ Clicking checkbox at index {answer_index}:\n{html}\n")
                
                # log human-readable audit for each pick
                reasoning = answer.get("reasoning", "").strip()
                label = wrapper.find_element(
                    By.CSS_SELECTOR,
                    f"label[for='{target_checkbox.get_attribute('id')}']"
                ).text.strip()
                debug_print(f"🔹 Question: {question_text}")
                debug_print(f"🔸 Chosen:   [{answer_index}] "{label}"")
                debug_print(f"   Reason:   {reasoning}\n")
                
                # Scroll into view and click
                driver.execute_script("arguments[0].scrollIntoView(true);", target_checkbox)
                time.sleep(0.5)
                
                try:
                    target_checkbox.click()
                except:
                    driver.execute_script("arguments[0].click();", target_checkbox)
                
                # Verify the click worked
                if target_checkbox.get_attribute("aria-checked") != "true":
                    raise Exception("Checkbox not checked after click")
                
                debug_print(f"Successfully selected option at index {answer_index}")
                time.sleep(0.5)
            
            # Click continue
            try:
                continue_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='continue-button']"))
                )
                continue_button.click()
                debug_print("Clicked continue")
                return True
            except Exception as e:
                debug_print(f"Error clicking continue: {str(e)}")
                return False
                
        except Exception as e:
            debug_print(f"Error processing answers: {str(e)}")
            return False
            
    except Exception as e:
        debug_print(f"Error: {str(e)}")
        return False
    finally:
        try:
            driver.switch_to.default_content()
        except:
            pass 