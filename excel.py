import time, json, xlsxwriter
def save_excel(interesting_states, interesting_requests, base_directory):
        
    workbook = xlsxwriter.Workbook('./' + base_directory + '/interesting' + str(time.time()) + '.xlsx')
    state_worksheet = workbook.add_worksheet("Interesting States")
    action_worksheet = workbook.add_worksheet("Interesting Requests")
    filtered_worksheet = workbook.add_worksheet("Filtered Requests")
    cell_format = workbook.add_format()
    cell_format.set_align('left')
    cell_format.set_align('vcenter')
    cell_format.set_text_wrap()
    bold_format = workbook.add_format({'bold': True})
    merge_format = workbook.add_format(
        {
            "bold": True,
            "align": "center"
        }
    )
    state_worksheet.merge_range('A1:C1', 'INTERESTING STATES', merge_format)
    state_worksheet.write(1, 0, "STATE", bold_format)
    state_worksheet.write(1, 1, "LABEL", bold_format)
    state_worksheet.write(1, 2, "MOTIVATION", bold_format)
    action_worksheet.merge_range('A1:E1', 'INTERESTING REQUESTS', merge_format)
    action_worksheet.write(1, 0, "START STATE", bold_format)
    action_worksheet.write(1, 1, "LABEL START STATE", bold_format)
    action_worksheet.write(1, 2, "ACTION", bold_format)
    action_worksheet.write(1, 3, "HTTP REQUEST", bold_format)
    action_worksheet.write(1, 4, "DATA (Type, Name, Value, Motivation)", bold_format)
    action_worksheet.write(1, 5, "FINAL STATE", bold_format)
    action_worksheet.write(1, 6, "LABEL FINAL STATE", bold_format)
    filtered_worksheet.merge_range('A1:E1', 'FILTERED REQUESTS', merge_format)
    filtered_worksheet.write(1, 0, "START STATE", bold_format)
    filtered_worksheet.write(1, 1, "LABEL START STATE", bold_format)
    filtered_worksheet.write(1, 2, "ACTION", bold_format)
    filtered_worksheet.write(1, 3, "DATA (Type, Name, Value, Motivation)", bold_format)
    filtered_worksheet.write(1, 4, "FINAL STATE", bold_format)
    filtered_worksheet.write(1, 5, "LABEL FINAL STATE", bold_format)



    current_state_row = 2
    current_request_row = 2
    current_filtered_row = 2


    for state, label, sensitive in interesting_states:
        state_worksheet.write(current_state_row, 0, state, cell_format)
        state_worksheet.write(current_state_row, 1, label, cell_format)
        state_worksheet.write(current_state_row, 2, sensitive, cell_format)
        current_state_row += 1


    for previousState, previousState_label, currentAction, req, parameters, next_state, next_state_label in interesting_requests:
        action_worksheet.write(current_request_row, 0, previousState, cell_format)
        action_worksheet.write(current_request_row, 1, previousState_label, cell_format)
        action_worksheet.write(current_request_row, 2, currentAction, cell_format)
        req_string = ""
        req = json.loads(req)
        for k in req:
            req_string += k + ": " + str(req[k]) + "\n"
        action_worksheet.write(current_request_row, 3, req_string, cell_format)
        params = ""
        parameters = json.loads(parameters)
        for tup in parameters:
            params += "Type: " + tup[0] + "; Name: " + tup[1] + "; Value: " + tup[2] + '; Motivation: ' + tup[3] +'.\n\n'
        action_worksheet.write(current_request_row, 4, params, cell_format)
        action_worksheet.write(current_request_row, 5, next_state, cell_format)
        action_worksheet.write(current_request_row, 6, next_state_label, cell_format)
        current_request_row += 1

    filtered_requests = set()
    for previousState, previousState_label, currentAction, _, parameters, next_state, next_state_label in interesting_requests:
        filtered_requests.add((previousState, previousState_label, currentAction, parameters, next_state, next_state_label))

    for previousState, previousState_label, currentAction, parameters, next_state, next_state_label in filtered_requests:
        filtered_worksheet.write(current_filtered_row, 0, previousState, cell_format)
        filtered_worksheet.write(current_filtered_row, 1, previousState_label, cell_format)
        filtered_worksheet.write(current_filtered_row, 2, currentAction, cell_format)
        params = ""
        parameters = json.loads(parameters)
        for tup in parameters:
            params += "Type: " + tup[0] + "; Name: " + tup[1] + "; Value: " + tup[2] + '; Motivation: ' + tup[3] +'.\n\n'
        filtered_worksheet.write(current_filtered_row, 3, params, cell_format)
        filtered_worksheet.write(current_filtered_row, 4, next_state, cell_format)
        filtered_worksheet.write(current_filtered_row, 5, next_state_label, cell_format)
        current_filtered_row += 1

    state_worksheet.autofit()
    action_worksheet.autofit()
    workbook.close()