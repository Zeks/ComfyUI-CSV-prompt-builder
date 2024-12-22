import os
import csv
import json
import random
from collections import defaultdict


class CSVConfigBase:
    _config_path = ""

    @classmethod
    def load_config(cls):
        if not cls._csv_filename:  # assuming this would be set elsewhere dynamically in subclass or init method.
            return
        elif os.path.isfile(cls._config_path):
            with open(cls._config_path, "r") as file:
                config = json.load(file)
                cls._csv_filename = config.get("csv_file", cls._csv_filename)

    @classmethod
    def save_config(cls):
        with open(cls._config_path, "w") as file:
            json.dump({"csv_file": cls._csv_filename}, file)

class BuildPromptBase(CSVConfigBase):
    cycle_indices = defaultdict(int)
    cached_categories = {}

    @classmethod
    def get_categories(cls, file_path):
        if file_path in cls.cached_categories:
            return cls.cached_categories[file_path]

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File '{file_path}' cannot be found. Please make sure the CSV file exists in the 'prompt_sets' folder and restart ComfyUI.")

        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension != ".csv":
            raise ValueError("Unsupported file type. Please provide a .csv file.")

        categories = defaultdict(list)
        with open(file_path, "r") as file:
            reader = csv.reader(file)
            headers = next(reader)  # Skip the first row containing category titles
            for row in reader:
                for i, value in enumerate(row):
                    categories[headers[i]].append(value.strip())

        if not all(categories.values()):
            raise ValueError("One or more categories in the CSV file are empty.")

        cls.cached_categories[file_path] = (categories, headers)
        return categories, headers

    @classmethod
    def INPUT_TYPES(cls):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        csv_directory = os.path.join(script_directory, "prompt_sets")

        file_path = os.path.join(csv_directory, cls._csv_filename)

        if not os.path.isfile(file_path):  # ...
            raise FileNotFoundError(f"File '{file_path}' cannot be found.")

        categories, headers = cls.get_categories(file_path)

        inputs = {
            "required": {
                "seed": ("INT", {"default": 42, "min": 0, "max": 2**32 - 1}),
            }
        }

        for i, header in enumerate(headers):
            category_options = ["None"] + categories[header]
            default_mode = "Fixed"
            if i == 0:
                default_mode = "Cycle"
            elif i == 1:
                default_mode = "Randomize"
            
            inputs["required"][f"{header}_mode"] = (["Fixed", "Randomize", "Follow", "Cycle"], {"default": default_mode})
            inputs["required"][f"{header}_val"] = (category_options, {"label": header})
            inputs["required"][f"{header}_weight"] = ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0, "step": 0.01, "precision": 2})
            if i < len(headers) - 1:
                next_header = headers[i + 1]
                inputs["required"][f"{header}_to_{next_header}"] = ("STRING", {"default": ", "})


        return inputs

    RETURN_TYPES = ("STRING",)
    FUNCTION = "build_prompt"

    CATEGORY = "Prompt Nodes"

    def build_prompt(self, seed, **kwargs):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        csv_directory = os.path.join(script_directory, "prompt_sets")

        random.seed(seed)
        file_path = os.path.join(csv_directory, self._csv_filename)

        categories, headers = self.get_categories(file_path)
        prompt_parts = []
        part1 = ""
        part2 = ""
        current_random = 0
        for i, header in enumerate(headers): 
            mode = kwargs.get(f"{header}_mode", "Fixed")
            weight = kwargs.get(f"{header}_weight", 1.0)
            choice = None
            parts = []
            if mode == "Randomize":
                current_random = random.randint(0, len(categories[header]))
                temp = categories[header][current_random]
                parts = [item.strip() for item in temp.split(',', 1)]
                if len(parts) == 2:
                    choice, part2 = parts
                else:
                    choice = parts[0]
                    part2 = None
            elif mode == "Follow":
                choice =categories[header][current_random]
            elif mode == "Cycle":
                if header not in self.cycle_indices:
                    selected_value = kwargs.get(f"{header}_val", "None")
                    start_index = categories[header].index(selected_value) if selected_value in categories[header] else 0
                    self.cycle_indices[header] = start_index
                choice = categories[header][self.cycle_indices[header]]
                self.cycle_indices[header] = (self.cycle_indices[header] + 1) % len(categories[header])
            else:
                choice = kwargs.get(f"{header}_val", "None")
                if choice == "None":
                    continue
                    
            if weight == 1.0:
                prompt_parts.append(choice)
            else:
                if len(parts) == 1:
                    prompt_parts.append(f"({choice}:{weight:.2f})")                    
                else:
                    prompt_parts.append(f"({choice}:{weight:.2f}), {part2}")                    

            if i < len(headers) - 1:
                next_header = headers[i + 1]
                separator = kwargs.get(f"{header}_to_{next_header}", ", ")
                prompt_parts.append(separator)

        combined_prompt = "".join(prompt_parts)
        return (combined_prompt,)
