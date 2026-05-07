class Executor:

    async def execute(
        self,
        action
    ):

        return {
            "action": action,
            "status": "completed"
        }
