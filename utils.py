import json
import discord


def load_config():
    try:
        with open("config.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("No config file is present. consider copying the default example config")
        return {}


config = load_config()


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
