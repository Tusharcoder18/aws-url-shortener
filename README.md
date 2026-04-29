# ⚡ Serverless URL Shortener

A production-ready URL shortener built entirely on AWS serverless infrastructure. Paste a long URL, get a short one instantly — no servers to manage, scales automatically, costs near zero.

**Live demo:** `https://wvpbmi0ywl.execute-api.ap-south-1.amazonaws.com/prod/shorten`

---

## Architecture

```
Browser (S3) ──► API Gateway ──► Lambda (Python) ──► DynamoDB
                                        │
                                  CloudWatch Logs
```

| Component | Service | Purpose |
|-----------|---------|---------|
| Frontend | AWS S3 (static hosting) | Hosts the HTML/JS UI |
| API | AWS API Gateway | Public HTTPS endpoints |
| Backend | AWS Lambda (Python 3.11) | Business logic |
| Database | AWS DynamoDB | Stores URL mappings |
| Monitoring | AWS CloudWatch | Logs & observability |
| Auth | AWS IAM | Least-privilege role for Lambda |

---

## Features

- 🔗 Shorten any URL to a 6-character alphanumeric code
- 📊 Click tracking — every redirect increments a counter in DynamoDB
- ☁️ Fully serverless — no EC2, no containers, no maintenance
- 🌍 CORS-enabled — works from any frontend origin
- 📋 One-click copy to clipboard
- 📈 CloudWatch logging on every Lambda invocation

---

## How it works

### Shorten a URL (`POST /shorten`)
```
Client → API Gateway → Lambda → DynamoDB (write)
                             ↓
                    Returns short_id (e.g. "5zziZJ")
```

1. Client sends `POST /shorten` with `{ "url": "https://example.com" }`
2. Lambda generates a random 6-char ID
3. Stores `{ short_id, long_url, created_at, click_count: 0 }` in DynamoDB
4. Returns the short URL to the client

### Redirect (`GET /{short_id}`)
```
Client → API Gateway → Lambda → DynamoDB (read + update)
                             ↓
                    Returns HTTP 301 → original URL
```

1. Client requests `GET /5zziZJ`
2. Lambda looks up `short_id` in DynamoDB
3. Increments `click_count` by 1
4. Returns `HTTP 301` with `Location: long_url`
5. Browser auto-navigates to the original URL

---

## Project structure

```
url-shortener/
├── lambda/
│   └── lambda_function.py   # Core Lambda handler (POST + GET logic)
├── lambda.zip               # Deployment package
├── index.html               # S3-hosted frontend
└── README.md
```

---

## API reference

### `POST /shorten`

**Request**
```json
{ "url": "https://your-long-url.com/" }
```

**Response**
```json
{
  "short_id": "5zziZJ",
  "short_url": "/5zziZJ"
}
```

### `GET /{short_id}`

Redirects to the original URL with HTTP 301.

**Error (not found)**
```json
{ "error": "URL not found" }
```

---

## Infrastructure setup

### Prerequisites
- AWS account with CLI configured (`aws configure`)
- Python 3.11+
- Region: `ap-south-1` (Mumbai) (Update to preferred region in below commands)

### Deploy from scratch

**1. Create DynamoDB table**
```bash
aws dynamodb create-table \
  --table-name url-shortener \
  --attribute-definitions AttributeName=short_id,AttributeType=S \
  --key-schema AttributeName=short_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-south-1
```

**2. Create IAM role**
```bash
aws iam create-role \
  --role-name url-shortener-lambda-role \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'

aws iam attach-role-policy --role-name url-shortener-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

aws iam attach-role-policy --role-name url-shortener-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
```

**3. Deploy Lambda**
```bash
cd lambda && zip ../lambda.zip lambda_function.py && cd ..

aws lambda create-function \
  --function-name url-shortener \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/url-shortener-lambda-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda.zip \
  --region ap-south-1
```

**4. Create API Gateway + deploy**

```bash
aws apigateway create-rest-api --name url-shortener-api --region ap-south-1
aws apigateway create-resource --rest-api-id YOUR_API_ID --parent-id YOUR_ROOT_ID --path-part shorten --region ap-south-1
aws apigateway create-resource --rest-api-id YOUR_API_ID --parent-id YOUR_ROOT_ID --path-part "{short_id}" --region ap-south-1
```
Connect POST '/shorten' integration and GET '/{short_id}' integration to Lambda.
Add permissions to invoke/trigger Lambda
Enable CORS for POST, GET, OPTIONS
Deploy the api

```bash
aws apigateway create-deployment --rest-api-id YOUR_API_ID --stage-name prod --region ap-south-1
```

**5. Deploy frontend to S3**
```bash
aws s3 mb s3://url-shortener-frontend-YOUR_ACCOUNT_ID --region ap-south-1
aws s3 website s3://url-shortener-frontend-YOUR_ACCOUNT_ID --index-document index.html
aws s3 cp index.html s3://url-shortener-frontend-YOUR_ACCOUNT_ID/
```

---

## Monitoring

CloudWatch automatically captures logs for every Lambda invocation.

```bash
# View latest logs
aws logs describe-log-streams \
  --log-group-name /aws/lambda/url-shortener \
  --order-by LastEventTime --descending \
  --region ap-south-1
```

Navigate to **AWS Console → CloudWatch → Log Groups → /aws/lambda/url-shortener** to see real-time invocation logs, errors, and duration metrics.

---

## Cost estimate

At 10,000 requests/month (well within free tier):

| Service | Free tier | Estimated cost |
|---------|-----------|----------------|
| Lambda | 1M requests/month | $0.00 |
| API Gateway | 1M requests/month | $0.00 |
| DynamoDB | 25 GB + 200M requests | $0.00 |
| S3 | 5 GB storage | $0.00 |
| **Total** | | **~$0/month** |

---

## What I learned

- Designing serverless REST APIs with AWS Lambda + API Gateway
- IAM least-privilege roles for Lambda execution
- DynamoDB single-table design with partition keys
- CORS configuration for cross-origin API access
- HTTP redirect mechanics (301 vs 302 tradeoffs)
- CloudWatch log-based observability

---

## Tech stack

![AWS](https://img.shields.io/badge/AWS-Lambda-orange?logo=amazonaws)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![DynamoDB](https://img.shields.io/badge/AWS-DynamoDB-blue?logo=amazondynamodb)
![S3](https://img.shields.io/badge/AWS-S3-green?logo=amazons3)

---

## Author

**Tushar Pulakala** — [LinkedIn](https://linkedin.com/in/tusharpulakala) · [GitHub](https://github.com/Tusharcoder18)
