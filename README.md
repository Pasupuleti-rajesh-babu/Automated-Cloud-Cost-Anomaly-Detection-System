# Fully LLM-Powered Cloud Cost Anomaly Detection System

This project is an end-to-end, serverless application that uses a two-stage Large Language Model (LLM) pipeline to monitor AWS cloud spending, detect anomalies, and provide intelligent analysis of their root causes. It is built with a focus on cutting-edge AI application, Infrastructure as Code (IaC) with Terraform, a containerized deployment with Docker, and a complete CI/CD pipeline using GitHub Actions.

## Architecture

The following diagram illustrates the architecture of the system:

```mermaid
graph TD
    subgraph "GitHub & CI/CD"
        A[Code Push to Main] --> B{GitHub Actions CI/CD};
        B -- Builds & Pushes --> D[Amazon ECR Repository];
        B -- Deploys --> E{Terraform Apply};
    end

    subgraph "AWS Cloud"
        D -- Deploys to --> F[AWS Lambda Function];
        E -- Provisions --> G{AWS Resources};
        
        subgraph "LLM-Powered Pipeline"
            F -- 1. Fetches Cost History --> H[AWS Cost Explorer];
            F -- 2. Asks "Is this an anomaly?" --> I[Amazon Bedrock LLM - Call 1];
            I -- 3. "YES" --> F;
            F -- 4. Fetches Cost Breakdown --> H;
            F -- 5. Asks "Why did this happen?" --> J[Amazon Bedrock LLM - Call 2];
            J -- 6. Returns Analysis --> F;
        end

        F -- 7. Sends Intelligent Alert --> K[Slack Channel];
    end

    style F fill:#FF9900,stroke:#333,stroke-width:2px
    style I fill:#9B59B6,stroke:#333,stroke-width:2px
    style J fill:#9B59B6,stroke:#333,stroke-width:2px
    style K fill:#4A154B,stroke:#333,stroke-width:2px
```

## Features

*   **Fully LLM-Powered Pipeline**:
    *   **Detection**: Uses a **Large Language Model (LLM)** on **Amazon Bedrock** to analyze historical cost data and determine if the latest cost is an anomaly.
    *   **Analysis**: When an anomaly is detected, it invokes a second LLM call to perform a root cause analysis on a detailed cost breakdown.
*   **Intelligent Alerts**: Delivers rich, human-readable summaries to Slack, explaining the likely cause of any cost spike, with the entire process driven by generative AI.
*   **Containerized & Serverless**: The application is packaged in a **Docker container** and deployed on **AWS Lambda**.
*   **End-to-End Automation**:
    *   **Infrastructure as Code**: All AWS resources are managed by **Terraform**.
    *   **CI/CD**: A full CI/CD pipeline with **GitHub Actions** automates the entire workflow.

## Getting Started

### Prerequisites

1.  **AWS Account**:
    *   An active AWS account with programmatic access.
    *   Ensure you have access to your desired foundation models (e.g., Anthropic Claude) enabled in **Amazon Bedrock**.
2.  **Slack Workspace**: A Slack app with a **Bot User OAuth Token** that has the `chat:write` permission.
3.  **GitHub Account** & **Docker**.

### Setup and Deployment

1.  **Fork and Clone the Repository**
2.  **Create an ECR Repository in AWS** (e.g., `cost-anomaly-detector-repo`)
3.  **Configure GitHub Secrets**:
    *   `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY`
    *   `ECR_REPOSITORY_NAME`: The name of your ECR repository.
    *   `SLACK_BOT_TOKEN`: Your Slack Bot User OAuth Token.
4.  **Push to `main` to Trigger Deployment**

## Configuration

*   **LLM Model**: The model ID is specified in `src/main.py`. You can change this to any supported model on Bedrock.
*   **Cron Schedule & Lambda Resources**: These can be adjusted in `terraform/main.tf`. 