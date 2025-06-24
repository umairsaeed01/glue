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

# ─────────────────────────────────────────────────────────────────────────────
# Extractor #1: single‐choice <select> elements
# ─────────────────────────────────────────────────────────────────────────────
def extract_selects(driver, form):
    fields = []
    try:
        for sel in form.find_elements(By.TAG_NAME, "select"):
            try:
                question = sel.find_element(By.XPATH, "preceding::strong[1]").text.strip()
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
                    "type": "select",  # Treat as dropdown for consistency
                    "options": options
                })
                
    except Exception as e:
        print(f"[extract_radio_groups] error: {e}")
    
    return fields

# ─────────────────────────────────────────────────────────────────────────────
# MAIN HANDLER
# ─────────────────────────────────────────────────────────────────────────────
def handle_dynamic_questions(driver):
    wait = WebDriverWait(driver, 15)
    try:
        form = wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
    except TimeoutException:
        print("[Dynamic] No form detected")
        return False

    extractors = [
        extract_selects,
        extract_by_container,
        extract_by_name_grouping,
        extract_all_checkboxes,
        extract_radio_groups,
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
        return False

    system_msg = {
        "role": "system",
        "content": """
You are a job-application assistant. You will receive a JSON array of questions:
- type \"select\": choose exactly one option.
- type \"multiselect\": choose zero or more options.
FOR EACH question you MUST choose at least one answer. Always explain your reasoning.
Respond ONLY with valid JSON:
{
  \"answers\":[
    {
      \"question\":\"...\",
      \"selected\": ..., // string for select, array of strings for multiselect
      \"reasoning\":\"...\"
    },
    ...
  ]
}"""
    }

    user_msg = {
        "role": "user",
        "content": (
            "RÉsumÉ summary:\n\"\"\"\n"
            + RÉSUMÉ_SUMMARY
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
        return False

    answered = set()
    for ans in data.get("answers", []):
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
                    # Handle dropdowns (existing logic)
                    print(f"[Dynamic] Selecting for question: {entry['question']} with value: {sel}")
                    dropdown = Select(input_element)
                    dropdown.select_by_value(sel)
                    print(f"[Dynamic] Successfully selected dropdown value {sel} for question '{entry['question']}'")
                else:
                    # Handle radio buttons (new logic)
                    print(f"[Dynamic] Selecting radio for question: {entry['question']} with value: {sel}")
                    radio = form.find_element(By.CSS_SELECTOR, f"input[type='radio'][value='{sel}']")
                    radio.click()
                    print(f"[Dynamic] Successfully selected radio value {sel} for question '{entry['question']}'")
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
    return True
