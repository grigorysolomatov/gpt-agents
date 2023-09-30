#!/usr/bin/env python3

import typer
import openai
import toml
import os
import dotenv
import inspect
import importlib.util
import json

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
        agent: str     = typer.Argument(),
        prompt: str    = typer.Argument(),
        agents: str    = typer.Option(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "agents.toml")
        ),
        functions: str = typer.Option(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "functions.py")
        ),
):
    dotenv.load_dotenv()    
    openai.api_key = os.getenv("API_KEY")
    agent          = Agent(agent, toml.load(agents)[agent])
    functions      = get_classes_from_module(get_module_from_path(functions)) if functions else {}
    
    messages = [
        {"role" : "system", "content" : agent.get_system_msg()},
        {"role" : "user", "content" : prompt},
    ]

    while True:
        chat_args = dict(
            model       = agent.model,
            max_tokens  = agent.max_tokens,
            temperature = agent.temperature,
            messages    = messages,
        )

        if functions:
            chat_args["functions"] = [function.info() for function in functions.values()]
        
        response = openai.ChatCompletion.create(**chat_args)

        if response["choices"][0]["finish_reason"] != "function_call": break
        process_function_call(response, messages, functions)
        
    print(agent.process_response(response))

def process_function_call(response, messages, functions):
    message = response["choices"][0]["message"]
    messages.append(message)
    function = functions[message["function_call"]["name"]]
    print("content:\n{}".format(message["content"]))
    print("function_call:\n{}".format(message["function_call"]))
    if input("Allow? [y/n]: ") == "y":
        function_response = function.run(message["function_call"]["arguments"])
    else:
        function_response = "Not allowed to run this command"
        
    messages.append({
        "role": "function",
        "name": function.info()["name"],
        "content": function_response,
    })
    print("function_result:\n{}".format(function_response))

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
        functions: str = typer.Option(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "functions.py")
        ),
):
    dotenv.load_dotenv()
    openai.api_key = os.getenv("API_KEY")
    agent          = Agent(agent, toml.load(agents)[agent])
    functions      = get_classes_from_module(get_module_from_path(functions)) if functions else {}
   
    convo     = prompt_to_convo(prompt, length=length, sep=sep)
    gpt_convo = convo_to_gpt(convo, functions)

    #if gpt_convo[-1]["role"] == "function":
    #    print("\n".join([
    #        make_role_sep("function", length=length, sep=sep),
    #        gpt_convo[-1]["content"]            
    #    ]))
    #    return
    
    messages = [{"role" : "system", "content" : agent.get_system_msg()}] + gpt_convo

    chat_args = dict(
        model       = agent.model,
        max_tokens  = agent.max_tokens,
        temperature = agent.temperature,
        messages    = messages,
    )

    if functions:
        chat_args["functions"] = [function.info() for function in functions.values()]
    
    response = openai.ChatCompletion.create(**chat_args)
    message = response["choices"][0]["message"]
    out_convo = [{
        "role": agent.name,
        "content": message["content"] if message["content"] is not None else "",
    }]

    comming_role = "user"
    if response["choices"][0]["finish_reason"] == "function_call":
        out_convo += [{
            "role": "function_call",
            "content": str(message["function_call"]),
        }]
        comming_role = "function"

    returned = convo_to_prompt(out_convo, length=length, sep=sep)
                                
    print("\n".join([
        returned,
        make_role_sep(comming_role, length=length, sep=sep),
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

def convo_to_prompt(convo, length=80, sep="#"):
    return "\n".join(
        "\n".join([make_role_sep(part["role"], length=length, sep=sep), part["content"]])
        for part in convo
    )

def convo_to_gpt(convo, functions):    
    for agent, func_call, func in zip(convo[:-2], convo[1:-1], convo[2:]):
        if func_call["role"] != "function_call": continue
        agent["function_call"] = json.loads(func_call["content"])
        func["name"] = agent["function_call"]["name"]

    convo = [part for part in convo if part["role"] != "function_call"]
        
    for part in convo:
        part["role"] = part["role"] if part["role"] in ["user", "function"] else "assistant"
        
    return convo

@app.command(name="convofunc", help="Execute function in conversation")
def command_convofunc( 
        prompt: str    = typer.Argument(help = "Prompt to send to agent"),
        sep: str       = typer.Option("#", help = "Message separator symbol (one character)"),
        length: int    = typer.Option(80, help = "Separator length"),
        functions: str = typer.Option(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "functions.py")
        ),
):    
    convo = prompt_to_convo(prompt, length=length, sep=sep)
    
    if len(convo) <= 2:
        raise ValueError()

    if (convo[-2]["role"], convo[-1]["role"]) != ("function_call", "function"):
        raise ValueError()

    functions     = get_classes_from_module(get_module_from_path(functions)) if functions else {}    
    function_call = json.loads(convo[-2]["content"])
    function      = functions[function_call["name"]]

    print(function.run(function_call["arguments"]))        

def func_eval(convo):
    if len(convo) <= 2:
        raise ValueError()

    if (convo[-2]["role"], convo[-1]["role"]) != ("function_call", "function"):
        raise ValueError()
        
    func_call, user_allow = convo[-2:]
        
    func_call_content = json.loads(func_call["content"])
    function          = functions[func_call_content["name"]]        
    function_response = function.run(func_call_content["arguments"])    
        
    convo.append({
        "role": "function",
        "name": function.info()["name"],
        "content": function_response
    })

    return convo
    
# Helpers ######################################################################
def get_module_from_path(filepath):
    spec = importlib.util.spec_from_file_location("module.name", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def get_classes_from_module(module):
    return {member[1].info()["name"]: member[1] for member in inspect.getmembers(module)
            if inspect.isclass(member[1])
            and member[1].__module__ == module.__name__}
if __name__ == "__main__": app()
