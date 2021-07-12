"""
Talia Discord Bot
GNU General Public License v3.0
resetinfo.py (Commands/Administration)

resetinfo command
"""
import discord
from Utils import user, message, other

name = "resetinfo"
dm_capable = True


async def run(bot, msg, conn):
    if msg.author.id not in other.load_config().owners:
        await message.send_error(msg, "You have insufficient permissions to use this command")
        return

    split_data = msg.content.split(" ")

    if len(split_data) < 2:
        await message.send_error(msg, "No scope given")
        return

    split_data[1] = split_data[1].lower()
    cur = conn.cursor()

    if split_data[1] == "guild":
        cur.execute("DELETE FROM guilds WHERE id = %s", (msg.guild.id,))
        conn.commit()
        await message.send_message(msg, "All information for this guild has been cleared")

    else:
        split_data[1] = split_data[1].replace("<@", "").replace("!", "").replace(">", "")

        try:
            person = await user.load_user_obj(bot, int(split_data[1]))
        except ValueError:
            await message.send_error(msg, "Invalid user")
            return
        except discord.NotFound:
            await message.send_error(msg, "I can't find that person")
            return
        except discord.HTTPException:
            await message.send_error(msg, "An error occurred and the command couldn't be run")
            return

        if person.bot:
            await message.send_error(msg, "I can't clear the information of a bot")
            return

        cur.execute("DELETE FROM users WHERE id = %s", (person.id,))
        cur.execute("DELETE FROM timers WHERE user = %s", (person.id,))
        conn.commit()
        await message.send_message(msg, f"All information for {str(person)} has been cleared")