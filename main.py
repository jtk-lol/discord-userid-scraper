import time
import re
import discum

bot = discum.Client(token='yourtokenhere', log=False)

bot.gateway.resetMembersOnSessionReconnect = False 

#code for op8 fetching
allchars = [' ', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?', '@', '[', ']', '^', '_', '`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~']
bot.gateway.guildMemberSearches = {}

class Queries:
    qList = ["!"] #query list
    

guild_id = "yourserverid"
channel_id = "yourchannelid"

def calculateOption(guild_id, action): #action == 'append' or 'replace'
    if action == 'append':
        lastUserIDs = bot.gateway.guildMemberSearches[guild_id]["queries"][''.join(Queries.qList)]
        data = [bot.gateway.session.guild(guild_id).members[i] for i in bot.gateway.session.guild(guild_id).members if i in lastUserIDs]
        lastName = sorted(set([re.sub(' +', ' ', j['nick'].lower()) if (j.get('nick') and re.sub(' +', ' ', j.get('nick').lower()).startswith(''.join(Queries.qList))) else re.sub(' +', ' ', j['username'].lower()) for j in data]))[-1]
        try:
            option = lastName[len(Queries.qList)]
            return option
        except IndexError:
            return None
    elif action == 'replace':
        if Queries.qList[-1] in allchars:
            options = allchars[allchars.index(Queries.qList[-1])+1:]
            if ' ' in options and (len(Queries.qList)==1 or (len(Queries.qList)>1 and Queries.qList[-2]==' ')): #cannot start with a space and cannot have duplicate spaces
                options.remove(' ')
            return options
        else:
            return None

def findReplaceableIndex(guild_id):
    afor i in range(len(Queries.qList)-2, -1, -1):
        if Queries.qList[i] != '~':
            return i
    return None

def bruteForceTest(resp, guild_id, wait):
    if resp.event.guild_members_chunk:
        remove = False
        if len(bot.gateway.guildMemberSearches[guild_id]["queries"][''.join(Queries.qList)]) == 100: 
            appendOption = calculateOption(guild_id, 'append')
            if appendOption:
                Queries.qList.append(appendOption)
            else:
                remove = True
        else: #if <100 results returned, replace
            replaceOptions = calculateOption(guild_id, 'replace')
            if replaceOptions:
                Queries.qList[-1] = replaceOptions[0]
            else:
                remove = True
        if remove: #if no replace options, find first replaceable index & replace it
            if len(Queries.qList) == 1: 
                bot.gateway.removeCommand(bruteForceTest)
                bot.gateway.close()
            else:
                replaceableInd = findReplaceableIndex(guild_id)
                if replaceableInd != None:
                    Queries.qList = Queries.qList[:replaceableInd+1]
                    replaceOptions = calculateOption(guild_id, 'replace')
                    Queries.qList[-1] = replaceOptions[0]
                else:
                    bot.gateway.removeCommand(bruteForceTest)
                    bot.gateway.close()
        if wait: time.sleep(wait)
        print("members fetched so far: {}".format(len(bot.gateway.session.guild(guild_id).members)))
        bot.gateway.queryGuildMembers([guild_id], query=''.join(Queries.qList), limit=100, keep="all")


def after_op14_fetching(resp, guild_id, use_op8=True, wait=1):
    if bot.gateway.finishedMemberFetching(guild_id):
        bot.gateway.removeCommand({'function': after_op14_fetching, 'params': {'guild_id': guild_id, 'use_op8': use_op8, 'wait': wait}})
        num_members = len(bot.gateway.session.guild(guild_id).members)
        print('Finished op14 member fetching. Fetched {} members from guild {}'.format(num_members, guild_id))

        # Save member IDs to a file
        user_ids = list(bot.gateway.session.guild(guild_id).members.keys())
        with open('user_ids.txt', 'w') as file:
            for user_id in user_ids:
                file.write(user_id + '\n')

        if use_op8 and bot.gateway.session.guild(guild_id).memberCount > num_members:
            print('Scraping members using op8 (this might take a while)...')
            bot.gateway.command({"function": bruteForceTest, "params": {"guild_id": guild_id, "wait": wait}})
            bot.gateway.queryGuildMembers([guild_id], query=''.join(Queries.qList), limit=100, keep="all")
        else:
            bot.gateway.close()


def get_members(guild_id, channel_id, extra_scrape=True, wait=1): 
    print('scraping members using op14...')
    bot.gateway.fetchMembers(guild_id, channel_id, keep="all", reset=False, wait=wait)
    bot.gateway.command({'function': after_op14_fetching, 'params': {'guild_id': guild_id, 'use_op8':extra_scrape, 'wait':wait}})
    bot.gateway.run()
    return bot.gateway.session.guild(guild_id).members

members = get_members(guild_id, channel_id) 

user_ids = list(members.keys())
with open('user_ids.txt', 'w') as file:
    for user_id in user_ids:
        file.write(user_id + '\n')
