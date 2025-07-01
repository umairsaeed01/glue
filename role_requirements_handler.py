import os
import json
import hashlib
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from openai import OpenAI
from resume_summarizer import RÉSUMÉ_SUMMARY
from resume_summary_manager import ResumeSummaryManager

# NOTE: This file uses the OpenAI >=1.0.0 client interface. Do not use openai.ChatCompletion.create or openai.Completion.create.
# Only use: from openai import OpenAI; client = OpenAI(...); client.chat.completions.create(...)

# ------------------------------------------------------------
# 1) PATHS & CONSTANTS
# ------------------------------------------------------------
RESUME_SUMMARY_PATH = os.path.abspath("./resume_summary.txt")
PLAYBOOK_PATH = os.path.abspath("./role_requirements_playbook.json")

# Create empty playbook if it doesn't exist
if not os.path.exists(PLAYBOOK_PATH):
    with open(PLAYBOOK_PATH, "w") as f:
        json.dump({}, f)

# Load latest playbook
try:
    with open(PLAYBOOK_PATH, "r") as f:
        content = f.read().strip()
        if content:
            playbook = json.loads(content)
        else:
            playbook = {}
except (FileNotFoundError, json.JSONDecodeError):
    playbook = {}

def save_playbook():
    """Save the role playbook to disk."""
    with open(PLAYBOOK_PATH, "w") as f:
        json.dump(playbook, f, indent=2)

# -------------------------------
# QA CACHE CONFIG
# -------------------------------
QA_CACHE_PATH = os.path.abspath("./role_requirements_qa_cache.json")

def load_qa_cache():
    if os.path.exists(QA_CACHE_PATH):
        with open(QA_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_qa_cache(cache):
    with open(QA_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

# ------------------------------------------------------------
# MAIN HANDLER FUNCTION
# ------------------------------------------------------------
def handle_role_requirements_page(driver, resume_pdf_path=None, company_name=None):
    """
    Handle role requirements page with job-specific resume summary.
    
    Args:
        driver: Selenium WebDriver instance
        resume_pdf_path (str): Path to the job-specific resume PDF (optional)
        company_name (str): Company name for summary file naming (optional)
    """
    wait = WebDriverWait(driver, 10)
    
    # Debug logging to confirm which summary is being used
    print(f"[RoleReq] Resume PDF path: {resume_pdf_path}")
    print(f"[RoleReq] Company name: {company_name}")
    
    # Get job-specific resume summary on-demand
    summary_manager = ResumeSummaryManager()
    job_summary = summary_manager.get_job_specific_summary(
        resume_pdf_path=resume_pdf_path,
        company_name=company_name,
        fallback_summary=RÉSUMÉ_SUMMARY
    )
    
    # Debug logging to confirm which summary was used
    if resume_pdf_path and company_name:
        print(f"[RoleReq] Using job-specific summary for {company_name}")
        print(f"[RoleReq] Summary length: {len(job_summary)} characters")
        print(f"[RoleReq] Summary preview: {job_summary[:200]}...")
    else:
        print(f"[RoleReq] Using fallback summary (no resume path or company name provided)")
        print(f"[RoleReq] Fallback summary length: {len(job_summary)} characters")
    
    # 1) wait for at least one question to appear (more flexible detection)
    try:
        # Try multiple selectors for question detection
        question_selectors = [
            "label[for^='question-']",
            "strong",  # Questions in strong tags
            "input[type='checkbox']",  # Checkbox questions
            "input[type='radio']",  # Radio questions
            "select",  # Dropdown questions
            "textarea"  # Text input questions
        ]
        
        question_found = False
        for selector in question_selectors:
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                question_found = True
                print(f"[RoleReq] Found questions using selector: {selector}")
                break
            except:
                continue
                
        if not question_found:
            print("[RoleReq] No questions found on page with any selector.")
            return False
    except:
        print("[RoleReq] Error during question detection.")
        return False

    # 2) scrape all questions + options
    questions = []
    for lbl in driver.find_elements(By.CSS_SELECTOR, "label[for^='question-']"):
        q_id = lbl.get_attribute("for").strip()
        q_text = lbl.text.strip()
        if not q_text or not q_id:
            continue

        opts = []
        question_type = "unknown"
        
        # try <select> dropdown
        try:
            sel = driver.find_element(By.CSS_SELECTOR, f"select[id='{q_id}']")
            for o in sel.find_elements(By.TAG_NAME, "option"):
                t = o.text.strip()
                if t: opts.append(t)
            question_type = "dropdown"
        except:
            # try textarea
            try:
                textarea = driver.find_element(By.CSS_SELECTOR, f"textarea[id='{q_id}']")
                question_type = "textarea"
                # For textarea, we don't need options - the LLM will generate text
                opts = ["[TEXT_INPUT]"]
            except:
                # fallback: radio/checkbox
                radio_name = None  # Capture the name attribute for radio buttons
                for inp in driver.find_elements(By.CSS_SELECTOR, f"input[name^='{q_id}'], input[id^='{q_id}']"):
                    rid = inp.get_attribute("id")
                    if not rid: continue
                    try:
                        lab2 = driver.find_element(By.CSS_SELECTOR, f"label[for='{rid}']")
                        opts.append(lab2.text.strip())
                        # Capture the name attribute from the first radio button
                        if not radio_name and inp.get_attribute("type") == "radio":
                            radio_name = inp.get_attribute("name")
                    except: 
                        pass
                if opts:
                    question_type = "radio_checkbox"

        if not opts and question_type != "textarea":
            continue

        multi = bool(driver.find_elements(By.CSS_SELECTOR,
            f"input[type='checkbox'][name^='{q_id}']"))
        question_obj = {
            "id":    q_id,
            "text":  q_text,
            "options": opts,
            "multi": multi,
            "type":  question_type
        }
        
        # Add name attribute for radio buttons if available
        if question_type == "radio_checkbox" and radio_name:
            question_obj["name"] = radio_name
            
        questions.append(question_obj)

    # 2b) Add radio button questions from fieldsets (NEW ENHANCEMENT)
    try:
        fieldsets = driver.find_elements(By.CSS_SELECTOR, "fieldset[role='radiogroup']")
        for fieldset in fieldsets:
            try:
                # Extract question text from legend
                legend = fieldset.find_element(By.TAG_NAME, "legend")
                strong = legend.find_element(By.TAG_NAME, "strong")
                q_text = strong.text.strip()
                
                if not q_text:
                    continue
                
                # Extract radio button options and name
                opts = []
                radio_name = None
                radios = fieldset.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                
                for radio in radios:
                    radio_id = radio.get_attribute("id")
                    if not radio_id:
                        continue
                    # Capture the name attribute from the first radio button
                    if not radio_name:
                        radio_name = radio.get_attribute("name")
                    try:
                        label = driver.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                        label_text = label.text.strip()
                        if label_text:
                            opts.append(label_text)
                    except:
                        pass
                
                if opts:
                    question_obj = {
                        "id": fieldset.get_attribute("id") or f"fieldset_{len(questions)}",
                        "text": q_text,
                        "options": opts,
                        "multi": False,
                        "type": "radio"
                    }
                    
                    # Add name attribute if available
                    if radio_name:
                        question_obj["name"] = radio_name
                        
                    questions.append(question_obj)
                    print(f"[RoleReq] Found radio button question: {q_text} with options: {opts}")
                    
            except Exception as e:
                print(f"[RoleReq] Error processing fieldset: {e}")
                continue
    except Exception as e:
        print(f"[RoleReq] Error finding fieldsets: {e}")

    # 2a) ENHANCEMENT: Also extract grouped checkbox questions by name (like dynamic_handler)
    def extract_checkbox_groups_by_name(driver):
        grouped = {}
        for cb in driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
            name = cb.get_attribute("name")
            if not name:
                continue
            grouped.setdefault(name, []).append(cb)
        found = []
        for name, group in grouped.items():
            if not group:
                continue
            # Try to find question text in ancestor strong tag
            try:
                q_text = group[0].find_element(By.XPATH, "./ancestor::div[.//strong][1]//strong").text.strip()
            except:
                q_text = name
            # Avoid duplicates (if already in questions from main logic)
            if any(q.get("text") == q_text for q in questions):
                continue
            opts = []
            for cb in group:
                cb_id = cb.get_attribute("id")
                if not cb_id:
                    continue
                try:
                    lbl = driver.find_element(By.CSS_SELECTOR, f"label[for='{cb_id}']").text.strip()
                except:
                    lbl = cb.get_attribute("value") or cb_id
                opts.append(lbl)
            if q_text and opts:
                found.append({
                    "id": name,  # Use name as id for group
                    "text": q_text,
                    "options": opts,
                    "multi": True,
                    "type": "checkbox_group"
                })
        return found

    # Add these grouped checkbox questions (if any)
    questions.extend(extract_checkbox_groups_by_name(driver))

    # 2c) ENHANCED EXTRACTORS: Add comprehensive extractors from dynamic_handler
    def extract_selects_enhanced(driver):
        """Enhanced select dropdown extraction"""
        fields = []
        try:
            for sel in driver.find_elements(By.TAG_NAME, "select"):
                try:
                    # Try multiple strategies to find the question text
                    question = None
                    
                    # Strategy 1: Look for label with for attribute matching select id
                    select_id = sel.get_attribute("id")
                    if select_id:
                        try:
                            label = driver.find_element(By.CSS_SELECTOR, f"label[for='{select_id}']")
                            strong = label.find_element(By.TAG_NAME, "strong")
                            question = strong.text.strip()
                        except:
                            pass
                    
                    # Strategy 2: Original strategy (preceding strong)
                    if not question:
                        question = sel.find_element(By.XPATH, "preceding::strong[1]").text.strip()
                    
                    # Strategy 3: Fallback to name attribute
                    if not question:
                        question = sel.get_attribute("name") or "Unnamed select question"
                        
                except:
                    question = sel.get_attribute("name") or "Unnamed select question"
                name = sel.get_attribute("name")
                options = []
                for opt in sel.find_elements(By.TAG_NAME, "option"):
                    val = opt.get_attribute("value")
                    txt = opt.text.strip()
                    if val:
                        options.append({"value": val, "label": txt})
                if question and name and options:
                    # Avoid duplicates
                    if not any(q.get("text") == question for q in questions):
                        fields.append({
                            "question": question,
                            "type": "select",
                            "name": name,
                            "options": options
                        })
        except Exception as e:
            print(f"[RoleReq] extract_selects_enhanced error: {e}")
        return fields

    def extract_by_container(driver):
        """Extract checkbox groups via container classname -> <strong> + inputs"""
        fields = []
        seen_questions = set()
        try:
            containers = driver.find_elements(By.CSS_SELECTOR, "div[class*='_1fz17ikh']")
            for c in containers:
                try:
                    q = c.find_element(By.TAG_NAME, "strong").text.strip()
                except:
                    continue
                if not q or q in seen_questions:
                    continue
                seen_questions.add(q)
                # Avoid duplicates
                if any(q.get("text") == q for q in questions):
                    continue
                opts = []
                for cb in c.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
                    cb_id = cb.get_attribute("id")
                    if not cb_id:
                        continue
                    try:
                        lbl = c.find_element(By.CSS_SELECTOR, f"label[for='{cb_id}']").text.strip()
                    except:
                        lbl = None
                    if lbl:
                        opts.append({"id": cb_id, "label": lbl})
                if opts:
                    fields.append({
                        "question": q,
                        "type": "multiselect",
                        "options": opts
                    })
        except Exception as e:
            print(f"[RoleReq] extract_by_container error: {e}")
        return fields

    def extract_all_checkboxes(driver):
        """Fallback — treat every checkbox on the page as one big multi"""
        opts = []
        for cb in driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
            cb_id = cb.get_attribute("id")
            if not cb_id:
                continue
            try:
                lbl = driver.find_element(By.CSS_SELECTOR, f"label[for='{cb_id}']").text.strip()
            except:
                lbl = cb_id
            opts.append({"id": cb_id, "label": lbl})
        if not opts:
            return []
        # Only add if no other questions found
        if not questions:
            return [{
                "question": "Select all that apply",
                "type": "multiselect",
                "options": opts
            }]
        return []

    def extract_radio_groups(driver):
        """Extract radio button groups (yes/no questions)"""
        fields = []
        radio_groups = {}
        
        try:
            # Find all radio buttons and group by name
            radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            print(f"[RoleReq] extract_radio_groups: Found {len(radios)} radio buttons")
            
            for radio in radios:
                name = radio.get_attribute("name")
                if not name:
                    continue
                if name not in radio_groups:
                    radio_groups[name] = []
                radio_groups[name].append(radio)
            
            print(f"[RoleReq] extract_radio_groups: Grouped into {len(radio_groups)} groups")
            
            # For each group, find the question and options
            for name, radios in radio_groups.items():
                if len(radios) < 2:  # Skip single radio buttons
                    continue
                    
                print(f"[RoleReq] extract_radio_groups: Processing group '{name}' with {len(radios)} radios")
                
                # Find question text using multiple strategies
                question_text = None
                first_radio = radios[0]
                
                # Strategy 1: Look for nearby strong tag
                try:
                    question_text = first_radio.find_element(By.XPATH, "./ancestor::div[.//strong][1]//strong").text.strip()
                    print(f"[RoleReq] extract_radio_groups: Found question via Strategy 1: {question_text}")
                except:
                    pass
                
                # Strategy 2: Look for fieldset legend
                if not question_text:
                    try:
                        fieldset = first_radio.find_element(By.XPATH, "./ancestor::fieldset[1]")
                        legend = fieldset.find_element(By.TAG_NAME, "legend")
                        question_text = legend.text.strip()
                        print(f"[RoleReq] extract_radio_groups: Found question via Strategy 2: {question_text}")
                    except:
                        pass
                
                # Strategy 3: Look for nearby label or div with question text
                if not question_text:
                    try:
                        # Look for a label that contains the radio button
                        parent_label = first_radio.find_element(By.XPATH, "./ancestor::label[1]")
                        question_text = parent_label.text.strip()
                        print(f"[RoleReq] extract_radio_groups: Found question via Strategy 3: {question_text}")
                    except:
                        pass
                
                # Strategy 4: Use name as fallback
                if not question_text:
                    question_text = name.replace("_", " ").title()
                    print(f"[RoleReq] extract_radio_groups: Using fallback question: {question_text}")
                
                # Avoid duplicates
                if any(q.get("text") == question_text for q in questions):
                    print(f"[RoleReq] extract_radio_groups: Skipping duplicate question: {question_text}")
                    continue
                
                # Get options (value and visible text)
                options = []
                for radio in radios:
                    value = radio.get_attribute("value")
                    if not value:
                        continue
                        
                    # Find the label for this radio button
                    radio_id = radio.get_attribute("id")
                    label_text = None
                    
                    if radio_id:
                        try:
                            label = driver.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                            label_text = label.text.strip()
                        except:
                            pass
                    
                    # If no label found, try to get text from parent or sibling
                    if not label_text:
                        try:
                            # Look for text in the same container
                            container = radio.find_element(By.XPATH, "./ancestor::div[contains(@class, '_1fz17ikh') or contains(@class, 'question')][1]")
                            label_text = container.text.strip()
                        except:
                            label_text = value  # Use value as fallback
                    
                    options.append({"value": value, "label": label_text})
                
                if question_text and options:
                    fields.append({
                        "question": question_text,
                        "name": name,
                        "type": "radio",
                        "options": options
                    })
                    print(f"[RoleReq] extract_radio_groups: Added question '{question_text}' with {len(options)} options")
                    
        except Exception as e:
            print(f"[RoleReq] extract_radio_groups error: {e}")
        
        return fields

    def extract_textareas_enhanced(driver):
        """Enhanced textarea extraction"""
        fields = []
        try:
            # Find all textarea elements
            textareas = driver.find_elements(By.TAG_NAME, "textarea")
            
            for textarea in textareas:
                textarea_id = textarea.get_attribute("id")
                if not textarea_id:
                    continue
                    
                # Find the label for this textarea
                try:
                    label = driver.find_element(By.CSS_SELECTOR, f"label[for='{textarea_id}']")
                    question_text = label.text.strip()
                except:
                    # If no label found, try to get text from parent container
                    try:
                        container = textarea.find_element(By.XPATH, "./ancestor::div[contains(@class, '_1fz17ikh') or contains(@class, 'question')][1]")
                        question_text = container.text.strip()
                    except:
                        question_text = textarea_id.replace("_", " ").title()
                
                # Avoid duplicates
                if not any(q.get("text") == question_text for q in questions):
                    if question_text:
                        fields.append({
                            "question": question_text,
                            "name": textarea.get_attribute("name") or textarea_id,
                            "id": textarea_id,
                            "type": "textarea"
                        })
                        
        except Exception as e:
            print(f"[RoleReq] extract_textareas_enhanced error: {e}")
        
        return fields

    def extract_radios_enhanced(driver):
        """Enhanced radio button extraction from fieldsets"""
        fields = []
        # Find all fieldsets with role radiogroup
        for fieldset in driver.find_elements(By.TAG_NAME, "fieldset"):
            if fieldset.get_attribute("role") == "radiogroup":
                try:
                    legend = fieldset.find_element(By.TAG_NAME, "legend")
                    question_text = legend.text.strip()
                    
                    # Avoid duplicates
                    if any(q.get("text") == question_text for q in questions):
                        continue
                        
                    options = []
                    for radio in fieldset.find_elements(By.CSS_SELECTOR, "input[type='radio']"):
                        value = radio.get_attribute("value")
                        # Find label for this radio
                        label = None
                        radio_id = radio.get_attribute("id")
                        if radio_id:
                            try:
                                label_elem = fieldset.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                                label = label_elem.text.strip()
                            except:
                                pass
                        if not label:
                            # fallback: try parent label
                            try:
                                label_elem = radio.find_element(By.XPATH, "ancestor::label")
                                label = label_elem.text.strip()
                            except:
                                label = value
                        options.append({"label": label, "value": value})
                    if question_text and options:
                        fields.append({
                            "type": "radio",
                            "name": radio.get_attribute("name"),
                            "question": question_text,
                            "options": options
                        })
                except Exception as e:
                    print(f"[RoleReq] Error processing fieldset: {e}")
                    continue
        return fields

    # Run all enhanced extractors and add their results
    enhanced_extractors = [
        extract_selects_enhanced,
        extract_textareas_enhanced,
        extract_by_container,
        extract_all_checkboxes,
        extract_radio_groups,
        extract_radios_enhanced,
    ]

    print(f"[RoleReq] Running {len(enhanced_extractors)} enhanced extractors...")
    total_enhanced_questions = 0
    
    for extractor in enhanced_extractors:
        try:
            additional_questions = extractor(driver)
            if additional_questions:
                print(f"[RoleReq] Enhanced extractor {extractor.__name__} found {len(additional_questions)} questions:")
                for q in additional_questions:
                    print(f"  - {q.get('question', 'No question text')} (type: {q.get('type', 'unknown')})")
                
                # Check for duplicates before adding
                questions_before = len(questions)
                questions.extend(additional_questions)
                questions_after = len(questions)
                actually_added = questions_after - questions_before
                
                if actually_added < len(additional_questions):
                    print(f"[RoleReq] ⚠️ {len(additional_questions) - actually_added} questions were duplicates and skipped")
                
                total_enhanced_questions += actually_added
                print(f"[RoleReq] Enhanced extractor {extractor.__name__} added {actually_added} new questions")
            else:
                print(f"[RoleReq] Enhanced extractor {extractor.__name__} found 0 questions")
        except Exception as e:
            print(f"[RoleReq] Enhanced extractor {extractor.__name__} error: {e}")
    
    print(f"[RoleReq] Total enhanced questions added: {total_enhanced_questions}")
    print(f"[RoleReq] Total questions after all extractors: {len(questions)}")

    if not questions:
        print("[RoleReq] no valid Q→options sets scraped.")
        return False

    # 3) build a single prompt
    system = {
        "role": "system",
        "content":
            "You are an assistant that fills out job-application forms on my behalf.  "
            "I will give you a list of questions and their available options, plus my résumé summary.  "
            "For each question pick the option (or options) that best fit my background.  "
            "For text input questions (marked as [TEXT_INPUT]), provide a relevant, professional response based on my background. "
            "Return **only** valid JSON, in this exact shape:\n\n"
            "{\n"
            '  "answers": [\n'
            '    { "question": "<the full question text>",\n'
            '      "selected": "<one option>" | ["<opt1>","<opt2>"] | "<text response for textarea>"\n'
            "    },\n"
            "    …\n"
            "  ]\n"
            "}"
    }
    user = {
        "role": "user",
        "content":
            "Résumé summary:\n\"\"\"\n" + job_summary + "\n\"\"\"\n\n"
            "Here are the questions + options:\n" +
            json.dumps(questions, indent=2)
    }

    client = OpenAI()
    rsp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[system, user],
        temperature=0.0
    )

    # ——— GPT-3.5-turbo usage logging ———
    try:
        usage = rsp.usage
        pt = usage.prompt_tokens
        ct = usage.completion_tokens
        tt = usage.total_tokens
        ir, orate = (0.03, 0.06) if "gpt-4" in rsp.model else (0.0015, 0.002)
        ic = pt * ir / 1000
        oc = ct * orate / 1000
        tc = ic + oc
        print(f"[{rsp.model} usage] prompt={pt}, completion={ct}, total={tt} tokens;"
              f" cost_input=${ic:.4f}, cost_output=${oc:.4f}, cost_total=${tc:.4f}")
    except Exception:
        print(f"[{rsp.model} usage] ⚠️ failed to read response.usage")
    # ———————————————————————

    raw = rsp.choices[0].message.content
    # strip any ```json fences if present:
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if m:
        raw = m.group(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("[RoleReq] ❌ could not parse JSON from LLM:")
        print(raw)
        return False

    answer_map = { ent["question"]: ent["selected"] 
                   for ent in data.get("answers", []) }

    # 4) apply each answer
    question_logs = []  # Collect question/answer logs
    for q in questions:
        sel = answer_map.get(q["text"])
        if not sel:
            print(f'[RoleReq] no answer for "{q["text"]}" – skipping.')
            continue

        # SOLUTION 1: Smart Answer Type Detection - Convert array to string for radio buttons
        if q["type"] == "radio" and isinstance(sel, list):
            # Convert array to string for radio buttons
            sel = sel[0] if sel else ""
            print(f'[RoleReq] Converted array answer {sel} to string for radio button')
        elif q["type"] == "radio" and isinstance(sel, str):
            # Already correct format
            pass

        print(f'[RoleReq] Processing question: "{q["text"]}" with answer: {sel}')
        
        if q["type"] == "textarea":
            # Handle text input
            try:
                textarea = driver.find_element(By.CSS_SELECTOR, f"textarea[id='{q['id']}']")
                textarea.clear()
                textarea.send_keys(sel)
                print(f'[RoleReq] Filled textarea for "{q["text"]}" with: {sel[:50]}...')
                question_logs.append(f"Q: {q['text']} | A: {sel[:100]}...")
            except Exception as e:
                print(f'[RoleReq] Error filling textarea for "{q["text"]}": {e}')
        elif q["type"] == "radio":
            # Handle radio button questions (NEW ENHANCEMENT)
            try:
                selected_radio = None
                
                # Strategy 1: Find the specific fieldset containing this question
                question_fieldset = None
                try:
                    # Look for fieldset that contains the question text in its legend
                    fieldsets = driver.find_elements(By.TAG_NAME, "fieldset")
                    for fieldset in fieldsets:
                        try:
                            legend = fieldset.find_element(By.TAG_NAME, "legend")
                            legend_text = legend.text.strip()
                            if q["text"] in legend_text or legend_text in q["text"]:
                                question_fieldset = fieldset
                                break
                        except:
                            continue
                except:
                    pass
                
                # Strategy 2: If no fieldset found, try to find by question name/ID
                if not question_fieldset and "name" in q:
                    try:
                        # Find radio buttons with the specific name attribute
                        radio_buttons = driver.find_elements(By.CSS_SELECTOR, f"input[type='radio'][name='{q['name']}']")
                        for radio in radio_buttons:
                            radio_id = radio.get_attribute("id")
                            if not radio_id:
                                continue
                            try:
                                label = driver.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                                label_text = label.text.strip()
                                
                                # Check if this radio button's label matches our selection
                                if label_text.lower() == sel.lower():
                                    selected_radio = radio
                                    break
                            except:
                                continue
                    except:
                        pass
                
                # Strategy 3: If fieldset found, search within it
                if question_fieldset and not selected_radio:
                    try:
                        radio_buttons = question_fieldset.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                        for radio in radio_buttons:
                            radio_id = radio.get_attribute("id")
                            if not radio_id:
                                continue
                            try:
                                label = question_fieldset.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                                label_text = label.text.strip()
                                
                                # Check if this radio button's label matches our selection
                                if label_text.lower() == sel.lower():
                                    selected_radio = radio
                                    break
                            except:
                                continue
                    except:
                        pass
                
                # Strategy 4: Fallback to original method (search all radio buttons)
                if not selected_radio:
                    print(f'[RoleReq] Warning: Using fallback search for "{q["text"]}"')
                    radio_buttons = driver.find_elements(By.CSS_SELECTOR, f"input[type='radio']")
                    
                    for radio in radio_buttons:
                        radio_id = radio.get_attribute("id")
                        if not radio_id:
                            continue
                        try:
                            label = driver.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                            label_text = label.text.strip()
                            
                            # Check if this radio button's label matches our selection
                            if label_text.lower() == sel.lower():
                                selected_radio = radio
                                break
                        except:
                            continue
                
                if selected_radio:
                    selected_radio.click()
                    print(f'[RoleReq] Selected radio button "{sel}" for "{q["text"]}"')
                    question_logs.append(f"Q: {q['text']} | A: {sel}")
                else:
                    print(f'[RoleReq] Could not find radio button with text "{sel}" for "{q["text"]}"')
                    question_logs.append(f"Q: {q['text']} | A: ERROR - Could not select '{sel}'")
            except Exception as e:
                print(f'[RoleReq] Error selecting radio button for "{q["text"]}": {e}')
        elif q["type"] == "checkbox_group":
            # Handle grouped checkboxes (multi-select)
            for choice in sel:
                # Find the checkbox by label
                try:
                    cb = None
                    for cbx in driver.find_elements(By.CSS_SELECTOR, f"input[type='checkbox'][name='{q['id']}']"):
                        cb_id = cbx.get_attribute("id")
                        label = driver.find_element(By.CSS_SELECTOR, f"label[for='{cb_id}']").text.strip()
                        if label == choice:
                            cb = cbx
                            break
                    if cb and not cb.is_selected():
                        cb.click()
                        print(f'[RoleReq] Checked: {choice} for "{q["text"]}"')
                        question_logs.append(f"Q: {q['text']} | A: {choice}")
                except Exception as e:
                    print(f'[RoleReq] Error checking box for "{choice}" in "{q["text"]}": {e}')
        elif q["type"] == "select":
            # Handle enhanced select dropdowns
            try:
                select_element = driver.find_element(By.NAME, q["name"])
                from selenium.webdriver.support.ui import Select
                dropdown = Select(select_element)
                
                # Try to match by value first (for LLM returning internal value)
                try:
                    dropdown.select_by_value(sel)
                    print(f'[RoleReq] Selected dropdown value {sel} for "{q["text"]}"')
                    question_logs.append(f"Q: {q['text']} | A: {sel}")
                except:
                    # Fallback: try to match by label (for LLM returning visible label)
                    try:
                        dropdown.select_by_visible_text(sel)
                        print(f'[RoleReq] Selected dropdown label "{sel}" for "{q["text"]}"')
                        question_logs.append(f"Q: {q['text']} | A: {sel}")
                    except Exception as e:
                        print(f'[RoleReq] Failed to select dropdown option "{sel}" for "{q["text"]}": {e}')
                        question_logs.append(f"Q: {q['text']} | A: ERROR - Could not select '{sel}'")
            except Exception as e:
                print(f'[RoleReq] Error selecting dropdown for "{q["text"]}": {e}')
        elif q["type"] == "multiselect":
            # Handle multiselect checkboxes from enhanced extractors
            for choice in sel:
                try:
                    # Find the checkbox by matching the option
                    opt = next((o for o in q["options"] if o.get("label") == choice), None)
                    if opt:
                        cb = driver.find_element(By.ID, opt["id"])
                        if not cb.is_selected():
                            cb.click()
                            print(f'[RoleReq] Checked: {choice} for "{q["text"]}"')
                            question_logs.append(f"Q: {q['text']} | A: {choice}")
                    else:
                        print(f'[RoleReq] Option not found for: {choice} in "{q["text"]}"')
                except Exception as e:
                    print(f'[RoleReq] Error checking box for "{choice}" in "{q["text"]}": {e}')
        elif isinstance(sel, list):
            # multi-select checkboxes
            for choice in sel:
                xpath = f"//label[contains(.,{json.dumps(choice)})]/preceding-sibling::input"
                driver.find_element(By.XPATH, xpath).click()
                question_logs.append(f"Q: {q['text']} | A: {choice}")
        else:
            # single <select> dropdown
            dd = driver.find_element(By.CSS_SELECTOR, f"select[id='{q['id']}']")
            for o in dd.find_elements(By.TAG_NAME, "option"):
                if o.text.strip() == sel:
                    o.click()
                    question_logs.append(f"Q: {q['text']} | A: {sel}")
                    break

    print(f"[RoleReq] Processed {len(question_logs)} questions")
    print(f"[RoleReq] Question logs: {question_logs}")

    # 5) click "Continue"
    btn = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "button[data-testid='continue-button']")))
    btn.click()
    return True, "\n".join(question_logs) 