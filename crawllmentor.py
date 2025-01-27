import json
import time
import os 
from seleniumwire import webdriver


# Create a new instance of the Firefox driver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

from excel import save_excel
from state import State
from action import *
from state_utility import *
from http_utility import *
from utility import draw, deterministic_hash

import gravis as gv
from utility import *
import html
import traceback
from chatgpt import ChatGpt

import argparse

from collections import deque

from graph import Graphs

import pandas as pd



session_expired = True
logged_in = False
loggin_in = False


exclamation_mark = gv.convert.image_to_data_url('https://upload.wikimedia.org/wikipedia/commons/d/dd/Achtung.svg', 'svg')
alert_http = gv.convert.image_to_data_url('https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/OOjs_UI_icon_alert-invert.svg/1024px-OOjs_UI_icon_alert-invert.svg.png')



options = {
    'enable_har': True  # Capture HAR data, retrieve with driver.har
}
chrome_options = Options()
chrome_options.add_argument("--disable-search-engine-choice-screen")
# comment these lines if you want to accept http UNSECURE connections
#chrome_options.add_argument("--allow-running-insecure-content")
#chrome_options.add_argument('--ignore-certificate-errors')
#chrome_options.add_argument('--disable-web-security')
#chrome_options.add_argument("--unsafely-treat-insecure-origin-as-secure=http://php.testsparker.com")  # Replace example.com with your site's domain
#chrome_options.add_argument("--ignore_ssl")
#chrome_options.add_argument('--ignore-ssl-errors')
#chrome_options.add_argument("--user-data-dir=USER DATA DIR")
#chrome_options.add_argument('--profile-directory=Profile 2')
chrome_install = ChromeDriverManager().install()

folder = os.path.dirname(chrome_install)
chromedriver_path = os.path.join(folder, "chromedriver.exe")
driver = webdriver.Chrome(seleniumwire_options=options, chrome_options = chrome_options, service=ChromeService(chromedriver_path))
driver.maximize_window()
a = driver.get_window_size()
parser = argparse.ArgumentParser()
parser.add_argument("-bu","--base_urls", help="base url of the website to crawl", required=True)
parser.add_argument("-wl","--white_list", nargs='+', help="white list of the website to crawl", required=True)
parser.add_argument("-a","--authentication", help="authentication json file")
parser.add_argument("-lc","--logout_conditions", help="logout conditions json file")
parser.add_argument("-fa", "--forbidden_actions", help="forbidden actions json file")
parser.add_argument("-d","--directory", help="directory where to save the results", required=True)
parser.add_argument("-cc","--chatgpt_cache", help="chatgpt cache to use", required=True)
parser.add_argument("-htc","--header_token_cookie", help="headers/tokens/cookies to set", required=False)

args = parser.parse_args()

# multiple URL
base_urls = args.base_urls
if not isinstance(base_urls, list):
    base_urls = [base_urls]
white_list = args.white_list
base_directory = args.directory 

# check if screenshots directory exists 
if not os.path.exists("./" + base_directory):
    os.makedirs("./" + base_directory)
if not os.path.exists("./" + base_directory + "/screenshots"):
    os.makedirs("./" + base_directory + "/screenshots")

with open("./http_interesting_parameters.json") as f:
    http_interesting_params = json.load(f)

    
chatgpt = ChatGpt(args.chatgpt_cache)

graphs = Graphs()

if args.authentication is not None:
    with open("./demonstrations/" + args.authentication) as f:
        authentication_demonstration = json.load(f)
else:
    authentication_demonstration = None
if args.logout_conditions is not None:
    with open("./demonstrations/" + args.logout_conditions) as f:
        logout_conditions = json.load(f)
else:
    logout_conditions = None

if args.forbidden_actions is not None:
    with open("./demonstrations/" + args.forbidden_actions) as f:
        forbidden_actions = json.load(f)
else:
    forbidden_actions = None

try:
    with open("./" + base_directory + "/cookies.json") as f:
        cookie_banner_detection_patterns = json.load(f)
except:
    cookie_banner_detection_patterns = None

# Add the headers to the request
def interceptor(request):
    for header in headers:
        request.headers[header] = headers[header]


if args.header_token_cookie is not None:
    with open("./" + base_directory + "/" + args.header_token_cookie) as f:
        htc = json.load(f)
    for key in htc:
        if key == "headers":
            driver.request_interceptor = interceptor
            headers = htc[key]
        elif key == "session":
            tokens = htc[key]
            for token in tokens:
                a = driver.execute_script("return window.sessionStorage.setItem('" + token + "', '" + json.dumps(tokens[token]) + "')")
        elif key == "local":
            tokens = htc[key]
            for token in tokens:
                driver.execute_script("return window.localStorage.setItem('" + token + "', '" + tokens[token] + "')")
        elif key == "cookies":
            cookies = htc[key]
            for cookie in cookies:
                driver.add_cookie({"name": cookie, "value": cookies[cookie]})



cookies = pd.read_csv("./open-cookie-database.csv")
cookies = cookies[cookies['Category'] != 'Functional']['Cookie / Data Key name'].tolist()
# black list of cookies
cookies += []
# black list of headers
headers = ['sec-ch-ua', 'user-agent', 'sec-fetch-site', 'sec-fetch-mode', 'sec-fetch-dest', 'accept-encoding', 'accept-language', 'sec-ch-ua-mobile', 'referer']


states = {}


for base_url in base_urls:
    # Navigate to the starting URL
    driver.implicitly_wait(0.5)
    driver.get(base_url)

    time.sleep(5)
    driver.get(base_url)
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
    queue = deque()

    loop_actions = []
    pending_actions = {}
    dead_ends = []
    har_history = []

    labels = []
    states_labels = {}

    loggin_in = False
    logged_in = False
    session_expired = False
    cookie_banner_detected = False

    visited_urls = set()
    interesting_states = set()
    interesting_requests = set()


    def crawl_website():
        
        global loggin_in
        global logged_in
        global session_expired
        global cookie_banner_detected

        previousState = None
        currentAction = None
        iteration_count = 0
        path = []
        arbitrary_actions = None
        params = None


        while True:
            current_window = driver.current_window_handle
            num_windows = len(driver.window_handles)
            action_executed = True
            exit_action = False
            timer = 1
            current_interesting_requests = set()
            
            if iteration_count > 300:
                return
            
            
            visited_urls.add(driver.current_url)

            if currentAction is not None:

                try:
                    if currentAction.get_type() == "Follow" and currentAction.get_element().get('accessible_name') == "cookie policy":
                        print("Here")
                    action_image = currentAction(driver)
                    if arbitrary_actions and arbitrary_actions[0]["action_name"] == "Wait":
                        a = arbitrary_actions.popleft()
                        timer = a['seconds']
                    time.sleep(timer)
                    # Reset the timer
                    timer = 1
                    try:
                        # Check if there is an element with class "carousel"
                        carousel_elements = driver.find_element(By.CLASS_NAME, "carousel")
                        if carousel_elements and not driver.current_url in visited_urls:
                            driver.execute_script("$('.carousel').each(function() {$(this).carousel('cycle'); $(this).carousel(0); });")
                            time.sleep(5)
                            driver.execute_script("$('.carousel').each(function() {$(this).carousel('pause'); $(this).carousel(0); });")
                            time.sleep(5)
                    except NoSuchElementException:
                        pass

                    # Check if a new window has been opened
                    if num_windows != len(driver.window_handles):
                        for window in driver.window_handles:
                            if window != current_window:
                                driver.close()
                                # switch to the new window
                                driver.switch_to.window(window)

                    # check if the current URL is in the white list. If not, exit. If I'm logging in I allow the URL to be out of the white list
                    if not loggin_in and not check_url_white_list(driver.current_url.split('/')[2], white_list):
                        exit_action = True


                    # If logout is detected, go back to the base page
                    if logout_conditions and logged_in and logout_detection(driver, logout_conditions):
                        if pending_actions.get(hash_state(currentState, states)):
                            pending_actions[hash_state(currentState, states)].appendleft(currentAction)
                        session_expired = True
                        logged_in = False
                        driver.get(authentication_demonstration["url"])
                        time.sleep(5)
                    else:
                        graphs.add_action(deterministic_hash((hash_state(previousState, states), repr(currentAction))), action=vars(currentAction), label=str(currentAction), others_dict = {"click" : '<img src='+action_image+'>'})
                        graphs.add_edge(hash_state(previousState, states), deterministic_hash((hash_state(previousState, states), repr(currentAction))), size=3, arrow_size = 50)

                except Exception as e: 
                    traceback.print_exc()
                    action_executed = False
                    if path:
                        del pending_actions[path[-1]]
                    

            else:
                # If the current state is the start state, add the start action
                previousState = "None"
                currentAction = "Start"
                graphs.add_action(deterministic_hash((hash_state(previousState, states), repr(currentAction))), action=currentAction, label=str(currentAction), color="orange")

            if authentication_demonstration and session_expired and not loggin_in:
                loggin_in = True
                arbitrary_actions = deque(authentication_demonstration['actions'])
            elif action_executed:
                if exit_action:
                    # If the current URL is not in the white list, add an exit state
                    currentState = State(driver.current_url, [driver.current_url, "exit"], "", "", label = "Out of domain")
                    states_labels[hash_state(currentState, states)] = "Out of domain"
                    if not graphs.node_in_graph(hash_state(currentState, states)):
                        res = driver.save_screenshot("./" + base_directory + "/screenshots/" + str(hash_state(currentState, states)) + ".png")
                        state_image = gv.convert.image_to_data_url("./" + base_directory + "/screenshots/" + str(hash_state(currentState, states)) + ".png")
                        graphs.add_state(hash_state(currentState, states), state = currentState.to_json(), label="Out of domain", hover=driver.current_url, click='<img src='+state_image+'>', color="green")

                else:

                    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
                    driver.execute_script("window.scrollTo(0,0)")

                    currentState, actions, meanings_rects = generate_state_actions(driver = driver, chatgpt=chatgpt, visited_urls=visited_urls, white_list=white_list)
                    if forbidden_actions:
                        for a in actions:
                            if a.get_type() in forbidden_actions:
                                keywords = forbidden_actions[a.get_type()]
                                if any([k in a.get_element()['text'] for k in keywords]):
                                    actions.remove(a)
                            


                    driver.execute_script("window.scrollTo(0,0)")

                    if cookie_banner_detection_patterns and not cookie_banner_detected and not loggin_in and cookie_banner_detection(driver, cookie_banner_detection_patterns, currentState): 
                        arbitrary_actions = deque(cookie_banner_detection_patterns['actions'])
                        cookie_banner_detected = True

                    if authentication_demonstration and not loggin_in and not logged_in and not cookie_banner_detected and login_page_detection(driver, authentication_demonstration, currentState):
                        loggin_in = True
                        arbitrary_actions = deque(authentication_demonstration['actions'])


                # handle the HTTP requests/responses
                edges_to_add = []
                requests = []
                requests_str = ""
                responses = []
                responses_str =  ""
                requests_no_response = []
                har = json.loads(driver.har)['log']['entries']
                html_table = "<style>table, th, td {border: 1px solid black;border-collapse: collapse;vertical-align: top;}</style><table style='width:100%'> <tr><th style='width:50%'>HTTP Request</th><th style='width:50%'>HTTP Response</th></tr>"
                at_least_one = False
                sensitive_lines = []
                lines = []
                for r in har:
                    request = r['request']
                    response = r['response']

                                        
                    if json.dumps(r) not in har_history and check_url_white_list(request['url'].split('/')[2], white_list):
                        at_least_one = True
                        har_history.append(json.dumps(r))
                        table_line = "<tr><td style='width:50%'>"
                        method = request['method']
                        url = request['url']
                        last_part = url.split("?")[0].split("/")[-1]
                        req_filtered = request.copy()
                        req_filtered['headers'] = [header for header in req_filtered['headers'] if header["name"] not in headers]
                        req_filtered['cookies'] = [cookie for cookie in req_filtered['cookies'] if cookie["name"] not in cookies]
                        del req_filtered['headersSize']
                        shape = "circle"
                        color = "yellow"
                        size = 5
                        sensitive_information = False
                        parameters_found = ""
                        interesting_url, parameters_found_in_url = check_url(url, http_interesting_params['parameters'])
                        interesting_parameters = False
                        parameters_found_in_request = []
                        if len(req_filtered['queryString']) > 0 or req_filtered.get('postData'):
                            params = req_filtered['queryString']
                            if req_filtered.get('postData'):
                                if req_filtered['postData'].get('params'):
                                    params += req_filtered['postData']['params']
                                elif req_filtered['postData'].get('mimeType') and 'json' in req_filtered['postData']['mimeType']:
                                    json_data = json.loads(req_filtered['postData']['text'])
                                    json_list = [{"name": key, "value": str(value)} for key, value in json_data.items()]
                                    for _, value in json_data.items():
                                        if isinstance(value, dict):
                                            json_list += [{"name": key, "value": str(value)} for key, value in value.items()]
                                    params += json_list

                                
                            # parametric state
                            currentState.placeholder_param_in_page(params)

                            interesting_parameters, parameters_found_in_request = check_http_request(parameters= params, cookies = req_filtered['cookies'], headers = req_filtered['headers'], http_interesting_params= http_interesting_params)
                        if not last_part.endswith('.js') and not last_part.endswith('.css') and (interesting_url or interesting_parameters):
                            parameters_found = parameters_found_in_url + parameters_found_in_request
                            current_interesting_requests.add((previousState.get_url() if previousState != "None" else "Start", previousState.get_label() if previousState != "None" else "Start", str(currentAction), json.dumps(req_filtered), json.dumps(parameters_found), currentState.get_url(), "label_temp_current_state"))
                            shape = "hexagon"
                            color = "tomato"
                            size = 15
                            table_line = "<tr><td style='width:50%; background-color: tomato'>"
                            sensitive_information = True
                        
                        request = json.dumps(request, indent=4)
                        table_line += request + "<br>" + str(parameters_found) + "</td>"
                        requests.append(deterministic_hash(request))
                        requests_str += request + '\n\n'
                        
                        graphs.add_http_request(deterministic_hash(request), label="HTTP " + method + " " + url, shape = shape, size = size, click=str(parameters_found) + "\n" + request, color=color)

                        if response:
                            response['content']['text'] = html.escape(response['content']['text'], True)
                            status = response['status']
                            response = json.dumps(response, indent=4)
                            table_line += "<td>" + response + "</td></tr>"
                            responses_str += response + '\n\n'
                            responses.append(deterministic_hash(response))
                            graphs.add_http_response(deterministic_hash(response), label=status, click=response)
                            graphs.add_edge(deterministic_hash(request), deterministic_hash(response), which_graph=["complete"])
                        else:
                            table_line += "<td> None </td></tr>"
                            requests_no_response.append(deterministic_hash(request))

                        if sensitive_information:
                            sensitive_lines.append(table_line)
                        else:
                            lines.append(table_line)

                for line in sensitive_lines:
                    html_table += line
                for line in lines:
                    html_table += line

                html_table += "</table>"

                if at_least_one:
                    others_dict = {}
                    others_dict["click"] = html_table
                    if sensitive_lines:
                        others_dict["image"] = alert_http
                    
                    
                    graphs.add_http_group(deterministic_hash((tuple(requests), tuple(responses), "start")), others_dict=others_dict)

                    graphs.add_http_group(deterministic_hash((tuple(requests), tuple(responses), "end")), which_graph=["complete"])
                    
                    graphs.add_edge(deterministic_hash((hash_state(previousState, states), repr(currentAction))), deterministic_hash((tuple(requests), tuple(responses), "start")), size=2, which_graph=["complete", "req_res"])
                    

                    edges_to_add.append((deterministic_hash((tuple(requests), tuple(responses), "end")), hash_state(currentState, states), {"size" : 2 }, ["complete"]))
                    edges_to_add.append((deterministic_hash((tuple(requests), tuple(responses), "start")), hash_state(currentState, states), {"size" : 2 }, ["req_res"]))

                    if requests or requests_no_response:
                        for r in requests:
                            graphs.add_edge(deterministic_hash((tuple(requests), tuple(responses), "start")), r, which_graph=["complete"])

                        for r in requests_no_response:
                            graphs.add_edge(r, deterministic_hash((tuple(requests), tuple(responses), "end")), which_graph=["complete"])

                        for r in responses:
                            graphs.add_edge(r, deterministic_hash((tuple(requests), tuple(responses), "end")), which_graph=["complete"])
                    else:
                        graphs.add_edge(deterministic_hash((tuple(requests), tuple(responses), "start")), deterministic_hash((tuple(requests), tuple(responses), "end")), size=2, which_graph=["complete"])
                else:
                    edges_to_add.append((deterministic_hash((hash_state(previousState, states), repr(currentAction))), hash_state(currentState, states), {"size" : 2 }, ["complete", "req_res"]))


                


                is_present = graphs.state_in_graph(currentState, states) 
                if not is_present and not exit_action:
                    states[hash_state(currentState, states)] = currentState
                    res = driver.save_screenshot("./" + base_directory + "/screenshots/" + str(hash_state(currentState, states)) + ".png")
                    draw("./" + base_directory + "/screenshots/" + str(hash_state(currentState, states)) + ".png", meanings_rects)
                    state_image = gv.convert.image_to_data_url("./" + base_directory + "/screenshots/" + str(hash_state(currentState, states)) + ".png")
                    if not arbitrary_actions:
                        if hash_state(currentState, states) in pending_actions:
                            pending_actions[hash_state(currentState, states)].extend(actions)
                        else:
                            pending_actions[hash_state(currentState, states)] = deque(actions)

                    fun_label = chatgpt.ask("Find a label of JUST THREE WORDS for this HTML page: ", currentState.get_body())
                    while fun_label in labels:
                        try:
                            prefix, number = fun_label.rsplit(" ", 1)
                            fun_label = prefix + " " + str(int(number) + 1)
                        except:
                            fun_label += " 1"
                            
                    labels.append(fun_label)
                    states_labels[hash_state(currentState, states)] = fun_label
                    currentState.set_label(fun_label)
                    for i_r in current_interesting_requests:
                        i_r = list(i_r)
                        i_r[-1] = fun_label
                        interesting_requests.add(tuple(i_r))
                    functionality = chatgpt.ask("Describe the functionality and the semantic meaning of the visible HTML page. Few words.", currentState.get_body())
                    sensitive = chatgpt.ask("Does this HTML page COULD POTENTIALLY contain any sensitive information? Respond starting with Yes or No, and then explain why.", currentState.get_body())
                    others_dict = {}
                    if sensitive.lower().startswith("yes"):
                        interesting_states.add((currentState.get_url(), fun_label, sensitive))
                        others_dict = {"image" : exclamation_mark}

                    graphs.add_state(hash_state(currentState, states), state = currentState.to_json(), label=fun_label, hover=functionality, click=sensitive + '</br></br><img src='+state_image+'>', others_dict=others_dict)
                else:
                    if not hash_state(currentState, states) in states_labels:
                        print("here")
                    currentState.set_label(states_labels[hash_state(currentState, states)])
                    
                    for i_r in current_interesting_requests:
                        i_r = list(i_r)
                        i_r[-1] = states_labels[hash_state(currentState, states)]
                        interesting_requests.add(tuple(i_r))
                for edge in edges_to_add:
                    graphs.add_edge(start_node=edge[0], end_node=edge[1], size= edge[2]["size"], which_graph=edge[3])

                graphs.add_edge(deterministic_hash((hash_state(previousState, states), repr(currentAction))), hash_state(currentState, states), color="lime", size=3, arrow_size = 50, which_graph=["state_action"])

                
            else:
                currentState = previousState

            currentAction = None
            while True:
                if cookie_banner_detected:
                    if arbitrary_actions:
                        previousState = currentState
                        currentAction = parse_arbitrary_action(driver, arbitrary_actions.popleft())

                        if not arbitrary_actions:
                            cookie_banner_detected = False
                        if currentAction is not None:
                            break
                    else:
                        cookie_banner_detected = False
                
                if loggin_in:
                    if arbitrary_actions:
                        previousState = currentState
                        currentAction = parse_arbitrary_action(driver, arbitrary_actions.popleft())

                        if currentAction is not None:
                            break
                    else:
                        logged_in = True
                        loggin_in = False
                        session_expired = False
                    
                if hash_state(currentState, states) in pending_actions and len(pending_actions[hash_state(currentState, states)]) > 0:
                    action = pending_actions[hash_state(currentState, states)].popleft()
                    if action is not None:
                        iteration_count += 1
                        previousState = currentState
                        currentAction = action
                        break
                else:
                    states_to_delete = []
                    for state in pending_actions.keys():
                        if pending_actions[state]:
                            currentAction = pending_actions[state].popleft()
                            path = graphs.shortest_path(state, start = deterministic_hash((hash_state("None", states), repr("Start"))))
                            try:
                                logged_in = False
                                previousState, _ , _ = move_to_state(path=path, driver=driver, base_url=base_url, DG_state_action=graphs.get_state_action_graph(), white_list=white_list)
                                previousState.set_label(states_labels[state])
                            except Exception as e:
                                currentAction = None
                                continue
                            break
                        else:
                            states_to_delete.append(state)
                    for state in states_to_delete:
                        del pending_actions[state]
                if currentAction is None:
                    return
                break
                
                
    try:
        crawl_website()
    except Exception as e:
        traceback.print_exc()
        print(e)
    while pending_actions:
        try:
            logged_in = False
            driver.get(base_url)
            driver.delete_all_cookies()
            driver.refresh()
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
            crawl_website()
        except Exception as e:
            traceback.print_exc()
            print(e)
            break

#graphs.display()
graphs.save_figs(base_directory)
graphs.save_graphs(base_directory)



# Close the browser
try:
    driver.quit()
except: 
    pass


save_excel(interesting_states, interesting_requests, base_directory)
    
