class BatchBuilder:
    def __init__(self):
        self.commands = []

    def add_command(self, cmd: str):
        self.commands.append(cmd.strip())
        return self

    def build(self):
        return "\n".join(self.commands) + "\nexit\n"

