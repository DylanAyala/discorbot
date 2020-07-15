import discord
import youtube_dl
from discord.ext import commands
import os
from discord.utils import get
import time

client = commands.Bot(command_prefix='$')
players= {}

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.command(pass_context=True)
async def hola(ctx):
    await ctx.channel.send('{0.author.mention}\nWrong text channel\nUse '.format(ctx))

@client.command(pass_context=True)
async def gato(ctx):
    await ctx.channel.send('<@355496877241794560>', file=discord.File('audio/capi.mp3', 'capi.mp3'))

@client.command(pass_context=True)
async def gatoa(ctx):
    voice = await ctx.message.author.voice.channel.connect()
    await voice.play(discord.FFmpegPCMAudio("audio/capi.mp3"))
    time.sleep(5)
    await voice.disconnect()

@client.command(pass_context=True)        
async def all(ctx):
    await ctx.channel.send('@everyone', file=discord.File('audio/allp.mp3', 'allp.mp3'))

@client.command(pass_context=True)        
async def all2(ctx):
    voice = await ctx.message.author.voice.channel.connect()
    voice.play(discord.FFmpegPCMAudio("audio/allp.mp3"))
    time.sleep(5)
    await voice.disconnect()
    

@client.command(pass_context=True)        
async def play(ctx, url):
    song_there = os.path.isfile("song.mp3")
    try:
        if song_there:
            os.remove("song.mp3")
    except PermissionError:
        await ctx.send("Wait for the current playing music end or use the 'stop' command")
        return
    voice = await ctx.message.author.voice.channel.connect()
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            os.rename(file, 'song.mp3')
    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            os.rename(file, 'song.mp3')
    voice.play(discord.FFmpegPCMAudio("song.mp3"))
    #voice.is_playing()
   
client.run('t')