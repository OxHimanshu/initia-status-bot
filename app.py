import re
import asyncio
import nest_asyncio
from flask import Flask, request
import requests
import telegram
from telegram.request import HTTPXRequest
from telebot.credentials import bot_token, bot_user_name,URL


global bot
global TOKEN
TOKEN = bot_token
trequest = HTTPXRequest(connection_pool_size=20)
bot = telegram.Bot(token=TOKEN, request=trequest)

app = Flask(__name__)

nest_asyncio.apply()

# @app.route('/{}'.format(TOKEN), methods=['POST'])
@app.route('/', methods=['POST'])
def respond():
    asyncio.new_event_loop()
    # retrieve the message in JSON and then transform it to Telegram object
    update = telegram.Update.de_json(request.get_json(force=True), bot)

    chat_id = update.message.chat.id
    msg_id = update.message.message_id

    # Telegram understands UTF-8, so encode text for unicode compatibility
    text = update.message.text.encode('utf-8').decode()
    # for debugging purposes only
    print("got text message :", text)
    # the first time you chat with the bot AKA the welcoming message
    if text == "/start":
        # print the welcoming message
        bot_welcome = """
        Welcome to Initia status bot. Please enter your validator address to check the stats.
        """
        # send the welcoming message
        asyncio.run(bot.sendMessage(chat_id=chat_id, text=bot_welcome, reply_to_message_id=msg_id))


    else:
        try:
            # clear the message we got from any non alphabets
            text = re.sub(r"\W", "_", text)
            
            url = "https://celatone-api-prod.alleslabs.dev/v1/initia/initiation-1/validators/" + text + "/info"
            response = requests.get(url)
            response_data = response.json()
            
            if response_data["info"] is None:
                raise Exception("Something went wrong")
            
            uptime_url = "https://celatone-api-prod.alleslabs.dev/v1/initia/initiation-1/validators/" + text + "/uptime?blocks=100"
            uptime_response = requests.get(uptime_url).json()

            outputString = 'Account Address: {} \n Moniker: {} \n Is Active: {} \n Is Jailed: {} \n Rank: {} \n Website: {} \n Uptime: {}% \n Signed Blocks: {} \n Missed Blocks: {} \n Proposed Blocks: {} \n Details: {} \n'.format(response_data["info"]["account_address"], response_data["info"]["moniker"], response_data["info"]["is_active"], response_data["info"]["is_jailed"], response_data["info"]["rank"], response_data["info"]["website"], 100 - uptime_response["uptime"]["missed_blocks"], uptime_response["uptime"]["signed_blocks"], uptime_response["uptime"]["missed_blocks"], uptime_response["uptime"]["proposed_blocks"], response_data["info"]["details"])

            # reply with a photo to the name the user sent,
            # note that you can send photos by url and telegram will fetch it for you
            asyncio.run(bot.sendMessage(chat_id=chat_id, text=str(outputString), reply_to_message_id=msg_id))
        except Exception as e:
            print(e)
            if response_data["info"] is not None:
                asyncio.run(bot.sendMessage(chat_id=chat_id, text=str(outputString), reply_to_message_id=msg_id))
            else:
            # if things went wrong
                asyncio.run(bot.sendMessage(chat_id=chat_id, text="Couldn't find validator details. Kindly check validator address", reply_to_message_id=msg_id))

    return 'ok'

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook('{URL}{HOOK}'.format(URL=URL, HOOK=TOKEN))
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"
    
@app.route('/ping')
def ping():
    return 'pong'

if __name__ == '__main__':
    app.run(threaded=True, port=5000)