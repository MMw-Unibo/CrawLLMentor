# CrawLLMentor

## Project Overview
Web applications play a vital role in various critical aspects of daily life, from social platforms to healthcare and banking systems. Their widespread use and the massive volume of data flowing through them make them an attractive target for cyberattacks. While numerous tools exist to identify vulnerabilities, most focus primarily on technical issues. Business logic vulnerabilities, however, are often overlooked due to the challenges associated with their automated detection. In this paper, we present CrawLLMentor, a novel black-box framework designed to assist penetration testers in identifying business logic vulnerabilities. The framework acts as an intelligent assistant for penetration testers, leveraging Large Language Models (LLMs) to analyze the semantics of web pages and enabling a deeper understanding of HTML element functionalities. By providing insights into the website’s structure and behavior, the tool helps testers uncover potential flaws in business logic. We implemented and tested the tool on several web applications, demonstrating its effectiveness in real-world scenarios. This innovative approach enhances the security of web applications, addressing a critical gap in cybersecurity.

---

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [File Descriptions](#file-descriptions)
- [License](#license)

---

## Installation
1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd <repository_name>
   ```

2. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the OpenAI API key:**
   - Create a file named `api_key.txt` in the root directory.
   - Add your OpenAI API key to this file.
  
4. **Create a folder to save the results.**

---

## Usage
To run the crawler, use the following command:
```bash
python crawllmentor.py -bu <base_url> -wl <white_list> -d <results_directory>
```

### Command Line Arguments
- `-bu`, `--base_urls`: Base URL of the website to crawl (required).
- `-wl`, `--white_list`: White list of the website to crawl (required).
- `-d`, `--directory`: Directory where to save the results (required).
- `-a`, `--authentication`: Authentication JSON file (optional).
- `-lc`, `--logout_conditions`: Logout conditions JSON file (optional).
- `-fa`, `--forbidden_actions`: Forbidden actions JSON file (optional).
- `-cc`, `--chatgpt_cache`: ChatGPT cache to use (optional).
- `-htc`, `--header_token_cookie`: Headers/tokens/cookies to set (optional).

---

## File Descriptions

### Main Files
- **`crawllmentor.py`**: Main script to run the web crawler.
- **`graph.py`**: Contains the `Graphs` class for managing and visualizing the website's structure.
- **`state.py`**: Defines the `State` class representing the state of a web page.
- **`action.py`**: Defines various action classes (`Click`, `Follow`, `Select`, `Type`, etc.) for interacting with web elements.
- **`state_utility.py`**: Utility functions for generating state actions and managing state transitions.
- **`html_utility.py`**: Functions for parsing and cleaning HTML elements.
- **`http_utility.py`**: Functions for checking URLs and HTTP requests for interesting parameters.
- **`chatgpt.py`**: Interacts with OpenAI's GPT for semantic analysis of web pages.
- **`excel.py`**: Functions for saving interesting states and requests to an Excel file.
- **`utility.py`**: General utility functions, including hashing and drawing on images.

### Example Files
- **`demonstrations/`**: Contains JSON files for authentication and logout conditions.
- **`http_interesting_parameters.json`**: JSON file defining interesting HTTP parameters.
- **`open-cookie-database.csv`**: CSV file containing cookie data.


## License
This project is licensed under the MIT License. See the `LICENSE` file for details.
