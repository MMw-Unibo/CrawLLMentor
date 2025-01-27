from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import html
import numpy as np

def parse_html_element(web_element):
    parsed_element = {}
    parsed_element["aria_role"] = web_element.aria_role
    parsed_element["accessible_name"] = web_element.accessible_name
    parsed_element["size"] = web_element.size
    parsed_element["tag"] = web_element.tag_name
    parsed_element["text"] = web_element.text
    #parsed_element["class"] = "" if web_element.get_attribute("class") is None else web_element.get_attribute("class")
    parsed_element["location"] = web_element.location
    parsed_element["location_view"] = web_element.location_once_scrolled_into_view
    parsed_element["name"] = "" if web_element.get_attribute("name") is None else web_element.get_attribute("name")
    parsed_element["type"] = "" if web_element.get_attribute("type") is None else web_element.get_attribute("type")
    parsed_element["value"] = "" if web_element.get_attribute("value") is None else web_element.get_attribute("value")
    #parsed_element["id"] = "" if web_element.get_attribute("id") is None else web_element.get_attribute("id")
    parsed_element["href"] = "" if web_element.get_attribute("href") is None else web_element.get_attribute("href")
    parsed_element["title"] = "" if web_element.get_attribute("title") is None else web_element.get_attribute("title")
    parsed_element["src"] = "" if web_element.get_attribute("src") is None else web_element.get_attribute("src")
    try:
        z_index = web_element.value_of_css_property("z-index")
        child = web_element
        while z_index == "auto":
            parent = child.find_element(By.XPATH, "..")
            z_index = parent.value_of_css_property("z-index")
            child = parent
        if isinstance(z_index, str):
            z_index = int(z_index)
    except:
        z_index = 0
    parsed_element["z_index"] = z_index
    for el in parsed_element:
        if isinstance(parsed_element[el], str):
            parsed_element[el] = html.escape(parsed_element[el])
    return parsed_element


def check_semantic(element, keywords):
    for k in keywords:
        if k.lower() in element.lower():
            return True
    return False
def choose_parameters(element, parameters):
    for p_name in parameters:
        if p_name.lower() in element.lower():
            return parameters[p_name]
    return ""

def clean_outer_html(element):
    soup = BeautifulSoup(element, "html.parser")
    for element in soup(['script','iframe','noscript','style', 'svg']):
        element.decompose()
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

    return soup.prettify()


def same_element(element1, element2):
    try:
        location = True
        location_view = True
        for key in element1:
            if key == "location":
                if np.abs(element1[key]["x"] - element2[key]["x"]) >= 10 or np.abs(element1[key]["y"] - element2[key]["y"]) >= 10:
                    location = False
                    if not location_view:
                        return False
            elif key == "location_view":
                if np.abs(element1[key]["x"] - element2[key]["x"]) >= 10 or np.abs(element1[key]["y"] - element2[key]["y"]) >= 10:
                    location_view = False
                    if not location:
                        return False
            elif key == "size":
                if np.abs(element1[key]["height"] - element2[key]["height"]) >= 10 or np.abs(element1[key]["width"] - element2[key]["width"]) >= 10:
                    return False
            elif element1[key] != element2[key]:
                return False
    except:
        return False
    return True
