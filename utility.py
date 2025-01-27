
import cv2

import hashlib

def draw(image_name, meanings_rects):
    img = cv2.imread(image_name, cv2.IMREAD_COLOR)

    for meaning, rect in meanings_rects:
        for key in rect:
            if key != 'toJSON':
                rect[key] = round(rect[key]*1.25)
        if meaning != "" and rect['y'] > 1920:
            continue
        x = rect['x']
        y = rect['y']
        img = cv2.rectangle(img, (x, y), (x + rect['width'], y + rect['height']), (0,0,240), 1)
        cv2.putText(img, meaning, (x, y - 10), cv2.FONT_HERSHEY_PLAIN, 0.9, (0,0,240), 1)
        #img = cv2.rectangle(img, (rect['x'], rect['y']), (rect['x'] + rect['width'], rect['y'] + rect['height']), (0,0,240), 1)
        #cv2.putText(img, meaning, (rect['x'], rect['y'] - 10), cv2.FONT_HERSHEY_PLAIN, 0.9, (0,0,240), 1)
    cv2.imwrite(image_name, img)


def hash_state(current_state, states):
    for key in states:
        if states[key] == current_state:
            return key
    return hashlib.sha256(repr(current_state).encode('utf-8')).hexdigest()  


def deterministic_hash(data):
    return hashlib.sha256(repr(data).encode('utf-8')).hexdigest()    