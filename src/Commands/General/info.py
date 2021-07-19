"""
Talia Discord Bot
GNU General Public License v3.0
info.py (Commands/General)

info command
"""
import discord
from Utils import user, company, message, other

name = "info"
dm_capable = True

_edu_levels = {
    1: "Elementary",
    2: "Highschool",
    3: "College",
    4: "PhD"
}


async def run(args, bot, msg, conn):
    if len(args) < 2:
        args.append(str(msg.author.id))
    else:
        args[1] = args[1].replace("<@", "").replace("!", "").replace(">", "")

    try:
        person_id = int(args[1])
    except ValueError:
        await message.send_error(msg, "Invalid user")
        return

    if person_id == msg.author.id:
        person = msg.author
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
        await message.send_error(msg, "I can't get the information of a bot")
        return

    personinfo = user.load_user(person.id, conn)

    partner, parents, children = await _load_family_info(bot, personinfo)
    jobinfo = _load_job_info(personinfo.job)
    pickaxeinfo = _load_pickaxe_info(personinfo.pickaxe)
    petinfo = _load_pet_info(personinfo.pet)

    if personinfo.company is not None:
        companyinfo = company.load_company(personinfo.company, conn)
        company_name = companyinfo.name
    else:
        company_name = "None"

    emojis = other.load_emojis(bot)

    if personinfo.showcase is None:
        send_str = f"**Level {personinfo.level}**"
    else:
        send_str = f"**Level {personinfo.level}**\n**{personinfo.showcase.name}**"

    fields = [
        ["**General**", f"""Coins: {personinfo.coins:,} {emojis.coin}
XP: {personinfo.xp:,}/{personinfo.level * 25:,}
Multiplier: x{other.load_multi(personinfo, conn)}
Education level: {_edu_levels[personinfo.edu_level]}
Company: {company_name}""", False],
        ["**Family**", f"""Partner: {partner}
Parents: {parents}
Children: {children}""", False],
    ]

    if jobinfo is not None:
        fields.append(["**Job**", jobinfo])

    if pickaxeinfo is not None:
        fields.append(["**Pickaxe**", pickaxeinfo])

    if petinfo is not None:
        fields.append(["**Pet**", petinfo])

    await message.send_message(msg, send_str, title=str(person), thumbnail=person.avatar_url, color=personinfo.color,
        fields=fields
    )


async def _load_family_info(bot, personinfo):
    if personinfo.partner is None:
        partner = None
    else:
        try:
            partner = await user.load_user_obj(bot, personinfo.partner)
        except discord.NotFound:
            partner = "Unknown#0000"
        except discord.HTTPException:
            partner = "Unknown#0000"

    if len(personinfo.parents) == 0:
        parents = None
    else:
        all_parents = []
        for parent in personinfo.parents:
            try:
                parent_user = await user.load_user_obj(bot, parent)
            except discord.NotFound:
                parent_user = "Unknown#0000"
            except discord.HTTPException:
                parent_user = "Unknown#0000"
            all_parents.append(str(parent_user))
        parents = ", ".join(all_parents)

    if len(personinfo.children) == 0:
        children = None
    else:
        all_children = []
        for child in personinfo.children:
            try:
                child_user = await user.load_user_obj(bot, child)
            except discord.NotFound:
                child_user = "Unknown#0000"
            except discord.HTTPException:
                child_user = "Unknown#0000"
            all_children.append(str(child_user))
        children = ", ".join(all_children)

    return partner, parents, children


def _load_job_info(job):
    if job is None:
        return None
    else:
        return f"""Job: {job.name}
Level: {job.level}
XP: {job.xp:,}/{(job.level * 25):,} ({round(job.xp / (job.level * 25) * 100)}%)"""


def _load_pickaxe_info(pickaxe):
    if pickaxe is None:
        return None
    else:
        return f"""Pickaxe: {pickaxe.name}
Mining Speed: {pickaxe.speed}
Mining Multiplier: x{pickaxe.multiplier}"""


def _load_pet_info(pet):
    if pet is None:
        return None
    else:
        return f"""Name: {pet.name}
Breed: {pet.breed} ({pet.type})"""
