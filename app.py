from flask import Flask, request, render_template
import json, requests
from urllib import parse
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('./index.html')

tk = 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJkYllCQm12YUprSGM0MmFHNHpZOVB4ZzJYMU82aDZkQyIsImV4cCI6MTY4NjIzMTMwMSwiaXNzIjoiaHR0cHM6Ly9zd2l0LmlvIiwic3ViIjoiMjIxMDE0MDYyNTYwem54eldJMyIsImNtcF9pZCI6IjIyMTAxNDA2MjE2MHIwRnhVOHkiLCJhcHBzX2lkIjoiMjMwNTEwMTQyNTM3MjdFQlA3MlUiLCJhcHBfdXNlcl9pZCI6IjIzMDUxMDE0MjUzNzA3NU1PN0lEIiwiaXNzdWVfdHlwZSI6MX0.LVzSSASxMW4jwEOWfHOlFvVedVa8vQIXLERXMhgUv0d8ZAA90TWKdMwe7zEkBRCWJ4-L1KvJSXLkgoOHHZ4YMA'

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

  invite_check = requests.get(
    url = 'https://openapi.swit.io/v1/api/channel.info?id='+channel_id,
    headers = {'authorization': 'Bearer ' + tk}
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
    client_id = '1kpS2zc95PgatbjV3Eiy'
    client_secret = 'LBOypYfzgT'
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
        'X-Naver-Client-Id': client_id,
        'X-Naver-Client-Secret': client_secret
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
    headers = {'authorization': 'Bearer ' + tk},
    json = {
      'channel_id': channel_id,
      'body_type': 'json_string',
      'content': json.dumps(content)
      }
  )
  print(news_post.json, json.dumps(news_post.json(), indent=1).encode('utf-8').decode('unicode-escape'), sep="\n")

#   if news_post:
#     callback = {"callback_type": "views.close"}   
#   else:
#     callback = {
#       "callback_type": "bot.invite_prompt",
#       "destination": {
#         "type": "channel",
#         "id": channel_id
#       }
#     }

  return callback
