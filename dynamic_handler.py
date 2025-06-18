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
            # question text is the nearest preceding <strong>, or fall back to name
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
        # SEEK's usual question wrapper class fragment
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
        # derive question text from the first element's nearest <strong>
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
    ]

    questions = []
    for ex in extractors:
        try:
            fields = ex(driver, form)
        except Exception as e:
            print(f"[Dynamic] {ex.__name__} raised {e}")
            fields = []
        if fields:
            print(f"[Dynamic] Using extractor: {ex.__name__} (found {len(fields)} questions)")
            questions = fields
            break

    if not questions:
        print("[Dynamic] No questions found by any extractor")
        return False

    # --- build LLM prompts ---
    system_msg = {
        "role": "system",
        "content": """
You are a job-application assistant. You will receive a JSON array of questions:
- type "select": choose exactly one option.
- type "multiselect": choose zero or more options.

FOR EACH question you MUST choose at least one answer.  Always explain your reasoning.

Respond ONLY with valid JSON:
{
  "answers":[
    {
      "question":"…",
      "selected": … ,    // string for select, array of strings for multiselect
      "reasoning":"…"
    },
    …
  ]
}
"""
    }
    user_msg = {
        "role": "user",
        "content": (
            "Résumé summary:\n\"\"\"\n"
            + RÉSUMÉ_SUMMARY
            + "\n\"\"\"\n\nQuestions:\n"
            + json.dumps(questions, indent=2)
        )
    }

    # --- call OpenAI ---
    client = OpenAI()
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[system_msg, user_msg],
        temperature=0.0
    )
    raw = resp.choices[0].message.content
    print("[Dynamic] LLM raw response:\n", raw)

    # strip markdown fences
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if m:
        raw = m.group(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print("[Dynamic] JSON parse error:", e)
        return False

    # --- apply each answer ---
    for ans in data.get("answers", []):
        q_text = ans["question"]
        sel = ans["selected"]
        entry = next(e for e in questions if e["question"] == q_text)

        print(f"[Dynamic] Answer for '{q_text}': {sel}")
        if entry["type"] == "select":
            dropdown = Select(form.find_element(By.NAME, entry["name"]))
            dropdown.select_by_value(sel)

        else:  # multiselect
            for choice in sel:
                opt = next(o for o in entry["options"] if o["label"] == choice)
                cb = driver.find_element(By.ID, opt["id"])
                if not cb.is_selected():
                    cb.click()

    # --- click Continue ---
    try:
        btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[data-testid='continue-button']")
        ))
    except:
        btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Continue') or contains(.,'Next')]")
        ))
    btn.click()
    wait.until(EC.staleness_of(form))
    return True
