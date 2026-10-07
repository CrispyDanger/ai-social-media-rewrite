from pydantic import Agent


class AgentInit():

    def __init__(self, model):
        self.model = model


    def get_agent(self):
