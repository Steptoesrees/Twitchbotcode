from typesafe_sdk import Noul, TypeSafeClient
import asyncio

from config import TYPESAFE_KEY

async def vet_message(text: str) -> dict[str, float]:

    messagestate = text


    with TypeSafeClient(model="jev-latest", api_key=TYPESAFE_KEY) as client:
        response = client.system_one(
            state=messagestate,
            questions={
                        "sexual": Noul(
                            instructions= "Is this chat message excessively sexual or sexually explicit?"
                                            "Answer yes only for messages that are sexual, erotic, talk about sexual organs, "
                                            "or describe sexual acts. Answer no for flirtatious banter, "
                                            "mild innuendo, or non-sexual content.",
                            criteria={
                                "true": "sexual, erotic, or describes sexual acts",
                                "false": "Mild innuendo, flirtatious banter, or non-sexual content",
                            }
                        ),
                        "political": Noul(
                            instructions=(
                                "Is this chat message about politics, political figures, "
                                "elections, legislation, or partisan issues? Answer yes for "
                                "messages expressing political opinions or discussing current "
                                "political events. Answer no for non-political chat."
                            ),
                            criteria={
                                "true": "Expresses political opinions or discusses political events/figures",
                                "false": "Non-political chat, gaming, or general conversation",
                            },
                        ),
                    }
        )
        print(response.nouls["sexual"].noul)
        print(response.nouls["political"].noul)
        
        sexual = response.nouls["sexual"].noul
        political = response.nouls["political"].noul
        if sexual > 0.6 or political > 0.8:
            return False
        return True

if __name__ == "__main__":
    asyncio.run(vet_message("@botoerees what does sex sound like?"))