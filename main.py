import discord
import asyncio
import utils

client = discord.Client()
config = utils.load_config()
prefix = config.get("prefix", ";")
prefix_length = len(prefix)
commands = {}


def cmd(name, help="", mod=False, admin=False, master=False):
    def _(fn):
        commands[name] = {
            "name": name,
            "fn": fn,
            "help": help,
            "mod": mod,
            "admin": admin,
            "master": master
        }
        return fn

    return _


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


async def get_stream(message):
    channel = message.channel
    m = await channel.send("Which stream do you want?")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not message.content.startswith(prefix):
        return
    content = message.content[prefix_length:]
    if " " in content:
        call, arguments = content.split(" ", 1)
    else:
        call = content
        arguments = ""
    for argument, command in commands.items():
        if argument != call:
            continue
        if command["mod"] and not utils.check_mod(message.author):
            continue
        if command["admin"] and not utils.check_admin(message.author):
            continue
        if command["master"] and not utils.check_master(message.author):
            continue
        result = await command["fn"](message, arguments)
        if result is not None:
            if type(result) is str:
                await message.channel.send(result)
            elif type(result) is discord.Embed:
                await message.channel.send(embed=result)


@cmd("help", "Get this help message")
async def command_help(message, arguments):
    start = "```"
    end = "```"
    result = ""
    for command, details in commands.items():
        if details["mod"] and not utils.check_mod(message.author):
            continue
        if details["admin"] and not utils.check_admin(message.author):
            continue
        if details["master"] and not utils.check_master(message.author):
            continue
        result += command
        if details["help"]:
            result += ": " + details["help"] + "\n"
        else:
            result += "\n"
    return start + result + end


@cmd("commands", "Get a list of commands")
async def command_commands(message, arguments):
    cmds = []
    for argument, command in commands.items():
        if details["mod"] and not utils.check_mod(message.author):
            continue
        if details["admin"] and not utils.check_admin(message.author):
            continue
        if details["master"] and not utils.check_master(message.author):
            continue
        cmds.append(argument)

    return "`" + "`, `".join(cmds) + "`"


client.run(open("token").read().strip())
