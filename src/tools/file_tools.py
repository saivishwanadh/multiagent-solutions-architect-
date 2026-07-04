import os
from datetime import datetime

def save_document(content: str, filename: str = None) -> str:
    """
    Saves the provided text content to a Markdown file in the outputs/ directory.
    Returns the absolute path to the saved file.
    """
    # Create outputs directory if it doesn't exist
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    outputs_dir = os.path.join(base_dir, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)
    
    # Generate a unique filename if none is provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"project_proposal_{timestamp}.md"
        
    # Ensure it ends with .md
    if not filename.endswith(".md"):
        filename += ".md"
        
    filepath = os.path.join(outputs_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"\n[File Tool] Successfully saved document to: {filepath}")
    return filepath
