import sys
import argparse
from cli import run_cli_session
from agent.core import Agent
from agent.llm_provider import create_llm_provider
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown


def main():
    parser = argparse.ArgumentParser(description="Autonomous Python AI Agent CLI")
    parser.add_argument("--mock", action="store_true", help="Run agent in offline mock simulation mode")
    parser.add_argument("--query", "-q", type=str, help="Single query execution mode (non-interactive)")
    parser.add_argument("--model", type=str, default="gemini-2.5-flash", help="Gemini API model name")
    parser.add_argument("--max-steps", type=int, default=10, help="Maximum ReAct reasoning steps per turn")

    args = parser.parse_args()

    if args.query:
        console = Console()
        provider_type = "mock" if args.mock else "auto"
        llm = create_llm_provider(provider_type=provider_type, model=args.model)
        agent = Agent(llm_provider=llm, max_steps=args.max_steps)

        def on_thought(t): console.print(f"[cyan]Thought:[/cyan] {t}")
        def on_action(name, a): console.print(f"[yellow]Action:[/yellow] {name}({a})")
        def on_observation(o, s): console.print(f"[{'green' if s else 'red'}]Observation:[/{'green' if s else 'red'}] {o[:200]}")
        def on_final_answer(ans): console.print(Panel(Markdown(ans), title="Final Answer", border_style="magenta"))

        agent.run(
            user_query=args.query,
            on_thought=on_thought,
            on_action=on_action,
            on_observation=on_observation,
            on_final_answer=on_final_answer
        )
    else:
        run_cli_session(mock_mode=args.mock, model_name=args.model)


if __name__ == "__main__":
    main()
