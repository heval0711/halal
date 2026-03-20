import discord
import asyncio
from discord.ext import commands, tasks


client = commands.Bot(command_prefix=".", intents=discord.Intents.all())
# client.remove_command("help")


TEST_QUESTIONS = [
    {"question": "what is your name?", "answer": "Halal Bot"},
    {"question": "When were you born?", "answer": "today?"},
    {"question": "Why?", "answer": "learning and knowledge"},
]


def main():
    ...


@tasks.loop(seconds=1, count=None)
async def test_task():
    channel = client.get_channel(1108966462451875871)

    loop_count = test_task.current_loop
    output = ""

    # last question, stop looping
    if loop_count == len(TEST_QUESTIONS):
        output = f"The answer of the previous question was: {TEST_QUESTIONS[-1]['answer']}\n\n"
        output += "No more questions. Come back later."
        await channel.send("```" + output + "\n```")

        test_task.stop()
        return

    # First question
    if loop_count == 0:
        output += TEST_QUESTIONS[loop_count]["question"]
        await channel.send("```" + output + "\n```")

    else:
        output += f"The answer of the previous question was: {TEST_QUESTIONS[loop_count - 1]['answer']}\n\n"
        output += TEST_QUESTIONS[loop_count]["question"]
        await channel.send("```" + output + "\n```")


@client.command()
async def test(ctx, *args):
    await ctx.send("Starting quiz")
    test_task.start()


@client.command()
async def end_test(ctx, *args):
    await ctx.send("ending quiz")
    test_task.stop()


if __name__ == "__main__":
    main()
    import os
    from dotenv import load_dotenv

    load_dotenv()
    TOKEN = os.getenv("TOKEN")
    client.run(TOKEN)
