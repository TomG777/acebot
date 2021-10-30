import json
import discord
from more_itertools import peekable


def load_config():
    try:
        with open("config.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("No config file is present. consider copying the default example config")
        return {}


config = load_config()


def get_word(iterator: iter, multi=False):
    word = []
    letter = next(iterator)
    if multi and letter == '"':
        for letter in iterator:
            if letter == "\\":
                if iterator.peek(False) is False:
                    return "".join(word)
                next_letter = next(iterator)
                if next_letter == '"':
                    word.append(next_letter)
                else:
                    word.append(letter + next_letter)
            if letter == '"':
                return "".join(word)
            word += letter
        return "".join(word)
    word.append(letter)
    for letter in iterator:
        if letter == " " or letter == "\n":
            return "".join(word)
        word.append(letter)
    return "".join(word)


def get_words(text: str):
    words = []
    if text == "":
        return []
    iterator = peekable(text)
    while iterator.peek(False) is not False:
        while iterator.peek() in [" ", "\n"]:
            next(iterator)
        words.append(get_word(iterator, True))
    return words


def argument_parser(text: str):
    if text == "":
        return [], {}, ""
    flags = []
    parameters = {}
    iterator = peekable(text)
    text = ""

    while iterator.peek(False) is not False:
        word = []
        next_letter = iterator.peek()
        if next_letter == "-":
            _ = next(iterator)
            next_letter = iterator.peek(None)
            if next_letter is None:
                text += "-"
                break
            if next_letter == "-":
                _ = next(iterator)  # Get rid if the character
                if iterator.peek(False) is not False:
                    parm = get_word(iterator)
                    if iterator.peek(False) is not False:
                        value = get_word(iterator, True)
                    else:
                        value = None
                    parameters[parm] = value
                else:
                    text += "--"
                    break
            else:
                flag = get_word(iterator)
                flags.append(flag)

        else:
            text += "".join([l for l in iterator])
            break

    return flags, parameters, text


def get_ip():
    ip = config.get("hostip")
    if ip:
        return ip
    import requests
    return requests.get("http://ipecho.net/plain").text


def build_command(title, url, number=1, bitrate=600000):
    #  --live-cache-type memory
    command_parts = []
    command_parts.append(config.get("engine", "/opt/acestream/acestreamengine"))
    command_parts.append("--stream-source")
    command_parts.append("--title '" + title + "'")
    command_parts.append("--source '" + url + "'")
    command_parts.append("--name live" + str(number))
    command_parts.append("--port " + str(int(config.get("portstart", 888)) + int(number)))
    command_parts.append("--host " + get_ip())
    command_parts.append("--publish-dir '" + config.get("publishdir", "/var/www/html/stream") + "'")
    command_parts.append(
        "--cache-dir '" + config.get("publishdir", "/var/www/html/stream") + "/" + config.get("cachedir",
                                                                                              "cache") + "'")
    command_parts.append("--bitrate " + str(config.get("bitrate", bitrate)))
    command_parts.append("--quality 'HD'")
    command_parts.append("--category " + config.get("category"))
    command_parts.append("--max-upload-slots " + str(config.get("maxslots", 100)))
    command_parts.append("--max-peers " + str(config.get("maxpeers", 100)))

    for tracker in config.get("trackers", []):
        command_parts.append("--tracker " + tracker)
    if config.get("permanent", True):
        command_parts.append("--permanent")
    if config.get("remoteaccess", False):
        if config.get("remotetoken", False):
            command_parts.append("--service-remote-access")
            command_parts.append("--service-access-token " + config.get("remotetoken"))
        else:
            import random
            import string
            token = [random.choice(string.ascii_letters) for _ in range(16)]
            print("Random access token: " + token)
            command_parts.append("--service-remote-access")
            command_parts.append("--service-access-token " + token)

    return " ".join(command_parts)


def check_mod(user: discord.User):
    if user.id in config.get("mod.ids", []):
        return True
    elif user.id in config.get("mod.roles", []):
        return True
    return check_admin(user)


def check_admin(user: discord.User):
    if user.id in config.get("admin.ids", []):
        return True
    elif user.id in config.get("admin.roles", []):
        return True
    return check_master(user)


def check_master(user: discord.User):
    if user.id in config.get("master.ids", []):
        return True
    elif user.id in config.get("master.roles", []):
        return True
    return False
