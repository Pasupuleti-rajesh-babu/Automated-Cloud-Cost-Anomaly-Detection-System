import json
import os
from datetime import datetime, timedelta
import boto3
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def get_cost_history(days=30):
    """
    Fetches daily cost history and formats it for an LLM prompt.
    """
    client = boto3.client('ce', region_name='us-east-1')
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    response = client.get_cost_and_usage(
        TimePeriod={'Start': start_date, 'End': end_date},
        Granularity='DAILY',
        Metrics=['UnblendedCost']
    )
    
    costs = ""
    for item in response['ResultsByTime']:
        date_str = item['TimePeriod']['Start']
        cost = float(item['Total']['UnblendedCost']['Amount'])
        costs += f"- {date_str}: ${cost:.2f}\n"
    
    # Get the latest cost for the summary message
    latest_cost_str = response['ResultsByTime'][-1]['Total']['UnblendedCost']['Amount']
    latest_cost = float(latest_cost_str)
    anomaly_date = response['ResultsByTime'][-1]['TimePeriod']['Start']

    return costs, latest_cost, anomaly_date

def is_anomaly_llm(cost_history_str):
    """
    Asks an LLM on Amazon Bedrock if the last data point is an anomaly.
    """
    try:
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        prompt = f"""
        Human: Here is a list of daily cloud costs. Please analyze this time-series data and determine if the cost on the most recent day represents a significant anomaly compared to the historical pattern.
        
        Historical Costs:
        {cost_history_str}
        
        Based on your analysis, is the final day's cost an anomaly? Please answer with a single word: YES or NO.
        
        Assistant:
        """
        
        body = json.dumps({
            "prompt": prompt,
            "max_tokens_to_sample": 5,
            "temperature": 0.0,
        })

        response = bedrock.invoke_model(body=body, modelId='anthropic.claude-v2')
        response_body = json.loads(response.get('body').read())
        llm_response = response_body.get('completion').strip().upper()
        
        return "YES" in llm_response

    except Exception as e:
        print(f"Error during LLM anomaly detection: {e}")
        return False

def get_cost_breakdown_by_service(date_str):
    """
    Fetches the cost breakdown by service for a specific day.
    """
    client = boto3.client('ce', region_name='us-east-1')
    
    response = client.get_cost_and_usage(
        TimePeriod={'Start': date_str, 'End': (datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')},
        Granularity='DAILY',
        Metrics=['UnblendedCost'],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
    )
    
    breakdown = ""
    for item in response['ResultsByTime'][0]['Groups']:
        service_name = item['Keys'][0]
        amount = float(item['Metrics']['UnblendedCost']['Amount'])
        if amount > 0:
            breakdown += f"- {service_name}: ${amount:.2f}\n"
            
    return breakdown

def get_anomaly_analysis_from_llm(cost_breakdown, latest_cost):
    """
    Invokes an LLM on Amazon Bedrock to analyze the cost anomaly.
    """
    try:
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        prompt = f"""
        Human: A cloud cost anomaly has been detected. The total cost for the day was ${latest_cost:.2f}.
        
        Here is the detailed cost breakdown by service for the anomalous day:
        {cost_breakdown}
        
        Please provide a brief, data-driven analysis of the likely cause of this cost spike. Focus on the service with the most significant cost. Do not use any preamble, just provide the analysis.
        
        Assistant:
        """
        
        body = json.dumps({
            "prompt": prompt,
            "max_tokens_to_sample": 300,
            "temperature": 0.1,
        })

        response = bedrock.invoke_model(body=body, modelId='anthropic.claude-v2')
        response_body = json.loads(response.get('body').read())
        return response_body.get('completion').strip()

    except Exception as e:
        print(f"Error getting analysis from LLM: {e}")
        return "Could not retrieve AI analysis."

def send_slack_alert(message):
    """
    Sends a message to a Slack channel using the Slack SDK.
    """
    try:
        ssm = boto3.client('ssm', region_name='us-east-1')
        parameter_name = os.environ.get('SLACK_TOKEN_PARAMETER_NAME', 'CostAnomalyDetectionSlackBotToken')
        slack_token = ssm.get_parameter(Name=parameter_name, WithDecryption=True)['Parameter']['Value']
        
        slack_channel = os.environ.get('SLACK_CHANNEL', '#general')
        
        client = WebClient(token=slack_token)
        client.chat_postMessage(channel=slack_channel, text=message)
        print("Slack alert sent successfully.")
    except (SlackApiError, Exception) as e:
        print(f"Error sending Slack alert: {e}")

def lambda_handler(event, context):
    """
    The entry point for the AWS Lambda function.
    """
    print("Lambda function executed.")
    
    cost_history_str, latest_cost, anomaly_date = get_cost_history()
    
    if not cost_history_str:
        print("Could not retrieve cost data.")
        return {'statusCode': 500, 'body': json.dumps('Error fetching cost data.')}

    if is_anomaly_llm(cost_history_str):
        cost_breakdown = get_cost_breakdown_by_service(anomaly_date)
        ai_analysis = get_anomaly_analysis_from_llm(cost_breakdown, latest_cost)
        
        alert_message = (
            f"COST ANOMALY DETECTED!\n"
            f"Yesterday's total cost was ${latest_cost:.2f}.\n\n"
            f"*AI Analysis:*\n{ai_analysis}"
        )
        print(alert_message)
        send_slack_alert(alert_message)
        final_message = alert_message
    else:
        final_message = f"No anomaly detected. Yesterday's cost was ${latest_cost:.2f}."
        print(final_message)
    
    return {
        'statusCode': 200,
        'body': json.dumps(final_message)
    } 