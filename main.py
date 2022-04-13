import os
os.system("pip install genshinstats")
os.system("pip install pymongo[srv]")
os.system("pip install flask")
from keepAlive import keep_alive
import genshinstats as gs
import discord
from pymongo import MongoClient
from discord.ext import commands
import time
user = os.environ["user"]
password = os.environ["password"]
client = MongoClient(f"mongodb+srv://{user}:{password}@cluster0.npogp.mongodb.net/genshin?retryWrites=true&w=majority")
mydb = client['genshin']
mycollection = mydb['token']
current_discord_id = 0
bot = commands.Bot(command_prefix='!')



class genshinUtil:
    async def validAcc(account_id, cookie_token, ctx=None, discord_id=None):
          try:
            #gs.set_cookie(account_id=account_id, cookie_token=cookie_token)
            if not account_id.isdigit() or len(account_id)<6 or len(cookie_token)<15:
                raise ValueError("info như con cac")
            user = await bot.fetch_user(discord_id)
            await ctx.reply(f"Ready to use for user: {user.name}.")
            return True
          except Exception as VE:
            user = await bot.fetch_user(discord_id)
            await ctx.reply(f"Your info has some problem: {VE}, \nplease put correct,{user.name} information with discord id: {discord_id}")
          return False
    async def redeemPrimo(account_id, cookie_token, primoCode=0, ctx=None, discord_id=None):
        gs.set_cookie(account_id=account_id, cookie_token=cookie_token)
        user = await bot.fetch_user(discord_id)
        try:
            gs.redeem_code(primoCode)
            
            await ctx.channel.send(f"sucessfully claimed reward from primo-codes: {primoCode} for {user.name}")
        except Exception as e:
            await ctx.channel.send(str(e) + f"with id_discord: {discord_id} of {user.name}")
            if (str(e) == "Invalid redemption code"):
                return
        time.sleep(5)
class mongoUtil:
    async def returnDiscordProfile(user, returnOnly = False, ctx=None):
        name=""
        id=""
        discord_id=""
        for i in user:
            id = i["_id"]
            name = i["name"]
            for info in i["info"]:
                for specificInfo in info:
                    if(specificInfo=="discord_id"):
                        discord_id = info["discord_id"]
            if returnOnly == False:
                await ctx.send(f"\nid={id}, \nname={name}, \ndiscord_id={discord_id}")
        return id,name,discord_id
    async def myinfo(discord_id, returnOnly = False, ctx=None):
        mongodict = list(mongoUtil.find(discord_id=f"{discord_id}"))
        return await mongoUtil.returnDiscordProfile(mongodict, returnOnly, ctx=ctx)
    async def allinfo(ctx=None):
        return await mongoUtil.returnDiscordProfile(mycollection.find(), ctx=ctx)
    async def insert(name, discord_id, account_id, cookie_token, ctx=None):
        id=0
        for i in mycollection.find().limit(1).sort([('$natural',-1)]):
            id=i["_id"] +1
        info={
        "_id": id,
        "name": name,
        "info":[{"discord_id":discord_id},
                {"account_id":account_id},
                {"cookie_token":cookie_token}]
        
        }
        
        if await genshinUtil.validAcc(account_id=account_id, cookie_token=cookie_token, ctx=ctx, discord_id=discord_id):
            await ctx.reply("Info valid now it's in db")
        await ctx.message.delete()
        #mycollection.insert_one(info)
    async def delete(id):
        mycollection.delete_one({"_id": id})
    def deleteAll():
        mycollection.delete_many({})
    def find(id=0, discord_id="", findall=False):
        if findall==True:
                return mycollection.find()
        if id==0:
            print("There's no id.")
            if discord_id == "":
                print("Couldn't get info on this user.")
            else:
                return mycollection.find( {"info.discord_id":f"{discord_id}"} )
        else:
            return mycollection.find({"_id":id})
    async def getUserId(discord_id, ctx=None, returnOnly=False):
        id = await mongoUtil.myinfo(f"{discord_id}", returnOnly=returnOnly, ctx=ctx)
        return int(id[0])
    def updateName(discord_id,currentName):
        mycollection.update_one({"_id":mongoUtil.getUserId(discord_id=discord_id)},
        {"$set": {"name": currentName} } )
    async def returnAccountId(discord_id, ctx=None):
        id = await mongoUtil.getUserId(discord_id=discord_id, ctx=ctx, returnOnly=True)
        infoOfDiscordId = mongoUtil.find(id=id)[0]["info"]
        for i in infoOfDiscordId:
            for info in i:
                if info=="account_id":
                    return i[info]
    async def returnCookieToken(discord_id, ctx=None):
        id = await mongoUtil.getUserId(discord_id=discord_id, ctx=ctx, returnOnly=True)
        infoOfDiscordId = mongoUtil.find(id=id)[0]["info"]
        for i in infoOfDiscordId:
            for info in i:
                if info=="cookie_token":
                    return i[info]
    def returnAllDiscordId():
        discordList={}
        rtlist = mycollection.find({}, {"_id": 1, "info":{"discord_id":1} } )
        for i in rtlist:
            id=i["_id"]
            discord_id=i["info"][0]["discord_id"]
            discordList[id]=discord_id
        return discordList
thisdict = mongoUtil.returnAllDiscordId()
@bot.event
async def on_messages(message):
    current_discord_id = message.author.id
    
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send('pong')
@bot.command()
async def bùmbùm(ctx):
    await ctx.send('chéo chéo')

@bot.command()
async def hello(ctx):
    await ctx.send("Choo choo! 🚅")

@bot.command(pass_context=True)
async def info(ctx):
    #await ctx.send(ctx.author.id)
    id = ctx.author.id
    print(id)
    await mongoUtil.myinfo(discord_id=str(id), ctx=ctx)
    await ctx.send("Finished")

@bot.command()
async def info_all(ctx):
    await mongoUtil.allinfo(ctx=ctx)
    await ctx.send("Finished")

@bot.command()
async def valid_info(ctx):
    await genshinUtil.validAcc(account_id= await mongoUtil.returnAccountId(ctx.author.id, ctx=ctx), 
                               cookie_token= await mongoUtil.returnCookieToken(ctx.author.id,ctx=ctx), 
                               ctx=ctx, 
                               discord_id=ctx.author.id)

@bot.command()
async def redeem_one(ctx, *param):
    for item in param:
        if len(item)>8:
            await genshinUtil.redeemPrimo(account_id= await mongoUtil.returnAccountId(ctx.author.id, ctx=ctx),
                                          cookie_token= await mongoUtil.returnCookieToken(ctx.author.id,ctx=ctx), 
                                          primoCode=item, 
                                          ctx=ctx, 
                                          discord_id=ctx.author.id)
    await ctx.send(f"All following code:  {str(param)}")

@bot.command()
async def redeem(ctx, *param):
    for item in param:
        if len(item)>8:
            for value in thisdict:
                await genshinUtil.redeemPrimo(account_id= await mongoUtil.returnAccountId(thisdict[value], ctx=ctx),
                                          cookie_token= await mongoUtil.returnCookieToken(thisdict[value],ctx=ctx), 
                                          primoCode=item, 
                                          ctx=ctx, 
                                          discord_id=thisdict[value])
    await ctx.send(f"All following code:  {str(param)}")


@bot.command()
async def multi_param(ctx, *param):
    for item in param:
        await ctx.send(item)
    await ctx.send(f"final param content as whole:  {str(param)}")
    await ctx.send(f"type of param {str(type(param))}")

@bot.command()
async def insert(ctx, *param):
    account_id=""
    cookie_token=""
    for i in param:
        if not i.find("account_id="):
            account_id=i.split("=")[1]
        if not i.find("cookie_token="):
            cookie_token=i.split("=")[1]
    user = await bot.fetch_user(ctx.author.id)
    await mongoUtil.insert(name=user.name, discord_id=ctx.author.id, account_id=account_id, cookie_token=cookie_token, ctx=ctx)

@bot.command()
async def remove(ctx, idToRemove):
    await mongoUtil.delete(idToRemove)
    await ctx.send("Removed from database")
    
@bot.command()
async def sing(ctx):
    await ctx.send('Đà đí đa đí đu'),time.sleep(1.5),await ctx.send('Hà shí ê nố san'),time.sleep(2),await ctx.send('À nà ta gồ su ma tề ngá'),time.sleep(3),await ctx.send('A i ní'),time.sleep(1),await ctx.send('Ta ka lí'),time.sleep(1),await ctx.send('Kí la'),time.sleep(0.75),await ctx.send('Kí la'),time.sleep(0.75),await ctx.send('Mố ê tế shi mai i ta rì'),time.sleep(15),await ctx.send('Kà qua i ghế na'),time.sleep(2),await ctx.send('Kít sù nồ oăn tu thi'),time.sleep(2),await ctx.send('Mề sề un số na shi tề shu gồ y ô nế'),time.sleep(3.5),await ctx.send('Kồ tê đi đát su'),time.sleep(2),await ctx.send('Bô kù nồ ki mô chi'),time.sleep(2),await ctx.send('Mồ tê át sô mu mí tai i tề'),time.sleep(3),await ctx.send('À quỳ ca kít chà'),time.sleep(2),await ctx.send('Đa mê na nú quà'),time.sleep(2),await ctx.send('Qua ka tế ru'),time.sleep(2),await ctx.send('Đế mô mú ni sàn'),time.sleep(2),await ctx.send('Ì chì nồ hú mí ta sê bàn bồ đố nếm ma ku tề'),time.sleep(5),await ctx.send('Ka mêm qua nu ki su tề I tề'),time.sleep(4),await ctx.send('I kê nài y'),time.sleep(2),await ctx.send('Kô tô mà tê'),time.sleep(2),await ctx.send('Hai su bi gam ma chế ni rà nu'),time.sleep(7),await ctx.send('Đà đí đa đí đu'),time.sleep(2),await ctx.send('Hà shí ê nố san'),time.sleep(2),await ctx.send('À nà ta gồ su ma tề ngá'),time.sleep(3),await ctx.send('Đa ma số'),time.sleep(1),await ctx.send('Lê ta lá'),time.sleep(1),await ctx.send('Sú lế tê mố i'),time.sleep(2),await ctx.send('Mô tô phù ru qua sề tế'),time.sleep(2),await ctx.send('Mì sế tê cú rê'),time.sleep(2),await ctx.send('Mồ cú ta kế ri'),time.sleep(2),await ctx.send('Ề nga hô hù nu ma kề tế '),time.sleep(3),await ctx.send('Ai i ní'),time.sleep(1),await ctx.send('Ta ka lí'),time.sleep(1),await ctx.send('Kí la '),time.sleep(1),await ctx.send('Kí la '),time.sleep(1),await ctx.send('Mố ê tế shi mai I ta rì')

@bot.command()
async def dlAndSend(ctx, *param):
    url=param[0]
    os.system(f"wget {url} -O video.mp4")
    videoSize = os.path.getsize("video.mp4")
    if videoSize >> 20 >= 8:
        ctx.send(f"Size too large: {videoSize>>20}")
    else:
        await bot.send_file(ctx.message.channel, r"video.mp4",filename="video",content="Sent")
    os.system("rm video.mp4")
    
@bot.command()
async def validallinfo(ctx):
    for value in thisdict:
        await genshinUtil.validAcc(account_id = await mongoUtil.returnAccountId(thisdict[value], ctx=ctx),
                                   cookie_token = await mongoUtil.returnCookieToken(thisdict[value], ctx=ctx), 
                                   ctx=ctx, 
                                   discord_id=thisdict[value])
keep_alive()
bot.run(os.environ["DISCORD_TOKEN"])
