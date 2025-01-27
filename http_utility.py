import re
import base64
import json
import time


def check_url(url, http_interesting_params):
    interesting_params_found = []
    found = False
    url = url.split("?")[0]
    url_parts = list(filter(None, url.split("/")[1:]))
    for part in url_parts:
        if part == "":
            continue
        for k in http_interesting_params["name"]["regexes"]:
            for reg in http_interesting_params["name"]["regexes"][k]:
                if re.match(reg, part.lower()):
                    interesting_params_found.append(('url', part, "", "Regex on URL. Category: " + k))
                    found = True
        for k in http_interesting_params["name"]["keywords"]:
            for keyword in http_interesting_params["name"]["keywords"][k]:
                if keyword.lower() in part.lower():
                    interesting_params_found.append(('url', part, "", f"Keyword match on URL. Category: {k}"))
                    found = True
                    break # only one keyword per category
        for k in http_interesting_params["value"]["regexes"]:
            for reg in http_interesting_params["value"]["regexes"][k]:
                if re.match(reg, part.lower()):
                    interesting_params_found.append(('url', "", part, "Regex on URL. Category: " + k))
                    found = True
        for k in http_interesting_params["value"]["keywords"]:
            for keyword in http_interesting_params["value"]["keywords"][k]:
                if keyword.lower() in part.lower():
                    interesting_params_found.append(('url', "", part, f"Keyword match on URL. Category: {k}"))
                    found = True
                    break 
        try:
            decoded_base64 = base64.b64decode(part.lower())
            if decoded_base64.decode().isdigit() and len(decoded_base64.decode()) >= 5:
                interesting_params_found.append(('url', "", part, "base64 value"))
                found = True
        except:
            pass

        try:
                int_value = int(part.lower())
                now = time.time() * 1000 # in milliseconds
                now_minus_two_years = now - 63113904
                now_plus_two_years = now + 63113904
                if int_value >= now_minus_two_years and int_value <= now_plus_two_years:
                    interesting_params_found.append(('url', "", part, "Timestamp"))
                    found = True
        except:
            pass

        try:
            bytes.fromhex(part.lower()).decode('ascii')
            interesting_params_found.append(('url', "", part, "Hex value"))
            found = True
        except:
            pass
        
    return found, interesting_params_found

def check_http_request(parameters, cookies, headers, http_interesting_params):

    interesting_params_found = []
    found = False
    for key in http_interesting_params:
        if key == "parameters":
            p_c_h = parameters
        elif key == "cookies":
            p_c_h = cookies
        elif key == "headers":
            p_c_h = headers
        for param in p_c_h:
            try:
                int_value = int(param['value'].lower())
                now = time.time() * 1000 # in milliseconds
                now_minus_two_years = now - 63113904
                now_plus_two_years = now + 63113904
                if int_value >= now_minus_two_years and int_value <= now_plus_two_years:
                    interesting_params_found.append((key, param['name'], param['value'], "Timestamp"))
                    found = True
                    continue
            except:
                pass
            for k in http_interesting_params[key]["name"]["regexes"]:
                for reg in http_interesting_params[key]["name"]["regexes"][k]:
                    if re.match(reg, param['name'].lower()):
                        interesting_params_found.append((key, param['name'], param['value'], "Regex on parameter name. Category: " + k))
                        found = True
    
            for k in http_interesting_params[key]["name"]["keywords"]:
                for keyword in http_interesting_params[key]["name"]["keywords"][k]:
                    if keyword.lower() in param['name'].lower() and not (key == "headers" and param['name'].lower() == "user-agent"):
                        interesting_params_found.append((key, param['name'], param['value'], f"Keyword match on parameter name. Category: {k}"))
                        found = True
                        break 
            for k in http_interesting_params[key]["value"]["regexes"]:
                for reg in http_interesting_params[key]["value"]["regexes"][k]:
                    if re.match(reg, param['value'].lower()):
                        interesting_params_found.append((key, param['name'], param['value'], "Regex on parameter value. Category: " + k))
                        found = True
            for k in http_interesting_params[key]["value"]["keywords"]:
                for keyword in http_interesting_params[key]["value"]["keywords"][k]:
                    if keyword.lower() in param['value'].lower():
                        interesting_params_found.append((key, param['name'], param['value'], f"Keyword match on parameter value. Category: {k}"))
                        found = True
                        break 


                
            try:
                decoded_base64 = base64.b64decode(param['value'].lower())
                if decoded_base64.decode().isdigit() and len(decoded_base64.decode()) >= 5:
                    interesting_params_found.append((key, param['name'], param['value'], "base64 value"))
                    found = True
            except:
                pass

            try:
                bytes.fromhex(param['value'].lower()).decode('ascii')
                interesting_params_found.append((key, param['name'] , param['value'].lower(), "Hex value"))
                found = True
            except:
                pass

            


    return found, interesting_params_found
    


def check_url_white_list(url, white_list):
    for w in white_list:
        if (w.startswith("*") and url.endswith(w[1:])) or url == w:
            return True
    return False