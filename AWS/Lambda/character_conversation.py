import json
import boto3
import openai
import uuid
import time

# DynamoDBクライアントの初期化
dynamodb = boto3.resource('dynamodb')

# ここにテーブル名を指定します
CHARACTERS_TABLE_NAME = 'CV_Characters'  # キャラクター情報を格納するテーブル
CONVERSATIONS_TABLE_NAME = 'CV_Conversations'  # 会話記録を格納するテーブル

# OpenAI APIキーを設定します
OPENAI_API_KEY = os.environ['API_KEY']

# OpenAIクライアントのセットアップ
openai.api_key = OPENAI_API_KEY

def lambda_handler(event, context):
    # リクエストパラメータを抽出します
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
        
        # プロンプトの生成
        prompt = generate_prompt(character_data['prompt_template'], message)
        
        # ChatGPT APIへのリクエスト
        response_message = call_chatgpt_api(prompt)
        
        # ユニークなセッションIDを生成
        session_id = str(uuid.uuid4())
        
        # 会話記録をDynamoDBに保存
        save_conversation(session_id, user_id, character_id, message, response_message)
        
        # 実行時間の計算
        execution_time = time.time() - start_time
        
        # レスポンスを返します
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
    # 指定されたcharacter_idに基づいて、Charactersテーブルからデータを取得します
    table = dynamodb.Table(CHARACTERS_TABLE_NAME)
    response = table.get_item(Key={'character_id': character_id})
    return response.get('Item')

def generate_prompt(template, user_message):
    # キャラクターデータに基づいて、ChatGPT APIに送るプロンプトを生成します
    # templateとuser_messageを連結してプロンプトを作成します
    return template + user_message

def call_chatgpt_api(prompt):
    # ChatGPT APIにプロンプトを送信し、応答を取得します
    response = openai.Completion.create(
      engine="text-davinci-003",
      prompt=prompt,
      max_tokens=150
    )
    return response.choices[0].text.strip()

def save_conversation(session_id, user_id, character_id, user_message, character_message):
    # Conversationsテーブルに会話記録を保存します
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
