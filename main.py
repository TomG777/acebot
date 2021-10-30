import base64

import discord
import asyncio
import utils
import requests

client = discord.Client()
config = utils.load_config()
prefix = config.get("prefix", ";")
prefix_length = len(prefix)
commands = {}

engines = []


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


@cmd("start", "Start a stream", master=True)
async def command_run(message, arguments):
    title, url = arguments.split(None, 1)
    words = utils.get_words(arguments)
    if len(words) < 2:
        return "Missing arguments: <title> <url> [number] [bitrate]"

    command = utils.build_command(*words[:4])
    print(command)
    proc = await asyncio.create_subprocess_shell(
        command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE)
    proc.stdin.write(b'Hello\n')
    data = await proc.stdout.readline()
    print(data.decode().strip())
    data = {
        "proc": proc,
        "title": words[0],
        "url": words[1],
    }
    if len(words) >= 3:
        data["number"] = words[2]
    else:
        data["number"] = 1
    engines.append(data)
    return len(engines)


@cmd("stop", "Stop a running stream process", master=True)
async def command_stop(message, arguments):
    if arguments:
        number = utils.get_words(arguments)[0]
    else:
        number = 0
    data = engines[number]
    proc = data.get("proc")
    data = await proc.stdout.read()
    print(data.decode().strip())
    proc.terminate()
    return str(data)[:1950]


@cmd("read", "Read process output", master=True)
async def command_stop(message, arguments):
    if arguments:
        number = utils.get_words(arguments)[0]
    else:
        number = 0
    data = engines[int(number)]
    proc = data.get("proc")
    data = await proc.stdout.read()
    print(data.decode().strip())
    return str(data.decode())[:1950]


@cmd("count", "Get the count of streams", mod=True)
async def command_count(**_):
    return len(engines)


@cmd("get_id", "Get the content_id for a stream", mod=True)
async def get_id(message, arguments):
    if arguments:
        number = int(utils.get_words(arguments)[0])
    else:
        number = 0
    if number < len(engines):
        data = engines[int(number)]
        num = data["number"]
    else:
        num = number
    dir = config.get("publishdir", "/var/www/html/stream")
    file = dir + "/live" + str(num) + ".acelive"
    with open(file, "rb") as f:
        filedata = base64.b64encode(f.read())

    r = requests.post("http://api.torrentstream.net/upload/raw", data=filedata)
    print(r)
    return r.text


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


client.run(open("token").read().strip())
