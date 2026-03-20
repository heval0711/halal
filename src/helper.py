# import datetime
import discord
import asyncio
from discord.ext import commands
from typing import Any, Callable, Coroutine, Literal, List, Mapping, Optional, Type, Union

from discord.ext.commands.cog import Cog
from discord.ext.commands.core import Command


EMBED_COLOUR = discord.Colour.dark_gold()


class MyBot(commands.Bot):
    # def __init__(self, command_prefix, *, description=None, intents):
    #     super().__init__(command_prefix=command_prefix, description=description, intents=intents)

    async def on_ready(self):
        print(f"Logged in as {self.user}. ID:{self.user.id}")

        await self.tree.sync()
        print(f'Synced')

    async def on_message(self, message):
        if message.author == self.user:
            return

        print(f"{message.author}: {message.content}")
        await self.process_commands(message)


class MyHelpCommand(commands.DefaultHelpCommand):
    def __init__(self, **options: Any) -> None:
        super().__init__(**options)

    async def send_bot_help(self, mapping: Mapping[Cog | None, List[Command[Any, Callable[..., Any], Any]]]) -> Coroutine[Any, Any, None]:
        embed = make_embed(
            title="Help",
            description="Use ?help <command> to get detailed info for a particular command",
            footer=f"Requested by {self.context.author}",
            footer_icon=self.context.author.avatar,
        )

        embed.add_field(name="help", value="Show this message")
        for cog in mapping:
            for command in await self.filter_commands(mapping[cog], sort=True):
                if command.name == "help":
                    continue
                embed.add_field(
                    name=command.name,
                    value=command.short_doc,
                )

        # return await self.get_destination().send(embed=embed)
        return await self.context.send(embed=embed)

    async def send_command_help(self, command: Command[Any, Callable[..., Any], Any]) -> Coroutine[Any, Any, None]:
        embed = make_embed(
            title=f"{self.get_command_signature(command)} {command.signature}",
            # description="**" + command.short_doc + "**",
            description=command.short_doc,
            footer=f"Requested by {self.context.author}",
            footer_icon=self.context.author.avatar,
        )

        if command.help:
            embed.add_field(name="__HOW TO USE__", value=command.help)

        data = [{"embed": embed, "file": None}]
        if command.extras:
            for info in command.extras["embeds"]:
                embed = MyEmbed.from_dict(info)
                embed.set_footer(text=f"Requested by {self.context.author}", icon_url=self.context.author.avatar)

                file = None
                f_name = info.get("image")
                if f_name:
                    file = discord.File(f"src/{f_name}", filename=f"{f_name}")
                    embed.set_image(url=f"attachment://{f_name}")

                data.append({"embed": embed, "file": file})

        view = HelpPaginationView(data=data)
        # await view.send(self.get_destination(), view=view)
        await view.send(self.context, view=view)

    async def send_error_message(self, error: str) -> Coroutine[Any, Any, None]:
        embed = make_embed(
            title="Incorrect Usage",
            description=error,
            colour=discord.Colour.dark_red(),
        )

        # return await self.get_destination().send(embed=embed)
        return await self.context.send(embed=embed)

    def code_blockify(self, string):
        return f"\n```{string}\n```"

class MyEmbed(discord.Embed):
    def __init__(self, *, colour = None, title: Any | None = None, type = 'rich', url: Any | None = None, description: Any | None = None):
        colour = colour or EMBED_COLOUR
        super().__init__(colour=colour, title=title, type=type, url=url, description=description)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]):
        embed = cls(
            title=data.get("title", ""),
            description=data.get("description", None),
            colour=data.get("colour", None),
            url=data.get("url", None),
        )

        if fields := data.get("fields"):
            for field in fields:
                embed.add_field(
                    name=field.get("name", ""),
                    value=field.get("value", ""),
                    inline=field.get("inline", None)
                )

        if author := data.get("author"):
            embed.set_author(
                name=author.get("name", ""),
                url=author.get("url", None),
                icon_url=author.get("icon_url", None),
            )

        if footer := data.get("footer"):
            embed.set_footer(
                text=footer.get("text"),
                icon_url=footer.get("text", None),
            )

        return embed

    def add_field(self, *, name: Any, value: Any, inline: bool | None = None):
        inline = inline or False
        return super().add_field(name=name, value=value, inline=inline)


class HelpPaginationView(discord.ui.View):
    def __init__(self, data: List[dict[MyEmbed, discord.File]], *, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        self.data = data
        self.current = 0

    async def send(self, loc: discord.abc.Messageable, view: discord.ui.view):
        self.update_buttons()
        self.message = await loc.send(file=self.data[self.current]["file"], embed=self.data[self.current]["embed"], view=view)

    def update_buttons(self):
        self.display.label = f"{self.current + 1}/{len(self.data)}"

        if self.current == 0:
            self.left.disabled = True
            self.left.style = discord.ButtonStyle.secondary
        else:
            self.left.disabled = False
            self.left.style = discord.ButtonStyle.success

        if self.current == len(self.data) - 1:
            self.right.disabled = True
            self.right.style = discord.ButtonStyle.secondary
        else:
            self.right.disabled = False
            self.right.style = discord.ButtonStyle.success


    @discord.ui.button(label="◀", style=discord.ButtonStyle.success)
    async def left(self, interaction: discord.Interaction, button: discord.Button):
        self.current -= 1
        self.update_buttons()

        embed = self.data[self.current].get("embed")
        file = self.data[self.current].get("file")
        await interaction.response.edit_message(attachments=[file] if file else [], embed=embed, view=self)

        if file:
            file.reset()

    @discord.ui.button(label="", disabled=True)
    async def display(self, interaction: discord.Interaction, button: discord.Button):
        return

    @discord.ui.button(label="▶", style=discord.ButtonStyle.success)
    async def right(self, interaction: discord.Interaction, button: discord.Button):
        self.current += 1
        self.update_buttons()

        embed = self.data[self.current].get("embed")
        file = self.data[self.current].get("file")
        await interaction.response.edit_message(attachments=[file] if file else [], embed=embed, view=self, )

        if file:
            file.reset()


# view for pagination version of quiz -- no longer maintained
class PaginationView(discord.ui.View):
    q_no = 0
    score = 0

    async def send(self, ctx: commands.Context):
        self.message = await ctx.send(view=self)
        await self.quiz(self.message)

    async def quiz(self, ctx: commands.Context):
        if self.q_no == len(self.data):
            self.stop()
            return

        embed = discord.Embed(
            title=f"Question {self.q_no + 1}:",
            description=self.data[self.q_no]["question"],
            colour=discord.Colour.red(),
        )
        for alpha, option in self.data[self.q_no]["options"].items():
            embed.add_field(
                name=f"{alpha}) {option}",
                value="",
                inline=False
            )

        self.clear_items()
        for alpha in self.data[self.q_no]["options"]:
            custom_id = "correct" if alpha == self.data[self.q_no]["answer"] else None
            self.add_item(self.CustomButton(label=alpha, custom_id=custom_id))

            await self.message.edit(embed=embed, view=self)


    async def button_callback(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        if button.custom_id == "correct":
            self.score += 1
            button.style = discord.ButtonStyle.success
            await self.message.edit(view=self)

        else:
            button.style = discord.ButtonStyle.danger
            await self.message.edit(view=self)
            await asyncio.sleep(0.25)


        for child in self.children:
            if child.custom_id == "correct":
                child.style = discord.ButtonStyle.success

            child.disabled = True

        await self.message.edit(view=self)
        self.q_no += 1
        await self.quiz(self.message)
        # self.stop()

    class CustomButton(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            return await self.view.button_callback(interaction, self)

# A custom button that uses `button_callback` method of its view as its callback method
class CustomButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        if self.view:
            return await self.view.button_callback(interaction, self)

# view for quiz command
class QuizView(discord.ui.View):
    def __init__(self, score, *, timeout=180.0):
        super().__init__(timeout=timeout)
        self.score = score

    async def send(self, ctx: commands.Context, embed: MyEmbed, view):
        self.embed = embed
        self.message = await ctx.send(embed=embed, view=view)

    async def on_timeout(self):
        for child in self.children:
            child.style = discord.ButtonStyle.success if child.custom_id == "correct" else discord.ButtonStyle.danger
            child.disabled = True

        self.embed.set_footer(text="⌛ You took too long")
        await self.message.edit(embed=self.embed, view=self)

    async def button_callback(self, interaction: discord.Interaction, button):
        if button.custom_id == "correct":
            self.score += 1
            button.style = discord.ButtonStyle.success
            await interaction.response.edit_message(view=self)

        else:
            button.style = discord.ButtonStyle.danger
            await interaction.response.edit_message(view=self)
            await asyncio.sleep(0.25)

        for child in self.children:
            if child.custom_id == "correct":
                child.style = discord.ButtonStyle.success

            child.disabled = True

        await interaction.followup.edit_message(message_id=interaction.message.id, view=self)
        self.stop()

# View for post command
class PostView(discord.ui.View):
    def __init__(self, client, *, timeout=180.0):
        super().__init__(timeout=timeout)
        self.client = client
        self.command = client.command_prefix + "post"

    async def send(self, ctx: commands.Context, embed: MyEmbed, view: discord.ui.View):
        self.ctx = ctx
        self.embed: MyEmbed = embed
        self.message: discord.Message = await ctx.send(embed=embed, view=view)

    @discord.ui.button(label="Confirm?", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return

        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.message.delete())
            tg.create_task(self.ctx.message.delete())

        self.clear_items()
        self.embed.remove_footer()
        await self.ctx.send(embed=self.embed, view=self)

        self.stop()

    @discord.ui.button(label="Edit")
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()  # idk why but interaction fails without this
        if interaction.user.id != self.ctx.author.id:
            return

        button.disabled = True
        self.embed.set_footer(text="Edit the message to update this embed")
        await self.message.edit(embed=self.embed, view=self)

        try:
            _, after = await self.client.wait_for("message_edit", check=lambda before, _: before.id == self.ctx.message.id, timeout=60)
            button.disabled = False
            self.embed.remove_footer()
            await self.message.edit(embed=self.embed, view=self)
        except asyncio.TimeoutError:
            if not self.is_finished():
                print("Edit failed")
                button.disabled = False
                self.embed.remove_footer()
                await self.message.edit(embed=self.embed, view=self)
            return

        embed = await self.handle_edited(after.content)
        if embed is None:
            return

        self.embed = embed
        await self.message.edit(embed=self.embed)

    async def handle_edited(self, msg):
        if not msg.startswith(f"{self.command} "):
            print("Edit changed the command")
            return

        parsed_msg = post_args_converter(msg[len(self.command):])
        if not parsed_msg:
            return

        body, fields = parsed_msg

        embed = await make_post_embed(self.ctx, body, fields)
        return embed

class PostViewBeta(PostView):
    def __init__(self, client, *, timeout=180.0):
        super().__init__(client, timeout=timeout)
        # self.client = client
        self.command = client.command_prefix + "p"


def is_guild_owner():
    def predicate(ctx: commands.Context):
        return ctx.guild is not None and ctx.guild.owner_id == ctx.author.id
    return commands.check(predicate)

def make_embed(title=None, description=None, colour=None, *, url=None, fields=[], image=None, thumbnail=None, footer=None, footer_icon=None, author=None, author_url=None, author_icon=None):
    embed = MyEmbed(
        title=title,
        description=description,
        url=url,
        colour=colour,
    )

    if image:
        embed.set_image(url=url)

    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    if author:      # if is necessary because name is required param
        embed.set_author(name=author, url=author_url, icon_url=author_icon)

    if footer:
        embed.set_footer(text=footer, icon_url=footer_icon)

    for field in fields:
        name = field.get("name", "")
        value = field.get("value", "")
        embed.add_field(name=name, value=value, inline=field.get("inline"))

    return embed


# parses the post command to its args
def post_args_converter(msg: str):
    msg_split = []
    start = None
    for i, c in enumerate(msg):
        if (c == "\"" and i == 0) or (c == "\"" and msg[i - 1] != "\\"):
            if start is None:
                start = i
            else:
                if part := msg[start+1:i].strip(" "):
                    msg_split.append(part)
                start = None

        elif start is None and not c.isspace():
            raise Exception(f"Expected '\"' found '{c}'")

    if not msg_split:
        return None

    print(f"{msg_split = }")
    body = msg_split[0]
    fields = msg_split[1:]
    return body, fields

async def parse_post_params(ctx: commands.Context, object, items, *, check=None):
    check = check or []

    items_dict = {k: "" for k in items}
    current = ""

    for row in object.strip(" ").split("\n"):
        print(f"{row = }")
        try:
            k, v = row.split("=", maxsplit=1)
            print(f"{k, v = }")

            # if valid key found
            if (k := k.strip().lower()) in items_dict.keys():
                current = k
                # if key repeating, output error
                if items_dict[current]:
                    embed = make_embed(
                        title="Incorrect Usage",
                        description=f"`{current}` key is repeating",
                        colour=discord.Colour.dark_red(),
                    )

                    await ctx.send(embed=embed)
                    return None

                # else, start storing text
                items_dict[current] += v.strip(" ")

            # elif key is in check instead, this is to check if title & description were omitted
            elif k in check:
                return False

            # elif current storing already, this means that a '=' sign was part of user's text
            elif current in items_dict.keys():
                items_dict[current] += "\n" + row

            # else, this means an invalid key was found, output error
            else:
                raise NotImplementedError("Need to output error when an invalid key is passed to post command")

        except ValueError:
            if not current:
                embed = make_embed(
                    title="Incorrect Usage",
                    description=f"A component required at least one of the following keys:\n- {items[0]}\n- {items[1]}",
                    colour=discord.Colour.dark_red(),
                )

                await ctx.send(embed=embed)
                return

            items_dict[current] += "\n" + row

    return items_dict


# makes an embed based on the params of post command
async def make_post_embed(ctx: commands.Context, body: str, fields: List[str]) -> (MyEmbed | None):
    print(f"{body = }")
    body_items = await parse_post_params(ctx, body, ["title", "description"], check=["name", "value"])
    if body_items is None:
        return
    if not body_items:
        fields.insert(0, body)

    print(f"{body_items = }")
    title, description = body_items.values()

    embed = make_embed(
        title=title,
        description=description,
        author=f"Posted by @{ctx.author}",
        author_icon=ctx.author.avatar,
    )

    print(f"{fields = }")
    for field in fields:
        field_items = await parse_post_params(ctx, field, ["name", "value"])
        if field_items is None:
            return

        print(f"{field_items = }")
        name, value = field_items.values()
        embed.add_field(
            name=name,
            value=value,
        )

    return embed


async def make_post_embed_from_dict(ctx: commands.Context, body: str, fields: List[str]) -> (MyEmbed | None):
    embed_dict = {
        "author": {"name" : f"Posted by {ctx.author}"},
        "fields": [],
    }

    print(f"{body = }")
    body_items = await parse_post_params(ctx, body, ["title", "description"], check=["name", "value"])
    if body_items is None:
        return
    if not body_items:
        fields.insert(0, body)

    print(f"{body_items = }")

    embed_dict.update(body_items)

    print(f"{fields = }")
    for field in fields:
        field_items = await parse_post_params(ctx, field, ["name", "value"])
        if field_items is None:
            return

        print(f"{field_items = }")
        embed_dict["fields"].append(field_items)

    embed = MyEmbed.from_dict(embed_dict)
    return embed
