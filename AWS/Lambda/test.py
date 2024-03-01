# OpenAI API テスト用
import os
from openai import OpenAI


def lambda_handler(event, context):
    
    # OpenAI実行
    client = OpenAI(
        api_key=os.environ['API_KEY'],
    )


    messages = [
        {"role": "system", "content": "あなたは優秀なAIアシスタントです。"},
        {"role": "user", "content": "一人旅したい、長崎県でおすすめの場所１つ教えて"}
    ]

    #  OpenAI　実行コード↓
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )
    
    response = completion.choices[0].message.content

    return response