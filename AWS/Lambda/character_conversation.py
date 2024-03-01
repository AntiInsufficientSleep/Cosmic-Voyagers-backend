import os
import json
import boto3
import uuid
import time
from openai import OpenAI

# DynamoDBクライアントの初期化
dynamodb = boto3.resource('dynamodb')

# テーブル名を指定
CHARACTERS_TABLE_NAME = 'CV_Characters'  # キャラクター情報を格納
CONVERSATIONS_TABLE_NAME = 'CV_Conversations'  # 会話記録を格納

def lambda_handler(event, context):
    # リクエストパラメータを抽出
    user_id = event.get('user_id')
    character_id = event.get('character_id')
    message = event.get('message')

    # 基本的なバリデーション
    if not all([user_id, character_id, message]):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': '必要なパラメータが足りません'})
        }

    # 処理開始時刻
    start_time = time.time()

    try:
        # DynamoDBからキャラクターデータを取得
        character_data = get_character_data(character_id)
        if not character_data:
            return {'statusCode': 404, 'body': json.dumps({'error': 'キャラクターが見つかりません'})}
        
        # OpenAI実行
        client = OpenAI(api_key=os.environ['API_KEY'])

        messages = [
            {"role": "system", "content": character_data['prompt_template']},
            {"role": "user", "content": message}
        ]

        # OpenAI実行
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )
        
        response_message = completion.choices[0].message.content

        # ユニークなセッションIDを生成
        session_id = str(uuid.uuid4())
        
        # 会話記録をDynamoDBに保存
        save_conversation(session_id, user_id, character_id, message, response_message)
        
        # 実行時間の計算
        execution_time = time.time() - start_time
        
        # レスポンスを返す
        return {
            'statusCode': 200,
            'body': json.dumps({
                'session_id': session_id,
                'message': response_message,
                'status': {
                    'code': 'success',
                    'execution_time': execution_time
                }
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_character_data(character_id):
    # 指定されたcharacter_idに基づいてCharactersテーブルからデータを取得
    table = dynamodb.Table(CHARACTERS_TABLE_NAME)
    response = table.get_item(Key={'character_id': character_id})
    return response.get('Item')

def save_conversation(session_id, user_id, character_id, user_message, character_message):
    # Conversationsテーブルに会話記録を保存
    table = dynamodb.Table(CONVERSATIONS_TABLE_NAME)
    now = int(time.time())
    table.put_item(Item={
        'session_id': session_id,
        'user_id': user_id,
        'character_id': character_id,
        'messages': [{'type': 'user', 'content': user_message, 'timestamp': now},
                     {'type': 'character', 'content': character_message, 'timestamp': now}],
        'created_at': now,
        'updated_at': now
    })
