import discord
import asyncio
import os
import json
import funcs
import settings
import subprocess
import importlib
import random
import zstd

client = discord.Client()

commands = {
    "!help": "Show this message",
    "!submit": "Select your file and write this as a comment to submit your bot",
    "!matches": "Print upcoming matches",
    "!languages": "Check supported languages for submissions, add a language name to know how it's compiled/run \n\t*!language python*",
    "!battle": "Run a match between two players, \n\t*!battle [players tags] \n\tdo this in the **#battles channel**",
    "!specs": "Check tournament specs",
    "!engine": "Know how to get the engine of the current tournament, \n\t*!engine [win/mac/linux]*",
    "!leaderboard": "Check who signed up for this season and if they submitted a bot",
    "!utc": "Get current UTC time, make sure to check it now and then.",
}

adminCommands = {
    "!clear": "!clear [n of message to delete] [channel, use * to select current]",
    "!type": "!type [message to make the HTBot type]",
    "!post": "!post [path to file in the server] [channel, se * to Select current] to post a file from the server",
    "!admin": "Print this message",
    "!embed": "Create embed message, !embed [title] | [content]",
}

results = {}
global res
res = 0

global haliteBackup
haliteBackup = None


@client.event
async def on_ready():  # startup
    print("\nBot " + client.user.name + " ready to operate!")
    print("-------\n")

    battles = discord.utils.get(
        client.get_all_channels(), server__name=settings.serverName, name="battles"
    )
    embed = discord.Embed(
        title="CUCPC Discord Bot is back!",
        description="Get over to " + battles.mention + " and have some fun! ",
        color=0xFFAE00,
    )

    embed.set_footer(text=funcs.getTime() + " (UTC) - CUCPCP Discord Bot")

    general = discord.utils.get(
        client.get_all_channels(), server__name=settings.serverName, name="general"
    )

    await client.send_message(general, embed=embed)
    await client.change_presence(game=discord.Game(name="!help"))


@client.event
async def on_message(message):

    server = discord.utils.get(client.servers, name=settings.serverName)

    try:
        if message.content.startswith("!submit"):

            """
            This command submits a player's bot. This command can be run in 
            `tank-game-commands` and via PMs to the bot.
            This command adds a queue to the handler, the handler then picks
            up the queue from the database and :
                - Checks if it's a valid submission
                - If the user isn't already running something
                - Installs external libraries (if required)
                - Compiles the code (if required)
                - Runs a test game against itself to make sure it works
                - Sends logs and compiler outputs via DM to the player
            """

            if (
                str(message.channel) != "tank-game-commands"
                and not message.channel.is_private
            ):  # if message is in the wrong channel
                if not message.channel.is_private:
                    await client.delete_message(message)
                await client.send_message(
                    message.channel,
                    "**Cannot use this command in this channel!** "
                    + message.author.mention,
                )
            else:
                try:
                    await client.send_message(
                        message.channel,
                        "`Submitting, compiling and testing your bot...` "
                        + message.author.mention,
                    )
                    response, compileLog, sub = await funcs.uploadBot(
                        message.attachments[0].get("url"),
                        str(message.author),
                        message.attachments[0].get("filename"),
                    )
                    await client.send_message(
                        message.channel, "`" + response + "` " + message.author.mention,
                    )
                    if not message.channel.is_private:
                        await client.delete_message(message)
                    if compileLog != "":  # if compiled and run successfully
                        if message.channel.is_private:
                            global haliteBackup
                            await client.send_file(
                                haliteBackup,
                                sub,
                                content=">store " + message.author.id,
                            )

                        await client.send_message(
                            message.author,
                            "**Here your compile and run log for yout bot submission!**",
                        )
                        await client.send_file(message.author, compileLog)

                except IndexError:  # no attachments present
                    await client.send_message(
                        message.channel,
                        "`No attachment present!` " + message.author.mention,
                    )

        elif message.content.startswith("!help"):  # help function

            """
            This command simply prints the name of all
            other commands with a brief explaination
            """

            battles = discord.utils.get(
                client.get_all_channels(),
                server__name=settings.serverName,
                name="battles",
            )
            embed = discord.Embed(
                title="Commands for HTBot",
                description="Currently on Season-" + settings.season,
                color=0xFFAE00,
            )

            embed.set_footer(text=funcs.getTime() + " (UTC) - HTBot")

            for k, c in sorted(commands.items()):
                embed.add_field(name=k, value=c, inline=False)

            await client.send_message(message.channel, embed=embed)

        elif message.content.startswith("!utc"):
            text = "**Current UTC time :** *" + funcs.getTime() + "*"
            await client.send_message(message.channel, text)

        elif message.content.startswith("!matches"):  # check upcoming matches

            """
            This command allows everyone to check the upcoming
            matches. A player can also run :
                !matches @Splinter
            And this will return all the games that Splinter is in
            """

            if settings.onTour:  # if we are running in a tournament
                m = str(message.content).split()
                matches = settings.matches
                if matches is None or len(matches) < 2:
                    await client.send_message(
                        message.channel, "**No scheduled matches!**"
                    )

                elif len(m) == 1:  # check all matches
                    embed = discord.Embed(
                        title="Matches",
                        description="Here are the upcoming matches! "
                        + settings.emojis["explosion"],
                        color=0xFFAE00,
                    )
                    embed.set_thumbnail(
                        url="https://raw.githubusercontent.com/Splinter0/Tournament-Environment/master/imgs/logo.png"
                    )
                    embed.set_footer(text=funcs.getTime() + " (UTC) - HTBot")
                    for k, v in sorted(matches.items()):
                        if k == "placeholder":
                            continue
                        text = "**" + k + "** : \n"
                        value = ""
                        for r in v:
                            value += "\t" + r + "\n"

                        embed.add_field(name=text, value=value, inline=False)

                    await client.send_message(message.channel, embed=embed)

            else:
                await client.send_message(message.channel, "**No scheduled matches!**")

        elif message.content.startswith("!battle"):

            """
            This command allows the players to battle against
            themselves whenever they want when there's an ongoing
            tournament. This feature is to allow the players to
            try out the game environment and debug their bots
            properly.
            Example of a command :
                !battle @Sisyphus192 @WillN210
            This command starts a game between Sisyphus192 and WillN210.
            """

            # if we are in a tournament and in the right channel
            if settings.onTour and str(message.channel) == "battles":
                try:
                    # get the players from mentions
                    pp = []
                    for p in message.raw_mentions:
                        pp.append(str(server.get_member(p)))

                    await client.send_message(
                        message.channel, "*Running battle...* ",
                    )
                    status, result, logs, replay = await funcs.battle(pp)

                    await client.send_message(message.channel, status)
                    if result != "":  # if we have an output
                        await client.send_message(message.channel, result)
                        if replay != "":
                            await client.send_file(message.channel, replay)

                        # check if logs are present and send them
                        for l in range(len(logs)):
                            try:
                                if logs[l] != "":
                                    await client.send_message(
                                        message.mentions[l],
                                        "**Here is the logfile of your bot : (timstamp battle : "
                                        + funcs.getTime()
                                        + ")**",
                                    )
                                    await client.send_file(message.mentions[l], logs[l])
                                    os.remove(logs[l])
                                else:
                                    await client.send_message(
                                        message.mentions[l],
                                        "**No log file present : (timstamp battle : "
                                        + funcs.getTime()
                                        + ")**",
                                    )

                            except:
                                pass

                except (KeyError, IndexError):  # formatting error
                    await client.send_message(
                        message.channel,
                        "**Bad formatting! Run !help for info about commands**",
                    )

            elif str(message.channel) != "battles":  # wrong channel!
                battles = discord.utils.get(
                    client.get_all_channels(),
                    server__name=settings.serverName,
                    name="battles",
                )
                await client.send_message(
                    message.channel,
                    "**Run this in the " + battles.mention + " channel!**",
                )

            else:  # tournament is closed
                await client.send_message(
                    message.channel, "**Feature not avaible at the moment!**"
                )

        elif message.content.startswith("!languages"):  # send all supported languages

            """
            This command outputs all the languages that are
            currently supported. To check in specific a language :
                !languages python
            This will output the command used to compile the player's code,
            the command used to install the external libraries and
            the command used to run a test game
            """

            m = message.content.split()
            if len(m) == 1:
                embed = discord.Embed(
                    title="Languages",
                    description="All languages supported " + settings.emojis["paper"],
                    color=0xFFAE00,
                )

                embed.set_footer(text=funcs.getTime() + " (UTC) - HTBot")

                for k, c in sorted(funcs.languages.items()):
                    content = "Compile command : "
                    content += "*" + c[1] + "*" if c[1] != "" else "*not needed*"
                    content += "\nRun command : *" + c[2] + "*"
                    embed.add_field(name=k, value=content, inline=False)

                await client.send_message(message.channel, embed=embed)

            else:
                content = ""
                for k, v in sorted(funcs.languages.items()):
                    if m[1] == k:
                        embed = discord.Embed(
                            title=k,
                            description="Specs for "
                            + k
                            + " "
                            + settings.emojis["paper"],
                            color=0xFFAE00,
                        )

                        embed.set_footer(text=funcs.getTime() + " (UTC) - HTBot")
                        content = "*" + v[1] + "*" if v[1] != "" else "*not needed*"
                        embed.add_field(
                            name="Compile command", value=content, inline=False
                        )
                        content = "*" + v[2] + "*"
                        embed.add_field(
                            name="Run command :", value=content, inline=False
                        )

                        await client.send_message(message.channel, embed=embed)
                        break

                if content == "":
                    content = "**Language not supported!**"
                    await client.send_message(message.channel, content)

        elif message.content.startswith("!specs"):

            """
            This command prints the specs for the current
            season like : constants, map sizes and environment
            changes.
            """

            try:
                with open(settings.specs, "r") as s:
                    infos = s.read()
                    infos = infos.replace("\\n", "\n")
                    await client.send_message(
                        message.channel, infos + "\n" + settings.emojis["logo"]
                    )

            except FileNotFoundError:
                text = (
                    "**Specs for season-"
                    + settings.season
                    + " are still not out!** "
                    + settings.emojis["paper"]
                )

            await client.send_message(message.channel, text)

        elif message.content.startswith("!engine"):

            """
            This will give the players access to the code
            of the Halite environment used in the ongoing
            tournament. It will also give away a percompiled
            version of it.
            """

            if len(message.content.split()) > 1:
                engine = None
                try:
                    if message.content.split()[1] == "win":
                        engine = settings.engine[0]
                    elif message.content.split()[1] == "mac":
                        engine = settings.engine[1]
                    elif message.content.split()[1] == "linux":
                        engine = settings.engine[2]

                except:
                    engine = None

                try:
                    await client.send_file(message.author, engine)
                    await client.send_message(
                        message.channel,
                        "*Sending precompiled engine in DMs* "
                        + message.author.mention
                        + " "
                        + settings.emojis["engine"],
                    )
                    await client.send_message(
                        message.author,
                        "**Here is your precompiled engine for "
                        + message.content.split()[1]
                        + "**",
                    )

                except:
                    await client.send_message(
                        message.channel,
                        "**Precompile engine for "
                        + message.content.split()[1]
                        + " is not avaible yet!** "
                        + message.author.mention
                        + " "
                        + settings.emojis["engine"],
                    )

            else:
                if settings.engineLink != "" and settings.onTour:
                    await client.send_message(
                        message.channel,
                        "**Here is the link containing the info for the engine : "
                        + settings.engineLink
                        + "** "
                        + settings.emojis["engine"],
                    )
                else:
                    await client.send_message(
                        message.channel,
                        "**Link still not avaible!** " + settings.emojis["paper"],
                    )

        # admin commands
        elif str(message.author) in settings.admins:

            """
            This commands are only avaible for the members
            in the `admins` group
            """

            if message.content.startswith("!type"):  # make bot type in current channel

                """
                This will send a message from HTBot
                """

                await client.delete_message(message)
                await client.send_message(
                    message.channel, str(message.content).replace("!type", "")
                )

            elif message.content.startswith("!admin"):  # print admin commands

                """
                A help command for admins
                """

                text = "```\n"
                for k, c in sorted(adminCommands.items()):
                    text += k + " : " + c + "\n"
                text += "```"
                await client.send_message(message.channel, text)

            elif message.content.startswith("!clear"):  # delete n messages in a channel

                """
                This command allows to delete x messages in a y channel
                E.g :
                    !clear 20 battles
                Will delete 20 messages in the battles channel
                """

                try:
                    n = int(message.content.split()[1])  # number of messages
                    ch = message.content.split()[2]  # channel
                    if ch != "*":  # current channel
                        channel = discord.utils.get(
                            client.get_all_channels(),
                            server__name=settings.serverName,
                            name=ch,
                        )
                    else:
                        channel = message.channel
                    await client.purge_from(channel, limit=n)

                except IndexError:
                    await client.send_message(
                        discord.utils.get(
                            client.get_all_channels(),
                            server__name=settings.serverName,
                            name="halite",
                        ),
                        "**Wrong command formatting**",
                    )

            elif message.content.startswith(
                "!post"
            ):  # upload a file from server to channel

                """
                This will upload a file from the server to the channel
                wanted.
                """

                try:
                    await client.delete_message(message)
                    c = message.content.replace("!post", "")
                    f, ch = c.split()[0], c.split()[1]
                    if ch != "*":
                        channel = discord.utils.get(
                            client.get_all_channels(),
                            server__name=settings.serverName,
                            name=ch,
                        )
                    else:
                        channel = message.channel
                    await client.send_file(
                        channel, f, content=c.replace(f + " " + ch, "")
                    )

                except FileNotFoundError:
                    s = funcs.log("File " + f + " not found!")
                    await client.send_message(
                        discord.utils.get(
                            client.get_all_channels(),
                            server__name=settings.serverName,
                            name="halite",
                        ),
                        s,
                    )

                except IndexError:
                    await client.send_message(
                        discord.utils.get(
                            client.get_all_channels(),
                            server__name=settings.serverName,
                            name="halite",
                        ),
                        "**Wrong command formatting**",
                    )

            elif message.content.startswith("!embed"):
                try:
                    content = message.content.split()[1:]
                    t = []
                    for w in content:
                        if w == "|":
                            break
                        else:
                            t.append(w)
                    title = " ".join(t)
                    content = " ".join(content[len(t) + 1 :])

                    embed = discord.Embed(
                        title=title, description=content, color=0xFFAE00
                    )

                    await client.send_message(message.channel, embed=embed)
                    await client.delete_message(message)

                except:
                    await client.send_message(message.channel, "**Invalid command**")

            elif message.content.startswith("!handler"):
                try:
                    command = message.content.split()[1]

                    if command == "start":
                        if funcs.checkPulse():
                            await client.send_message(
                                message.channel, "**Handler already running**"
                            )
                        else:
                            funcs.manageHandler()
                            await client.send_message(
                                message.channel, "**Handler starting up...**"
                            )

                    elif command == "stop":
                        if not funcs.checkPulse():
                            await client.send_message(
                                message.channel, "**Handler is not running!**"
                            )
                        else:
                            funcs.manageHandler(start=False)
                            await client.send_message(
                                message.channel, "**Handler going down...**"
                            )

                    elif command == "restart":
                        await client.send_message(
                            message.channel, "**Restarting handler...**"
                        )
                        if not funcs.checkPulse():
                            funcs.manageHandler()
                            await client.send_message(
                                message.channel, "**Handler starting up...**"
                            )
                        else:
                            funcs.manageHandler(start=False)
                            await client.send_message(
                                message.channel, "**Handler going down...**"
                            )
                            funcs.manageHandler()
                            await client.send_message(
                                message.channel, "**Handler starting up...**"
                            )

                    else:
                        await client.send_message(
                            message.channel, "**Invalid command**"
                        )

                except IndexError or KeyError:
                    await client.send_message(message.channel, "**Invalid command**")

    except Exception as e:
        s = funcs.log(str(e))
        await client.send_message(
            discord.utils.get(
                client.get_all_channels(),
                server__name=settings.serverName,
                name="halite",
            ),
            s,
        )


@client.event
async def on_member_join(member):
    channel = discord.utils.get(
        client.get_all_channels(),
        server__name=settings.serverName,
        name="tank-game-discussion",
    )
    role = discord.utils.get(member.server.roles, name="Member")
    await client.add_roles(member, role)
    funcs.log("Member joined : " + str(member))
    await client.send_message(
        discord.utils.get(
            client.get_all_channels(), server__name=settings.serverName, name="general"
        ),
        "Welcome "
        + member.mention
        + " to the CU Competitive Programming Club! Check out the section "
        + channel.mention
        + " to participate in our in-house Competitive Programming game! ",
    )


if __name__ == "__main__":
    try:
        # Custom settings if you want to run handler on different user
        handler = subprocess.Popen(
            "python3 " + settings.path + "/handler.py", shell=True
        )
        handlerRunning = True
        client.run(settings.token)

    except KeyboardInterrupt:
        print("\nExiting...")
        handler.terminate()
        os._exit(1)

    except discord.errors.LoginFailure:
        if settings.token is None or settings.token == "":
            print("\nYou need to register a token in the database!")
        else:
            print("\nToken insered is not valid!")
        handler.terminate()
        os._exit(1)

    except Exception as e:
        funcs.log(str(e))
