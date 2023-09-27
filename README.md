# GPT Agent

## Disclaimer

> :warning: **This README was generated using ChatGPT**: The content of this document was generated through an AI model, and while every effort has been made to ensure accuracy, there may be some discrepancies or missing information. Please feel free to contribute or raise issues as necessary.

This repository contains a Python script that uses OpenAI's GPT model to generate responses to prompts. The script uses the Typer library to create a command-line interface (CLI) for interacting with the GPT model.

## Dependencies

The script requires the following Python libraries:

- `typer`
- `openai`
- `toml`
- `os`
- `dotenv`

## Usage

The script provides three commands:

1. `ask`: Send a prompt to a GPT agent.
2. `agents`: List available GPT agents.
3. `convo`: Have a back and forth conversation with a GPT agent.

### Ask Command

The `ask` command sends a prompt to a GPT agent and prints the agent's response. The command requires two arguments: the name of the agent and the prompt. The command also accepts an optional `agents` option that specifies the path to a TOML file containing the agent configurations.

```bash
python main.py ask <agent> <prompt> --agents <path_to_agents.toml>
```

### Agents Command

The `agents` command lists the names of the available GPT agents. The command accepts an optional `agents` option that specifies the path to a TOML file containing the agent configurations.

```bash
python main.py agents --agents <path_to_agents.toml>
```

### Convo Command

The `convo` command initiates a back and forth conversation with a GPT agent. The command requires two arguments: the name of the agent and the initial prompt. The command also accepts an optional `agents` option that specifies the path to a TOML file containing the agent configurations.

```bash
python main.py convo <agent> <prompt> --agents <path_to_agents.toml>
```

## Configuration

The script uses a TOML file to configure the GPT agents. Each agent is represented by a table in the TOML file. The table includes the following keys:

- `system_msg`: The initial system message.
- `model`: The name of the GPT model.
- `max_tokens`: The maximum number of tokens in the response.
- `temperature`: The temperature of the response.

The script also uses the `dotenv` library to load environment variables from a `.env` file. The script requires the `API_KEY` environment variable, which should be set to your OpenAI API key.

## License

This project is licensed under the terms of the MIT license.
