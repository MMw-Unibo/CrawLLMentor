
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select as SelectSelenium
from utility import draw
from html_utility import parse_html_element, check_semantic, same_element

import json
import time
import gravis as gv

import Levenshtein




TAGS = {
    "Click" : ["button", "input"],
    "Type" : ["input"],
    "Select" : ["select"],
    "Follow" : ["a"]
}

def parse_graph_action(action):
    action_type = action["_action_type"]
    if action_type == "Click":
        action = Click(action["_element"], action["_by"], action["_search_criterion"])
    elif action_type == "Follow":
        action = Follow(action["_element"])
    elif action_type == "Select":
        action = Select(action["_element"], action["_option"])
    elif action_type == "Type":
        action = Type(action["_element"], action["_text"])
    elif "Multiple" in action_type:
        actions = []
        for a in action["_actions"]:
            actions.append(parse_graph_action(a))
        action = MultipleActions(actions)
    return action

def parse_arbitrary_action(driver, action, already_parsed = []):
    elements = {}
    if action["action_name"] == "MultipleActions":
        return parse_arbitrary_multiple_action(driver, action)
    for tag in TAGS[action["action_name"]]:
        elements[tag] = driver.find_elements(By.TAG_NAME, tag)
    for tag in elements:
        for el in elements[tag]:
            if el.is_displayed() and check_semantic(el.get_attribute("outerHTML"), action["keywords"]):
                if action["action_name"] == "Type" and el.get_attribute("value") != "":
                    continue
                match action["action_name"]:
                    case "Follow":
                        return Follow(parse_html_element(el))
                    case "Click":
                        return Click(parse_html_element(el), By.TAG_NAME, tag)
                    case "Type":
                        return Type(parse_html_element(el), action["parameter"]) ###choose_parameters(el.get_attribute("outerHTML"), authentication["parameters"]))
                    case "Select":
                        pass
                        #SelectSelenium(el).select_by_value(authentication["actions"]["action_name"][0])
                break
    return None

def parse_arbitrary_multiple_action(driver, action):
    actions = []
    used_elements = []
    for a in action["actions"]:
        elements = {}
        for tag in TAGS[a["action_name"]]:
            elements[tag] = driver.find_elements(By.TAG_NAME, tag)
        for tag in elements:
            found = False
            for el in elements[tag]:
                if el.is_displayed() and not el.id in used_elements and check_semantic(el.get_attribute("outerHTML"), a["keywords"]):
                    found = True
                    used_elements.append(el.id)
                    if a["action_name"] == "Type" and el.get_attribute("value") != "":
                        continue
                    match a["action_name"]:
                        case "Follow":
                            actions.append(Follow(parse_html_element(el)))
                        case "Click":
                            actions.append(Click(parse_html_element(el), By.TAG_NAME, tag))
                        case "Type":
                            actions.append(Type(parse_html_element(el), a["parameter"])) ###choose_parameters(el.get_attribute("outerHTML"), authentication["parameters"]))
                        case "Select":
                            pass
                            #SelectSelenium(el).select_by_value(authentication["actions"]["action_name"][0])
                    break
            if found:
                break
    return MultipleActions(actions)


def sort_actions(action, visited_urls):
    priority = 0
    multiplier = 1
    if action.is_pop_up():
        multiplier = 1000
    if action.is_form():
        multiplier = 10
    if action.get_type() == "Click":
        priority = 2.1 * multiplier
    elif action.get_type() == "Follow":
        link = action.get_element()["href"]
        max_similarity = 0
        for url in visited_urls:
            max_similarity = max(max_similarity, Levenshtein.ratio(link, url))
        priority = (5 + (1 - max_similarity)) * multiplier
    elif action.get_type() == "Type":
        priority = 4 * multiplier
    elif action.get_type() == "Select":
        priority = 3 * multiplier
    elif "Multiple" in action.get_type():
        priority = 5 * multiplier
    
    return priority

class Action:
    def __call__(self, driver):
        raise NotImplementedError()
class Click(Action):
    def __init__(self, element, by, search_criterion, form=False):
        self. _action_type = "Click"
        self._element = element
        self._by = by
        self._search_criterion = search_criterion
        self._form = form
        self._pop_up = element["z_index"] > 1000

    def __call__(self, driver):
        elements = driver.find_elements(self._by, self._search_criterion)
        for e in elements:
            if same_element(self._element, parse_html_element(e)):
                res = driver.execute_script('arguments[0].scrollIntoView({block: "center"}); return arguments[0].getBoundingClientRect()', e)
                driver.save_screenshot("./screenshots/" + str(hash(self)) + ".png")
                draw("./screenshots/" + str(hash(self)) + ".png", [("", res)])
                action_image = gv.convert.image_to_data_url("./screenshots/" + str(hash(self)) + ".png")
                e.click()
                return action_image
        for e in elements:
            if same_element(self._element, parse_html_element(e)):
                continue
        raise Exception("No elements found")

    def __hash__(self):
        return hash(self.__str__())
    
    def __eq__(self, other):
        if isinstance(other, Click):
            return self._element == other.get_element()
        
    def get_type(self):
        return self._action_type
    
    def get_element(self):
        return self._element
    
    def is_form(self):
        return self._form
    
    def is_pop_up(self):
        return self._pop_up

    def __str__(self):
        return "Click " + self._element["aria_role"] + " " + self._element["text"]
    def __repr__(self):
        return self._action_type + " " + json.dumps(self._element)
    


class Follow(Action):
    def __init__(self, element, form=False):
        self._action_type = "Follow"
        self._element = element
        self._form = form
        self._pop_up = element["z_index"] > 1000

    
    def get_type(self):
        return self._action_type

    def __call__(self, driver):
        links = driver.find_elements(By.TAG_NAME, "a")
        for l in links:

            if same_element(self._element, parse_html_element(l)):
                res = driver.execute_script('arguments[0].scrollIntoView({block: "center"}); return arguments[0].getBoundingClientRect()', l)
                driver.save_screenshot("./screenshots/" + str(hash(self)) + ".png")
                draw("./screenshots/" + str(hash(self)) + ".png", [("", res)])
                action_image = gv.convert.image_to_data_url("./screenshots/" + str(hash(self)) + ".png")
                l.click()
                return action_image
        for l in links:
            if same_element(self._element, parse_html_element(l)):
                continue
        raise Exception("No elements found")

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        if isinstance(other, Follow):
            return self._element == other.get_element()
        
    def get_element(self):
        return self._element
    
    def is_form(self):
        return self._form
    
    def is_pop_up(self):
        return self._pop_up

    def __str__(self):
        return "Follow " + self._element["aria_role"] + " " + self._element["text"]
    def __repr__(self):
        return self._action_type + " " + json.dumps(self._element)

class Select(Action):

    def __init__(self, element, option, form=False):
        self._action_type = "Select"
        self._element = element
        self._option = option
        self._form = form
        self._pop_up = element["z_index"] > 1000


    def get_type(self):
        return self._action_type

    def __call__(self, driver):
        selects = driver.find_elements(By.TAG_NAME, "select")
        for s in selects:
            if same_element(self._element, parse_html_element(s)):
                res = driver.execute_script('arguments[0].scrollIntoView({block: "center"}); return arguments[0].getBoundingClientRect()', s)
                driver.save_screenshot("./screenshots/" + str(hash(self)) + ".png")
                draw("./screenshots/" + str(hash(self)) + ".png", [("", res)])
                action_image = gv.convert.image_to_data_url("./screenshots/" + str(hash(self)) + ".png")
                SelectSelenium(s).select_by_index(self._option)
                return action_image
        raise Exception("No elements found")

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        if isinstance(other, Select):
            return self._element == other.get_element()
        
    def get_element(self):
        return self._element
    
    def is_form(self):
        return self._form
    
    def is_pop_up(self):
        return self._pop_up

    def __str__(self):
        return "Select " + json.dumps(self._element)
    def __repr__(self):
        return self._action_type + " " + json.dumps(self._element)

class Type(Action):
    def __init__(self, element, text, form=False):
        self. _action_type = "Type"
        self._element = element
        self._text = text
        self._form = form
        self._pop_up = element["z_index"] > 1000


    def get_type(self):
        return self._action_type

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        if isinstance(other, Type):
            return self._element == other.get_element()

    def __str__(self):
        return "Type " + self._element["aria_role"] + " " + self._text
    
    def __call__(self, driver):
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for i in inputs:
            if same_element(self._element, parse_html_element(i)) and i.get_attribute("value") == "":
                res = driver.execute_script('arguments[0].scrollIntoView({block: "center"}); return arguments[0].getBoundingClientRect()', i)
                driver.save_screenshot("./screenshots/" + str(hash(self)) + ".png")
                draw("./screenshots/" + str(hash(self)) + ".png", [("", res)])
                action_image = gv.convert.image_to_data_url("./screenshots/" + str(hash(self)) + ".png")
                i.send_keys(self._text)
                return action_image
        for i in inputs:
            if same_element(self._element, parse_html_element(i)) and i.get_attribute("value") == "":
                continue
        raise Exception("No elements found")
    def __repr__(self):
        return self._action_type + " " + json.dumps(self._element)
    
    def get_element(self):
        return self._element
    
    def is_pop_up(self):
        return self._pop_up
    
    def is_form(self):
        return self._form

class MultipleActions(Action):
    def __init__(self, actions):
        
        self._actions = actions
        self._form = self._actions[0].is_form()
        self._pop_up = self._actions[0].is_pop_up()
        self._action_type = "Multiple " + self._actions[0].get_type()
    
    def __call__(self, driver):
        image = None
        for action in self._actions:
            image = action(driver)
            time.sleep(1)
        return image

    def __repr__(self):
        return self._action_type + " " + " ".join([repr(action) for action in self._actions])
    
    @property
    def __dict__(self):
        return {'_action_type': self._action_type, '_actions': [vars(a) for a in self._actions]}
    
    def get_element(self):
        return "multiple"
    
    def is_pop_up(self):
        return self._pop_up
    
    def is_form(self):
        return self._form
    
    def __str__(self):
        return  self._action_type + " " + " ".join([str(action) for action in self._actions])
    
    def get_type(self):
        return self._action_type

    



    





    
