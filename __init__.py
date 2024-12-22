import os

from .build_prompt_from_csv import BuildPromptBase

def gen_classes_from_csv():
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}

    script_directory = os.path.dirname(os.path.abspath(__file__))
    csv_directory = os.path.join(script_directory, "prompt_sets")

    for filename in os.listdir(csv_directory):
        if not filename.lower().endswith('.csv'):
            continue

        file_path = os.path.join(csv_directory, filename)

        class GeneratedPrompt(BuildPromptBase):

            _config_path = f"{os.path.dirname(file_path)}/{filename.split('.')[0]}_config.json"
            _csv_filename = filename

            @classmethod
            def CLASS(cls):
                cls.load_config()

            CATEGORY = f"Prompt Nodes/{os.path.splitext(filename)[0]}"

        unique_class_name = f"BuildPromptFrom_{filename.replace('.csv', '')}"
        globals()[unique_class_name] = GeneratedPrompt

        NODE_CLASS_MAPPINGS[unique_class_name] = GeneratedPrompt
        NODE_DISPLAY_NAME_MAPPINGS[GeneratedPrompt.CATEGORY] = os.path.splitext(filename)[0]

    return NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS


NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS = gen_classes_from_csv()

__all__ = NODE_CLASS_MAPPINGS
