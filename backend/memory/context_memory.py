class ContextMemory:

    def __init__(self):

        self.buffer = []

    def add(
        self,
        item
    ):

        self.buffer.append(item)

    def latest(
        self,
        limit=10
    ):

        return self.buffer[-limit:]

    def build_context(self):

        return "\n".join(
            str(x)
            for x in self.latest()
        )
