import discord
from binance.client import Client
import dill as pickle

disc_client = discord.Client()

# loads the list of Dictionaries that hold the user keys
public_Keys = pickle.load(open("env/publicKeys.env", "rb"))
key_dictionary_list = pickle.load(open("env/tokens.env", "rb"))

bin_client = Client(api_key=public_Keys['Binance'], tld='us')


# Saves the user dictionary list
def list_update():
    pickle.dump(key_dictionary_list, open("env/tokens.env", "wb"))


# returns dictionary corresponding to the desired member
# @param member discord member reference with a .id attribute
def list_find(member):
    for uDict in key_dictionary_list:
        if member.id == uDict['User']:
            return uDict
    return None


@disc_client.event
async def on_ready():
    print(f'We have logged in as {disc_client.user}')

# triggers any time a message is seen by the bot
# @param message the message reference that triggered the event


@disc_client.event
async def on_message(message):

    # checks author is not self, finds author in dictionary, prepares message for parsing
    author = message.author
    if author == disc_client.user:
        return
    userDict = list_find(author)
    sMessage = message.content.split()

    # hello world
    if sMessage[0] == '$hello':
        await message.channel.send('$hello')
        await author.send('This is a direct message')

    # format should be
    # $value [person] where person is member ref
    if sMessage[0] == '$value':
        try:
            userDict = list_find(message.mentions[0])
            bin_client.API_SECRET = userDict['binanceSecret']
            total = 0
            textBuilder = "Symbol  Amount      Price       Value    \n" \
                          "------------------------------------------------"
            for asset in bin_client.get_account()['balances']:
                if (float(asset['free']) > 0) and asset['asset'] != 'USD':
                    quant = float(asset['free'])
                    value = float(bin_client.get_avg_price(symbol=f"{asset['asset']}USD")['price'])
                    usdValue = quant * value
                    total = total + usdValue
                    textBuilder = f"{textBuilder}\n{asset['asset']:5}{quant:8.2f}" \
                                  f"  at {value:8.2f}$ = {usdValue:7.2f} USD"
            textBuilder = f"{textBuilder}\n------------------------------------------------\n" \
                          f"Coming out to a grand total of {total:.2f} USD"
            await message.channel.send("```" + textBuilder + "```")
        except IndexError:
            message.channel.send("Correct format:\n$value [discord Tag]")
        except KeyError:
            message.channel.send("Could not find user data, make sure the user has enrolled")
        finally:
            bin_client.API_SECRET = None

    # adds user to list
    # does not accept key if not sent in DM
    # functionality to come for different app enrollment, enrollment validation!
    # enrollment just means keys being stored in the key dictionary
    # $enroll [application] [public key] [private key] //Public key may not be necessary and may be removed later
    if sMessage[0] == '$enroll':
        if type(message.channel) == discord.DMChannel:
            try:
                if sMessage[1] == "binance":
                    key = sMessage[2]
                    pKey = sMessage[3]
                    if userDict is None:
                        key_dictionary_list.append({'User': author.id, 'binanceKey': key, 'binanceSecret': pKey})
                    else:
                        userDict.update({'binanceKey': key, 'binanceSecret': pKey})
                    list_update()
                    await message.channel.send(f"User {message.author.mention} added to database!")
            except IndexError:
                await author.send("Please enter in this format:\n$enroll [platform] [public key] [secret key]")
        else:
            await message.channel.send(
                f"To enroll in this service, direct message {disc_client.user.mention} in this format:\n"
                f"$enroll [platform] [public key] [secret key]")


disc_client.run(public_Keys['Discord'])
