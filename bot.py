#!/usr/bin/env py3
import asyncio
from typing import Optional
from datetime import datetime, timedelta, date, timezone, time
import discord
import json
from discord.ext import commands
from discord import app_commands
from typing import Literal, Optional
from discord.ext import commands
from discord.ext.commands import Greedy, Context
import requests
from discord import *
import gspread
from google.oauth2.service_account import Credentials


with open("config.json", "r") as read: # Imports config json file
    config_json = json.load(read)

with open("metrics.json", "r") as read: # Imports metrics json file
    metrics_list = json.load(read)

# Static variables

token = config_json["token"]

home_server_ID = int(config_json["homeserver_id"])

status = str(config_json["status"])

prefix = config_json["prefix"]

WOM_key = str(config_json["WOM_key"])

WOM_group = int(config_json["WOM_group"])

moderator_role_IDs = config_json["moderator_role_ids"]
moderator_role_IDs = [int(m) for m in moderator_role_IDs] # Making sure they are ints

drops_channel_id = int(config_json["drops_channel_id"])

denied_drop_channel_id = int(config_json["denied_drop_channel_id"])

clan_member_id = int(config_json["clan_member_id"]) # ID of the clan member role

max_amount_points_per_drop = int(config_json["max_amount_points_per_drop"])

google_spreadsheet_id = str(config_json["google_spreadsheet_id"])

google_service_account_json = str(config_json["google_service_account_json"])

google_sheet_worksheet_name = str(config_json["google_sheet_worksheet_name"])


# Enable intents
intents = discord.Intents.all()
intents.members = True

# Logging in to the bot

bot = commands.Bot(command_prefix=prefix,activity=discord.Activity(type=discord.ActivityType.playing), name=status, intents=intents)


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=home_server_ID)
        await self.tree.sync(guild=home_server_ID)


#def GoogleSheetExport:
    # Code to export data to Google Sheets


@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))

# Use ServiceAccountCredentials to create gspread client
gc = gspread.service_account(f"Google Service Account/{google_service_account_json}")

def ExportToGoogleSheets(rsn,
                         name_of_drop,
                         screenshot_url,
                         points_given,
                         discord_id,
                         Date_of_drop,
                         Discord_link_to_submission):

    """
    Exports data to a Google Sheet using gspread.

    Args:
        rsn (str): RSN of the player.
        name_of_drop (str): Name of the dropped item.
        screenshot_url (str): URL of the screenshot.
        points_given (float): Points awarded for the drop.
        discord_id (str): Discord ID of the player.
        date_of_drop (str): Date of the drop in YYYY-MM-DD format.
        discord_link_to_submission (str): Discord link to the submission.
    """

    spreadsheet = gc.open_by_key(google_spreadsheet_id)
    worksheet = spreadsheet.google_sheet_worksheet_name

    Export = [
        rsn,
        name_of_drop,
        screenshot_url,
        points_given,
        discord_id,
        Date_of_drop,
        Discord_link_to_submission
    ]

    worksheet.append_rows(Export)

def ConvertEmbedToData(posted_message : MessageType.default):

    embed_fields = posted_message.embeds[0].fields

    data = {}

    # Loop through each field and add it to the list
    for field in embed_fields:
        if field["Discord IDs"]:
            user_id_list = (field["Discord IDs"]).split(",")
            user_id_list = [user_id.strip() for user_id in user_id_list]
        else:
            data[field.name] = field.value

    return data

    #for clannie in data["Clannies"]







@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):

    if payload.member == bot.user: # Ignores the bots own messages
        return


    if payload.channel_id != drops_channel_id: # Ignores reaction if not in posted drops channel
        return


    if (payload.emoji.name != "✅") and (payload.emoji.name != "❌"): # Ignores any emoji that do not correspond to these two
        return


    if payload.member.top_role.id not in moderator_role_IDs: # Ignores reaction if not a moderator role
        return


    guild = bot.get_guild(payload.guild_id)
    drops_channel = bot.get_channel(drops_channel_id) # #logs channel


    if payload.emoji.name == '✅':
        posted_drop = await drops_channel.fetch_message(payload.message_id)
        data = ConvertEmbedToData(posted_drop)
        await posted_drop.clear_reactions()
        await drops_channel.send(f"Drop approved by <@{payload.member.id}>")


        

        #GoogleSheetExport


    if payload.emoji.name == '❌':
        posted_drop = await drops_channel.fetch_message(payload.message_id)
        denied_drop_channel = await drops_channel.fetch_message(denied_drop_channel_id)
        await denied_drop_channel.send(content=posted_drop.content, embed=posted_drop.embeds[0] if posted_drop.embeds else None)
        await posted_drop.delete()






# The rename decorator allows us to change the display of the parameter on Discord.
# In this example, even though we use `text_to_send` in the code, the client will use `text` instead.
# Note that other decorators will still refer to it as `text_to_send` in the code.
@bot.tree.command()
@app_commands.rename(text_to_send='text')
@app_commands.describe(text_to_send='Text to send in the current channel')
async def send(interaction: discord.Interaction, text_to_send: str):
    """Sends the text into the current channel."""
    await interaction.response.send_message(text_to_send)

@bot.tree.command()
@commands.has_any_role(*[clan_member_id])
async def submit_drop(interaction: discord.Interaction,
                       username: str,
                       drop_name: str,
                       drop_value: int,
                       screenshot: Optional[discord.Attachment] = None,
                       screenshot_url: Optional[str] = None,
                       non_clanmates: int = 0,
                       note: Optional[str] = ""):
    """
    This function handles the submit-drop slash command.

    Args:
        interaction (discord.Interaction): The interaction object representing the command invocation.
        username (str): The username of the player who got the drop.
        drop_name (str): The name of the dropped item.
        drop_value: (int) The estimated value of the drop.
        screenshot (discord.Attachment, optional): An attached screenshot of the drop (mutually exclusive with screenshot_url). Defaults to None.
        screenshot_url (str, optional): A URL to a screenshot of the drop (mutually exclusive with screenshot). Defaults to None.
        non_clanmates (int, optional): The number of non-clanmates present during the drop. Defaults to 0.
    """

    # Input validation (ensure only one screenshot option is provided)
    if screenshot and screenshot_url:
        await interaction.response.send_message("Please provide only one screenshot option (attachment OR URL, not both)")
        return
    
    # Validate that non_clanmates is a whole non-negative number
    if not isinstance(non_clanmates, int) or non_clanmates < 0:
        await interaction.response.send_message("Invalid number of non-clanmates. Please provide a non-negative number.")
        return

    # Validate that non_clanmates is a whole non-negative number
    if not isinstance(drop_value, int) or drop_value < 0:
        await interaction.response.send_message("Invalid drop value. Please provide a non-negative number.")
        return


    # Check for mentions and usernames
    mentioned_users_objects = []
    mentioned_users_ids = []
    nicknames = []
    for word in username.split():
        if word.startswith("<@"):
            try:
                user_id = int(word[2:-1])
                mentioned_user = interaction.guild.get_member(user_id)
                if mentioned_user:
                    mentioned_users_objects.append(mentioned_user)
                    mentioned_users_ids.append(str(mentioned_user.id))
                    nicknames.append(mentioned_user.nick if mentioned_user.nick else mentioned_user.name)  # Add nickname or username
            except (ValueError, discord.HTTPException):
                pass


    # Check if any usernames or mentions were found
    if not mentioned_users_objects:
        await interaction.response.send_message("Please provide mentioned usernames only.")
        return

    if non_clanmates >= 1:
        drop_value = round(drop_value,1)
        points_each = round((drop_value / (len(mentioned_users_objects) + non_clanmates)),1)
        if points_each > max_amount_points_per_drop:
            points_each = max_amount_points_per_drop
    elif non_clanmates == 0:
        drop_value = round(drop_value,1)
        points_each = round((drop_value / len(mentioned_users_objects)),1)
        if points_each > max_amount_points_per_drop:
            points_each = max_amount_points_per_drop # Caps points per drop to max amount of points 
    else:
        await interaction.response.send_message("Unspecified error occured with non_clanmates variable. Please contact your administrator.")
        return


    author_object = interaction.guild.get_member(interaction.user.id)
    nicknames_string =  ', '.join(nicknames)

    if len(mentioned_users_objects) == 1:
        # Build the embed message
        embed = discord.Embed(title=f"{author_object.nick} drop submission", color=0x00ffff)
        embed.add_field(name='Value', value=f'{drop_value}')
        embed.add_field(name='Clannies', value=f'{nicknames_string}')
        embed.add_field(name='Drop name', value=f'{drop_name}')
        embed.add_field(name='Points each', value=f'{points_each}')
        if note:
            embed.add_field(name='Notes', value=f'{note}')
        embed.add_field(name='Discord IDs', value=', '.join(mentioned_users_ids))

    elif len(mentioned_users_objects) > 1:
        embed = discord.Embed(title=f"{author_object.nick} drop submission", color=0x00ffff)
        embed.add_field(name='Value', value=f'{drop_value}')
        embed.add_field(name='Clannies', value=f'{nicknames_string}')
        embed.add_field(name='Drop name', value=f'{drop_name}')
        embed.add_field(name='Points each', value=f'{points_each}')
        embed.add_field(name="Non-Clanmates", value=f'{non_clanmates}')
        if note:
            embed.add_field(name='Notes', value=f'{note}')
        embed.add_field(name='Discord IDs', value=', '.join(mentioned_users_ids))




    if screenshot:
        embed.set_image(url=screenshot.url)  # Use attachment url for image
    elif screenshot_url:
        embed.set_image(url=screenshot_url)

    # Send the embed message in the drop channel
    drops_channel = bot.get_channel(drops_channel_id) # #logs channel
    posted_drop_message = await drops_channel.send(embed=embed)
    await posted_drop_message.add_reaction('✅')
    await posted_drop_message.add_reaction('❌')
    await interaction.response.send_message(f"Successfully posted drop! Please wait for a staff member to approve it. View your drop here: https://discord.com/channels/1116473389817802884/1234688342935732235/{posted_drop_message.id}")




@bot.tree.command(name="create_competition")
@commands.guild_only()
@commands.has_any_role(*moderator_role_IDs)
async def create_competition(interaction: discord.Interaction,
                                  competition_name: str,
                                  start_date: str,
                                  metric: str,
                                  duration: Optional[int] = 7):
    """
    This function handles the create_competition slash command.

    Args:
        interaction (discord.Interaction): The interaction object representing the command invocation.
        competition_name (str): The title of the competition on WOM.
        metric (str): The metric the competition will be on. Example: EHB, General Graardor, Tombs of Amascut, Theatre of Blood
        start_date: (str) The start date in YYYY-MM-DD format. Automatically starts at 12AM ET and ends at 12AM ET the next week (unless a custom duration is specified)
    """

    if metric not in metrics_list:
        await interaction.response.send_message(f"Invalid metric `{metric}`. Please use one of the following metrics: {metrics_list}")
        return


    # Convert the string to a date object
    try:
        midnight = time(hour=0, minute=0)
        # Parse the date string
        date_part = datetime.strptime(start_date, "%Y-%m-%d").date()
        # Create a timezone-aware datetime object for 12:00 AM ET on that date
        eastern_time = timezone(timedelta(hours=-4))  # ET is UTC-4
        start_date_datetime = datetime.combine(date_part, midnight, eastern_time)

        competition_duration = timedelta(days=duration)

        end_date_datetime = start_date_datetime + competition_duration

        # Convert datetimes to string for use in JSON response
        start_date_str = start_date_datetime.isoformat()
        end_date_str = end_date_datetime.isoformat()

        # Convert datetime to Eastern time readable format
        formatted_start_date = start_date_datetime.strftime("%Y-%m-%d %H:%M")
        formatted_end_date = start_date_datetime.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD format.", ephemeral=True)
        return


    base_url = "https://api.wiseoldman.net/v2/competitions"

    request_body = {
        "title": competition_name,
        "metric": metric,
        "startsAt": start_date_str,
        "endsAt": end_date_str,
        "groupId": WOM_group,
        "groupVerificationCode": WOM_key
    }

    # Set headers (optional, can be used for authentication)
    headers = {
        "Content-Type": "application/json"
    }

    # Send the POST request
    response = requests.post(base_url, json=request_body, headers=headers)


    # Check for successful response
    if response.status_code == 201:
        # Process the response data

        data = response.json()
        competition_id = data["competition"]["id"]

        embed = discord.Embed(title=f"Competition under Marina created ✅", description=f"Name of the competition: {competition_name}\n Skill/Boss: {metric} \n Start date: {formatted_start_date} ET \n End date: {formatted_end_date} ET \n Link to the competition: https://wiseoldman.net/competitions/{competition_id}", color=0x00ffff)


        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f"Error creating competition: {response.status_code} - {response.text}")

# Bot commands
@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(
  ctx: Context, guilds: Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")



bot.run(token)

# https://gist.github.com/AbstractUmbra/a9c188797ae194e592efe05fa129c57f




