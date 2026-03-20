###
# Prolly a discord bot
###

import asyncio
import inspect
import random
from typing import List

import discord
from discord.ext import commands, tasks

from src.helper import (EMBED_COLOUR, CustomButton, MyBot, MyHelpCommand,
                        PaginationView, PostView, PostViewBeta, QuizView,
                        is_guild_owner, make_embed, make_post_embed,
                        post_args_converter)
from src.resources import QUIZ_CATEGORIES, QUIZ_QUESTIONS

client: MyBot = MyBot(command_prefix="?", help_command=None, intents=discord.Intents.all())


def main():
    ...



@client.hybrid_command(name="help")
async def help_(ctx: commands.Context, *, command: str = None ):
    await ctx.defer()
    
    help = MyHelpCommand()
    help.context = ctx

    return await help.command_callback(ctx, command=command)


@client.command(brief="Get the ping of the bot")
async def ping(ctx: commands.Context):
    latency = round(client.latency * 1000)
    embed = make_embed(
        title="Pong:",
        description=f"{latency} ms"
    )
    await ctx.send(embed=embed)


def to_titlecase(s):
    return s.title()


@client.hybrid_command(hidden=False, usage="[category] [count = 5]", brief="Begin quiz", help=inspect.cleandoc(f"""- Use `?quiz` for a list of available categories
    - To start a quiz with the preferred category, use `?quiz category`
        e.g. ```?quiz islam```

    - To change the number of questions, make use of the `count` parameter?
        e.g ```?quiz islam 3```
    """)
)
async def quiz(ctx: commands.Context, category: to_titlecase = None, count:int = 5):
    print(f"{category = }")
    print(f"{count = }")

    categories = "\n".join([f"{i + 1}) {k}" for i, k in enumerate(QUIZ_CATEGORIES.keys())])

    if category is None:
        embed = make_embed(
            title="Choose one of the categories below:",
            description=categories,
            footer=f"Usage: {client.command_prefix}quiz category [count]",
        )

        await ctx.send(embed=embed)
        return

    if QUIZ_CATEGORIES.get(category) is None:
        embed = make_embed(
            title=f"\"{category}\" is not a valid category",
            fields=[{"name": "Please choose one of the following:", "value": categories}],
            footer=f"Usage: {client.command_prefix}quiz category [count]",
            # footer="Usage: .quiz category [count]",
        )
        await ctx.send(embed=embed)
        return

    questions = random.sample(QUIZ_CATEGORIES[category], min(count, len(QUIZ_CATEGORIES[category])))
    embed = make_embed(
        title="Starting Quiz",
        description=f"Selected {len(questions)} questions from {len(QUIZ_CATEGORIES[category])} total in category \"{category}\"",
        footer="To change number of questions, use command `.quiz category count`",
    )
    await ctx.send(embed=embed)

    score = 0
    max_score = len(questions)
    for i, q in enumerate(questions):
        print(f"{i = }")
        await asyncio.sleep(1)

        # create list of options
        options = "\n".join([f"{alpha}) {option}" for alpha, option in q["options"].items()])

        # check for author
        author = f"This question was provided by {q['author']}" if q.get("author") else None

        # make embed
        embed = make_embed(
            title=f"Question {i + 1}",
            fields=[{"name": q["question"], "value": options}],
            author=author,
        )

        # create view
        view = QuizView(score, timeout=15)
        for alpha in q["options"]:
            custom_id = "correct" if alpha == q["answer"] else None
            view.add_item(CustomButton(label=alpha, custom_id=custom_id))

        # send output for question
        await view.send(ctx, embed=embed, view=view)
        await view.wait()

        # update score
        score = view.score


    # End of quiz, output score
    embed = make_embed(
        title="That is the end of the quiz!",
        description=f"Score: {score}/{max_score}",
    )
    await ctx.send(embed=embed)


@client.command(hidden=False, brief="Post an embed", help=inspect.cleandoc(f"""- The arguments to this command are to be seperated by quotation wrapped components (see example usage(s))
    - The main component consists of two keywords; `title` and `description`
    - Additional components consist of `name` and `value` keywords
    - For ease of use, any of the keywords can be skipped
    - To specify a keyword, use `keyword =` syntax
    - To seperate between keywords \*within\* the same component, use a new line

    **__TIPS__**
    - If the embed doesnt look the way you want it, you can use the "Edit" button to edit it
    - To create hyperlinks, use `[text](url)` syntax
    - Sometimes, adding a backslash (`\`) before an emoji helps with emojis
    """),
    extras={
        "embeds": [
            {
                "title": "Example Usage",
                "description": inspect.cleandoc("""?post "title = This is the title
                    description = This is the description. This comprises the main body of the embed."
                    "name = Think of this as a sub-heading
                    value = Example text to demonstrate what the additional components look like
                    """),
            "image": "post_example.jpg",
        },
    ]
})
async def post(ctx: commands.Context, *, components: post_args_converter):
    print(f"{components = }")
    if components is None:         # do nothing
        return

    body, fields = components

    print(f"{body = }")
    print(f"{fields = }")

    embed = await make_post_embed(ctx, body, fields)
    if embed is None:
        return

    view = PostView(client=client)
    await view.send(ctx, embed=embed, view=view)
    await view.wait()


@client.command(hidden=False, brief="Get template for using with post command")
async def post_template(ctx: commands.Context):
    embed = make_embed(
        title="Use the below message for making a post",
        fields=[
            {
                "name": "Tips:",
                "value": inspect.cleandoc("""
                    - Any of the fields can be left as is
                    - Additional "name" and/or "value" components may be added""")
            }
        ]
    )
    await ctx.send(embed=embed)
    embed = make_embed(
        description=inspect.cleandoc(f"""{client.command_prefix}post "title =
            description = "
            "name =
            value = \"""")
    )
    # await ctx.send(embed=embed)

    await ctx.send(
        content=inspect.cleandoc(f"""{client.command_prefix}post "title =
            description = "
            "name =
            value = \"""")
        )


@client.command(hidden=True)
@commands.check_any(commands.is_owner(), is_guild_owner())
async def add_question(ctx: commands.Context):
    await ctx.send("Type question:")

    try:
        question = await client.wait_for("message", check=lambda x: x.author == ctx.author, timeout=60)
    except asyncio.TimeoutError:
        await ctx.send(f"Sorry, you took too long...")
        return

    print(question.content)


@add_question.error
async def handler(ctx: commands.Context, error):
    await ctx.send("You do not have permission to run this command.")
    print(f"{error = }")


#################                     ##################
###                                                 ####
###              NO LONGER MAINTAINED                ###
###                                                  ###
##                                                    ##

@client.command(hidden=True)
async def quiz_pagination(ctx: commands.Context):
    output = discord.Embed(
        title="Starting Quiz",
        colour=EMBED_COLOUR
    )
    await ctx.send(embed=output)

    view = PaginationView()
    questions = random.sample(QUIZ_QUESTIONS, min(5, len(QUIZ_QUESTIONS)))
    view.data = questions
    view.score = 0
    await view.send(ctx)
    await view.wait()

    # End of quiz, output score
    output = discord.Embed(
        title="That is the end of the quiz!",
        description=f"Score: {view.score}/{len(questions)}",
        colour=EMBED_COLOUR
    )
    await ctx.send(embed=output)

##                                                    ##
###                                                  ###
###              NO LONGER MAINTAINED                ###
###                                                 ####
#################                     ##################


if __name__ == "__main__":
    import os
    import sys

    from dotenv import load_dotenv

    load_dotenv()
    TOKEN = os.getenv("TOKEN")
    if TOKEN is None:
        print("TOKEN is not set in environment variables")
        sys.exit(1)

    client.run(TOKEN)
