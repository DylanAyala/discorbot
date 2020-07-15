import discord

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hola'):
        await message.channel.send('{0.author.mention}\nWrong text channel\nUse '.format(message))

    if message.content.startswith('$gato'):
        await message.channel.send('<@355496877241794560>', file=discord.File('capi.mp3', 'capi.mp3'))
        
    if message.content.startswith('$all'):
        print(message.channel)
        await message.channel.send('@everyone', file=discord.File('allp.mp3', 'allp.mp3'))

client.run('test')