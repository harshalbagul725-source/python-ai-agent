import sys
import os
import json
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text
from rich.table import Table
from agent.core import Agent
from agent.llm_provider import create_llm_provider


console = Console()


def print_banner():
    banner_text = """
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║                🤖 AUTONOMOUS PYTHON AI AGENT 🤖                  ║
    ║               Built with ReAct Reasoning & Tools                 ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner_text, style="bold cyan", expand=False))
    console.print(
        "[bold green]Commands:[/bold green] Type [yellow]/help[/yellow] for commands, [yellow]/tools[/yellow] to list tools, [yellow]/exit[/yellow] to quit.\n"
    )


def display_tools(agent: Agent):
    table = Table(title="🛠️ Registered Agent Tools", style="blue")
    table.add_column("Tool Name", style="bold yellow", no_wrap=True)
    table.add_column("Description", style="white")

    for tool_instance in agent.registry.list_tools():
        table.add_row(tool_instance.name, tool_instance.description)

    console.print(table)


def run_cli_session(mock_mode: bool = False, model_name: str = "gemini-2.5-flash"):
    print_banner()

    provider_type = "mock" if mock_mode else "auto"
    llm = create_llm_provider(provider_type=provider_type, model=model_name)
    agent = Agent(llm_provider=llm)

    mode_status = "[bold yellow]OFFLINE MOCK SIMULATION MODE[/bold yellow]" if mock_mode or provider_type == "mock" else f"[bold green]LIVE API MODE ({model_name})[/bold green]"
    console.print(f"Status: {mode_status}\n")

    def on_thought(thought_text: str):
        console.print(Panel(
            thought_text,
            title="🧠 Thought / Reasoning",
            title_align="left",
            border_style="cyan",
            expand=False
        ))

    def on_action(tool_name: str, tool_args: dict):
        args_json = json.dumps(tool_args, indent=2)
        syntax = Syntax(args_json, "json", theme="monokai", line_numbers=False)
        console.print(Panel(
            syntax,
            title=f"🛠️ Action: [bold yellow]{tool_name}[/bold yellow]",
            title_align="left",
            border_style="yellow",
            expand=False
        ))

    def on_observation(obs_text: str, success: bool):
        border = "green" if success else "red"
        status_label = "✅ Observation" if success else "❌ Error Observation"
        console.print(Panel(
            obs_text,
            title=f"{status_label}",
            title_align="left",
            border_style=border,
            expand=False
        ))

    def on_final_answer(answer_text: str):
        md = Markdown(answer_text)
        console.print(Panel(
            md,
            title="🎯 Final Answer",
            title_align="left",
            border_style="bold magenta",
            expand=False
        ))

    while True:
        try:
            user_input = console.input("\n[bold green]User ❯ [/bold green]").strip()
            if not user_input:
                continue

            if user_input.lower() in ["/exit", "/quit", "exit", "quit"]:
                console.print("[bold red]Exiting Python AI Agent. Goodbye![/bold red]")
                break

            if user_input.lower() == "/help":
                console.print(
                    "[bold yellow]Available Commands:[/bold yellow]\n"
                    "  [cyan]/tools[/cyan]   - List all available tools\n"
                    "  [cyan]/memory[/cyan]  - View persistent long-term memory\n"
                    "  [cyan]/clear[/cyan]   - Clear conversation history\n"
                    "  [cyan]/exit[/cyan]    - Exit agent CLI\n"
                )
                continue

            if user_input.lower() == "/tools":
                display_tools(agent)
                continue

            if user_input.lower() == "/memory":
                mem_data = agent.long_term_memory.list_all()
                console.print(Panel(json.dumps(mem_data, indent=2), title="💾 Long-term Memory Store", border_style="blue"))
                continue

            if user_input.lower() == "/clear":
                agent.memory.clear()
                console.print("[green]Conversation history cleared.[/green]")
                continue

            # Execute agent query
            agent.run(
                user_query=user_input,
                on_thought=on_thought,
                on_action=on_action,
                on_observation=on_observation,
                on_final_answer=on_final_answer
            )

        except KeyboardInterrupt:
            console.print("\n[bold red]Interrupted by user. Exiting...[/bold red]")
            break
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")


if __name__ == "__main__":
    mock = "--mock" in sys.argv
    run_cli_session(mock_mode=mock)
