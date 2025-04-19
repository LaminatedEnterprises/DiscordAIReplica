import time
import json
import os
import discord
import datasets

import lmstudio as lms

from colored import Fore, Style
from discord import app_commands

#enable console colours
os.system("")


#-----HELPER FUNCTIONS-----
def read_prompt() -> str:
    with open("base_prompt.txt", "r") as f:
        return f.read()
    
def read_token() -> str:
    with open("token.txt", "r") as f:
        return f.read()
    
def read_schema() -> dict:
    with open("response.schema.json", "r") as f:
        return json.loads(f.read())
    
def pretty(obj) -> str:
    return json.dumps(obj, indent=4)


class Bot(discord.Client):
    PROMPT = read_prompt()
    SCHEMA = read_schema()
    MANIFESTS = datasets.load_manifests()

    def __init__(self, model, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.chats: dict[int, lms.Chat] = dict()
        self.tree: app_commands.CommandTree = app_commands.CommandTree(self)

        self.model: lms.LLM = lms.llm(model)

        self.tree.add_command(
            app_commands.Command(
                name="begin-conversation", 
                description="Begins a conversation with the specified dataset",
                callback=self.begin_conversation
            )
        )
        self.tree.add_command(
            app_commands.Command(
                name="share-prompt", 
                description="Displays the model's template prompt",
                callback=self.share_prompt
            )
        )
        self.tree.add_command(
            app_commands.Command(
                name="share-schema", 
                description="Displays the model's response schema",
                callback=self.share_schema
            )
        )
        
    #-----EVENTS-----
    async def on_ready(self) -> None:
        print(f'Logged on as {self.user}!')
        await self.tree.sync()

    async def on_message(self, message) -> None:
        if message.author.bot:
            return
        
        if not message.channel.id in self.chats:
            return

        print(f"{Fore.green}Received: \"{message.content}\" from {message.author}{Style.reset}")
        chat = self.chats[message.channel.id]
        chat.add_user_message(str(message.content))

        result = json.loads(self.model.respond(chat, response_format=Bot.SCHEMA).content)
        print(f"{Fore.cyan}AI Response: {pretty(result)}{Style.reset}")
        await message.channel.send(result["body"])


    #-----COMMANDS-----
    async def share_prompt(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"Prompt: ```\n{Bot.PROMPT}```")
    
    async def share_schema(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"Prompt: ```json\n{pretty(Bot.SCHEMA)}```")

    async def begin_conversation(self, interaction: discord.Interaction, dataset_name: str) -> None:
        escaped_name = dataset_name.replace("\\", "\\\\").replace("`", "\\`")
        if dataset_name in Bot.MANIFESTS:
            await interaction.response.send_message(f"Beginning conversation with `{escaped_name}`")
            self.chats[interaction.channel_id] = self.create_chat(Bot.MANIFESTS[dataset_name])
        else:
            await interaction.response.send_message(f"No dataset found under `{escaped_name}`")


    #-----HELPER METHODS-----
    def create_chat(self, manifest: datasets.Manifest) -> lms.Chat:
        chat = lms.Chat(Bot.prepare_prompt(manifest))
        return chat
    
    @staticmethod
    def prepare_prompt(manifest: datasets.Manifest) -> str:
        prompt = Bot.PROMPT + "\n\n"
        reminder = "\n\nREMINDER: YOU ARE TO EMULATE THIS SPEECH, PRETENDING TO BE {USER_NAME}:\n"
        text_length = len(prompt)

        for i, message in enumerate(manifest.load_messages()):
            #prompt += f"\"{message}\"\n"
            text_length += len(message)

            #count on the latter end of the message groups so the reminder doesn't appear at the start
            if i % 200 == 199: 
                #prompt += reminder
                text_length += len(reminder)

            if text_length > 500:
                break

        prompt += "YOU HAVE BEEN CONNECTED. HERE IS THE FIRST MESSAGE THAT YOU CAN SEE:\n"
        return prompt.replace("{USER_NAME}", manifest.username)


if __name__ == "__main__":
    print(f"{Fore.green}Enforcing prompt: \n{Bot.PROMPT}{Style.reset}")
    print(f"{Fore.yellow}\nEnforcing schema: {pretty(Bot.SCHEMA)}{Style.reset}")
    for manifest_name, _ in Bot.MANIFESTS.items():
        print(f"Found manifest for: {manifest_name}")
    TOKEN = read_token()

    intents = discord.Intents.default()
    intents.message_content = True

    client = Bot("deepseek-r1-distill-llama-8b", intents=intents)
    client.run(TOKEN)