#!/usr/bin/env python3

import typer
import openai
import toml
import os
import dotenv

app = typer.Typer()

class Agent:
    def __init__(self, name, config):
        self.name = name
        
        self.system_msg  = config["system_msg"]
        self.model       = config["model"]
        self.max_tokens  = config["max_tokens"]
        self.temperature = config["temperature"]

    def get_system_msg(self):
        return self.system_msg

    def process_response(self, response):
        return response["choices"][0]["message"]["content"]

@app.command(name="ask", help="Send prompt to a gpt agent")
def command_ask(
        agent: str   = typer.Argument(),
        prompt: str  = typer.Argument(),
        agents: str  = typer.Option(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "agents.toml")
        ),
):
    dotenv.load_dotenv()
    openai.api_key = os.getenv("API_KEY")
    agent          = Agent(agent, toml.load(agents)[agent])
    
    response = openai.ChatCompletion.create(
        model       = agent.model,
        max_tokens  = agent.max_tokens,
        temperature = agent.temperature,
        messages    = [
            {"role" : "system", "content" : agent.get_system_msg()},
            {"role" : "user", "content" : prompt},
        ],
        
    )
    print(agent.process_response(response))

@app.command(name="agents", help="List available GPT agents")
def command_agents(
        agents: str  = typer.Option(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "agents.toml")
        ),
):
    print(" ".join(agent for agent in sorted(toml.load(agents))))

@app.command(name="convo", help="Have a back and forth converstaion")
def command_convo(
        agent: str  = typer.Argument(help = "GPT agent to use"),
        prompt: str = typer.Argument(help = "Prompt to send to agent"),
        sep: str    = typer.Option("#", help = "Message separator symbol (one character)"),
        length: int = typer.Option(80, help = "Separator length"),
        agents: str = typer.Option(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "agents.toml"),
            help = "Path to agents file (toml format)",
        ),        
):
    dotenv.load_dotenv()
    openai.api_key = os.getenv("API_KEY")
    agent          = Agent(agent, toml.load(agents)[agent])
   
    convo     = prompt_to_convo(prompt, length=length, sep=sep)
    gpt_convo = convo_to_gpt(convo)
    
    response = openai.ChatCompletion.create(
        model       = agent.model,
        max_tokens  = agent.max_tokens,
        temperature = agent.temperature,
        messages    = [{"role" : "system", "content" : agent.get_system_msg()}] + gpt_convo,
    )
    returned = convo_to_prompt([{
        "role": agent.name,
        "content": agent.process_response(response),
    }], length=length, sep=sep)
    print("\n".join([
        returned,
        make_role_sep("user", length=length, sep=sep),
    ]))

def get_sep_role(line, length=80, sep="#"):
    if len(line) != length:
        return

    parts = line.split()
    if len(parts) != 3:
        return

    if (parts[0], set(parts[2])) != (sep, {sep}):
        return
    
    return parts[1]

def make_role_sep(role, length=80, sep="#"):
    start = f"{sep} {role} "
    end = sep*(length - len(start))
    return start + end

def prompt_to_convo(prompt, length=80, sep="#"):
    lines = prompt.split("\n")
    if get_sep_role(lines[0], length=length, sep=sep) is None:
        lines.insert(0, make_role_sep("user", length=length, sep=sep))
    
    convo = []    
    for i, line in enumerate(lines):
        role = get_sep_role(line, length=length, sep=sep)
        if role is not None:
            convo.append({
                "role": role,
                "content": "",
            })
        else:
            convo[-1]["content"] += f"{line}" + ("\n" if i < len(lines)-1 else "")
            
    return convo

def convo_to_gpt(convo):
    return [
        {
            "role": "assistant" if part["role"] != "user" else "user",
            "content": part["content"],
        }
        for part in convo
    ]

def convo_to_prompt(convo, length=80, sep="#"):
    return "\n".join(
        "\n".join([make_role_sep(part["role"], length=length, sep=sep), part["content"]])
        for part in convo
    )

if __name__ == "__main__": app()
