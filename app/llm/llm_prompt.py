from app.llm.prompts import SystemPrompt


class Prompts_LLM:
    """
    Prompt matching layer for LLM Models
    """

    def build_prompt(self, query: str, provider: str = "openai") -> list[dict]:
        if provider == "openai":
            messages = [
                {"role": "system", "content": SystemPrompt},
                {"role": "user", "content": query}
            ]
            return messages


prompts_llm = Prompts_LLM()
