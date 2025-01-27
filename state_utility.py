import random
from graph import Graphs
from state import State
from selenium.common.exceptions import StaleElementReferenceException
from action import Click, Follow, Select, Type, sort_actions, MultipleActions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select as SelectSelenium

from html_utility import parse_html_element, clean_outer_html
from action import parse_graph_action
from utility import deterministic_hash

from bs4 import BeautifulSoup, Comment

import html

from http_utility import check_url_white_list


import time
from selenium.common.exceptions import NoSuchElementException

def logout_detection(driver, logout_conditions):
    ## Logout detection
    body = driver.find_element(By.TAG_NAME, "body").text
    if ((logout_conditions.get("keyword_based") and logout_conditions["keyword_based"] in body)
    or (logout_conditions.get("redirect") and driver.current_url == logout_conditions.get("redirect"))):
        return True
    else:
        return False

def login_page_detection(driver, authentication, currentState):
    if authentication['url'] in driver.current_url:
        elements = authentication["login_page_detection"]['elements']
        found = 0
        total = 0
        for tag in elements:
            for text in elements[tag]:
                total += 1
                if currentState.contains([tag, text]):
                    found += 1
        if found == sum(len(values) for values in elements.values()):
            return True
    return False


def cookie_banner_detection(driver, cookie_banner, currentState):
    elements = cookie_banner["cookie_banner_detection"]['elements']
    found = 0
    total = 0
    for tag in elements:
        for text in elements[tag]:
            total += 1
            if currentState.contains([tag, text]):
                found += 1
    if found == len(elements):
        return True
    return False

def generate_state_actions(driver, chatgpt, visited_urls, white_list = []):
    attempt = 0
    while True:
        try:
            actions = []
            state = []
            
            elements_id = []

            meanings_rects = []
            links = driver.find_elements(By.TAG_NAME, "a")
            buttons = driver.find_elements(By.TAG_NAME, "button")
            inputs = driver.find_elements(By.TAG_NAME, "input")
            selects = driver.find_elements(By.TAG_NAME, "select")

            forms = driver.find_elements(By.TAG_NAME, "form")
            for f in forms:
                links_in_form = f.find_elements(By.TAG_NAME, "a")
                for l in links_in_form:
                    if str(l.get_attribute("href")).startswith("http") and not check_url_white_list(str(l.get_attribute("href")).split('/')[2], white_list):
                        continue
                    if l.is_displayed() and l.id not in elements_id and l.size['height'] > 0 and l.size['width'] > 0 and not str(l.get_attribute("href")).startswith("mailto"):
                        
                        if chatgpt:
                            #meaning = "link"
                            meaning = chatgpt.ask("In max 5 words, which is the semantic meaning of this HTML element?", clean_outer_html(l.get_attribute("outerHTML")))
                            meanings_rects.append((meaning, l.rect))
                        elements_id.append(l.id)
                        actions.append(Follow(parse_html_element(l), True))
                        state.append(parse_html_element(l))

                
                buttons_in_form = f.find_elements(By.TAG_NAME, "button")
                for b in buttons_in_form:
                    if b.is_displayed() and b.id not in elements_id and b.size['height'] > 0 and b.size['width'] > 0:
                        if chatgpt:
                            #meaning = "button"
                            meaning = chatgpt.ask("In max 5 words, which is the semantic meaning of this HTML element?",  clean_outer_html(b.get_attribute("outerHTML")))
                            meanings_rects.append((meaning, b.rect))
                        elements_id.append(b.id)
                        actions.append(Click(parse_html_element(b), By.TAG_NAME, "button", True))
                        state.append(parse_html_element(b))


                inputs_in_form = f.find_elements(By.TAG_NAME, "input")
                type_temp = []
                for i in inputs_in_form:
                    if i.is_displayed() and i.id not in elements_id and i.size['height'] > 0 and i.size['width'] > 0:
                        if chatgpt:
                            #meaning = "input"
                            meaning = chatgpt.ask("In max 5 words, which is the semantic meaning of this HTML element?",  clean_outer_html(i.get_attribute("outerHTML")))
                            meanings_rects.append((meaning, i.rect))
                        if i.get_attribute("type") == "text":
                            if i.get_attribute("value") == "":  
                                elements_id.append(i.id)
                                type_temp.append(Type(parse_html_element(i), "abcde", True))
                        else:
                            elements_id.append(i.id)
                            actions.append(Click(parse_html_element(i), By.TAG_NAME, "input", True))

                        state.append(parse_html_element(i))

                if len(type_temp) > 2:
                    actions.append(MultipleActions(type_temp))
                selects_in_form = f.find_elements(By.TAG_NAME, "select")
                select_temp = []
                for s in selects_in_form:
                    if s.is_displayed() and s.id not in elements_id and s.size['height'] > 0 and s.size['width'] > 0:
                        if chatgpt:
                            #meaning = "select"
                            meaning = chatgpt.ask("In max 5 words, which is the semantic meaning of this HTML element?",  clean_outer_html(s.get_attribute("outerHTML")))
                            meanings_rects.append((meaning, s.rect))
                        elements_id.append(s.id)
                        sel = SelectSelenium(s)
                        # random pick an option
                        i = random.randint(0, len(sel.options) - 1)
                        select_temp.append(Select(parse_html_element(s), i, True))
                        state.append(parse_html_element(s))
                if len(select_temp) > 2:
                    actions.append(MultipleActions(select_temp))
            for l in links:
                if str(l.get_attribute("href")).startswith("http") and not check_url_white_list(str(l.get_attribute("href")).split('/')[2], white_list):
                    continue
                if l.is_displayed() and l.id not in elements_id and l.size['height'] > 0 and l.size['width'] > 0 and not str(l.get_attribute("href")).startswith("mailto"):

                    
                    if chatgpt:
                        #meaning = "link"
                        meaning = chatgpt.ask("In max 5 words, which is the semantic meaning of this HTML element?", clean_outer_html(l.get_attribute("outerHTML")))
                        meanings_rects.append((meaning, l.rect))
                    elements_id.append(l.id)
                    actions.append(Follow(parse_html_element(l)))
                    state.append(parse_html_element(l))

            
            for b in buttons:
                if b.is_displayed() and b.id not in elements_id and b.size['height'] > 0 and b.size['width'] > 0:
                    if chatgpt:
                        #meaning = "button"
                        meaning = chatgpt.ask("In max 5 words, which is the semantic meaning of this HTML element?",  clean_outer_html(b.get_attribute("outerHTML")))
                        meanings_rects.append((meaning, b.rect))
                    elements_id.append(b.id)
                    actions.append(Click(parse_html_element(b), By.TAG_NAME, "button"))
                    state.append(parse_html_element(b))


            for i in inputs:
                if i.is_displayed() and i.id not in elements_id and i.size['height'] > 0 and i.size['width'] > 0:
                    if chatgpt:
                        #meaning = "input"
                        meaning = chatgpt.ask("In max 5 words, which is the semantic meaning of this HTML element?",  clean_outer_html(i.get_attribute("outerHTML")))
                        meanings_rects.append((meaning, i.rect))
                    if i.get_attribute("type") == "text":
                        if i.get_attribute("value") == "":  
                            elements_id.append(i.id)
                            actions.append(Type(parse_html_element(i), "abcde"))
                    else:
                        elements_id.append(i.id)
                        actions.append(Click(parse_html_element(i), By.TAG_NAME, "input"))

                    state.append(parse_html_element(i))

            
            for s in selects:
                if s.is_displayed() and s.id not in elements_id and s.size['height'] > 0 and s.size['width'] > 0:
                    if chatgpt:
                        #meaning = "select"
                        meaning = chatgpt.ask("In max 5 words, which is the semantic meaning of this HTML element?",  clean_outer_html(s.get_attribute("outerHTML")))
                        meanings_rects.append((meaning, s.rect))
                    elements_id.append(s.id)
                    sel = SelectSelenium(s)
                    for i in range(len(sel.options)):
                        actions.append(Select(parse_html_element(s), i))
                    state.append(parse_html_element(s))

            body_el = driver.find_element(By.TAG_NAME, "body")
            body_elements = body_el.find_elements(By.XPATH, ".//*")
            body = body_el.get_attribute("outerHTML")
            soup = BeautifulSoup(body, features='html.parser')
            visible_text = ""
            hidden_elements = []
            hidden_tags = ['script','iframe','noscript','style', 'meta', 'comment']
            i = 0
            while i < len(body_elements):
                if i > 3000:
                    break
                if body_elements[i].tag_name in hidden_tags or not body_elements[i].is_displayed():
                    hidden_elements.append(body_elements[i].get_attribute("outerHTML"))
                    childs = body_elements[i].find_elements(By.XPATH, ".//*")
                    i = i + len(childs) + 1
                else:
                    if body_elements[i].text:
                        visible_text += body_elements[i].text + " "
                    o_h = body_elements[i].get_attribute("outerHTML")
                    s1 = """Array.from(document.querySelectorAll("*")).find(el => el.outerHTML === '"""+ o_h+ """')"""
                    res = driver.execute_cdp_cmd("Runtime.evaluate", {"expression": s1})['result']
                    event_listeners = None
                    if res == None or res.get('className') == None:
                        i += 1
                        continue
                    if res.get('className') and "Error" not in res['className']:
                        id = res['objectId']
                        event_listeners = driver.execute_cdp_cmd("DOMDebugger.getEventListeners", {"objectId": id})
                    if event_listeners and event_listeners['listeners'] and any(event['type'] == "click" for event in event_listeners['listeners']):           
                        if body_elements[i].is_displayed() and body_elements[i].id not in elements_id and body_elements[i].size['height'] > 0 and body_elements[i].size['width'] > 0:
                            if chatgpt:
                                #meaning = "click"
                                meaning = chatgpt.ask("In max 5 words, which is the semantic meaning of this HTML element?",  clean_outer_html(b.get_attribute("outerHTML")))
                                meanings_rects.append((meaning, body_elements[i].rect))
                            elements_id.append(body_elements[i].id)
                            actions.append(Click(parse_html_element(body_elements[i]), By.TAG_NAME, body_elements[i].tag_name, False))
                            state.append(parse_html_element(body_elements[i]))
                    i += 1


            all_elements = soup.find_all(True)
            i = 0
            while i < len(all_elements):
                if i > 3000:
                    break
                try:
                    element = all_elements[i]
                    if str(element) not in hidden_elements or str(element).startswith("<body>"):
                        attrs = dict(element.attrs)
                        for attr in attrs:
                            if attr.startswith("data") or attr == "class":
                                del element.attrs[attr]
                    else:
                        element.decompose()
                        for c in element.children:
                            i += 1
                except Exception as e:
                    i += 1
                    continue
                i += 1
            for element in soup(['script','iframe','noscript','style', 'svg']):
                element.decompose()
            # Find and remove hidden elements
            hidden_elements = soup.find_all(lambda tag: tag.has_attr('style') and (
                'display: none' in tag['style'] or 'visibility: hidden' in tag['style']))
            for element in hidden_elements:
                element.decompose()
            hidden_elements = soup.find_all(lambda tag: tag.has_attr('hidden'))
            for element in hidden_elements:
                element.decompose()
            hidden_elements = soup.find_all(lambda tag: tag.has_attr('disabled'))
            for element in hidden_elements:
                element.decompose()

            comments = soup.find_all(text=lambda t: isinstance(t, Comment))
            for comment in comments:
                comment.extract()
            
            
            body = soup.prettify()    
            body = " ".join(body.split())
            visible_text = html.escape(visible_text, quote=True)
            currentState = State(driver.current_url, state, visible_text, body, has_form=(len(forms) > 0))

            actions.sort(reverse=True, key=lambda action: sort_actions(action, visited_urls))
            
            return currentState, actions, meanings_rects
        except StaleElementReferenceException as e:
            attempt += 1
            if attempt > 2:
                raise Exception


def move_to_state(path, driver, base_url, DG_state_action, white_list):
    driver.get(base_url)
    driver.delete_all_cookies()
    time.sleep(1)
    driver.execute_script("window.localStorage.clear();")
    time.sleep(1)
    driver.execute_script("window.sessionStorage.clear();")
    time.sleep(1)
    driver.refresh()
    # cerca div con classe coursel
    time.sleep(5)
    try:
        # Check if there is an element with class "carousel"
        carousel_elements = driver.find_element(By.CLASS_NAME, "carousel")
        if carousel_elements:
            driver.execute_script("$('.carousel').each(function() {$(this).carousel('cycle'); $(this).carousel(0); });")
            time.sleep(5)
            driver.execute_script("$('.carousel').each(function() {$(this).carousel('pause'); $(this).carousel(0); });")
            time.sleep(5)
    except NoSuchElementException:
        pass  # Do nothing if there is no carousel element
    for element in path:
        action = DG_state_action.nodes[element].get("action")
        if action is not None and action != "Start":
            action = parse_graph_action(action)
            time.sleep(5)
            action(driver)
            time.sleep(5)
            try:
                # Check if there is an element with class "carousel"
                carousel_elements = driver.find_element(By.CLASS_NAME, "carousel")
                if carousel_elements:
                    driver.execute_script("$('.carousel').each(function() {$(this).carousel('cycle'); $(this).carousel(0); });")
                    time.sleep(5)
                    driver.execute_script("$('.carousel').each(function() {$(this).carousel('pause'); $(this).carousel(0); });")
                    time.sleep(5)
            except NoSuchElementException:
                pass  # Do nothing if there is no carousel element
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    driver.execute_script("window.scrollTo(0,0)")
    state = generate_state_actions(driver, None, [], white_list)
    driver.execute_script("window.scrollTo(0,0)")
    return state



def check_presence(currentState, graphs, nodes, currentAction):
    if graphs.node_in_graph(deterministic_hash(currentState)):
        return True, currentState
    return False, currentState


def check_error_in_page(currenState, error_conditions, chatgpt):
    visible_text = currenState.get_visible_text()
    for error_key in error_conditions:
        if error_key == "keywords":
            for keyword in error_conditions[error_key]:
                if keyword in visible_text:
                    return True
    res = chatgpt.ask("Is this HTML page contains an error message? Start you response with Yes or No: ", visible_text)
    if "Yes" in res:
        return True
    return False


