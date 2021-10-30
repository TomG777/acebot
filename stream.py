import utils
import asyncio

config = utils.load_config()


class Stream:
    proc = None

    def __init__(self, title, url, number=1, bitrate=600000, peers=100, slots=100):
        self.title = title
        self.url = url
        self.number = number
        self.bitrate = bitrate
        self.peers = peers
        self.slots = slots

        self.dir = config.get("publishdir", "/var/www/html/stream")
        self.cachedir = self.dir + "/" + config.get("cachedir", "cache")
        self.file = self.dir + "/live" + str(self.number) + ".acelive"

        self.remoteaccess = config.get("remoteaccess", False)
        if config.get("remotetoken", False):
            self.token = config.get("remotetoken")
        else:
            import random
            import string
            self.token = str([random.choice(string.ascii_letters) for _ in range(16)])

        self.command = self.build_command()
        print(self.command)

    def build_command(self):
        command_parts = []
        command_parts.append(config.get("engine", "/opt/acestream/acestreamengine"))
        command_parts.append("--stream-source")
        command_parts.append("--title '" + self.title + "'")
        command_parts.append("--source '" + self.url + "'")
        command_parts.append("--name live" + str(self.number))
        command_parts.append("--port " + str(int(config.get("portstart", 888)) + int(self.number)))
        command_parts.append("--host " + utils.get_ip())
        command_parts.append("--publish-dir '" + self.dir + "'")
        command_parts.append(
            "--cache-dir '" + self.cachedir + "'")
        if self.bitrate:
            command_parts.append("--bitrate " + str(self.bitrate))
        else:
            command_parts.append("--bitrate " + str(config.get("bitrate", 600000)))
        command_parts.append("--quality 'HD'")
        command_parts.append("--category " + config.get("category"))
        command_parts.append("--max-upload-slots " + str(self.slots))
        command_parts.append("--max-peers " + str(self.peers))

        for tracker in config.get("trackers", []):
            command_parts.append("--tracker " + tracker)
        if config.get("permanent", True):
            command_parts.append("--permanent")
        if self.remoteaccess:
            command_parts.append("--service-remote-access")
            command_parts.append("--service-access-token " + self.token)

        return " ".join(command_parts)

    async def start(self):
        self.proc = await asyncio.create_subprocess_shell(
            self.command,
            # stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE)

        data = await self.proc.stdout.readline()
        print(data.decode().strip())

    async def read(self, n=1990, channel=None):
        data = await self.proc.stdout.read(n=n)
        data = data.decode().strip()
        print(data)
        if channel:
            await channel.send(data)
        else:
            return data

    async def stop(self, clear):
        if clear:
            data = await self.proc.stdout.read(1990)
            data = data.decode().strip()
            print(data)
        try:
            self.proc.terminate()
        except ProcessLookupError:
            return "Process already stopped"
        if clear:
            return data

    def __del__(self):
        if self.proc:
            try:
                self.proc.terminate()
            except ProcessLookupError:
                pass
