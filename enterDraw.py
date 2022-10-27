import cloudscraper
import os
import random
from discord_webhook import DiscordWebhook, DiscordEmbed
from datetime import datetime
import json
from eth_account import Account
import secrets, json
from web3.auto import w3
from eth_account.messages import encode_defunct
import csv

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

userFile = open(__location__+"/userInfo.json")
userInfo = json.load(userFile)
userInfo = userInfo['userInfo'][0]

def timeLogging():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    timeLogging = "["+current_time+"] - "
    return timeLogging

def getProxy():
    lines = open(__location__+'/proxies.txt').read().splitlines()
    line =random.choice(lines)
    return line

def sendHook(wallet, entryId, authToken):
    webhook = DiscordWebhook(url=userInfo['webhook'], rate_limit_retry=True)
    embed = DiscordEmbed(title="Successfully entered RTFKT raffle :tada:", color=122717, url="https://oncyber.io/rift-mark-2?coords=-4.98x2.70x-48.26x-0.01")
    embed.add_embed_field(name="Wallet", value="||"+str(wallet)+"||")
    embed.add_embed_field(name="EntryID", value="||"+str(entryId)+"||")
    embed.add_embed_field(name="Auth Token", value="||"+str(authToken)+"||")
    embed.set_footer(icon_url="https://cdn.discordapp.com/attachments/819279757422100491/838377712330211328/giphy.gif",text='RTFKT By Cvnnor#0001')
    embed.set_timestamp()
    webhook.add_embed(embed)
    webhook.execute()

def getSignature(scraper, proxies, wallet, pKey):
    print(timeLogging()+"Getting Nonce..")
    signNonce = scraper.get("https://oncyber.io/api/user/nonce", proxies=proxies)
    if signNonce.status_code == 200:
        nonceCookie = signNonce.cookies['nonce']
        nonceJson = json.loads(signNonce.content)
        realNonce = nonceJson['nonce']
        print(timeLogging()+"Got nonce..")
    else:
        print("Error getting nonce: "+str(signNonce.status_code))

    print(timeLogging()+"Getting signature..")
    msg = realNonce
    private_key = pKey
    message = encode_defunct(text=msg)
    signed_message =  w3.eth.account.sign_message(message, private_key=private_key)
    realSignature = signed_message['signature'].hex()
    return realSignature, realNonce, nonceCookie

def entry(wallet, pKey):
    print(timeLogging()+"Getting signature")
    scraper = cloudscraper.create_scraper()

    proxies = {
        "http": getProxy(),
        "https": getProxy(),
    }

    signature, nonce, nonceCookie = getSignature(scraper, proxies, wallet, pKey)
    print(timeLogging()+"Got signature")

    print(timeLogging()+"Logging in...")
    cookies = {
        'nonce': str(nonceCookie)
    }

    headers = {
        'authority': 'oncyber.io',
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        'origin': 'https://oncyber.io',
        'pragma': 'no-cache',
        'referer': 'https://oncyber.io/rift-mark-2',
    }

    json_data = {
        'owner': str(wallet).lower(),
        'sig': {
            'type': 'ethereum',
            'sig': str(signature),
        },
        'type': 'ethereum',
    }

    loginResponse = scraper.post('https://oncyber.io/api/user/authenticate', cookies=cookies, headers=headers, json=json_data, proxies=proxies)
    if loginResponse.status_code == 200:
        print(timeLogging()+"Successfully logged in!")
        loginToken = json.loads(loginResponse.content)['token']
        print(timeLogging()+"Attempting to enter raffle..")

        cookies = {
            '_CCA': str(wallet),
            str(wallet): str(loginToken),
            'nonce': str(nonceCookie),
        }

        headers = {
            'authority': 'oncyber.io',
            'accept': '*/*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'content-type': 'text/plain;charset=UTF-8',
            'origin': 'https://oncyber.io',
            'pragma': 'no-cache',
            'referer': 'https://oncyber.io/rift-mark-2?coords=-4.63x2.70x-45.66x0.16',
        }

        params = {
            'type': 'RUA',
        }

        data = '{"raffleId":1}'

        entryResponse = scraper.post('https://oncyber.io/api/commerce/raffle', params=params, cookies=cookies, headers=headers, data=data, proxies=proxies)
        if entryResponse.status_code == 200:
            responseJson = json.loads(entryResponse.content)
            if str(responseJson) == '{"data":[]}':
                print(timeLogging()+"Error entering raffle..")
                print(responseJson)
            elif str(responseJson) == "{'name': 'DuplicateEntityException', 'message': 'DUPLICATE_ENTITY', 'error': {'message': 'Request failed with status code 422', 'code': 'ERR_BAD_REQUEST'}}":
                print(timeLogging()+"Wallet already entered..")
            else:
                entryId = responseJson['data']['id']
                sendHook(wallet, entryId, loginToken)
                print(timeLogging()+"Successfully entered raffle!")
                print(responseJson)
        else:
            print(timeLogging()+"Error entering raffle: "+str(entryResponse.status_code))
            print(entryResponse.content)

        scraper.close()

with open(os.path.join(__location__, 'wallets.csv'), 'r', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        wallet = row['wallet']
        pKey = row['pKey']
        try:
            entry(wallet, pKey)
        except Exception as e:
            print(timeLogging()+"Error submitting entry: "+str(e))