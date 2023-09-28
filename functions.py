import json
import subprocess
import os

class RunShellCommand:
    @staticmethod
    def info():
        return {
            "name": "run_shell_command",
            "description": "Run shell command",
            "parameters": {
                "type": "object",
                "properties": {
                    "shell_command": {
                        "type": "string",
                        "description": "Shell command to execute, e.g. ls, cd ..., cat ..., curl ..."
                },
                },
                "required": ["shell_command"]
            },
        }
    @staticmethod
    def run(args):
        args = json.loads(args)
        return subprocess.check_output(args["shell_command"], shell=True).decode()
