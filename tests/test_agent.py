import pytest
from agent.core import Agent
from agent.llm_provider import MockLLMProvider, create_llm_provider


def test_agent_response_parsing():
    agent = Agent(llm_provider=MockLLMProvider())

    raw_tool_call = (
        "Thought: I need to calculate the math problem.\n"
        "Action: calculator\n"
        'Action Input: {"expression": "25 * 4"}'
    )
    parsed = agent._parse_llm_response(raw_tool_call)

    assert parsed.is_final_answer is False
    assert parsed.tool_name == "calculator"
    assert parsed.tool_args == {"expression": "25 * 4"}
    assert "calculate the math" in parsed.thought


def test_agent_mock_execution():
    agent = Agent(llm_provider=MockLLMProvider())

    query = "Calculate 15 * 12 + 45"
    thoughts = []
    actions = []
    observations = []
    final_answers = []

    def on_thought(t): thoughts.append(t)
    def on_action(n, a): actions.append((n, a))
    def on_observation(o, s): observations.append((o, s))
    def on_final_answer(a): final_answers.append(a)

    result = agent.run(
        user_query=query,
        on_thought=on_thought,
        on_action=on_action,
        on_observation=on_observation,
        on_final_answer=on_final_answer
    )

    assert len(thoughts) > 0
    assert len(actions) > 0
    assert actions[0][0] == "calculator"
    assert len(observations) > 0
    assert observations[0][1] is True  # Success
