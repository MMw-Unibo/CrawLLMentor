import json
from openai import OpenAI
import tiktoken


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    encoding = tiktoken.encoding_for_model(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


class ChatGpt:
    def __init__(self, chatgpt_directory):
        with open('./api_key.txt', "r") as f:
            api_key = f.read().strip()
        self.client = OpenAI(
            # defaults to os.environ.get("OPENAI_API_KEY")
            api_key=api_key,
        )
        self._file = "./"+chatgpt_directory+"/chatgpt_cache.json"
        with open(self._file, "r") as f:
            self.chatgpt_cache = json.load(f)


        


    def ask_assistant(self, prompt):
        file = self.client.files.create(
            file=open("./gdpr.pdf", "rb"),
            purpose='assistants'
        )

        # Add the file to the assistant
        self.assistant = self.client.beta.assistants.create(
            instructions="You are a GDPR expert lawyer. Use your knowledge base to best respond to queries.",
            model="gpt-3.5-turbo-1106",
            tools=[{"type": "retrieval"}],
            file_ids=[file.id]
        )
        self.thread = self.client.beta.threads.create()
        message = self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content="Do you think this HTML is compliant to the GDPR? <html><body><form><input type='text' name='username'><input type='submit'></form></body></html>"
        )
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
        )
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=run.id
            )
            if run.completed_at:
                messages = self.client.beta.threads.messages.list(
                    thread_id=self.thread.id
                )
                message_content = messages[0].content[0].text
                '''MessageContentText(text=Text(annotations=[], value="I can't access the specific HTML file you've uploaded at the moment. However, based on the general structure you've described, it seems that the HTML form collects personal data (in this case, the username) through a text input field. \n\nTo comply with the GDPR, any collection of personal data needs to ensure that the principles of data protection, such as lawfulness, fairness, and transparency, are upheld. This typically involves providing clear information to the user about how their data will be used, obtaining explicit consent for such usage, and implementing measures to protect the security and privacy of the collected data.\n\nIf you can provide more details about how the collected data is processed, stored, and secured, I can provide a more specific assessment of whether the HTML form complies with the GDPR. Alternatively, if you can grant access to the HTML file, I can review it directly."), type='text')'''
                print(message_content)

    def chat_with_retry(self, prompt, code, model_engine, max_attempts=3):
        #return "Err"
        try:
            completion = self.client.chat.completions.create(
                model=model_engine,
                messages=[{"role": "user", "content": prompt + " " + code}],
                temperature=0.2,
            )
            return (max_attempts, completion.choices[0].message.content)
        except Exception as e:
            if max_attempts > 1:
                # Split the text in half
                half_len = len(code) // 2
                first_half = code[:half_len]
                second_half = code[half_len:]

                _ , first_response = self.chat_with_retry(prompt, first_half, model_engine, max_attempts - 1)
                _ , second_response = self.chat_with_retry(prompt, second_half, model_engine, max_attempts - 1)

                return (max_attempts, first_response + " " + second_response)
            else:
                # If max_attempts is 1, return an empty string to indicate failure
                max = 16000
                text = prompt + " " + code
                text = text[:max]
                max = int(max * 0.9)
                while True:
                    try:
                        completion = self.client.chat.completions.create(
                            model=model_engine,
                            messages=[{"role":"user", "content":text}],
                            temperature=0.2,
                        )
                        res = completion.choices[0].message.content
                        break
                    except Exception as e:
                        text = text[:max]
                        max = int(max * 0.9)
                return (max_attempts, res)

    def ask(self, prompt, code):
        #return "Err"
        # Set up the model and prompt
        #text = "What is the semantic meaning of this HTML page? " + text
        if "label" in prompt:
                key = "label " + code
        elif "Few words" in prompt:
                key = "func " + code
        elif "HTML element" in prompt:
                key = "element " + code
        elif "HTTP request" in prompt:
                key = "http " + code
        elif "sensitive" in prompt:
                key = "sensitive " + code
        elif "error" in prompt:
                key = "error" + code

        
        if key in self.chatgpt_cache:
            return self.chatgpt_cache[key]

        model_engine = "gpt-4o-mini-2024-07-18"

        max_attempts = 4  # You can adjust the number of retry attempts
        attempts, res = self.chat_with_retry(prompt, code, model_engine, max_attempts)

        if "ONLY TWO" in prompt  and max_attempts != attempts:
            second_part = prompt.split("HTML page.")[1]
            _ , res = self.chat_with_retry("Summarize all this possibile labels in JUST one label." + second_part, res, model_engine, 1)
        elif "sensitive" in prompt  and max_attempts != attempts:
            _ , summ = self.chat_with_retry("Summarize.", res, model_engine, 1)
            if "Yes" in res:
                res = "YES ----\n" + summ 
            else:
                res = "NO ----\n" + summ
            
        elif "Few words" in prompt:
            _ , res = self.chat_with_retry("Summarize.", res, model_engine, 1)
        '''
        
        completions = openai.Completion.create(
            engine='text-davinci-003',  # Determines the quality, speed, and cost.
            temperature=0.5,            # Level of creativity in the response
            prompt=text,           # What the user typed in           
            #max_tokens = 4097 - len(text), # Maximum tokens in the prompt AND response
            n=1,                        # The number of completions to generate
            stop=None,                  # An optional setting to control response generation
        )
        res = completions.choices[0].text.strip()
        '''
        self.chatgpt_cache[key] = res
        #time.sleep(20)
        with open(self._file, "w") as f:
            json.dump(self.chatgpt_cache, f)
        return res