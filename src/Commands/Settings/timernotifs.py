"""
Talia Discord Bot
GNU General Public License v3.0
timernotifs.py (Commands/Settings)

timernotifs command
"""
import asyncio
import discord
import discord_components
from Utils import user, message
from Storage import meta

name = "timernotifs"
dm_capable = True


async def run(args, bot, msg, conn, guildinfo, userinfo):
    if userinfo.settings.reaction_confirm:
        await message.send_error(msg,
            f"You need buttons enabled to run this command\nButtons can be enabled with the `button` command"
        )
        return

    components = []
    i = 0
    tmp = []

    for notif in userinfo.settings.timernotifs.keys():
        if userinfo.settings.timernotifs[notif]:
            tmp.append(discord_components.Button(
                label=meta.timer_names[notif], style=discord_components.ButtonStyle.green, id=notif
            ))
        else:
            tmp.append(discord_components.Button(
                label=meta.timer_names[notif], style=discord_components.ButtonStyle.red, id=notif
            ))

        if i == 2:
            components.append(tmp)
            i = 0
            tmp = []
        else:
            i += 1

    if len(tmp) != 0:
        components.append(tmp)

    sent_msg = await message.send_message(msg, f"""Enable or disable any timer notifications

Green: Enabled
Red: Disabled

(Press on the button to enable or disable the notification)""", title="Timer Notification Settings",
        components=components
    )

    def button_check(interaction):
        if interaction.author != msg.author:
            return False

        if interaction.message != sent_msg:
            return False

        return True

    while True:
        try:
            interaction = await bot.wait_for("button_click", timeout=120, check=button_check)
        except asyncio.TimeoutError:
            for section in components:
                for component in section:
                    component.disabled = True

            await message.edit_message(sent_msg, sent_msg.embeds[0].description, title="Timed out",
                components=components
            )
            return

        userinfo = user.load_user(msg.author.id, conn)
        userinfo.settings.timernotifs[interaction.component.id] = not userinfo.settings.timernotifs[interaction.component.id]
        user.set_user_attr(msg.author.id, "settings", userinfo.settings.cvt_dict(), conn)

        components = []
        i = 0
        tmp = []

        for notif in userinfo.settings.timernotifs.keys():
            if userinfo.settings.timernotifs[notif]:
                tmp.append(discord_components.Button(
                    label=meta.timer_names[notif], style=discord_components.ButtonStyle.green, id=notif
                ))
            else:
                tmp.append(discord_components.Button(
                    label=meta.timer_names[notif], style=discord_components.ButtonStyle.red, id=notif
                ))

            if i == 2:
                components.append(tmp)
                i = 0
                tmp = []
            else:
                i += 1

        if len(tmp) != 0:
            components.append(tmp)

        embed = discord.Embed(description=f"""Enable or disable any timer notifications

Green: Enabled
Red: Disabled

(Press on the button to enable or disable the notification)""", color=discord.Colour.purple(),
            title="Timer Notification Settings"
        )
        await interaction.respond(type=7, embed=embed, components=components)