import re
import asyncio
from flask import Flask, request
import requests
import telegram
from telebot.credentials import bot_token, bot_user_name,URL


global bot
global TOKEN
TOKEN = bot_token
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

# @app.route('/{}'.format(TOKEN), methods=['POST'])
@app.route('/', methods=['POST'])
def respond():
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
            
            # bot.sendChatAction(chat_id=chat_id, action = telegram.ChatAction.TYPING)

            url = "https://celatone-api-prod.alleslabs.dev/v1/initia/initiation-1/validators/" + text + "/info"
            response = requests.get(url)
            response_data = response.json()
            if len(response_data["info"]) == 0:
                raise Exception("Something went wrong")
            
            uptime_response = requests.get("https://celatone-api-prod.alleslabs.dev/v1/initia/initiation-1/validators/initvaloper19j6aw3lqs0qh97f9tlvhvgeufcr83a3wh0sxtn/uptime?blocks=100").json()

            outputString = 'Account Address: {} \n Moniker: {} \n Is Active: {} \n Is Jailed: {} \n Rank: {} \n Website: {} \n Uptime: {}% \n Signed Blocks: {} \n Missed Blocks: {} \n Proposed Blocks: {} \n Details: {} \n'.format(response_data["info"]["account_address"], response_data["info"]["moniker"], response_data["info"]["is_active"], response_data["info"]["is_jailed"], response_data["info"]["rank"], response_data["info"]["website"], 100 - uptime_response["uptime"]["missed_blocks"], uptime_response["uptime"]["signed_blocks"], uptime_response["uptime"]["missed_blocks"], uptime_response["uptime"]["proposed_blocks"], response_data["info"]["details"])

            # reply with a photo to the name the user sent,
            # note that you can send photos by url and telegram will fetch it for you
            asyncio.run(bot.sendMessage(chat_id=chat_id, text=str(outputString), reply_to_message_id=msg_id))
        except Exception:
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