#!/usr/bin/env python3
import json
import re
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
)
from openai import OpenAI
from resume_summarizer import RÉSUMÉ_SUMMARY
from resume_summary_manager import ResumeSummaryManager

# ─────────────────────────────────────────────────────────────────────────────
# Extractor #1: single‐choice <select> elements
# ─────────────────────────────────────────────────────────────────────────────
def extract_selects(driver, form):
    fields = []
    try:
        for sel in form.find_elements(By.TAG_NAME, "select"):
            try:
                # Try multiple strategies to find the question text
                question = None
                
                # Strategy 1: Look for label with for attribute matching select id
                select_id = sel.get_attribute("id")
                if select_id:
                    try:
                        label = form.find_element(By.CSS_SELECTOR, f"label[for='{select_id}']")
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
                fields.append({
                    "question": question,
                    "type": "select",
                    "name": name,
                    "options": options
                })
    except Exception as e:
        print(f"[extract_selects] error: {e}")
    return fields

# ─────────────────────────────────────────────────────────────────────────────
# Extractor #2: checkbox groups via container classname -> <strong> + inputs
# ─────────────────────────────────────────────────────────────────────────────
def extract_by_container(driver, form):
    fields = []
    seen_questions = set()
    try:
        containers = form.find_elements(By.CSS_SELECTOR, "div[class*='_1fz17ikh']")
        for c in containers:
            try:
                q = c.find_element(By.TAG_NAME, "strong").text.strip()
            except:
                continue
            if not q or q in seen_questions:
                continue
            seen_questions.add(q)
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
        print(f"[extract_by_container] error: {e}")
    return fields

# ─────────────────────────────────────────────────────────────────────────────
# Extractor #3: group checkboxes by their name attribute
# ─────────────────────────────────────────────────────────────────────────────
def extract_by_name_grouping(driver, form):
    fields = []
    checkboxes_by_name = {}
    for cb in form.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
        nm = cb.get_attribute("name")
        if not nm:
            continue
        checkboxes_by_name.setdefault(nm, []).append(cb)

    for nm, group in checkboxes_by_name.items():
        if not group:
            continue
        try:
            q = group[0].find_element(By.XPATH, "./ancestor::div[.//strong][1]//strong").text.strip()
        except:
            q = nm
        opts = []
        for cb in group:
            cb_id = cb.get_attribute("id")
            if not cb_id:
                continue
            try:
                lbl = form.find_element(By.CSS_SELECTOR, f"label[for='{cb_id}']").text.strip()
            except:
                lbl = cb.get_attribute("value") or cb_id
            opts.append({"id": cb_id, "label": lbl})
        if q and opts:
            fields.append({
                "question": q,
                "type": "multiselect",
                "options": opts
            })
    return fields

# ─────────────────────────────────────────────────────────────────────────────
# Extractor #4: fallback — treat every checkbox on the page as one big multi
# ─────────────────────────────────────────────────────────────────────────────
def extract_all_checkboxes(driver, form):
    opts = []
    for cb in form.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
        cb_id = cb.get_attribute("id")
        if not cb_id:
            continue
        try:
            lbl = form.find_element(By.CSS_SELECTOR, f"label[for='{cb_id}']").text.strip()
        except:
            lbl = cb_id
        opts.append({"id": cb_id, "label": lbl})
    if not opts:
        return []
    return [{
        "question": "Select all that apply",
        "type": "multiselect",
        "options": opts
    }]

# ─────────────────────────────────────────────────────────────────────────────
# Extractor #5: radio button groups (yes/no questions)
# ─────────────────────────────────────────────────────────────────────────────
def extract_radio_groups(driver, form):
    fields = []
    radio_groups = {}
    
    try:
        # Find all radio buttons and group by name
        radios = form.find_elements(By.CSS_SELECTOR, "input[type='radio']")
        for radio in radios:
            name = radio.get_attribute("name")
            if not name:
                continue
            if name not in radio_groups:
                radio_groups[name] = []
            radio_groups[name].append(radio)
        
        # For each group, find the question and options
        for name, radios in radio_groups.items():
            if len(radios) < 2:  # Skip single radio buttons
                continue
                
            # Find question text using multiple strategies
            question_text = None
            first_radio = radios[0]
            
            # Strategy 1: Look for nearby strong tag
            try:
                question_text = first_radio.find_element(By.XPATH, "./ancestor::div[.//strong][1]//strong").text.strip()
            except:
                pass
            
            # Strategy 2: Look for fieldset legend
            if not question_text:
                try:
                    fieldset = first_radio.find_element(By.XPATH, "./ancestor::fieldset[1]")
                    legend = fieldset.find_element(By.TAG_NAME, "legend")
                    question_text = legend.text.strip()
                except:
                    pass
            
            # Strategy 3: Look for nearby label or div with question text
            if not question_text:
                try:
                    # Look for a label that contains the radio button
                    parent_label = first_radio.find_element(By.XPATH, "./ancestor::label[1]")
                    question_text = parent_label.text.strip()
                except:
                    pass
            
            # Strategy 4: Use name as fallback
            if not question_text:
                question_text = name.replace("_", " ").title()
            
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
                        label = form.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
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
                
    except Exception as e:
        print(f"[extract_radio_groups] error: {e}")
    
    return fields

# ─────────────────────────────────────────────────────────────────────────────
# Extractor #6: textarea questions with their labels
# ─────────────────────────────────────────────────────────────────────────────
def extract_textareas(driver, form):
    """Extract textarea questions with their labels"""
    fields = []
    try:
        # Find all textarea elements
        textareas = form.find_elements(By.TAG_NAME, "textarea")
        
        for textarea in textareas:
            textarea_id = textarea.get_attribute("id")
            if not textarea_id:
                continue
                
            # Find the label for this textarea
            try:
                label = form.find_element(By.CSS_SELECTOR, f"label[for='{textarea_id}']")
                question_text = label.text.strip()
            except:
                # If no label found, try to get text from parent container
                try:
                    container = textarea.find_element(By.XPATH, "./ancestor::div[contains(@class, '_1fz17ikh') or contains(@class, 'question')][1]")
                    question_text = container.text.strip()
                except:
                    question_text = textarea_id.replace("_", " ").title()
            
            if question_text:
                fields.append({
                    "question": question_text,
                    "name": textarea.get_attribute("name") or textarea_id,
                    "id": textarea_id,
                    "type": "textarea"
                })
                
    except Exception as e:
        print(f"[extract_textareas] error: {e}")
    
    return fields

# ─────────────────────────────────────────────────────────────────────────────
# Extractor #7: radio button questions with their labels and options (label and value)
# ─────────────────────────────────────────────────────────────────────────────
def extract_radios(driver, form):
    """Extract radio button questions with their labels and options (label and value)."""
    fields = []
    # Find all fieldsets with role radiogroup
    for fieldset in form.find_elements(By.TAG_NAME, "fieldset"):
        if fieldset.get_attribute("role") == "radiogroup":
            legend = fieldset.find_element(By.TAG_NAME, "legend")
            question_text = legend.text.strip()
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
            fields.append({
                "type": "radio",
                "name": radio.get_attribute("name"),
                "question": question_text,
                "options": options
            })
    return fields

# ─────────────────────────────────────────────────────────────────────────────
# MAIN HANDLER
# ─────────────────────────────────────────────────────────────────────────────
def handle_dynamic_questions(driver, resume_pdf_path=None, company_name=None):
    """
    Handle dynamic questions with job-specific resume summary.
    
    Args:
        driver: Selenium WebDriver instance
        resume_pdf_path (str): Path to the job-specific resume PDF (optional)
        company_name (str): Company name for summary file naming (optional)
    """
    wait = WebDriverWait(driver, 15)
    
    # Debug logging to confirm which summary is being used
    print(f"[Dynamic] Resume PDF path: {resume_pdf_path}")
    print(f"[Dynamic] Company name: {company_name}")
    
    # Get job-specific resume summary on-demand
    summary_manager = ResumeSummaryManager()
    job_summary = summary_manager.get_job_specific_summary(
        resume_pdf_path=resume_pdf_path,
        company_name=company_name,
        fallback_summary=RÉSUMÉ_SUMMARY
    )
    
    # Debug logging to confirm which summary was used
    if resume_pdf_path and company_name:
        print(f"[Dynamic] Using job-specific summary for {company_name}")
        print(f"[Dynamic] Summary length: {len(job_summary)} characters")
        print(f"[Dynamic] Summary preview: {job_summary[:200]}...")
    else:
        print(f"[Dynamic] Using fallback summary (no resume path or company name provided)")
        print(f"[Dynamic] Fallback summary length: {len(job_summary)} characters")
    
    try:
        form = wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
    except TimeoutException:
        print("[Dynamic] No form detected")
        return False, ""

    extractors = [
        extract_selects,
        extract_textareas,  # Add textarea extractor
        extract_by_container,
        extract_by_name_grouping,
        extract_all_checkboxes,
        extract_radio_groups,
        extract_radios,
    ]

    all_questions = []
    for ex in extractors:
        try:
            fields = ex(driver, form)
            if fields:
                print(f"[Dynamic] Using extractor: {ex.__name__} (found {len(fields)} questions)")
                all_questions.extend(fields)
        except Exception as e:
            print(f"[Dynamic] {ex.__name__} raised {e}")

    if not all_questions:
        print("[Dynamic] No questions found by any extractor")
        return False, ""

    system_msg = {
        "role": "system",
        "content": """
You are a job-application assistant. You will receive a JSON array of questions and must respond with a JSON object containing an "answers" array.

For each question, you must provide an answer in this format:
{
    "answers": [
        {"question": "Question text here", "selected": "Selected option or text here"},
        {"question": "Another question", "selected": "Another answer"}
    ]
}

Question types:
- type "select": choose exactly one option from the provided options list. Use the exact label text from the options.
- type "multiselect": choose zero or more options from the provided options list.
- type "radio": choose exactly one option from the provided options list. Return the value attribute of the selected option, not the label.
- type "textarea": generate a relevant, professional text response based on the résumé. Do NOT select from options - create original content.

IMPORTANT: 
- For dropdown and radio questions (type "select" and "radio"), you MUST choose from the exact options provided. For radio, return the value attribute, not the label.
- For textarea questions (type "textarea"), you MUST generate original, relevant content based on the résumé. Do not use placeholder text.
- If you need to select an option that represents your experience level, choose the closest available option.

FOR EACH question you MUST choose at least one answer. Always answer in the required format.
"""
    }

    user_msg = {
        "role": "user",
        "content": (
            "RÉsumÉ summary:\n\"\"\"\n"
            + job_summary
            + "\n\"\"\"\n\nQuestions:\n"
            + json.dumps(all_questions, indent=2)
        )
    }

    client = OpenAI()
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[system_msg, user_msg],
        temperature=0.0
    )
    raw = resp.choices[0].message.content
    print("[Dynamic] LLM raw response:\n", raw)

    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if m:
        raw = m.group(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print("[Dynamic] JSON parse error:", e)
        return False, ""

    # Only handle the expected format with answers array
    answers = data.get("answers", [])
    if not answers:
        print("[Dynamic] No answers found in response")
        return False, ""

    answered = set()
    question_logs = []  # Collect question/answer logs
    
    for ans in answers:
        q_text = ans["question"]
        sel = ans["selected"]
        entry = next((e for e in all_questions if e["question"] == q_text), None)
        if not entry:
            print(f"[Dynamic] Could not match question: {q_text}")
            continue

        print(f"[Dynamic] Answer for '{q_text}': {sel}")
        if q_text in answered:
            print(f"[Dynamic] Skipping already answered question: {q_text}")
            continue

        try:
            if entry["type"] == "select":
                input_element = form.find_element(By.NAME, entry["name"])
                
                if input_element.tag_name == "select":
                    # Handle dropdowns with improved matching
                    print(f"[Dynamic] Selecting for question: {entry['question']} with selection: {sel}")
                    dropdown = Select(input_element)
                    
                    # Try to match by value first (for LLM returning internal value)
                    try:
                        dropdown.select_by_value(sel)
                        print(f"[Dynamic] Successfully selected dropdown value {sel} for question '{entry['question']}'")
                        question_logs.append(f"Selecting dropdown for question: {entry['question']} with value: {sel}")
                    except:
                        # Fallback: try to match by label (for LLM returning visible label)
                        try:
                            dropdown.select_by_visible_text(sel)
                            print(f"[Dynamic] Successfully selected dropdown label '{sel}' for question '{entry['question']}'")
                            question_logs.append(f"Selecting dropdown for question: {entry['question']} with label: {sel}")
                        except Exception as e:
                            print(f"[Dynamic] Failed to select dropdown option '{sel}' for question '{entry['question']}': {e}")
                            # Try to find the closest match
                            available_options = [opt.text for opt in dropdown.options]
                            print(f"[Dynamic] Available options: {available_options}")
                            continue
            elif entry["type"] == "radio":
                # Handle radio buttons by finding the correct value based on text
                print(f"[Dynamic] Processing radio button for question: {entry['question']} with selection: {sel}")
                
                # Find the radio button with the matching text
                radio_buttons = form.find_elements(By.CSS_SELECTOR, f"input[type='radio'][name='{entry['name']}']")
                selected_radio = None
                
                for radio in radio_buttons:
                    # Get the label text for this radio button
                    radio_id = radio.get_attribute("id")
                    try:
                        label = form.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                        label_text = label.text.strip()
                        
                        # Check if this radio button's label matches our selection
                        if label_text.lower() == sel.lower():
                            selected_radio = radio
                            break
                    except:
                        continue
                
                if selected_radio:
                    selected_radio.click()
                    print(f"[Dynamic] Successfully selected radio button '{sel}' for question '{entry['question']}'")
                    question_logs.append(f"Q: {entry['question']} | A: {sel}")
                else:
                    print(f"[Dynamic] ERROR: Could not find radio button with text '{sel}' for question '{entry['question']}'")
                    # Try to find by value as fallback
                    try:
                        radio = form.find_element(By.CSS_SELECTOR, f"input[type='radio'][name='{entry['name']}'][value='{sel}']")
                        radio.click()
                        print(f"[Dynamic] Successfully selected radio button by value '{sel}' for question '{entry['question']}'")
                        question_logs.append(f"Q: {entry['question']} | A: {sel}")
                    except:
                        print(f"[Dynamic] ERROR: Could not find radio button with value '{sel}' for question '{entry['question']}'")
                        question_logs.append(f"Q: {entry['question']} | A: ERROR - Could not select '{sel}'")
            elif entry["type"] == "textarea":
                # Handle textarea inputs
                print(f"[Dynamic] Filling textarea for question: {entry['question']} with: {sel[:50]}...")
                textarea = driver.find_element(By.ID, entry["id"])
                textarea.clear()
                textarea.send_keys(sel)
                print(f"[Dynamic] Successfully filled textarea for question '{entry['question']}'")
                question_logs.append(f"Filling textarea for question: {entry['question']} with: {sel[:100]}...")
            elif entry["type"] == "multiselect":
                for choice in sel:
                    # Try to match by value first (for LLM returning internal value)
                    opt = next((o for o in entry["options"] if o.get("value") == choice or o.get("id") == choice), None)
                    if not opt:
                        # Fallback: try to match by label (for LLM returning visible label)
                        opt = next((o for o in entry["options"] if o["label"] == choice), None)
                    if not opt:
                        print(f"[Dynamic] Option not found for value or label: {choice}")
                        continue
                    cb = driver.find_element(By.ID, opt["id"])
                    if not cb.is_selected():
                        cb.click()
                        print(f"[Dynamic] Checked: {choice} (label: {opt['label']}, value: {opt.get('value', opt.get('id'))})")
                        question_logs.append(f"Selecting checkbox for question: {entry['question']} with option: {choice}")
        except Exception as e:
            print(f"[ERROR] Failed to apply answer to '{q_text}': {e}")
            continue

        answered.add(q_text)

    try:
        btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[data-testid='continue-button']")
        ))
    except:
        btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Continue') or contains(.,'Next')]")
        ))

    print("[Dynamic] Clicking continue...")
    btn.click()
    wait.until(EC.staleness_of(form))
    print("[Dynamic] Finished handling questions.")
    
    # Return success status and question logs
    return True, "\n".join(question_logs)
