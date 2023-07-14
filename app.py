from flask import Flask, request, render_template
import requests
import json
from urllib import parse
from bs4 import BeautifulSoup

api = 'https://openapi.swit.io'
clientid = 'Q4IsuPdQeFck4wAeiHpMJHUfBHPXPOEE'
secret = 'uhHSNc2x0VMpYYqdcVns1SfT'

app = Flask(__name__)

def get_token_from_token_info_file():
    with open('token_info.txt', 'r') as f:
        data = json.load(f)
    return data['access_token']

def get_refresh_token_from_token_info_file():
    with open('token_info.txt', 'r') as f:
        data = json.load(f)
    return data['refresh_token']

def write_to_token_info_file(token_info):
    with open('token_info.txt', 'w') as f:
        json.dump(token_info, f)

def get_new_token_by_using_refresh_token(refresh_token):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'refresh_token',
        'client_id': clientid,
        'client_secret': secret,
        'refresh_token': refresh_token
    }
    response = requests.post('https://openapi.swit.io/oauth/token', headers=headers, data=data)
    if response.status_code == 200:
        new_token_info = response.json()
        write_to_token_info_file(new_token_info)
        return new_token_info['access_token']
    else:
        print('Error in refreshing token', response.text)
        return None

@app.route("/")
def index():
    return render_template('./index.html')

@app.route('/news', methods=['POST'])
def news():
  r = request.json
  print(json.dumps(r, indent=1).encode('utf-8').decode('unicode-escape'))
  
  action_id = r['user_action']['id']
  channel_id = r['context']['channel_id']
  command = r['user_action']['slash_command']
  command_parts = command.split(' ')
  value = command_parts[1]
  number = 5
  if value.isnumeric():
    number = int(value)
    if number > 10:
      number = 10
    keyword = ' '.join(command_parts[2:])
  else:
    keyword = ' '.join(command_parts[1:])
  
  news = []

  token = get_token_from_token_info_file()
  invite_check = requests.get(
    url = 'https://openapi.swit.io/v1/api/channel.info?id='+channel_id,
    headers = {'authorization': 'Bearer ' + token}
  )
  print(invite_check.json, json.dumps(invite_check.json(), indent=1).encode('utf-8').decode('unicode-escape'), sep="\n")

  if invite_check.json()['data']['channel']['id']=='':
    callback = {
      "callback_type": "bot.invite_prompt",
      "destination": {
        "type": "channel",
        "id": channel_id
      }
    }

  if action_id == 'naver':
    naver_client_id = '1kpS2zc95PgatbjV3Eiy'
    naver_client_secret = 'LBOypYfzgT'
    url = 'https://openapi.naver.com/v1/search/news.json'
    params = {
      'query': keyword,
      'display': number,
      'start': 1,
      'sort': 'date'
    }
    news_search = requests.get(
      url = f"{url}?{parse.urlencode(params)}",
      headers = {
        'X-Naver-Client-Id': naver_client_id,
        'X-Naver-Client-Secret': naver_client_secret
      }
    )
    if news_search.json()['total']:
      for item in news_search.json()['items']:
        news.append({'title': item['title'], 'link': item['originallink']})
    else: 
      number = 0
      news.append({'title': '결과 없음', 'link': 'swit.io'})

    content = {
      "type":"rich_text",
      "elements":[
        {
          "type":"rt_section",
          "elements":[
            {
              "type":"rt_text",
              "content":"네이버 뉴스 "
            },
            {
              "type":"rt_text",
              "content":f'"{keyword}"',
              "styles":{"bold":True}
            },
            {
              "type":"rt_text",
              "content":" 검색 결과 "
            },
            {
              "type":"rt_text",
              "content":f"{number}",
              "styles":{"bold":True}
            },
            {
              "type":"rt_text",
              "content":" 건 (최신순)"
            }
          ]
        },
        {
          "type":"rt_bullet_list",
          "elements":[]
        }
      ]
    }

    for item in news:
      content["elements"][1]["elements"].append(
        {
          "type":"rt_section",
          "indent":0,
          "elements":[
            {
              "type":"rt_link",
              "content":BeautifulSoup(item["title"], 'html.parser').get_text(),
              "url":item["link"]
            },
            {
              "type":"rt_text",
              "content":f'({item["link"]})'
            }
          ]
        }
      )

  elif action_id == 'google':
    search = 'google'
    engine = 'news.google.com'

  else:
    search = 'None'

  news_post = requests.post(
    url = 'https://openapi.swit.io/v1/api/message.create',
    headers = {'authorization': 'Bearer ' + token},
    json = {
      'channel_id': channel_id,
      'body_type': 'json_string',
      'content': json.dumps(content)
      }
  )
  print(news_post.json, json.dumps(news_post.json(), indent=1).encode('utf-8').decode('unicode-escape'), sep="\n")

  if news_post:
     callback = {"callback_type": "views.close"}

  if news_post.status_code == 401: # token expired
    refresh_token = get_refresh_token_from_token_info_file()
    token = get_new_token_by_using_refresh_token(refresh_token)    
    news_post_2nd = requests.post(
    url = 'https://openapi.swit.io/v1/api/message.create',
    headers = {'authorization': 'Bearer ' + token},
    json = {
      'channel_id': channel_id,
      'body_type': 'json_string',
      'content': json.dumps(content)
      }
    )
    print(news_post_2nd.json, json.dumps(news_post_2nd.json(), indent=1).encode('utf-8').decode('unicode-escape'), sep="\n")

    if news_post_2nd:
       callback = {"callback_type": "views.close"}

  return callback
