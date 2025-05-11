import json
import boto3
import botocore.config
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def content_generation(blogtopic:str)->str:
    prompt = f"""Write a 200 words blog post on {blogtopic}"""
    body = {
        "prompt": prompt,
        "max_gen_len" : 512,
        "temperature" : 0.5,
        "top_p" : 0.9
    }

    try:
        bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-east-1",
            config=botocore.config.Config(read_timeout = 300, retries = {'max_attempts':3})
        )
        response = bedrock.invoke_model(body=json.dumps(body), modelId="us.meta.llama3-1-70b-instruct-v1:0")
        response_content = response.get("body").read()
        response_data = json.loads(response_content)
        blog_details = response_data["generation"]
        
        logger.info(f"Generated Blog: {blog_details}")
        return blog_details
    except Exception as e:
        logger.error(f"Error in content generation: {e}")
        return ""


def s3_uploader(s3_key, s3_bucket, generate_blog):
    s3 = boto3.client('s3')
    try:
        # Log before uploading
        logger.info(f"Uploading to S3: Bucket={s3_bucket}, Key={s3_key}")
        
        # Convert the blog content to bytes
        generate_blog_bytes = generate_blog.encode('utf-8')
        
        # Upload the content to S3
        s3.put_object(Body=generate_blog_bytes, Bucket=s3_bucket, Key=s3_key)
        logger.info(f"File uploaded successfully to S3 bucket {s3_bucket}")
    except Exception as e:
        logger.error(f"Error uploading file to S3 bucket: {e}")

def lambda_handler(event, context):
    try:
        event = json.loads(event['body'])
        blog_topic = event['blogTopic']
        
        logger.info(f"Received blog topic: {blog_topic}")

        generate_blog = content_generation(blogtopic=blog_topic)

        if generate_blog:
            currrent_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            s3_key = f"blogs/{currrent_time}.txt"
            s3_bucket = "rmworksagent"
            s3_uploader(s3_key=s3_key, s3_bucket=s3_bucket, generate_blog=generate_blog)
        else:
            logger.info("No blog generated")

        return {
            'statusCode': 200,
            'body': json.dumps('Blog is Generated Successfully!')
        }
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {e}")
        }
