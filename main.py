import discord

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message, *args):
    if message.author == client.user:
        return

    if message.content.startswith('$hola'):
        await message.channel.send('{0.author.mention}\nWrong text channel\nUse '.format(message))

    if message.content.startswith('$gato'):
        await message.channel.send('<@355496877241794560>', file=discord.File('capi.mp3', 'capi.mp3'))
        
    if message.content.startswith('$all'):
        await message.channel.send('@everyone', file=discord.File('allp.mp3', 'allp.mp3'))
    
    if message.content.startswith('$audio'):
        voice_player = await message.author.voice.channel.connect()
       
        print("Playing chulp")
        voice_player.play(discord.FFmpegPCMAudio(executable="D:\\proyectos\\discord\\capi.mp3", source="capi.mp3"))

client.run('')