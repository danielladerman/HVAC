from crewai_tools import BaseTool

class FileWriteTool(BaseTool):
    name: str = "File Write Tool"
    description: str = "Writes content to a specified file. Use this to save your work, like email drafts or reports."

    def _run(self, file_path: str, content: str) -> str:
        """
        Writes the given content to the specified file.
        """
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            return f"Successfully wrote content to {file_path}"
        except Exception as e:
            return f"Error writing to file: {e}"

# Instantiate the tool for use in our crew
file_write_tool = FileWriteTool() 