import json
import re
from typing import Dict, Any, Optional, Callable, List
from pydantic import BaseModel
from .tools.base import ToolRegistry, ToolResult
from .tools.calculator import CalculatorTool
from .tools.code_runner import PythonInterpreterTool
from .tools.file_system import ReadFileTool, WriteFileTool, ListDirTool, SearchFilesTool
from .tools.web_search import WebSearchTool
from .tools.system_info import SystemInfoTool, CurrentDateTimeTool
from .memory import ConversationMemory, PersistentLongTermMemory
from .llm_provider import BaseLLMProvider, create_llm_provider, LLMResponse


SYSTEM_PROMPT_TEMPLATE = """You are an Autonomous AI Agent written in Python.
You solve tasks step-by-step using reasoning (ReAct pattern) and tool invocation.

## Available Tools:
{tools_description}

## Response Format Guidelines:
You MUST respond using ONLY one of the two strict formats below:

Format 1 (When you need to use a tool):
Thought: <Detailed step-by-step reasoning explaining why you need the tool>
Action: <exact_tool_name>
Action Input: <Valid JSON string containing the tool parameters>

Format 2 (When you have the final answer for the user):
Thought: <Reasoning explaining how you derived the solution>
Final Answer: <Your complete, well-formatted response to the user>

## Important Rules:
1. Do NOT guess facts or values if a tool can retrieve or compute them for you.
2. Ensure 'Action Input' is valid JSON.
3. Only output ONE Action per turn. Wait for the Observation before continuing.
4. When you have enough context to answer the user request fully, output 'Final Answer:'.
"""


class AgentStepResult(BaseModel):
    step_number: int
    thought: str
    action_name: Optional[str] = None
    action_input: Dict[str, Any] = {}
    observation: Optional[str] = None
    final_answer: Optional[str] = None
    is_complete: bool = False


class Agent:
    """Core ReAct Agent implementation."""

    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        tool_registry: Optional[ToolRegistry] = None,
        max_steps: int = 10,
        memory_file: str = "agent_memory.json",
    ):
        self.llm_provider = llm_provider or create_llm_provider("auto")
        self.registry = tool_registry or self._create_default_registry()
        self.max_steps = max_steps
        self.memory = ConversationMemory()
        self.long_term_memory = PersistentLongTermMemory(memory_file)

    def _create_default_registry(self) -> ToolRegistry:
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        registry.register(PythonInterpreterTool())
        registry.register(ReadFileTool())
        registry.register(WriteFileTool())
        registry.register(ListDirTool())
        registry.register(SearchFilesTool())
        registry.register(WebSearchTool())
        registry.register(SystemInfoTool())
        registry.register(CurrentDateTimeTool())
        return registry

    def _parse_llm_response(self, text: str) -> LLMResponse:
        """Parses LLM response to extract Thought, Action, Action Input, or Final Answer."""
        # 1. Check for Final Answer
        final_answer_match = re.search(r'Final Answer:\s*(.*)', text, re.DOTALL | re.IGNORECASE)
        thought_match = re.search(r'Thought:\s*(.*?)(?=(Action:|Final Answer:|$))', text, re.DOTALL | re.IGNORECASE)
        thought_str = thought_match.group(1).strip() if thought_match else text.strip()

        if final_answer_match:
            final_text = final_answer_match.group(1).strip()
            return LLMResponse(
                content=text,
                thought=thought_str,
                is_final_answer=True,
                final_answer=final_text
            )

        # 2. Check for Action and Action Input
        action_match = re.search(r'Action:\s*([a-zA-Z0-9_\-]+)', text, re.IGNORECASE)
        input_match = re.search(r'Action Input:\s*(\{.*\}|"[^"]*"|.*)', text, re.DOTALL | re.IGNORECASE)

        if action_match:
            tool_name = action_match.group(1).strip()
            raw_input = input_match.group(1).strip() if input_match else "{}"
            
            # Clean JSON string if enclosed in markdown code fences
            if raw_input.startswith("```"):
                raw_input = re.sub(r'^```(?:json)?\n?', '', raw_input)
                raw_input = re.sub(r'\n?```$', '', raw_input).strip()

            try:
                tool_args = json.loads(raw_input) if raw_input.startswith("{") else {"input": raw_input}
            except json.JSONDecodeError:
                tool_args = {"raw_input": raw_input}

            return LLMResponse(
                content=text,
                thought=thought_str,
                tool_name=tool_name,
                tool_args=tool_args,
                is_final_answer=False
            )

        # Fallback if neither format matched strictly
        return LLMResponse(
            content=text,
            thought=thought_str,
            is_final_answer=True,
            final_answer=text
        )

    def run(
        self,
        user_query: str,
        on_thought: Optional[Callable[[str], None]] = None,
        on_action: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        on_observation: Optional[Callable[[str, bool], None]] = None,
        on_final_answer: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Executes the ReAct loop for a given user query."""
        self.memory.add_user_message(user_query)
        
        system_instruction = SYSTEM_PROMPT_TEMPLATE.format(
            tools_description=self.registry.get_prompt_description()
        )

        current_prompt = f"User Request: {user_query}\n\nBegin ReAct Reasoning:\n"
        
        step_history: List[AgentStepResult] = []

        for step in range(1, self.max_steps + 1):
            # 1. Generate LLM turn
            raw_response = self.llm_provider.generate(
                prompt=current_prompt,
                system_instruction=system_instruction
            )
            
            parsed = self._parse_llm_response(raw_response)

            if parsed.thought and on_thought:
                on_thought(parsed.thought)

            # 2. Check for Final Answer
            if parsed.is_final_answer and parsed.final_answer:
                if on_final_answer:
                    on_final_answer(parsed.final_answer)
                self.memory.add_assistant_message(parsed.final_answer)
                return parsed.final_answer

            # 3. Execute Tool Action
            if parsed.tool_name:
                if on_action:
                    on_action(parsed.tool_name, parsed.tool_args)

                tool_result: ToolResult = self.registry.execute(parsed.tool_name, parsed.tool_args)
                obs_text = str(tool_result)

                if on_observation:
                    on_observation(obs_text, tool_result.success)

                # Update conversation history with Action & Observation
                step_record = AgentStepResult(
                    step_number=step,
                    thought=parsed.thought or "",
                    action_name=parsed.tool_name,
                    action_input=parsed.tool_args,
                    observation=obs_text,
                    is_complete=False
                )
                step_history.append(step_record)

                current_prompt += (
                    f"Thought: {parsed.thought}\n"
                    f"Action: {parsed.tool_name}\n"
                    f"Action Input: {json.dumps(parsed.tool_args)}\n"
                    f"Observation: {obs_text}\n\n"
                    f"Next Step:\n"
                )

        fallback_msg = f"Reached maximum reasoning steps limit ({self.max_steps}) without completing task."
        if on_final_answer:
            on_final_answer(fallback_msg)
        return fallback_msg
