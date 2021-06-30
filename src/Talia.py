"""
Talia Discord Bot
GNU General Public License v3.0
Talia.py

Main file for the discord bot

On startup
1. Initializes the configuration file
2. Creates an ssh tunnel to the server hosting the db
 and makes a connection to the database
3. Initializes the database and makes a new bot object
4. Starts the async event loop
"""
import asyncio
import discord
import discord_components
import traceback

from Routine import init, handle, loop, post_checks
from Utils import guild, user, message, abc, other

other.log("Preparing")
init.config()

conn = init.open_main_database(other.load_config().db)
init.db(conn)

bot = discord.Client(intents=discord.Intents.all(), max_messages=other.load_config().cache_size)
bot.activity = discord.Game(name="t!help")

guild_prefixes = {}


@bot.event
async def on_ready():
    """
    Async event that is called when the program has connected
     to discord and all data has processed

    1. A success log will be made
    2. Puts each timer into the main loop
    """
    other.log("Ready", "success")
    discord_components.DiscordComponents(bot)

    bot.loop.create_task(cache_loading_loop())
    bot.loop.create_task(loop.main_timer(bot, conn))
    bot.loop.create_task(loop.edu_timer(bot, conn))
    bot.loop.create_task(loop.invest_timer(bot, conn))
    bot.loop.create_task(loop.activity_loop(bot))


@bot.event
async def on_guild_join(new_guild):
    """
    Async event that is called when the client has been
     added to a new server

    1. An info log will be made
    2. The new guild will be written to the database
    """
    other.log(f"Added to guild {new_guild.name} ({new_guild.id})")
    new_guild = abc.Guild(new_guild.id)
    guild.write_guild(new_guild, conn)


@bot.event
async def on_guild_remove(remove_guild):
    """
    Async event that is called when the client has been
     removed from a server

    1. An info log will be made
    2. The guild will be deleted from the database
    """
    other.log(f"Removed from guild {remove_guild.name} ({remove_guild.id})")
    cur = conn.cursor()
    cur.execute("DELETE FROM guilds WHERE id = %s", (remove_guild.id,))
    conn.commit()


@bot.event
async def on_message(msg):
    """
    Async event that is called when a message has been
     received

    1. Verification that the message can be processed
    2. Check to see if it starts with the guild prefix
    3. Handle some database stuff
    4. Send the message to the command handler
    """
    if msg.author.bot:
        return

    if bot.user in msg.mentions:
        await handle.ping(bot, msg, conn)

    if not handle.prefix(msg, conn, guild_prefixes):
        return

    if msg.guild is not None:
        guildinfo = guild.load_guild(msg.guild.id, conn)
        if guildinfo is None:
            guildinfo = abc.Guild(msg.guild.id)
            guild.write_guild(guildinfo, conn, False)

        if not msg.channel.permissions_for(msg.guild.me).send_messages:
            return

        if msg.channel.id in guildinfo.disabled_channels:
            return

    userinfo = user.load_user(msg.author.id, conn)
    if userinfo is None:
        userinfo = abc.User(msg.author.id)
        user.write_user(userinfo, conn, False)

    await handle.mentioned_users(bot, msg, conn)
    conn.commit()

    if msg.guild is None:
        msg.content = msg.content[2:].strip()
    else:
        msg.content = msg.content[len(guild_prefixes[msg.guild.id]):].strip()

    try:
        await handle.command(bot, msg, conn)
    except Exception as errmsg:
        excinfo = traceback.format_exc()
        await message.send_error(msg, f"""\u26a0 An unexpected error occurred \u26a0
Error type: {type(errmsg).__name__}""")
        other.log(f"Error occurred, traceback below\n{excinfo}", "critical")
        return

    await post_checks.level(bot, msg, conn)
    await post_checks.achievements(bot, msg, conn)


async def cache_loading_loop():
    """
    An async loop that is called once every 10 minutes.
     It is used to load stat information and guild
     prefixes into the cache

    1. Creates a cursor object that will always be used
    2. Fetches all prefixes from the database
    3. Places each one into the cache
    """
    cur = conn.cursor()
    while True:
        cur.execute("SELECT id, prefix FROM guilds")
        all_prefixes = cur.fetchall()

        for prefix in all_prefixes:
            guild_prefixes[prefix[0]] = prefix[1]

        await asyncio.sleep(600)


if __name__ == "__main__":
    other.log("Establishing connection to discord")
    try:
        bot.run(other.load_config().token)
    except discord.LoginFailure:
        other.log("Invalid token passed", "critical")