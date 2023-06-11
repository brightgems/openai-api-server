# openai-api-server

proxy server for openai API

## Features

- chat
- embeding

## setup virtual environment

install

```
python -m venv ./env
```

activate

```
source env/bin/activate
```

## start application
`uvicorn` server is started with the `--ws websockets `

## chatGpt

Response format
An example API response looks as follows:

```
{
 'id': 'chatcmpl-6p9XYPYSTTRi0xEviKjjilqrWU2Ve',
 'object': 'chat.completion',
 'created': 1677649420,
 'model': 'gpt-3.5-turbo',
 'usage': {'prompt_tokens': 56, 'completion_tokens': 31, 'total_tokens': 87},
 'choices': [
   {
    'message': {
      'role': 'assistant',
      'content': 'The 2020 World Series was played in Arlington, Texas at the Globe Life Field, which was the new home stadium for the Texas Rangers.'},
    'finish_reason': 'stop',
    'index': 0
   }
  ]
}
```

## Documents

[Fast API Cookbook](https://fastapi.tiangolo.com/zh/tutorial/query-params/)
[Fastapi JWT](https://indominusbyte.github.io/fastapi-jwt-auth/usage/basic/)
[chatgpt-api](https://github.com/transitive-bullshit/chatgpt-api#reverse-proxy)
<https://github.com/rawandahmad698/PyChatGPT>
<https://github.com/Chanzhaoyu/chatgpt-web>

## openai shell command

```
openai api chat_completions.create -m gpt-3.5-turbo -g user "Hello world"
```
