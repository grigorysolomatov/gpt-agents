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
        try:
            return subprocess.run(args["shell_command"], capture_output=True, text=True, check=True, shell=True).stdout
        except subprocess.CalledProcessError as e:
            return e.stderr
        #try:            
        #    return subprocess.check_output(args["shell_command"], shell=True).decode()
        #except subprocess.CalledProcessError as e:
        #    return str(e)
        #except Exception as e:
        #    return str(e)
