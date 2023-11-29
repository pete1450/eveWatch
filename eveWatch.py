import keyboard
import mss
import cv2
import numpy
from paho.mqtt import client as mqtt_client
from playsound import playsound
from time import time, sleep
import pyautogui
from discordwebhook import Discord
from PIL import Image
import pytesseract
import discord as discordBot
from discord.ext import commands, tasks
import threading
import os
import asyncio
import requests


print(discordBot.__version__)


#
#Config
#

botToken = "longtokenstring"

#set this to zero to disable all discord posting. Good for testing
postToDiscord = 1

#channels to post to. This really needs to be updated to a list so it can be looped through. 20ish digit number
#mine
channelInt2 = 12345
#corp
channelInt = 12346

#mqtt settings
#use- client.publish(topic, "found a thing") to publish a message to a mqtt server
#awesome for kicking off home automations like flashing lights
broker = '192.168.1.189'
port = 18833
topic = "mytopic/eve"
client_id = 'neutbot'

#image filenames. These reference smal images matched against the screen. Really just used to verify we can see what we need.
eImage = 'exclamation.jpg'
mImage = 'minus.jpg'
eqImage = 'equals.jpg'
#image of the sidebar header to verify the correct one is up for showing ships. The ones that defaults to "Ship"
listImage = 'shiplist.jpg'

#url to poke that indicates the script is working
heartbeatUrl = 'http://192.168.1.234:3001/api/push/uksdfgF?status=up&msg=OK&ping='

#path to an annoying sound to play when your attention is needed
audio_file = './alarm.wav'

#define location that will be looked at for the list of ships on grid. don't bother with the one that expands to the bottom 
#because that doesnt show most of the time. Use just below what normally shows "no search results". It's important to include 
#that text because there is a check below that looks for that text missing
gridListDimensions = {
        'left': 1600,
        'top': 110,
        'width': 230,
        'height': 500,
        'mon': 1
    }

#define location that the local count bar can be found(the gray bar with the hostile/criminal/neut count)
localPosLeft = 1115
localPosTop = 559
dimensionsLocalCount = {
        'left': localPosLeft,
        'top': localPosTop,
        'width': 300,
        'height': 60,
        'mon': 1
    }

#this is just the bounding box for the grid filter so it knows where to grab a screenshot of 
#something that only shows if the game is on and you are undocked. Used in the !up command
filterDimensions = {
         'left': 1549,
         'top': 32,
         'width': 150,
         'height': 75,
         'mon': 1
     }



#
#End config
#











intents = discordBot.Intents.default()
intents.messages = True
intents.message_content = True  
bot = commands.Bot(command_prefix='!', intents=intents)

sct = mss.mss()

#name of an image to write when someone uses the !up command. Really just a temporary name to save as before attaching it. 
testImageName = 'shiplist.png'

@bot.command(name='up')
async def up_check(ctx):
    proofScreenshot = sct.grab(filterDimensions)
    img = Image.frombytes("RGB", proofScreenshot.size, proofScreenshot.bgra, "raw", "BGRX")
    img.save(testImageName)

    await ctx.send('If this image says "Ship" all is well. If not cam died :(')
    await ctx.send(file=discordBot.File(testImageName))

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client
    

client = connect_mqtt()

pyautogui.PAUSE = 0


excImage = cv2.imread(eImage)
excImageWidth = excImage.shape[1]
excImageHeight = excImage.shape[0]
minusImage = cv2.imread(mImage)
minusImageWidth = minusImage.shape[1]
minusImageHeight = minusImage.shape[0]
equalsImage = cv2.imread(eqImage)
eqImageWidth = equalsImage.shape[1]
eqImageHeight = equalsImage.shape[0]

shipListImage = cv2.imread(listImage)
shipListWidth = shipListImage.shape[1]
shipListHeight = shipListImage.shape[0]


    

prevHostileText = ''
prevCriminalText = ''
prevNeutralText = ''
gridText = ''
gridDict = {}

firstLoop = 1
errorCountIcon = 0
errorCountShip = 0
heartbeatCounter = 0
heartbeatCounter2 = 0

@tasks.loop(seconds=2)
async def task_loop():
    await long_running_function()


async def long_running_function():
    
    global prevHostileText
    global prevCriminalText
    global prevNeutralText
    global gridText
    global firstLoop
    global gridDict
    global heartbeatCounter
    global heartbeatCounter2
    global errorCountShip
    global errorCountIcon

    client.loop()
    
    
    #get these screenshots early so we can skip the checking if required elements arent on the screen
    localCountsScreenshot = sct.grab(dimensionsLocalCount)
    localCountsSSArray = numpy.array(localCountsScreenshot)
    localCountsSSArrayNoAlpha = localCountsSSArray[:,:,:3]
    result2 = cv2.matchTemplate(localCountsSSArrayNoAlpha, excImage, cv2.TM_CCORR_NORMED)
    _, max_val2, _, max_loc2 = cv2.minMaxLoc(result2)
    result3 = cv2.matchTemplate(localCountsSSArrayNoAlpha, minusImage, cv2.TM_CCORR_NORMED)
    _, max_val3, _, max_loc3 = cv2.minMaxLoc(result3)
    result4 = cv2.matchTemplate(localCountsSSArrayNoAlpha, equalsImage, cv2.TM_CCORR_NORMED)
    _, max_val4, _, max_loc4 = cv2.minMaxLoc(result4)
    
    
    dimensionsHostile = {
        'left': localPosLeft+max_loc2[0]+excImageWidth,
        'top': localPosTop+max_loc2[1]-5,
        'width': 50,
        'height': 30,
        'mon': 1
    }
    hostileCountScreenshot = sct.grab(dimensionsHostile)
    hostileCountArray = numpy.array(hostileCountScreenshot)
    ret,thresh = cv2.threshold(hostileCountArray,140,255,cv2.THRESH_BINARY)
    hostileText = pytesseract.image_to_string(thresh, config='--psm 6 -c tessedit_char_whitelist=0123456789')
   
        
    dimensionsCriminal = {
            'left': localPosLeft+max_loc3[0]+excImageWidth,
            'top': localPosTop+max_loc3[1]-5,
            'width': 50,
            'height': 30,
            'mon': 1
        }
    criminalCountScreenshot = sct.grab(dimensionsCriminal)
    criminalCountArray = numpy.array(criminalCountScreenshot)
    ret,thresh = cv2.threshold(criminalCountArray,140,255,cv2.THRESH_BINARY)
    criminalText = pytesseract.image_to_string(thresh, config='--psm 6 -c tessedit_char_whitelist=0123456789')
    
        
    dimensionsNeutral = {
            'left': localPosLeft+max_loc4[0]+excImageWidth,
            'top': localPosTop+max_loc4[1]-5,
            'width': 50,
            'height': 30,
            'mon': 1
        }
    neutralCountScreenshot = sct.grab(dimensionsNeutral)
    neutralCountArray = numpy.array(neutralCountScreenshot)
    ret,thresh = cv2.threshold(neutralCountArray,140,255,cv2.THRESH_BINARY)
    neutralText = pytesseract.image_to_string(thresh, config='--psm 6 -c tessedit_char_whitelist=0123456789')
    
    
    
    #make sure the filter is set to ships
    #if not, either set wrong or we're in a station
    filterScreenshot = sct.grab(filterDimensions)
    filterScreenshotArray = numpy.array(filterScreenshot)
    ret,filterThresh = cv2.threshold(filterScreenshotArray,77,255,cv2.THRESH_BINARY)
    filterText = pytesseract.image_to_string(filterThresh, config='--psm 6')
    filterText = filterText.rstrip()
    
    #cv2.imshow("", filterThresh)
    #key = cv2.waitKey(30)
        
    if filterText != 'Ship':
    
        #print(filterText)
        
    
        sleep(2)
        if keyboard.is_pressed('q'):
            quit()
        print('Cant find the Ship filter: {}'.format(time()))
        playsound(audio_file)
        client.publish(topic, "found a thing")
        
        errorCountShip += 1
        if errorCountShip == 30:
            await botDown()

        return
    
    #immediately reset error count.
    if errorCountShip > 30:
        errorCountShip = 0
        await botUp()
    elif errorCountShip == 1:
        errorCountShip = 0

    #pick one of the icons and if we can't find this something aint right
    #might have another window up or app died. Pause in here
    if max_val2 < .95:
        sleep(2)
        print('Required icon missing... : {}'.format(time()))
        playsound(audio_file)
        client.publish(topic, "found a thing")
        
        errorCountIcon += 1
        
        #if we go through this error enough times just mark the bot as down
        if errorCountIcon == 30:
            if postToDiscord:
                await botDown()
                
        return
    #immediately reset error count
    if errorCountIcon > 30:
        errorCountIcon = 0
        await botUp()
    elif errorCountIcon == 1:
        errorCountIcon = 0


    hostileText = hostileText.rstrip()
    criminalText = criminalText.rstrip()
    neutralText = neutralText.rstrip()

    
    #found something worth mentioning AND it's different from before
    if hostileText != '0' or criminalText != '0' or neutralText != '0':
    
        heartbeatCounter +=1
        if heartbeatCounter > 250:
            heartbeatCounter = 0
            x = requests.get(heartbeatUrl)
            print('Sending Hearbeat')

        #always alert me
        print('Baddies around!!!: {}'.format(time()))
        playsound(audio_file)
        client.publish(topic, "found a thing")
        
        #...but make sure it's new if alerting discord
        if hostileText != prevHostileText or criminalText != prevCriminalText or neutralText != prevNeutralText:
            
            #let discord know local count changed
            countImage = Image.frombytes("RGB", localCountsScreenshot.size, localCountsScreenshot.bgra, "raw", "BGRX")
            localCountFile = "localCount.png"
            countImage.save(localCountFile)
            
            if postToDiscord:
                print('DISCORD:localcount : {}'.format(time()))
                channel = bot.get_channel(channelInt)
                await channel.send('<@&1127080880880504913> <@&870645686830530600> Baddies around!!!')
                await channel.send(file=discordBot.File(localCountFile))
                channel2 = bot.get_channel(channelInt2)
                await channel2.send('<@&1127080880880504913> <@&870645686830530600> Baddies around!!!')
                await channel2.send(file=discordBot.File(localCountFile))
        
        #unless it's not new but we see a ship
        #find ships
        scr2 = sct.grab(gridListDimensions)
        thing = numpy.array(scr2)
        #ret,thresh = cv2.threshold(thing,50,255,cv2.THRESH_BINARY)
        
        #parse text. This is for messing with images to try ot make them more readable by the OCR
        thing_HSV = cv2.cvtColor(thing, cv2.COLOR_BGR2HSV)
        #low_H = 0
        #high_H = 360
        #low_S = 0
        #high_S = 255
        #low_V = 0
        #high_V = 34
        low_H = 0
        high_H = 278
        low_S = 0
        high_S = 100
        low_V = 59
        high_V = 255
        thresh = cv2.inRange(thing_HSV, (low_H, low_S, low_V), (high_H, high_S, high_V))
        
        #cv2.imshow("", thresh)
        #key = cv2.waitKey(30)
        
        gridText = pytesseract.image_to_string(thresh, config='--psm 6')
        gridText = gridText.rstrip()

        
        #######Build a dict of seen ships. This dict should persist until there are no more hostiles in the system
        #######Each name/ship element will be printed once then marked with 1 for "sent" so they are only sent once
        ####### an itemList is an array where the 0 element is the ship and the 1 element is a boolean representing if we've seen this char
        
        #turn the grid string into a list and every other element is the char name. offset that by one for the ship
        #put these in a dictionary
        if('ARCH RESULTS' not in gridText): 

            gridList = gridText.split('\n')
            for x in range(len(gridList) // 2):
                
                itemNum = x*2
                
                char = gridList[itemNum]
                ship = gridList[itemNum+1]
                
                #print("Char- " + char)
                
                #if this is true we dont have a ship for the last name due to probably being cut off. No idea yet if this would happen
                if itemNum+1 == len(gridList):
                    ship = 'unknown'
                #print("    Ship- " + ship)
                
                if gridDict.get(char, 'nothing') == 'nothing': #we havent seen this char yet
                    itemList = [ship, 0]
                    gridDict[char] = itemList


            #now we have a dict with newly seen and old ships
            #print(gridDict)
            for key in gridDict:
                char = key
                item = gridDict[key]
                if item[1] == 0 and 'somethingfriendly' not in char and 'somethingfriendly' not in char and 'somethingfriendly' not in char: #if its 0 we havent reported on them
                
                    #save everything for debugging
                    gridImage = Image.frombytes("RGB", scr2.size, scr2.bgra, "raw", "BGRX")
                    gridListFile = 'gridlist{}.png'.format(time())
                    gridImage.save(gridListFile)
                    with open('gridText{}.txt'.format(time()), 'w') as f:
                        f.write(gridText)
                
                    if postToDiscord:
                        alertText = 'Char- ' + char + '\n    Ship- ' + item[0]
                        print('DISCORD:ship grid item')
                        channel = bot.get_channel(channelInt)
                        await channel.send(alertText)
                        channel2 = bot.get_channel(channelInt2)
                        await channel2.send(alertText)
                    alertText = 'Char- ' + char + '\n    Ship- ' + item[0]
                    print(alertText)
                    gridDict[key][1] = 1 #note that we've reported on it
            
    
    #found nothing    
    else:
        print('All Good: {}'.format(time()))
        
        #send a heartbeat to a specified endpoint
        #delete this if not needed
        #BEGIN HEARTBEAT
        heartbeatCounter +=1
        if heartbeatCounter > 250:
            heartbeatCounter = 0
            x = requests.get(heartbeatUrl)
            print('Sending Hearbeat')
        #END HEARTBEAT
            
        heartbeatCounter2 +=1
        if heartbeatCounter2 > 1800:
            heartbeatCounter2 = 0
            if postToDiscord:
                channel = bot.get_channel(channelInt)
                await channel.send('Im alive')
                channel2 = bot.get_channel(channelInt2)
                await channel2.send('Im alive')
                print('Sending Discord Hearbeat')
        
        #if it's good now but the last check wasn't, let know all clear
        if len(gridDict) != 0 and not firstLoop:
            if postToDiscord:
                channel = bot.get_channel(channelInt)
                await channel.send('N7 now empty')
                channel2 = bot.get_channel(channelInt2)
                await channel2.send('N7 now empty')
            #empty out the dict of hostiles so we can start keeping track of a new event
            print('Resetting List')
            gridDict = {}
        elif firstLoop:
            firstLoop = 0
        
    #not sure why this heartbeat is here
    if heartbeatCounter > 26:
        heartbeatCounter = 0
        x = requests.get(heartbeatUrl)
        print('Sending Heartbeat')
    
    #store current so we can check changes
    prevHostileText = hostileText
    prevCriminalText = criminalText
    prevNeutralText = neutralText
   
async def botDown():
    if postToDiscord:
        print('DISCORD: bot down')
        channel = bot.get_channel(channelInt)
        await channel.send('Cam is down :(')
        channel2 = bot.get_channel(channelInt2)
        await channel2.send('Cam is down :(')

async def botUp():
    if postToDiscord:
        print('DISCORD: bot up')
        channel = bot.get_channel(channelInt)
        await channel.send('Cam is up :D')
        channel2 = bot.get_channel(channelInt2)
        await channel2.send('Cam is up :D')
        

@bot.event
async def on_ready():
    print('on ready')

    task_loop.start()

bot.run(botToken)