import difflib
import json
from html_utility import same_element
class State:
    def __init__(self, url, elements, visible_text, body, parametric_state = False, label = "temp", has_form = False):
        self._url = url.split("?")[0]
        self._elements = elements
        self._visible_text = visible_text
        self._body = body
        self._parametric_state = parametric_state
        self._label = label
        self._has_form = has_form

    """ def __hash__(self):
        return hash(json.dumps(self._elements) + ' ' + self._visible_text) """
    
    def __repr__(self):
        els = ""
        for el in self._elements:
            try:
                copy = el.copy()
                copy.pop('location', None)
                copy.pop('size', None)
                els += json.dumps(copy)
            except:
                els += json.dumps(el)
        return els + ' ' + self._visible_text
    
    def get_visible_text(self):
        return self._visible_text
    
    def get_body(self):
        return self._body
    
    def get_label(self):    
        return self._label
    
    def set_label(self, label):
        self._label = label
    
    def contains(self, params):
        for el in self._elements:
            el = str(el).lower()
            found = True
            for p in params:
                if p.lower() not in el:
                    found = False
                    break
            if found:
                return True
        return False

    def get_url(self):
        return self._url
    
    def get_elements(self):
        return self._elements
    
    def has_form(self):
        return self._has_form
    
    def to_json(self):
        return {"elements" : self._elements, "url" : self._url, "visible_text" : self._visible_text, "body" : self._body, "has_form" : self._has_form}

    def __str__(self):
        return self._visible_text

    def __eq__(self, other):
        if isinstance(other, State):
            for el in self._elements:
                found = False
                for other_el in other.get_elements():
                    if same_element(el, other_el):
                        found = True
                        break
                if not found:
                    return False
            if self._url == other.get_url() and self._visible_text == other.get_visible_text() :
                return True
        return False
    
    def placeholder_param_in_page(self, params):
        for param in params:
            if str(param['value']) != '' and str(param['value']) in self._visible_text and self._visible_text.count(str(param['value'])) < 5 :
                self._visible_text = self._visible_text.replace(param['value'], "##_PLACEHOLDER_##")
                self._parametric_state = True
    

