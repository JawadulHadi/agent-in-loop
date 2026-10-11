import argparse

from .agent import Agent
from .llm import OllamaLLM
from .tools import default_tools


def main() -> None:
    parser = argparse.ArgumentParser(description='Run the agent loop against a local Ollama model.')
    parser.add_argument('task')
    parser.add_argument('--model', default='llama3.2')
    parser.add_argument('--root', default='notes_demo')
    parser.add_argument('--log', default='run.jsonl')
    args = parser.parse_args()

    def confirm(name: str, tool_args: dict) -> bool:
        return input(f'Allow {name}({tool_args})? [y/N] ').strip().lower() == 'y'

    agent = Agent(OllamaLLM(args.model), default_tools(args.root),
                  confirm=confirm, log_path=args.log)
    result = agent.run(args.task)
    print(result.final or f'stopped: {result.stopped_reason}')
    print(f'steps={result.steps} tokens~{result.tokens_estimate}')


if __name__ == '__main__':
    main()
