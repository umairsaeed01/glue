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
    
    # 1) wait for at least one question label to appear
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "label[for^='question-']")))
    except:
        print("[RoleReq] No questions found on page.")
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
                for inp in driver.find_elements(By.CSS_SELECTOR, f"input[name^='{q_id}'], input[id^='{q_id}']"):
                    rid = inp.get_attribute("id")
                    if not rid: continue
                    try:
                        lab2 = driver.find_element(By.CSS_SELECTOR, f"label[for='{rid}']")
                        opts.append(lab2.text.strip())
                    except: 
                        pass
                if opts:
                    question_type = "radio_checkbox"

        if not opts and question_type != "textarea":
            continue

        multi = bool(driver.find_elements(By.CSS_SELECTOR,
            f"input[type='checkbox'][name^='{q_id}']"))
        questions.append({
            "id":    q_id,
            "text":  q_text,
            "options": opts,
            "multi": multi,
            "type":  question_type
        })

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
                
                # Extract radio button options
                opts = []
                radios = fieldset.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                
                for radio in radios:
                    radio_id = radio.get_attribute("id")
                    if not radio_id:
                        continue
                    try:
                        label = driver.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                        label_text = label.text.strip()
                        if label_text:
                            opts.append(label_text)
                    except:
                        pass
                
                if opts:
                    questions.append({
                        "id": fieldset.get_attribute("id") or f"fieldset_{len(questions)}",
                        "text": q_text,
                        "options": opts,
                        "multi": False,
                        "type": "radio"
                    })
                    print(f"[RoleReq] Found radio button question: {q_text} with options: {opts}")
                    
            except Exception as e:
                print(f"[RoleReq] Error processing fieldset: {e}")
                continue
    except Exception as e:
        print(f"[RoleReq] Error finding fieldsets: {e}")

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
                # Find the radio button with matching label text
                radio_buttons = driver.find_elements(By.CSS_SELECTOR, f"input[type='radio']")
                selected_radio = None
                
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