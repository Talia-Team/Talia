"""
Talia Discord Bot
GNU General Public License v3.0
resettimers.py (Commands/Administration)

resettimers command
"""
import discord
from Utils import user, message, other

name = "resettimers"
dm_capable = True


async def run(args, bot, msg, conn):
    if msg.author.id not in other.load_config().owners:
        await message.send_error(msg, "You have insufficient permissions to use this command")
        return

    if len(args) < 2:
        await message.send_error(msg, "No scope given")
        return

    args[1] = args[1].lower()
    cur = conn.cursor()

    if args[1] == "global":
        cur.execute("DELETE FROM timers")
        conn.commit()
        await message.send_message(msg, "All timers have been cleared")

    else:
        args[1] = args[1].replace("<@", "").replace("!", "").replace(">", "")

        try:
            person = await user.load_user_obj(bot, int(args[1]))
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
            await message.send_error(msg, "I can't clear the timers of a bot")
            return

        cur.execute("DELETE FROM timers WHERE user = %s", (person.id,))
        conn.commit()
        await message.send_message(msg, f"All timers have been cleared for {str(person)}")
