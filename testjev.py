import asyncio
import sys
sys.path.insert(0, "bot")
from jev_vetting import vet_message

samples = [
    # clean
    ("Ahh I see, I didn't know. I'm learning a lot", "clean"),
    ("lol", "clean"),
    ("Death counter", "clean"),
    # sexual
    ("i wanna shave so i can get some thigh pics", "sexual"),
    ("I prefer hentai", "sexual"),
    ("play femboy waifu goon simulater 69", "sexual"),
    # political
    ("Joe biden just pulled out his life from the presidential election", "political"),
    ("!btw is donald trump a femboy?", "political"),
    ("ur both banned for politics", "political"),
    # edge
    ("Does that make me a furry or a horny?", "edge"),
]

async def main():
    for msg, label in samples:
        print(msg, " | ", label)
        print(await vet_message(msg))
        print("----------")

asyncio.run(main())