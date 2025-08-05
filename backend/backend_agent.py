"""
backedn_agent.py
================
This to powered with autogen(version > 0.4)

#agent1 -> reads the Log Image and Analyze 
#agent2 -> reads the analysis and assort the risk situation
#agent3 -> reads the risk situation and generates the report
#agent3 -> reads the generated report and communication with necessary team
#agent4 -> reads the report and provides the quality assurance.
"""

# Importing necessary libaries..
from utils.logger import logging
from utils.exception import CustomException

from autogen_core.tools import FunctionTool 
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import MultiModalMessage , TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.conditions import TextMentionTermination
from autogen_core import Image as AGImage
from PIL import Image
import smtplib
from datetime import datetime ,timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from typing import AsyncGenerator ,Dict ,List ,Optional
from dotenv import load_dotenv
import os
import asyncio
import io
import sys


#=================================================================
#load_credientals
#=================================================================

load_dotenv('.env')
GMAIL_PASS = os.getenv("GMAIL_PASS")
GEMINI_KEY = os.getenv("GEMINI_KEY")
DEFAULT_SENDER = os.getenv("DEAFULT_MAIL_SENDER")
DEFAULT_RECEIVER = os.getenv("DEAFULT_MAIL_RECEIVER")


#helpers
PRIORITY_LEVELS = {
    "CRITICAL": {"urgency": "IMMEDIATE", "color": "🔴", "response_time": "0-2 hours"},
    "HIGH": {"urgency": "URGENT", "color": "🟠", "response_time": "2-8 hours"},
    "MEDIUM": {"urgency": "SCHEDULED", "color": "🟡", "response_time": "24-48 hours"},
    "LOW": {"urgency": "ROUTINE", "color": "🟢", "response_time": "1-2 weeks"}
}


#=================================================================
#tools
#=================================================================
def maintenance_priority(findings:str)-> Dict:
    """
    Analyses maintenance findings and assings the prority.
    """
    critical_keywords = ['crack','leak','failure','emergency','broken','damaged']
    high_keywords = ['worn','excessive','abnormal','warning','alert']
    medium_keywords = ['routine','schedule','preventive','inspection']

    lower_findings = findings.lower()
    if any(keyword in lower_findings for keyword in critical_keywords):
        priority = "CRITCAL"
    elif any(keyword in lower_findings for keyword in high_keywords):
        priority = "HIGH"
    elif any(keyword in lower_findings for keyword in medium_keywords):
        priority = "MEDIUM"
    else :
        priority = "LOW"

        return {
        "priority": priority,
        "details": PRIORITY_LEVELS[priority],
        "assessment_time": datetime.now().isoformat()
    }

def maintenance_schedule(priority : str , findings : str) -> dict:
    """
    Generates the maintenace schedule based on priority
    """
    now = datetime.now()

    if priority == "CRITICAL":
        next_action = now + timedelta(hours=2)
        follow_up = now + timedelta(days=1)
    elif priority == "HIGH":
        next_action = now + timedelta(hours=8)
        follow_up = now + timedelta(days=3)
    elif priority == "MEDIUM" :
        next_action = now + timedelta(days=2)
        follow_up = now + timedelta(weeks=1)
    else :
        next_action = now + timedelta(weeks=1)
        follow_up = now + timedelta(weeks=4)

    return {
        "next_maintance":next_action.strftime("%Y-%m-%d %H:%M"),
        "follow_up_date" : follow_up.strftime("%Y-%m-%d"),
        "estimated_duration" : "2-5 hours" if  priority in ["CRITICAL","HIGH"] else "1-2 hours",
        "required_personal" : 2 if priority in ["CRITCAL" , "HIGH"] else 1
    }
    
def log_aircraft_analysis(aircraft_id : str , findings :str ,priority : str) -> Dict:
    """
    Logs maintance record 
    """
    record = {
        "aricraft_id" : aircraft_id,
        "timestamp" : datetime.now().isoformat(),
        "findings" : findings,
        "priority" : priority,
        "analyst": "AutoGen_System",
        "status": "pending_review"
    }
    logging.info(f"Maintenance record logged for aircraft {aircraft_id}")
    return record


def send_email(subject: str, message: str, sender: str = DEFAULT_SENDER, receiver: str = DEFAULT_RECEIVER) -> Dict[str, str]:
    """
    Sends email with subject and message body.
    
    Args:
        subject: Subject of the email
        message: Email body content
        sender: Sender email address
        receiver: Receiver email address
    
    Returns:
        Dictionary with status and timestamp
    """
    try:
        email = MIMEMultipart()
        email['From'] = sender
        email['To'] = receiver
        email['Subject'] = subject

        email.attach(MIMEText(message, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(user=sender, password=GMAIL_PASS)
            server.sendmail(sender, receiver, email.as_string())

        return {
            "status": "success", 
            "message": f"Email sent to {receiver}",
            "timestamp": datetime.now().isoformat()
        }

    except smtplib.SMTPAuthenticationError:
        return {
            "status": "error",
            "message": "SMTP authentication failed."
        }

#tools.
send_email_tool = FunctionTool(
    send_email,
    description="This tool will send the email to the receiver about the report ans necessary ation to be taken."

)
priority_asserment_tool = FunctionTool(
    maintenance_priority,
    description = "Analyzes maintenance findings and assigns priority levels (CRITICAL/HIGH/MEDIUM/LOW)"
)

schedule_tool = FunctionTool(
    maintenance_schedule,
    description = "Generates maintenance schedule based on priority and findings" 
)

logging_tool = FunctionTool(
    log_aircraft_analysis,
    description = "Creates audit trail by logging maintenance findings and assessments",
    
)

action_termination = TextMentionTermination(text="Please provide the flight log chat for the anyalsis.")

#==================================================================
#building agents
#==================================================================

def agent_builder(model:str ="gemini-1.5-flash-8b" , model_api_key : str = GEMINI_KEY) -> RoundRobinGroupChat:
    """
    This will build a agent and retrun a RoundRobinGroupChat.    
    """
    llm_client = OpenAIChatCompletionClient(model=model ,api_key= model_api_key,temperature=0.1)

    #agent1
    image_analysis_agent = AssistantAgent(
        name = "AIRCRAFT_ANALYZER",
        model_client = llm_client,
        system_message = """You are an expert aircraft maintenance analyst with 20+ years of experience.

        Your role:
        1. Carefully examine aircraft log images for maintenance data
        2. Extract key information: aircraft ID, flight hours, maintenance items, anomalies
        3. Identify potential safety concerns, wear patterns, and maintenance needs
        4. Provide detailed technical analysis with specific component references

        IMPORTANT: 
        - Always provide a complete analysis in a structured format
        - Include aircraft ID, maintenance findings, and any anomalies
        - Use clear headings and bullet points for easy reading
        - End your response with "ANALYSIS COMPLETE - READY FOR RISK ASSESSMENT"

        If the image does not contain clear, readable maintenance data:
        - Explicitly state "NO READABLE MAINTENANCE DATA FOUND"
        - Describe what you can see in the image
        - Provide specific guidance on what type of maintenance log image is needed

        If the image is from non avitation realted image:
        Format your response as:
        ### *Please provide the flight log chat for the anyalsis.*

        else:
        Format your response as:
        ## AIRCRAFT ANALYSIS REPORT
        **Aircraft ID:** [ID from log] else missing
        **Analysis Date:** [Current date]
        
        ### EXTRACTED DATA:
        - [Key maintenance data points]
        
        ### FINDINGS:
        - [Specific maintenance issues or observations]
        
        ### ANOMALIES/CONCERNS:
        - [Any red flags or concerning patterns]
        
        ANALYSIS COMPLETE - READY FOR RISK ASSESSMENT
        """
    )

    #agent2
    risk_asserment_agent = AssistantAgent(
        name = "RISK_ASSERSSOR",
        model_client = llm_client,
        system_message = """You are a specialized aircraft safety risk assessor.
        
        IMPORTANT: You are NOT writing code. You are analyzing aircraft maintenance data and using tools.
        
        Your responsibilities:
        1. READ and ANALYZE the complete findings from AIRCRAFT_ANALYZER
        2. Assess risk levels and safety implications based on the analysis
        3. CALL the priority_assessment_tool with the findings text from the analysis
        4. CALL the logging_tool to create maintenance records
        
        STEP-BY-STEP PROCESS:
        1. First, read and summarize the analysis from AIRCRAFT_ANALYZER
        2. Extract the key findings and concerns from the analysis
        3. Use priority_assessment_tool by calling it with the findings text
        4. Use logging_tool to record the assessment with aircraft ID and findings
        5. Provide your own risk assessment reasoning
        
        Priority Categories:
        - CRITICAL: Safety-of-flight issues requiring immediate grounding
        - HIGH: Issues that could become safety concerns within days  
        - MEDIUM: Preventive maintenance that should be scheduled soon
        - LOW: Routine maintenance items
        
        DO NOT write print statements or code. Instead, analyze the data and use the available tools.
        
        Always end with: "RISK ASSESSMENT COMPLETE - READY FOR REPORT GENERATION"
        """,
        tools=[priority_asserment_tool,logging_tool],
        reflect_on_tool_use = True
    )

    #agent3
    report_gereration_agent = AssistantAgent(
        name = "REPORT_GENERATOR",
        model_client = llm_client,
        system_message ="""You are a technical documentation specialist for aircraft maintenance.
        
        IMPORTANT: You are NOT writing code. You are creating maintenance reports and using scheduling tools.
        
        Your tasks:
        1. READ the complete analysis and risk assessment from previous agents
        2. Compile comprehensive maintenance reports from the provided data
        3. CALL the schedule_tool to create maintenance schedules based on priority
        4. Generate detailed technical documentation
        
        STEP-BY-STEP PROCESS:
        1. Summarize the analysis and risk assessment you received
        2. Extract the priority level and findings from previous agents
        3. Use schedule_tool by calling it with the priority and findings
        4. Create a comprehensive maintenance report
        
        Report format should include:
        ## MAINTENANCE REPORT
        #### Executive Summary
        #### Detailed Findings (from previous agents)
        #### Risk Assessment Results (from *RISK_ASSESSOR*)
        #### Recommended Actions
        #### Maintenance Schedule (from *schedule_tool* results)
        #### Timeline and Resources Required
        #### Compliance Notes
        
        DO NOT write print statements or code. Create actual maintenance documentation.
        
        End with: "REPORT GENERATION COMPLETE - READY FOR COMMUNICATION"
        """,
        tools=[schedule_tool],
        reflect_on_tool_use = True
    )

    #agent4
    communication_agent = AssistantAgent(
        name="COMMUNICATOR",
        model_client=llm_client,
        system_message="""You are a professional aviation communications specialist.
        
        IMPORTANT: You are NOT writing code. You are creating and sending professional emails.
        
        Your responsibilities:
        1. READ the complete report from REPORT_GENERATOR
        2. Create professional email communications based on maintenance reports
        3. CALL the send_email_tool to send notifications to stakeholders
        4. Adapt tone and urgency based on priority levels
        
        STEP-BY-STEP PROCESS:
        1. Read and summarize the maintenance report received
        2. Extract priority level and key findings
        3. Create appropriate email content based on priority
        4. Use send_email_tool to actually send the email
        
        Email guidelines:
        - CRITICAL: Subject: "🔴 URGENT: Aircraft Maintenance - Immediate Action Required"
        - HIGH: Subject: "🟠 HIGH PRIORITY: Aircraft Maintenance Alert"
        - MEDIUM: Subject: "🟡 SCHEDULED: Aircraft Maintenance Update"
        - LOW: Subject: "🟢 ROUTINE: Aircraft Maintenance Notification"
        
        Email should include:
        - Clear subject line with priority indicator
        - Executive summary of findings
        - Specific action items
        - Timeline information
        - Contact information for follow-up
        
        DO NOT write print statements or code. Create and send actual emails.
        
        End with: "COMMUNICATION COMPLETE - READY FOR QA REVIEW"
        """,
        tools = [send_email_tool],
        reflect_on_tool_use = True
    )

    #agent5
    qa_agent = AssistantAgent(
        name = "QUALITY_ASSURENCE",
        model_client = llm_client,
        system_message ="""You are the quality assurance specialist ensuring all processes meet aviation standards.
        
        Your role:
        1. READ and REVIEW all previous agent outputs
        2. Verify compliance with aviation maintenance regulations
        3. Ensure proper documentation and audit trails
        4. Validate that all critical issues are properly escalated
        
        Quality checks:
        - Verify technical accuracy of findings
        - Confirm appropriate priority assignments
        - Ensure complete documentation
        - Validate communication protocols
        
        Provide a final QA summary with:
        ## QUALITY ASSURANCE REVIEW
        ### Process Verification
        ### Compliance Check
        ### Documentation Review
        ### Final Recommendations
        
        End with: "QUALITY ASSURANCE COMPLETE - WORKFLOW FINISHED"
        """
    )

    return RoundRobinGroupChat(
        participants=[image_analysis_agent,risk_asserment_agent,report_gereration_agent,communication_agent,qa_agent],
        max_turns = 5,
        termination_condition=action_termination
    )

#==================================================================
async def run_agent(img :bytes,
                    aircraft_id: Optional[str] = None,
                    priority_override: Optional[str] = None)-> AsyncGenerator[str, None]:
    """
    Enhanced function to run the complete aircraft maintenance analysis workflow.
    
    Args:
        img_data: Image data as bytes
        aircraft_id: Optional aircraft identifier
        priority_override: Optional priority level override
    """
    try:
        team = agent_builder()
        image = Image.open(io.BytesIO(img))

        task_content = f"""
            AIRCRAFT MAINTENANCE LOG ANALYSIS REQUEST
            
            Please analyze the attached aircraft journey/maintenance log image and perform a complete assessment:
            
            WORKFLOW STEPS:
            1. AIRCRAFT_ANALYZER: Extract and analyze all maintenance data from the image
            2. RISK_ASSESSOR: Assess risks and assign priorities using tools
            3. REPORT_GENERATOR: Generate comprehensive maintenance report with scheduling
            4. COMMUNICATOR: Create and send professional notifications
            5. QUALITY_ASSURANCE: Review entire process for compliance
            
            Parameters:
            - Aircraft ID: {aircraft_id or 'To be determined from log'}
            - Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            - Priority Override: {priority_override or 'None - determine from analysis'}
            
            Each agent must read the previous agent's complete output before proceeding.
            Focus on safety-critical items and provide specific, actionable recommendations.
            """
        
        task = MultiModalMessage(content=[task_content ,AGImage(image)],source="maintance_system",)
        
        async for msg in team.run_stream(task=task):
            if isinstance(msg, TextMessage):
                timestamp = datetime.now().strftime('%H:%M:%S')
                yield f"[{timestamp}] {msg.source}: {msg.content}"
                logging.info(f"Agent {msg.source} completed .")

        logging.info("Aircraft maintenance analysis workflow completed successfully")

    except Exception as e:
        raise CustomException(e,sys)


if __name__ == "__main__":
    async def _demo() -> None:
        async for line in run_agent(img = Image.open("backend\img1.png")):
            print(line)

    asyncio.run(_demo())