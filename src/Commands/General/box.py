"""
Talia Discord Bot
GNU General Public License v3.0
box.py (Commands/General)

box command
"""
import asyncio
import discord_components
import random
from Utils import user, message, abc, other
from Storage import help_list

name = "box"
dm_capable = True

_boxes = {
    1: {
        "name": "Carboard Box",
        "cost": 100,
        "items": [
            {
                "name": "Torn Shirt",
                "worth": 20
            },
            {
                "name": "Broken Clock",
                "worth": 70
            },
            {
                "name": "Cracked Knife",
                "worth": 110
            },
            {
                "name": "Damaged Fishing Rod",
                "worth": 180
            },
            {
                "name": "Old Staff",
                "worth": 230
            },
            {
                "name": "Sandal",
                "worth": 310
            }
        ]
    },
    2: {
        "name": "Cargo Box",
        "cost": 750,
        "items": [
            {
                "name": "Modern Shoe",
                "worth": 590
            },
            {
                "name": "Wizard's Staff",
                "worth": 720
            },
            {
                "name": "Leather Tophat",
                "worth": 815
            },
            {
                "name": "Flowerpot",
                "worth": 890
            },
            {
                "name": "Two Bite Brownie",
                "worth": 940
            },
            {
                "name": "Paper Folder",
                "worth": 1000
            }
        ]
    },
    3: {
        "name": "Shipping Container",
        "cost": 2500,
        "items": [
            {
                "name": "Small Pistol",
                "worth": 2370
            },
            {
                "name": "Silk Plant",
                "worth": 2510
            },
            {
                "name": "Dual Barrel Shotgun",
                "worth": 2690
            },
            {
                "name": "Silver Sword",
                "worth": 2905
            },
            {
                "name": "Rabbit Hide",
                "worth": 3150
            }
        ]
    },
    4: {
        "name": "Containment Cell",
        "cost": 6000,
        "items": [
            {
                "name": "Red Blob",
                "worth": 5805
            },
            {
                "name": "Unstable Lightning",
                "worth": 6110
            },
            {
                "name": "CPU",
                "worth": 6400
            },
            {
                "name": "NaN",
                "worth": 6650
            },
            {
                "name": "Mini Boat",
                "worth": 6870
            },
            {
                "name": "Number 9 Burger",
                "worth": 7000
            }
        ]
    },
    5: {
        "name": "Vibranium Box",
        "cost": 15000,
        "items": [
            {
                "name": "Thor's Hammer",
                "worth": 14800
            },
            {
                "name": "Stormbreaker",
                "worth": 15215
            },
            {
                "name": "Famous Painting",
                "worth": 15610
            },
            {
                "name": "Broken Sky",
                "worth": 16000
            },
            {
                "name": "Ski Mountain",
                "worth": 16500
            },
            {
                "name": "Potato",
                "worth": 16980
            }
        ]
    },
    6: {
        "name": "Space Crate",
        "cost": 40000,
        "items": [
            {
                "name": "Java File",
                "worth": 38200
            },
            {
                "name": "Garbage Bag",
                "worth": 42650
            },
            {
                "name": "Planet",
                "worth": 45320
            },
            {
                "name": "Fridge",
                "worth": 47000
            },
            {
                "name": "NULL",
                "worth": 50000
            }
        ]
    }
}


async def run(bot, msg, conn):
    split_data = msg.content.split(" ")

    if len(split_data) < 2:
        await message.invalid_use(msg, help_list.box, "No operation given")
        return

    split_data[1] = split_data[1].lower()

    if split_data[1] == "buy":
        await _box_buy(bot, msg, conn, split_data)

    elif split_data[1] == "list":
        await _box_list(bot, msg)

    else:
        await message.send_error(msg, "Unknown operation")


async def _box_buy(bot, msg, conn, split_data):
    if len(split_data) < 3:
        await message.invalid_use(msg, help_list.box, "No box given")
        return

    try:
        box_id = int(split_data[2])
    except ValueError:
        await message.send_error(msg, "Invalid box ID")
        return

    if box_id not in _boxes:
        await message.send_error(msg, "There's no box with that ID")
        return

    userinfo = user.load_user(msg.author.id, conn)

    if _boxes[box_id]["cost"] > userinfo.coins:
        await message.send_error(msg, f"You don't have enough coins to buy a {_boxes[box_id]['name']}")
        return

    if len(userinfo.inventory) >= 40:
        await message.edit_message(msg, "You don't have enough space in your inventory")
        return

    emojis = other.load_emojis(bot)

    if userinfo.settings.reaction_confirm:
        sent_msg, interaction, result = await _reaction_confirm(bot, msg, box_id, emojis)
    else:
        sent_msg, interaction, result = await _button_confirm(bot, msg, box_id, emojis)

    if result is None:
        return

    if result == "cancel":
        await message.response_edit(sent_msg, interaction, sent_msg.embeds[0].description, title="Cancelled",
            from_reaction=userinfo.settings.reaction_confirm
        )
        return

    userinfo = user.load_user(msg.author.id, conn)

    if _boxes[box_id]["cost"] > userinfo.coins:
        await message.response_send(sent_msg, interaction, "You no longer have enough coins to buy this box",
            from_reaction=userinfo.settings.reaction_confirm
        )
        return

    if len(userinfo.inventory) >= 40:
        await message.response_send(sent_msg, interaction, "You no longer have enough space in your inventory",
            from_reaction=userinfo.settings.reaction_confirm
        )
        return

    user.set_user_attr(msg.author.id, "coins", userinfo.coins - _boxes[box_id]["cost"], conn)
    await message.response_edit(sent_msg, interaction,
        f"You bought a {_boxes[box_id]['name']} for {_boxes[box_id]['cost']:,} {emojis.coin}\n\n**Opening..**",
        title="Box Bought", from_reaction=userinfo.settings.reaction_confirm
    )

    await asyncio.sleep(random.randint(2, 3))

    userinfo = user.load_user(msg.author.id, conn)
    item = random.choice(_boxes[box_id]["items"])

    userinfo.inventory.append(abc.Item(item["name"], item["worth"], "box_item", {}))
    user.set_user_attr(msg.author.id, "inventory", userinfo.inventory, conn)
    await message.edit_message(sent_msg, f"You found a {item['name']} in the {_boxes[box_id]['name']}", title="Opened")


async def _box_list(bot, msg):
    fields = []
    emojis = other.load_emojis(bot)

    for box in _boxes.keys():
        fields.append([_boxes[box]["name"], f"ID: {box}\nCost: {_boxes[box]['cost']:,} {emojis.coin}"])

    await message.send_message(msg, "You can use `box info` to get detailed information about a box", title="Boxes",
        fields=fields
    )


async def _reaction_confirm(bot, msg, box_id, emojis):
    sent_msg = await message.send_message(msg,
        f"Are you sure you want to buy a {_boxes[box_id]['name']} for {_boxes[box_id]['cost']:,} {emojis.coin}",
        title="Buying.."
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


async def _button_confirm(bot, msg, box_id, emojis):
    sent_msg = await message.send_message(msg,
        f"Are you sure you want to buy a {_boxes[box_id]['name']} for {_boxes[box_id]['cost']:,} {emojis.coin}",
        title="Buying..", components=[[
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