import base64

import discord
import asyncio
import utils
import requests
import stream

client = discord.Client()
config = utils.load_config()
prefix = config.get("prefix", ";")
prefix_length = len(prefix)
commands = {}

engines = []
streams: list[stream.Stream] = []


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
                await message.channel.send(result[:1999])
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
    for argument, details in commands.items():
        if details["mod"] and not utils.check_mod(message.author):
            continue
        if details["admin"] and not utils.check_admin(message.author):
            continue
        if details["master"] and not utils.check_master(message.author):
            continue
        cmds.append(argument)

    return "`" + "`, `".join(cmds) + "`"


@cmd("stream", "Start a stream")
async def command_stream(message, arguments):
    flags, parameter, text = utils.argument_parser(arguments)
    text = utils.get_words(text)
    print(text)
    print(parameter)
    str = stream.Stream(*text, **parameter)
    streams.append(str)
    data = await str.start()
    return data


@cmd("read", "Read console output for stream")
async def command_read(message, arguments):
    if not arguments:
        number = 0
    else:
        number = int(arguments)

    instance = streams[number]
    return await instance.read()


@cmd("stop", "Stop a stream")
async def command_stop(message, arguments):
    if not arguments:
        number = 0
    else:
        number = int(arguments)

    instance = streams[number]
    return await instance.stop(True)


@cmd("get_id", "Get the content_id for a stream", mod=True)
async def get_id(message, arguments):
    if not arguments:
        number = 0
    else:
        number = int(arguments)

    instance: stream.Stream = streams[number]
    file = instance.file
    with open(file, "rb") as f:
        filedata = base64.b64encode(f.read())

    r = requests.post("http://api.torrentstream.net/upload/raw", data=filedata)
    print(r)
    return r.json().get("content_id")


client.run(open("token").read().strip())
