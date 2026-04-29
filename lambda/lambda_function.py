import json
import boto3
import string
import random
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('url-shortener')

def generate_short_id(length=6):
	chars = string.ascii_letters + string.digits
	return ''.join(random.choices(chars, k=length))

def lambda_handler(event, context):
	http_method = event.get('httpMethod', '')
	path = event.get('path', '')

	#CORS headers
	headers = {
		'Access-Control-Allow-Origin': '*',
		'Access-Control-Allow-Headers': 'Content-Type',
		'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
	}

	#Handle CORS preflight
	if http_method == 'OPTIONS':
		return {'statusCode': 200, 'headers': headers, 'body': ''}

	#POST /shorten - create a short URL
	if http_method == 'POST' and path == '/shorten':
		body = json.loads(event.get('body', '{}'))
		long_url = body.get('url', '')

		if not long_url:
			return {
				'statusCode': 400,
				'headers': headers,
				'body': json.dumps({'error': 'URL is required'})
			}

		short_id = generate_short_id()
		table.put_item(Item={
			'short_id': short_id,
			'long_url': long_url,
			'created_at': datetime.utcnow().isoformat(),
			'click_count': 0
		})

		return {
			'statusCode': 200,
			'headers': headers,
			'body': json.dumps({'short_id': short_id, 'short_url': f'/{short_id}'})
		}

	# GET /{short_id} - redirect to long URL
	if http_method == 'GET' and len(path) > 1:
		short_id = path.lstrip('/')
		response = table.get_item(Key={'short_id': short_id})
		item = response.get('Item')

		if not item:
			return {
				'statusCode': 404,
				'headers': headers,
				'body': json.dumps({'error': 'URL not found'})
			}
		
		#Increment click count
		table.update_item(
			Key={'short_id': short_id},
			UpdateExpression='SET click_count = click_count + :val',
			ExpressionAttributeValues={':val': 1}
		)

		return {
			'statusCode': 301,
			'headers': {**headers, 'Location': item['long_url']},
			'body': '')
		}

	return {
		'statusCode': 400,
		'headers': headers,
		'body': json.dumps({'error': 'Invalid Request'}))
	}