import os
from jinja2 import Environment, FileSystemLoader


def load_prompt(file_path: str) -> str:
    """
    Load a prompt from a markdown file and render it using Jinja2.

    Args:
        file_path (str): The absolute path to the markdown file.

    Returns:
        str: The rendered content of the file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Prompt file not found: {file_path}")

    # Configure Jinja2 environment to load from the project root (assumed 3 levels up from this file)
    # This allows including files like 'src/common/prompts/rules.md'
    # src/common/utils.py -> src/common -> src -> root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../"))

    # Create environment with FileSystemLoader pointing to project root
    env = Environment(loader=FileSystemLoader(project_root))

    # Calculate the template path relative to the project root
    template_path = os.path.relpath(file_path, start=project_root)

    # Load and render the template
    template = env.get_template(template_path)
    return template.render()
