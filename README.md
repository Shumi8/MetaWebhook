# Lead Processing System

This repository contains the code for a lead processing system developed. The system was designed to handle and process leads generated from a marketing campaign on Meta platforms (such as Facebook and Instagram). The goal of the campaign was to drive membership signups by showing targeted ads to specific user groups. Once a user interacted with the ad and submitted their details, the system would automate the processing of their lead data.

## Features

- **Automated Lead Capture**: Leads are captured via a webhook when users submit their information through Meta platforms.
- **Webhook Verification**: Securely verifies incoming requests from Meta using HMAC signatures to ensure data authenticity.
- **Azure Blob Storage Integration**: The full JSON payload from each lead event is stored in Azure Blob Storage, allowing for data retention and backup.
- **Lead Categorization**: Processes each lead and classifies them into different categories: pending, terminated, or already subscribed.
- **Service Bus Integration**: Sends processed lead data to an Azure Service Bus topic for further categorization and handling.
- **Scalable and Serverless**: The entire system is deployed using Azure Functions, making it fully scalable to handle varying lead volumes.

## Technologies Used

### 1. **Azure Functions**
- A serverless compute service used to handle the webhook requests from Meta and process the leads.

### 2. **Azure Blob Storage**
- Stores the full lead event payload, providing a backup for all incoming data.

### 3. **Azure Service Bus**
- Handles communication and ensures that leads are properly categorized (pending, terminated, or already subscribed).

### 4. **Meta API**
- Used to fetch additional lead details for each user based on the lead generation ID.

### 5. **Azure Identity and HMAC Authentication**
- Provides security by validating incoming requests and ensuring the integrity of the lead data.

This project automates the end-to-end lead processing pipeline, making it easier for the organization to manage and respond to user signups efficiently.
