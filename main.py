import discord
import asyncio
import utils
import sys

client = discord.Client()
config = utils.load_config()
prefix = config.get("prefix", ";")
prefix_length = len(prefix)
commands = {}
proc = None


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
        print("Running command: ", argument, " By ", message.author)
        result = await command["fn"](message, arguments)
        if result is not None:
            if type(result) is str:
                await message.channel.send(result)
            elif type(result) is discord.Embed:
                await message.channel.send(embed=result)
            else:
                await message.channel.send(type(result))
                await message.channel.send(repr(result))


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


@cmd("run", "Run a specific command on the host OS", master=True)
async def command_run(message, arguments):
    global proc
    proc = await asyncio.create_subprocess_shell(
        arguments,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE)
    proc.stdin.write(b'Hello\n')
    data = await proc.stdout.readline()
    print(data.decode().strip())


@cmd("eval", "Evaluate custom python code", master=True)
async def command_eval(message, arguments):
    result = eval(arguments)
    return result


@cmd("print", "Print process output", master=True)
async def command_print(message, arguments):
    global proc
    data = await proc.stdout.readline()
    print(data.decode().strip())
    return data

@cmd("read", "Read process output", master=True)
async def command_read(message, arguments):
    global proc
    data = await proc.stdout.read()
    print(data.decode().strip())
    return data


@cmd("stop", "Terminate running process", master=True)
async def command_stop(message, arguments):
    global proc
    proc.terminate()


client.run(open("token").read().strip())
