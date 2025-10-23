from asyncio import StreamWriter

class NetworkComponent:
    def __init__(self, writer: StreamWriter, username: str):
        self.writer = writer
        self.username = username

    def __repr__(self):
        return f"Net(username={self.username})"