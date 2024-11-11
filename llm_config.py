import tomllib

class LLMConfig:

    def __init__(self, filename):

        with open(filename, "rb") as f:
            config = tomllib.load(f)

        self.intro_and_consent = config["consent"]["intro_and_consent"].strip()

        self.questions_intro = config["questions"]["intro"]
        self.questions_prompt_template = self.generate_questions_prompt_template(config["questions"])
        self.questions_outro = "Great, I think I got all I need -- but let me double check!"

        self.extraction_task = f"Create a scenario based on these responses. {config['summaries']['language_type']}"
        self.extraction_prompt_template = self.generate_extraction_prompt_template(config["summaries"])
        self.summary_keys = list(config["summaries"]["questions"].keys())
        self.extraction_adaptation_prompt_template = self.generate_adaptation_prompt_template()

        self.personas = [persona.strip() for persona in list(config["summaries"]["personas"].values())]
        self.one_shot = self.generate_one_shot(config["example"])

        self.main_prompt_template = self.generate_main_prompt_template(config["summaries"]["questions"])


    def generate_questions_prompt_template(self, questions):

        questions_prompt = f"{questions['persona']}\n\nYour goal is to gather structured answers to the following questions.\n\n"

        n_general = len(questions["general"])
        if questions["general"]:
            questions_prompt += f"You start with {n_general} general question{'s' if n_general > 1 else ''}:\n"
            for count, question in enumerate(questions["general"]):
                questions_prompt += f"{count+1}. {question}\n"

        n_specific = len(questions["specific"])
        questions_prompt += f"\nYou proceed to ask the following {n_specific} questions about a specific experience they had:\n"
        for count, question in enumerate(questions["specific"]):
            questions_prompt += f"{n_general+count+1}. {question}\n"

        questions_prompt += f"\nAsk each question one at a time. {questions['language_type']} "\
            "Ensure you get at least a basic answer to each question before moving to the next. "\
            "Never answer for the human. "\
            "If you unsure what the human meant, ask again."

        n_total = n_general + n_specific
        questions_prompt += f'\n\nOnce you have collected answers to all {n_total} question{"" if n_total == 1 else "s"}, stop the conversation and write a single word "FINISHED".\n\n'\
            "Current conversation:\n{history}\nHuman: {input}\nAI:"

        return questions_prompt


    def generate_extraction_prompt_template(self, summaries):

        keys = list(summaries['questions'].keys())
        keys_string = f"`{keys[0]}`"
        for key in keys[1:-1]:
            keys_string += f", `{key}`"
        if len(keys_string):
            keys_string += f", and `{keys[-1]}`"

        extraction_prompt = "You are an expert extraction algorithm. " \
            "Only extract relevant information from the Human answers in the text. " \
            "Use only the words and phrases that the text contains. " \
            "If you do not know the value of an attribute asked to extract, return null for the attribute's value.\n\n" \
            f"You will output a JSON with {keys_string} keys.\n\n" \
            f"These correspond to the following question{'s' if len(keys) else ''}:\n"


        for count, question in enumerate(summaries["questions"].values()):
            extraction_prompt += f"{count+1}: {question}\n"


        extraction_prompt += "\nMessage to date: {conversation_history}\n\n" \
            "Remember, only extract text that is in the messages above and do not change it. "

        return extraction_prompt


    def generate_adaptation_prompt_template(self):

        prompt_adaptation = "You're a helpful assistant, helping students adapt a scenario to their liking. The original scenario this student came with:\n\n" \
            "Scenario: {scenario}.\n\n" \
            "Their current request is {input}.\n\n" \
            "Suggest an alternative version of the scenario. Keep the language and content as similar as possible, while fulfilling the student's request.\n\n" \
            "Return your answer as a JSON file with a single entry called 'new_scenario'."

        return prompt_adaptation


    def generate_one_shot(self, example):

        one_shot = f"Example:\n{example['conversation']}"
        one_shot += f"\nThe scenario based on these responses: \"{example['scenario'].strip()}\""

        return one_shot


    def generate_main_prompt_template(self, questions):

        main_prompt_template = "{persona}\n\n"
        main_prompt_template += "{one_shot}\n\n"
        main_prompt_template += "Your task:\nCreate a scenario based on the following answers:\n\n"

        for key, question in questions.items():
            main_prompt_template += f"Question: {question}\n"
            main_prompt_template += f"Answer: {{{key}}}\n"
        main_prompt_template += "\n{end_prompt}\n\nYour output should be a JSON file with a single entry called 'output_scenario'."

        return main_prompt_template
