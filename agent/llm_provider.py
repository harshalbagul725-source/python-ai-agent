import os
import json
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class LLMResponse(BaseModel):
    content: str
    thought: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Dict[str, Any] = {}
    is_final_answer: bool = False
    final_answer: Optional[str] = None


class BaseLLMProvider:
    """Interface for LLM Providers."""

    def generate(self, prompt: str, system_instruction: str = "") -> str:
        raise NotImplementedError()


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini API Provider using google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.model = model
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[Warning] Failed to initialize google-genai client: {e}")

    def generate(self, prompt: str, system_instruction: str = "") -> str:
        if not self.client:
            raise RuntimeError("Gemini API key not configured. Set GEMINI_API_KEY environment variable or pass api_key.")

        try:
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"System Instruction:\n{system_instruction}\n\n{prompt}"
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt,
            )
            return response.text or ""
        except Exception as e:
            raise RuntimeError(f"Gemini API generation error: {e}")


class MockLLMProvider(BaseLLMProvider):
    """
    Intelligent Mock Provider for offline / demo mode.
    Simulates reasoning, tool execution decisions, and responses.
    """

    def generate(self, prompt: str, system_instruction: str = "") -> str:
        # If observation is present, complete turn with Final Answer
        obs_match = re.search(r'Observation:\s*(.*)', prompt, re.DOTALL)
        if obs_match:
            obs = obs_match.group(1).strip().split('\n')[0]
            return f"Thought: Based on the observation '{obs}', I now have the final answer.\nFinal Answer: The calculated result is {obs}."

        prompt_lower = prompt.lower()
        
        # 1. Math calculation request
        if any(op in prompt_lower for op in ["calculate", "math", "sqrt", "add", "multiply", "*", "+", "^", "pow"]):
            math_match = re.search(r'(\d+[\d\s\+\-\*\/\(\)\^]*\d+)', prompt)
            expr = math_match.group(1).strip() if math_match else "15 * 12 + 45"
            return (
                f"Thought: The user requested a mathematical computation. I will use the calculator tool to evaluate '{expr}'.\n"
                f"Action: calculator\n"
                f'Action Input: {{"expression": "{expr}"}}'
            )

        # 2. System info / time request
        if "time" in prompt_lower or "date" in prompt_lower:
            return (
                "Thought: The user is asking for current date and time information. I will call the current_date_time tool.\n"
                "Action: current_date_time\n"
                'Action Input: {}'
            )
        
        if "system" in prompt_lower or "os" in prompt_lower or "python version" in prompt_lower:
            return (
                "Thought: The user wants to check host system details. I will use the system_info tool.\n"
                "Action: system_info\n"
                'Action Input: {}'
            )

        # 3. File list / read / search
        if "list file" in prompt_lower or "list dir" in prompt_lower or "files in" in prompt_lower:
            return (
                "Thought: The user wants to inspect directory files. I will call list_dir tool.\n"
                "Action: list_dir\n"
                'Action Input: {"dir_path": "."}'
            )

        # 4. Search request
        if "search" in prompt_lower or "who is" in prompt_lower or "what is" in prompt_lower:
            return (
                f"Thought: The user is inquiring about information. I will search the web using web_search tool.\n"
                f"Action: web_search\n"
                f'Action Input: {{"query": "{prompt[:40]}"}}'
            )

        # 5. Default direct answer
        return (
            f"Thought: I have sufficient context to address the user request directly.\n"
            f"Final Answer: Hello! I am your Autonomous Python AI Agent. I am operational and ready to assist you with tool execution, calculations, file management, and problem solving."
        )


def create_llm_provider(provider_type: str = "auto", api_key: Optional[str] = None, model: str = "gemini-2.5-flash") -> BaseLLMProvider:
    """Factory to create LLM Provider instance based on environment or user request."""
    if provider_type == "mock":
        return MockLLMProvider()
    
    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key and provider_type in ("auto", "gemini"):
        try:
            return GeminiLLMProvider(api_key=key, model=model)
        except Exception as e:
            print(f"[Notice] Could not initialize Gemini provider ({e}), falling back to Mock provider.")
            return MockLLMProvider()
    
    return MockLLMProvider()
