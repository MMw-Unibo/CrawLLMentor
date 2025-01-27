import networkx as nx
from utility import deterministic_hash
import gravis as gv
import bs4
import re
import time
import pickle


class Graphs:
    def __init__(self, paths=None):
        if paths:
            self._complete_graph = pickle.load(open(paths['complete_graph'], 'rb'))
            self._req_res_graph = pickle.load(open(paths['req_res_graph'], 'rb'))
            self._state_action_graph = pickle.load(open(paths['state_action_graph'], 'rb'))
        else:
            self._complete_graph = nx.DiGraph()
            self._req_res_graph = nx.DiGraph()
            self._state_action_graph = nx.DiGraph()


        
    def get_complete_graph(self):
        return self._complete_graph
    
    def get_req_res_graph(self):
        return self._req_res_graph
    
    def get_state_action_graph(self):  
        return self._state_action_graph
    

    def add_state(self, id, state, label, hover, click, size=50, color="cyan", border_size=1, others_dict={}):
        if state['has_form']:
            color = "blue"
        self._complete_graph.add_node(id,  state = state, size=size, color=color, label=label, hover=hover, click=click, border_size=border_size, **others_dict)
        self._req_res_graph.add_node(id,  state = state, size=size, color=color, label=label, hover=hover, click=click, border_size=border_size, **others_dict)
        self._state_action_graph.add_node(id,  state = state, size=size, color=color, label=label, hover=hover, click=click, border_size=border_size, **others_dict)

    def add_action(self, id, action, label, size=30, color="red", border_size=1, others_dict={}):
        self._complete_graph.add_node(id, action=action, size=size, color=color, label=label, border_size=border_size, **others_dict)
        self._req_res_graph.add_node(id, action=action, size=size, color=color, label=label, border_size=border_size, **others_dict)
        self._state_action_graph.add_node(id, action=action, size=size, color=color, label=label, border_size=border_size, **others_dict)

    def add_http_group(self, id, color="blueviolet", border_size=2, border_color="red", size=20, others_dict={}, which_graph = ["all"]):
        if "complete" in which_graph or "all" in which_graph:
            self._complete_graph.add_node(id, size=size, color=color, border_size=border_size, border_color = border_color, **others_dict)
        if "req_res" in which_graph or "all" in which_graph:
            self._req_res_graph.add_node(id, size=size, color=color, border_size=border_size, border_color = border_color, **others_dict)

    def add_http_request(self, id, label, click, shape="circle", size = 5, color = "yellow"):
        self._complete_graph.add_node(id, shape = shape, size=size, color=color, label=label, click=click)

    def add_http_response(self, id, label, click, color="lime"):
        self._complete_graph.add_node(id, color=color, label=label, click=click)
    
    def add_edge(self, start_node, end_node, size=1, arrow_size = 10, color="black", which_graph = ["all"]):
        if "complete" in which_graph or "all" in which_graph:
            self._complete_graph.add_edge(start_node, end_node, size=size, arrow_size=arrow_size, color=color)
        if "req_res" in which_graph or "all" in which_graph:
            self._req_res_graph.add_edge(start_node, end_node, size=size, arrow_size=arrow_size, color=color)
        if "state_action" in which_graph or "all" in which_graph:
            self._state_action_graph.add_edge(start_node, end_node, size=size, arrow_size=arrow_size, color=color)


    def node_in_graph(self, node):
        return node in self._complete_graph
    
    def state_in_graph(self, current_state, states):
        for key in states:
            if states[key] == current_state:
                return True
        return False
    
    def shortest_path(self, end, start = deterministic_hash(("None", repr("Start")))):
        return nx.shortest_path(self._state_action_graph, start, end)
    

    def display(self):
        fig = gv.d3(self._state_action_graph, show_node_label=True, show_edge_label=False, node_label_data_source='label', node_drag_fix=True,  node_hover_neighborhood=True, edge_curvature=0.4)
        fig.display()
        fig = gv.d3(self._complete_graph, show_node_label=True, show_edge_label=False, node_label_data_source='label', node_drag_fix=True,  node_hover_neighborhood=True, edge_curvature=0.4)
        fig.display()
        fig = gv.d3(self._req_res_graph, show_node_label=True, show_edge_label=False, node_label_data_source='label', node_drag_fix=True,  node_hover_neighborhood=True, edge_curvature=0.4)
        fig.display()

    def save_graphs(self, base_directory):
        timestamp = str(time.time())
        pickle.dump(self._complete_graph, open("./" + base_directory + '/complete_graph_' + timestamp + '.pickle', 'wb'))
        pickle.dump(self._req_res_graph, open("./" + base_directory + '/req_res_graph_' + timestamp + '.pickle', 'wb'))
        pickle.dump(self._state_action_graph, open("./" + base_directory + '/state_action_graph_' + timestamp + '.pickle', 'wb'))

    def save_figs(self, base_directory):
        timestamp = str(time.time())
        fig = gv.d3(self._state_action_graph, show_node_label=True, show_edge_label=False, node_label_data_source='label', node_drag_fix=True,  node_hover_neighborhood=True, edge_curvature=0.4)
        html_text = fig.to_html_standalone()
        soup = bs4.BeautifulSoup(html_text)
        div = soup.find("div", id = re.compile(".*-left-inner-div"))
        legend = '<svg width = "200" heigth = "100" style = "position : absolute; top : 50px; left : 50px"><circle cx="10" cy="10" r="6" style="fill: cyan;" ></circle><circle cx="10" cy="30" r="6" style="fill: red;"></circle><circle cx="10" cy="50" r="6" style="fill: orange;"></circle><text x="30" y="10" alignment-baseline="middle" style="font-size: 15px;">State</text><text x="30" y="30" alignment-baseline="middle" style="font-size: 15px;">Action</text><text x="30" y="50" alignment-baseline="middle" style="font-size: 15px;">Start Action</text></svg>'
        div.append(bs4.BeautifulSoup(legend,"html.parser"))
        html_text = soup.prettify()
        with open("./" + base_directory + '/state_action_graph_' + timestamp + '.html', 'w+', encoding='utf-8') as f:
            f.write(html_text)

        fig = gv.d3(self._complete_graph, show_node_label=True, show_edge_label=False, node_label_data_source='label', node_drag_fix=True,  node_hover_neighborhood=True, edge_curvature=0.4)
        html_text = fig.to_html_standalone()
        soup = bs4.BeautifulSoup(html_text)
        div = soup.find("div", id = re.compile(".*-left-inner-div"))
        legend = '<svg width = "200" heigth = "100" style = "position : absolute; top : 50px; left : 50px"><circle cx="10" cy="10" r="6" style="fill: cyan;" ></circle><circle cx="10" cy="30" r="6" style="fill: red;"></circle><circle cx="10" cy="50" r="6" style="fill: orange;"></circle><text x="30" y="10" alignment-baseline="middle" style="font-size: 15px;">State</text><text x="30" y="30" alignment-baseline="middle" style="font-size: 15px;">Action</text><text x="30" y="50" alignment-baseline="middle" style="font-size: 15px;">Start Action</text></svg>'
        div.append(bs4.BeautifulSoup(legend,"html.parser"))
        html_text = soup.prettify()

        with open("./" + base_directory + '/complete_graph_' + timestamp + '.html', 'w+', encoding="utf-8") as f:
            f.write(fig.to_html_standalone())

        fig = gv.d3(self._req_res_graph, show_node_label=True, show_edge_label=False, node_label_data_source='label', node_drag_fix=True,  node_hover_neighborhood=True, edge_curvature=0.4)
        html_text = fig.to_html_standalone()
        soup = bs4.BeautifulSoup(html_text)
        div = soup.find("div", id = re.compile(".*-left-inner-div"))
        legend = '<svg width = "200" heigth = "100" style = "position : absolute; top : 50px; left : 50px"><circle cx="10" cy="10" r="6" style="fill: cyan;" ></circle><circle cx="10" cy="30" r="6" style="fill: red;"></circle><circle cx="10" cy="50" r="6" style="fill: orange;"></circle><text x="30" y="10" alignment-baseline="middle" style="font-size: 15px;">State</text><text x="30" y="30" alignment-baseline="middle" style="font-size: 15px;">Action</text><text x="30" y="50" alignment-baseline="middle" style="font-size: 15px;">Start Action</text></svg>'
        div.append(bs4.BeautifulSoup(legend,"html.parser"))
        html_text = soup.prettify()

        with open("./" + base_directory +  '/req_res_graph_' + timestamp + '.html', 'w+', encoding='utf-8') as f:
            f.write(fig.to_html_standalone())



