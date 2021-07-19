"""
Talia Discord Bot
GNU General Public License v3.0
company.py (Commands/General)

company command
"""
import asyncio
import datetime
import discord
import discord_components
from Utils import user, company, message, abc, other
from Storage import help_list

name = "company"
dm_capable = True


async def run(args, bot, msg, conn, guildinfo, userinfo):
    if len(args) < 2:
        await message.invalid_use(msg, help_list.company, "No operation given")
        return

    args[1] = args[1].lower()

    if args[1] == "create":
        await _company_create(args, msg, conn, userinfo)
    elif args[1] == "leave":
        await _company_leave(msg, conn, userinfo)
    elif args[1] == "invite":
        await _company_invite(args, bot, msg, conn, userinfo)
    elif args[1] == "kick":
        await _company_kick(args, bot, msg, conn, userinfo)
    elif args[1] == "disband":
        await _company_disband(bot, msg, conn, userinfo)
    elif args[1] == "info":
        await _company_info(args, bot, msg, conn, userinfo)
    elif args[1] == "upgrade":
        await _company_upgrade(bot, msg, conn, userinfo)
    else:
        await message.send_error(msg, f"Unknown operation: {args[1]}")


async def _company_create(args, msg, conn, userinfo):
    if len(args) < 3:
        await message.invalid_use(msg, help_list.company, "No company name given")
        return

    if userinfo.company is not None:
        await message.send_error(msg, "You're already in a company")
        return

    company_name = " ".join(args[2:])

    if len(company_name) > 64:
        await message.send_error(msg, "The company name can't be longer than 64 characters")
        return

    existing_company = company.load_company(company_name.lower(), conn)

    if existing_company is not None:
        await message.send_error(msg, "There's already a company with that name")
        return

    new_company = abc.Company(company_name.lower())
    new_company.name = company_name
    new_company.ceo = msg.author.id
    new_company.members[str(msg.author.id)] = datetime.datetime.now().strftime("%Y/%m/%d")
    new_company.date_created = datetime.datetime.now().strftime("%Y/%m/%d")

    company.write_company(new_company, conn, False)
    user.set_user_attr(msg.author.id, "company", new_company.discrim, conn)
    await message.send_message(msg, f"You created a new company: {new_company.name}", title="Company created")


async def _company_leave(msg, conn, userinfo):
    if userinfo.company is None:
        await message.send_error(msg, "You aren't in a company")
        return

    companyinfo = company.load_company(userinfo.company, conn)

    if companyinfo.ceo == msg.author.id:
        await message.send_error(msg,
            "You're the CEO of the company\nIf you want to leave, you have to disband the company"
        )
        return

    del companyinfo.members[str(msg.author.id)]
    company.set_company_attr(userinfo.company, "members", companyinfo.members, conn, False)
    user.set_user_attr(msg.author.id, "company", None, conn)
    await message.send_message(msg, f"You left {companyinfo.name}")


async def _company_invite(args, bot, msg, conn, userinfo):
    if len(args) < 3:
        await message.invalid_use(msg, help_list.company, "No user given")
        return

    if userinfo.company is None:
        await message.send_error(msg, "You aren't in a company")
        return

    companyinfo = company.load_company(userinfo.company, conn)

    if companyinfo.ceo != msg.author.id:
        await message.send_error(msg, "You aren't the CEO of the company")
        return

    if len(companyinfo.members) >= 50:
        await message.send_error(msg, "You've reached the limit of 50 company members")
        return

    args[2] = args[2].replace("<@", "").replace("!", "").replace(">", "")

    try:
        person_id = int(args[2])
    except ValueError:
        await message.send_error(msg, "Invalid user")
        return

    if person_id == msg.author.id:
        await message.send_error(msg, "You can't invite yourself to a company")
        return
    else:
        try:
            person = await user.load_user_obj(bot, int(args[2]))
        except discord.NotFound:
            await message.send_error(msg, "I can't find that person")
            return
        except discord.HTTPException:
            await message.send_error(msg, "An error occurred and the command couldn't be run")
            return

    if person.bot:
        await message.send_error(msg, "I can't invite a bot to the company")
        return

    personinfo = user.load_user(person.id, conn)

    if personinfo.company is not None:
        await message.send_error(msg, f"{str(person)} is already in a company")
        return

    if str(msg.author.id) in companyinfo.invites:
        await message.send_error(msg, f"{str(person)} has already been invited to the company")
        return

    try:
        sent_msg = await message.send_message(None, f"You've been invited to join {companyinfo.name}", title="Invite",
            channel=person, components=[[
                discord_components.Button(label="Accept", style=discord_components.ButtonStyle.green),
                discord_components.Button(label="Decline", style=discord_components.ButtonStyle.red)
            ]]
        )
    except discord.Forbidden:
        await message.send_error(msg, f"{str(person)} can't receive DMs from me")
        return

    await message.send_message(msg, f"{str(person)} has been invited to join {companyinfo.name}")

    companyinfo.invites.append(person.id)
    company.set_company_attr(userinfo.company, "invites", companyinfo.invites, conn)

    def button_check(interaction):
        if interaction.author != person:
            return False

        if interaction.message != sent_msg:
            return False

        return True

    try:
        interaction = await bot.wait_for("button_click", timeout=300, check=button_check)
    except asyncio.TimeoutError:
        userinfo = user.load_user(msg.author.id, conn)

        if userinfo.company is not None:
            companyinfo = company.load_company(userinfo.company, conn)

            if companyinfo is not None:
                companyinfo.invites.remove(person.id)
                company.set_company_attr(companyinfo.discrim, "invites", companyinfo.invites, conn)

                if userinfo.settings.notifs["company_invites"]:
                    try:
                        await message.send_message(None, f"{str(person)} didn't respond to the invite",
                            channel=msg.author
                        )
                    except discord.Forbidden:
                        pass

        await message.timeout_response(sent_msg)
        return

    if interaction.component.label == "Decline":
        userinfo = user.load_user(msg.author.id, conn)

        if userinfo.company is not None:
            companyinfo = company.load_company(userinfo.company, conn)

            if companyinfo is not None:
                companyinfo.invites.remove(person.id)
                company.set_company_attr(companyinfo.discrim, "invites", companyinfo.invites, conn)

                if userinfo.settings.notifs["company_invites"]:
                    try:
                        await message.send_message(None, f"{str(person)} declined the invite", channel=msg.author)
                    except discord.Forbidden:
                        pass

        await message.response_edit(sent_msg, interaction, sent_msg.embeds[0].description, title="Declined")
        return

    userinfo = user.load_user(msg.author.id, conn)

    companyinfo.invites.remove(person.id)
    company.set_company_attr(companyinfo.discrim, "invites", companyinfo.invites, conn)

    if userinfo.company is None:
        await message.response_edit(sent_msg, interaction, sent_msg.embeds[0].description, title="Invite")
        try:
            await message.send_error(None, "There was a problem with joining the company", channel=person)
        except discord.Forbidden:
            pass
        return

    personinfo = user.load_user(person.id, conn)

    if personinfo.company is not None:
        await message.response_edit(sent_msg, interaction, sent_msg.embeds[0].description, title="Invite")
        if userinfo.settings.notifs["company_invites"]:
            try:
                await message.send_error(None, f"{str(person)} joined another company", channel=msg.author)
            except discord.Forbidden:
                pass
        try:
            await message.send_error(None, "You're already in a company", channel=person)
        except discord.Forbidden:
            pass
        return

    companyinfo = company.load_company(userinfo.company, conn)

    if companyinfo is None:
        await message.response_edit(sent_msg, interaction, sent_msg.embeds[0].description, title="Invite")
        try:
            await message.send_error(None, "There was a problem with joining the company", channel=person)
        except discord.Forbidden:
            pass
        return

    if len(companyinfo.members) >= 50:
        await message.response_edit(sent_msg, interaction, sent_msg.embeds[0].description, title="Invite")
        try:
            await message.send_error(None, "The company no longer has enough space for you", channel=person)
        except discord.Forbidden:
            pass
        return

    companyinfo.members[str(person.id)] = datetime.datetime.now().strftime("%Y/%m/%d")
    user.set_user_attr(person.id, "company", companyinfo.discrim, conn, False)
    company.set_company_attr(companyinfo.discrim, "members", companyinfo.members, conn)

    await message.response_edit(sent_msg, interaction, "You joined the company", title="Joined")

    if userinfo.settings.notifs["company_invites"]:
        try:
            await message.send_message(None, f"{str(person)} joined the company", channel=msg.author)
        except discord.Forbidden:
            pass


async def _company_kick(args, bot, msg, conn, userinfo):
    if len(args) < 3:
        await message.invalid_use(msg, help_list.company, "No user given")
        return

    if userinfo.company is None:
        await message.send_error(msg, "You're not in a company")
        return

    companyinfo = company.load_company(userinfo.company, conn)

    if companyinfo.ceo != msg.author.id:
        await message.send_error(msg, "You're not the CEO")
        return

    try:
        person_id = int(args[2])
    except ValueError:
        await message.send_error(msg, "Invalid user")
        return

    if person_id == msg.author.id:
        await message.send_error(msg, "You can't kick yourself")
        return
    else:
        try:
            person = await user.load_user_obj(bot, int(args[1]))
        except discord.NotFound:
            await message.send_error(msg, "I can't find that person")
            return
        except discord.HTTPException:
            await message.send_error(msg, "An error occurred and the command couldn't be run")
            return

    if person.bot:
        await message.send_error(msg, f"{str(person)} isn't in the company")
        return

    if str(person.id) not in companyinfo.members.key():
        await message.send_error(msg, f"{str(person)} isn't in the company")
        return

    personinfo = user.load_user(person.id, conn)

    del companyinfo.members[str(person.id)]
    company.set_company_attr(companyinfo.discrim, "members", companyinfo.members, conn, False)
    user.set_user_attr(person.id, "company", None, conn)

    await message.send_message(msg, f"{str(person)} has been kicked from the company")

    if personinfo.settings.notifs:
        try:
            await message.send_message(None, f"You've been kicked from {companyinfo.name}", channel=person)
        except discord.Forbidden:
            pass


async def _company_disband(bot, msg, conn, userinfo):
    if userinfo.company is None:
        await message.send_error(msg, "You're not in a company")
        return

    companyinfo = company.load_company(userinfo.company, conn)

    if companyinfo.ceo != msg.author.id:
        await message.send_error(msg, "You're not the CEO")
        return

    if userinfo.settings.reaction_confirm:
        sent_msg, interaction, result = await _company_disband_reaction_confirm(bot, msg, companyinfo)
    else:
        sent_msg, interaction, result = await _company_disband_button_confirm(bot, msg, companyinfo)

    if result is None:
        return

    if result == "cancel":
        await message.response_edit(sent_msg, interaction, sent_msg.embeds[0].description, title="Cancelled",
            from_reaction=userinfo.settings.reaction_confirm
        )
        return

    companyinfo = company.load_company(companyinfo.discrim, conn)

    if companyinfo is None:
        await message.response_send(sent_msg, interaction, "The company no longer exists",
            from_reaction=userinfo.settings.reaction_confirm
        )
        return

    cur = conn.cursor()
    cur.execute("DELETE FROM companies WHERE discrim = %s", (companyinfo.discrim,))
    cur.execute("UPDATE users SET company = NULL WHERE company = %s", (companyinfo.discrim,))
    conn.commit()

    await message.response_edit(sent_msg, interaction, "Company disbanded", title="Disbanded",
        from_reaction=userinfo.settings.reaction_confirm
    )


async def _company_info(args, bot, msg, conn, userinfo):
    if len(args) < 3:
        if userinfo.company is None:
            await message.send_error(msg, "You're not in a company")
            return

        args.append(userinfo.company)

    companyinfo = company.load_company(args[2].lower(), conn)

    if companyinfo is None:
        await message.send_error(msg, "I can't find that company")
        return

    total_coins = 0
    for member in companyinfo.members.keys():
        memberinfo = user.load_user(int(member), conn)
        if memberinfo is not None:
            total_coins += memberinfo.coins

    try:
        ceo = await user.load_user_obj(bot, companyinfo.ceo)
    except discord.NotFound:
        ceo = companyinfo.ceo
    except discord.HTTPException:
        ceo = companyinfo.ceo

    emojis = other.load_emojis(bot)

    await message.send_message(msg, f"""**Level {companyinfo.level}**

CEO: {str(ceo)}
Total Coins: {total_coins:,} {emojis.coin}
Members: {len(companyinfo.members)}/50
Company Multiplier: x{companyinfo.multiplier}""", title=companyinfo.name)


async def _company_upgrade(bot, msg, conn, userinfo):
    if userinfo.company is None:
        await message.send_error(msg, "You're not in a company")
        return

    companyinfo = company.load_company(userinfo.company, conn)

    if companyinfo.ceo != msg.author.id:
        await message.send_error(msg, "You're not the CEO")
        return

    if companyinfo.level == 1:
        cost = 40000
        members = 4
    elif companyinfo.level == 2:
        cost = 300000
        members = 10
    elif companyinfo.level == 3:
        cost = 1000000
        members = 20
    elif companyinfo.level == 4:
        cost = 10000000
        members = 40
    else:
        await message.send_error(msg, f"The company has already reached level 5")
        return

    if members > len(companyinfo.members.keys()):
        await message.send_error(msg, f"The company doesn't have enough members to upgrade\nNeeds {members} members")
        return

    if cost > userinfo.coins:
        await message.send_error(msg, "You don't have enough coins to upgrade the company")
        return

    emojis = other.load_emojis(bot)
    original_level = companyinfo.level

    if userinfo.settings.reaction_confirm:
        sent_msg, interaction, result = await _company_upgrade_reaction_confirm(bot, msg, cost, emojis, companyinfo)
    else:
        sent_msg, interaction, result = await _company_upgrade_button_confirm(bot, msg, cost, emojis, companyinfo)

    if result is None:
        return

    if result == "cancel":
        await message.response_edit(sent_msg, interaction, sent_msg.embeds[0].description, title="Cancelled",
            from_reaction=userinfo.settings.reaction_confirm
        )
        return

    userinfo = user.load_user(msg.author.id, conn)

    if userinfo.company is None:
        await message.response_send(sent_msg, interaction, "You're no longer in a company",
            from_reaction=userinfo.settings.reaction_confirm
        )
        return

    if cost > userinfo.coins:
        await message.response_send(sent_msg, interaction, "You no longer have enough coins to upgrade the company",
            from_reaction=userinfo.settings.reaction_confirm
        )
        return

    companyinfo = company.load_company(userinfo.company, conn)

    if companyinfo.ceo != msg.author.id:
        await message.response_send(sent_msg, interaction, "You're no longer the CEO",
            from_reaction=userinfo.settings.reaction_confirm
        )
        return

    if original_level != companyinfo.level:
        await message.response_send(sent_msg, interaction, "The company level has changed",
            from_reaction=userinfo.settings.reaction_confirm
        )
        return

    if members > len(companyinfo.members.keys()):
        await message.response_send(sent_msg, interaction, "The company no longer has enough members to upgrade",
            from_reaction=userinfo.settings.reaction_confirm
        )
        return

    company.set_company_attr(companyinfo.discrim, "multiplier", round(companyinfo.multiplier + 0.1, 1), conn, False)
    company.set_company_attr(companyinfo.discrim, "level", companyinfo.level + 1, conn, False)
    user.set_user_attr(msg.author.id, "coins", userinfo.coins - cost, conn)

    await message.response_edit(sent_msg, interaction, f"You upgraded the company to level {companyinfo.level + 1}",
        title="Upgraded", from_reaction=userinfo.settings.reaction_confirm
    )


async def _company_disband_reaction_confirm(bot, msg, companyinfo):
    sent_msg = await message.send_message(msg, f"Are you sure you want to disband {companyinfo.name}",
        title="Disbanding.."
    )

    await sent_msg.add_reaction("\u2705")
    await sent_msg.add_reaction("\u274c")

    def reaction_check(reaction, reaction_user):
        if reaction_user != msg.author:
            return False

        if reaction.message != sent_msg:
            return False

        if str(reaction.emoji) != "\u2705" and str(reaction.emoji) != "\u274c":
            return False

        return True

    try:
        reaction, reaction_user = await bot.wait_for("reaction_add", timeout=120, check=reaction_check)
    except asyncio.TimeoutError:
        await message.timeout_response(sent_msg, from_reaction=True)
        return None, None, None

    if str(reaction.emoji) == "\u2705":
        return sent_msg, None, "confirm"
    else:
        return sent_msg, None, "cancel"


async def _company_disband_button_confirm(bot, msg, companyinfo):
    sent_msg = await message.send_message(msg, f"Are you sure you want to disband {companyinfo.name}",
        title="Disbanding..", components=[[
            discord_components.Button(label="Confirm", style=discord_components.ButtonStyle.green),
            discord_components.Button(label="Cancel", style=discord_components.ButtonStyle.red)
        ]]
    )

    def button_check(interaction):
        if interaction.author != msg.author:
            return False

        if interaction.message != sent_msg:
            return False

        return True

    try:
        interaction = await bot.wait_for("button_click", timeout=120, check=button_check)
    except asyncio.TimeoutError:
        await message.timeout_response(sent_msg)
        return None, None, None

    if interaction.component.label == "Confirm":
        return sent_msg, interaction, "confirm"
    else:
        return sent_msg, interaction, "cancel"


async def _company_upgrade_reaction_confirm(bot, msg, cost, emojis, companyinfo):
    sent_msg = await message.send_message(msg,
        f"Are you sure you want to spend {cost:,} {emojis.coin} to upgrade {companyinfo.name} to level {companyinfo.level + 1}",
        title="Upgrading.."
    )

    await sent_msg.add_reaction("\u2705")
    await sent_msg.add_reaction("\u274c")

    def reaction_check(reaction, reaction_user):
        if reaction_user != msg.author:
            return False

        if reaction.message != sent_msg:
            return False

        if str(reaction.emoji) != "\u2705" and str(reaction.emoji) != "\u274c":
            return False

        return True

    try:
        reaction, reaction_user = await bot.wait_for("reaction_add", timeout=120, check=reaction_check)
    except asyncio.TimeoutError:
        await message.timeout_response(sent_msg, from_reaction=True)
        return None, None, None

    if str(reaction.emoji) == "\u2705":
        return sent_msg, None, "confirm"
    else:
        return sent_msg, None, "cancel"


async def _company_upgrade_button_confirm(bot, msg, cost, emojis, companyinfo):
    sent_msg = await message.send_message(msg,
        f"Are you sure you want to spend {cost:,} {emojis.coin} to upgrade {companyinfo.name} to level {companyinfo.level + 1}",
        title="Upgrading..", components=[[
            discord_components.Button(label="Confirm", style=discord_components.ButtonStyle.green),
            discord_components.Button(label="Cancel", style=discord_components.ButtonStyle.red)
        ]]
    )

    def button_check(interaction):
        if interaction.author != msg.author:
            return False

        if interaction.message != sent_msg:
            return False

        return True

    try:
        interaction = await bot.wait_for("button_click", timeout=120, check=button_check)
    except asyncio.TimeoutError:
        await message.timeout_response(sent_msg)
        return None, None, None

    if interaction.component.label == "Confirm":
        return sent_msg, interaction, "confirm"
    else:
        return sent_msg, interaction, "cancel"