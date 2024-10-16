import discord
from discord.ext import commands
import os
import json
import random
from time import sleep



# next update: doesn't send message to the admin already in voice channel
# Set up the bot with a command prefix
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)
update_info = {"isUpdate": False, "version": "", "message": ""}

# get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.json')

try:
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    print(f"config file not found at {config_path}")
    # handle the error (e.g., exit the script or use default values)
except json.JSONDecodeError:
    print(f"invalid json in config file at {config_path}")
    # handle the error
except Exception as e:
    print(f"error reading config file: {e}")
    # handle other potential errors

TOKEN = config['discord_token']
admins = config['admins']
channelid = config['lockin_channel_id']
vclink = config['vc_link']
sleepchid = config['sleep_channel_id']
lockchid = config['lockin_channel_id']


#patchcount = "1.3"
admin_voice_states = {}

# some bot logic
async def set_bot_status(status_message):
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.custom, name=status_message))


async def update_status():
    if admin_voice_states:
        admin_names = list(admin_voice_states.keys())

        #len logic
        if len(admin_names) == 1:
            status_message = f"{admin_names[0]} is currently locked in" # if there's only one admin in vc
        elif len(admin_names) == 2:
            status_message = f"{admin_names[0]} and {admin_names[1]} are currently locked in" # if there's two admins in vc
        else:
            status_message = f"{', '.join(admin_names[:-1])}, and {admin_names[-1]} are locked in vc" # if there's more than two admins in vc (most likely never going to a use case)
        await set_bot_status(status_message)
    else:
        await set_bot_status("locked in")


# events
@bot.event
async def on_connect():
    global patchcount, updates, update_info
    try:
        with open('patchdata.json', 'r') as f:
            data = json.load(f)
            patchcount = data['patchcount']
            updates = data.get('updates', [])
    except FileNotFoundError:
        patchcount = "1.0"
        updates = []

    # ask if it's a new patch
    isUpdate = input(f"Salutations, the latest update patch is v{patchcount}, is this a new patch? (y/n)\n")
    if isUpdate == "y":
        # ask for patch notes
        updatemsg = input(f"any notes for this new patch? press enter to skip / no notes needed\n")
        if not updatemsg:
            updatemsg = "no notes needed"
        # update the patchcount
        major, minor = patchcount.split('.')
        patchcount = f"{major}.{int(minor) + 1}"
        updates.append({"version": patchcount, "message": updatemsg})
        with open('patchdata.json', 'w') as f:
            json.dump({'patchcount': patchcount, 'updates': updates}, f)
        
        update_info["isUpdate"] = True
        update_info["version"] = patchcount
        update_info["message"] = updatemsg
    elif isUpdate == "n":
        sleep(4)
        print("Regular restart, no update patch")
        return
    else:
        print("Invalid input, please enter 'y' or 'n'")
        return


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    channel = bot.get_channel(channelid)
    if channel is None:
        print(f"warning: channel {channelid} not found!")
    else:
        print(f"successfully found channel {channel.name}")

    # send update message if it's a new patch
    if update_info["isUpdate"]:
        # logic for sending update message to the channel
        try:
            await channel.send(f"update patch: v{update_info['version']}, '{update_info['message']}'")
            await channel.send(f"dwight currently online!")
        except Exception as e:
            print(f"error sending update messages: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    #checks to see if admin joined vc
    if member.id in admins:
        if after.channel:
            admin_voice_states[member.name] = after.channel.name
        else:
            admin_voice_states.pop(member.name, None)

        await update_status()

        admin_not_in_vc = [] # sets a list for admins not in vc
        for i in admins: # iterates through the admins list to see if the member.id of the admin in the vc matches, if it doesn't it adds that id to the list
            if member.id != i:
                admin_not_in_vc.append(i)
        
        try:
            message = None  # Initialize message to None at the start
            if before.channel is None and after.channel is not None: # checks to see is voice channel state is channed aka someone joined
                # making message a variable, setting it as a message preloaded
                
                status_message = f"{member} is currently locked in"
                await set_bot_status(status_message)
                gif = None
                try:    
                    # randomize the gif
                    mainpy_path = os.path.dirname(os.path.abspath(__file__))  # set the path to the main.py file
                    gifs_dir = os.path.join(mainpy_path, "docs", "vc-noti-gifs")  # set the path to the vc-noti-gifs folder
                    random_gif = random.choice([f for f in os.listdir(gifs_dir) if f.endswith('.gif')])  # randomize the gif
                    gif_path = os.path.join(gifs_dir, random_gif)  # set the path to the random gif
                except Exception as e:
                    print(f"error loading gif: {e}")
                
                
                message = f"it's time to lock in, {member} just joined the vc."  # set the message
            
            elif before.channel is not None and after.channel is None: # checks to see if voice channel state is changed aka someone left
                # they left the vc
                await set_bot_status("locked in")
                # you might want to set a different message here
                pass

            # if there's a message aka someone joining
            if message:
                # check to see what user is in vc, and do not send to that user
                for admin_id in admin_not_in_vc: # use for loop to iterate through every admin not in vc and send it to them
                    try:
                        admin = await bot.fetch_user(admin_id)
                        if gif_path:

                            with open(gif_path, 'rb') as f:
                                gif = discord.File(f, filename = os.path.basename(gif_path))
                                await admin.send(content=message, file=gif)
                        else:
                            await admin.send(content=message)
                    except Exception as e:
                        print(f"error sending message to {admin_id}: {e}")
        except Exception as e:
            print(f"there was an error in on_voice_state_update: {e}")





# commands
@bot.command()
async def yo(ctx):
    await ctx.send(f'{ctx.author.name} stop being a doof and @ing me')

@bot.command()
async def v(ctx):
    try:
        with open('patchdata.json', 'r') as f:
            data = json.load(f)
            patchcount = data['patchcount']
    except FileNotFoundError:
        patchcount = 1.3
    await ctx.send(f'current patch: v{patchcount}')

@bot.command()
async def prevupdates(ctx):
    try:
        with open('patchdata.json', 'r') as f:
            data = json.load(f)
            patchcount = data['patchcount']
            updates = data.get('updates', [])
    except FileNotFoundError:
        patchcount = 1.3
        updates = []
    if not updates:
        await ctx.send(f'current patch: v{patchcount}, and the previous updates were {patchcount-1}./n And the previous messages were')
    else:
        message = f"current patch: v{patchcount}\n\nprevious updates:"
        for update in reversed(updates[-5:]):  # show last 5 updates in reverse order
            message += f"\nv{update['version']}: {update['message']}"
        await ctx.send(message)


@bot.command()
async def ready(ctx):
    phrases = ["hooty hoo", "i'm ready, promotion!", "WOOOOO! YEAHHHHHHHHHHHH"]
    random_phrase = random.choice(phrases)
    if random_phrase == "hooty hoo":
        gif_path = gif_path = os.path.join(os.path.dirname(__file__), "docs", "ksu.gif")
        gif = discord.File(gif_path)
        await ctx.send(random_phrase, file=gif)
    elif random_phrase == "i'm ready, promotion!":
        gif_path = gif_path = os.path.join(os.path.dirname(__file__), "docs", "promotion.gif")
        gif = discord.File(gif_path)
        await ctx.send(random_phrase, file=gif)
    elif random_phrase == "WOOOOO! YEAHHHHHHHHHHHH":
        gif_path = gif_path = os.path.join(os.path.dirname(__file__), "docs", "wooyeah.gif")
        gif = discord.File(gif_path)
        await ctx.send(random_phrase, file=gif)
        
@bot.command() # set the vc link in the config.json file
async def notify(ctx, member: discord.Member, *, message=None):
    usermessage = f"get up and lock in {member.name}"
    if message:
        usermessage += f": {message}"
    link = vclink 
    try:
        await member.send(f"{usermessage}\n{link}") # sends the message to the member
        await ctx.send(f"successfully sent a noti and a link to {member.name}")
    except discord.errors.Forbidden: # dms disabled
        await ctx.send(f"couldn't send a message to {member.name}, they might have dms disabled")
    except Exception as e:
        print(f"an error occurred: {str(e)}")
        await ctx.send(f"an error occurred while trying to send a message to {member.name}")

@bot.command()
async def sleep(ctx): #cmd to move to sleep channel
    sleepChannel = bot.get_channel(sleepchid) # gets the sleep channel
    try:
        if not ctx.author.voice: # checks to see if the user is in a vc
            await ctx.send("you're not in a voice channel")
            return
        await ctx.author.move_to(sleepChannel) # moves the user to the sleep channel
        await ctx.author.edit(deafen=True, mute=True) # deafens and mutes the user
        await ctx.send(f"you're now asleep, do '.lockin' when you're ready to lock back in")
    # error handling
    except discord.errors.Forbidden:
        await ctx.send("i dont have permission to move your voice state")
    except discord.errors.HTTPException as e:
        await ctx.send(f"an error occurred while trying to move you: {str(e)}")
    except Exception as e:
        await ctx.send(f"an error occurred: {str(e)}")

@bot.command()
async def lockin(ctx): #cmd to lockin back into vc (only works in sleep channel)
    lockinChannel = bot.get_channel(lockchid)
    if not lockinChannel: # checks to see if the lockin channel is config
        await ctx.send("the lockin channel is not found, see dwight")
        return
    try:
        # checks to see if user is in vc
        if not ctx.author.voice: # checks to see if the user is in a vc
            await ctx.send("you're not in a voice channel")
            return
        # moves the user to the lockin channel and unmutes and undeafens them
        await ctx.author.move_to(lockinChannel)
        await ctx.author.edit(deafen=False, mute=False)
        await ctx.send(f"you're now locked back in, {ctx.author.name}")
    # error handling
    except discord.errors.Forbidden:
        await ctx.send("i dont have permission to move your voice state")
    except discord.errors.HTTPException as e:
        await ctx.send(f"an error occurred while trying to move you: {str(e)}")
    except Exception as e:
        await ctx.send(f"an error occurred: {str(e)}")

@bot.command()
async def status(ctx):
    try:
        with open('patchdata.json', 'r') as f:
            data = json.load(f)
            patchcount = data['patchcount']
    except FileNotFoundError:
        patchcount = "null"
    msg = f"im currently up and online! using v{patchcount}"
    await ctx.send(msg)

bot.run(TOKEN)