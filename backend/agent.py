import operator
import os
import time
import razorpay
from dotenv import load_dotenv
from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables
load_dotenv()

# Initialize Razorpay Client
rzp_client = razorpay.Client(auth=(os.getenv("RAZORPAY_KEY_ID", ""), os.getenv("RAZORPAY_KEY_SECRET", "")))

# Define the State Schema
class RevenueRecoveryState(TypedDict):
    transaction_id: str
    error_code: str
    intent_classification: str
    recovery_amount: int
    audit_trail: Annotated[List[str], operator.add]
    interrupt_flag: bool
    diagnostic_details: dict

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0, google_api_key=os.getenv("GEMINI_API_KEY"))

# Nodes (Subgraphs/Agents)
async def diagnostic_agent(state: RevenueRecoveryState):
    """
    Translates ISO 8583 response codes and isolates fault domain.
    """
    error_code = state.get("error_code")
    audit_trail = ["Diagnostic Agent invoked."]
    
    # Prompt LLM or use deterministic logic based on ISO 8583
    prompt = f"""
    Analyze the transaction failure code: {error_code}.
    Determine if this is a 'soft_decline' or 'hard_decline' and provide reasoning.
    Format your response exactly as: CLASS: [soft_decline|hard_decline]
    """
    response = await llm.ainvoke([SystemMessage(content="You are a payment diagnostic AI."), HumanMessage(content=prompt)])
    
    classification = "hard_decline"
    if "soft_decline" in response.content.lower():
        classification = "soft_decline"
        
    audit_trail.append(f"Diagnosis completed. Classified as {classification}.")
    
    # Trigger human review for very specific edge cases (e.g. lost/stolen card code 41 or 43)
    interrupt_flag = False
    if error_code in ["41", "43"]:
        interrupt_flag = True
        audit_trail.append("Fraud suspected. Raising interrupt_flag.")

    return {
        "intent_classification": classification,
        "audit_trail": audit_trail,
        "interrupt_flag": interrupt_flag
    }

async def intervention_agent(state: RevenueRecoveryState):
    """
    Selects recovery tool based on classification.
    """
    from ml_models import churn_model, retry_optimizer
    import numpy as np

    classification = state.get("intent_classification")
    audit_trail = ["Intervention Agent invoked."]
    
    if classification == "soft_decline":
        # Check churn probability
        # In a real app, features would be fetched from a user profile DB
        user_features = {"historical_failure_rate": 0.5} 
        churn_risk = churn_model.predict_churn_probability(user_features)
        
        if churn_risk > 0.7:
            audit_trail.append(f"High churn risk detected ({churn_risk:.2f}). Upgrading to 'dunning_outreach' with discount.")
            state["intent_classification"] = "hard_decline" # Force dunning
            classification = "hard_decline"
        else:
            # Use CMAB to find optimal retry window
            # Context vector could be [hour_of_day, day_of_month, ticket_size_normalized, historical_success]
            context_vector = np.array([12, 1, 0.5, 0.8]) 
            best_arm = retry_optimizer.choose_arm(context_vector)
            retry_windows = [24, 72, 168]
            selected_window = retry_windows[best_arm]
            audit_trail.append(f"Selected 'silent_retry' via CMAB scheduling. Scheduled for {selected_window} hours from now.")
    
    if classification == "hard_decline":
        audit_trail.append("Selected 'dunning_outreach' via Payment Links.")
        
    return {"audit_trail": audit_trail, "intent_classification": classification}

async def dunning_agent(state: RevenueRecoveryState):
    """
    Drafts compliant communication and generates a Razorpay Payment Link for Hard Declines.
    """
    classification = state.get("intent_classification")
    if classification == "soft_decline":
        return {"audit_trail": ["Dunning Agent bypassed (Soft Decline)."]}
        
    audit_trail = ["Dunning Agent invoked."]
    recovery_amount = state.get("recovery_amount", 0)
    
    # 1. Generate Razorpay Payment Link
    try:
        payment_link = rzp_client.payment_link.create({
            "amount": recovery_amount,
            "currency": "INR",
            "accept_partial": True,
            "expire_by": int(time.time()) + 86400, # Expires in 24 hours
            "reference_id": state.get("transaction_id"),
            "description": "Payment resolution for failed transaction",
            "notify": {
                "sms": True,
                "email": True
            }
        })
        link_url = payment_link.get('short_url', '[Link URL]')
        audit_trail.append(f"Successfully generated Payment Link: {link_url}")
    except Exception as e:
        audit_trail.append(f"Failed to generate Payment Link (check API keys). Mocking link for now.")
        link_url = "https://rzp.io/i/mock_link"
    
    # 2. Draft the compliant SMS using the LLM
    prompt = f"Draft a polite, compliant SMS notification (under 160 chars) requesting the user to pay their failed transaction of amount {recovery_amount / 100} INR. Include this payment link: {link_url}"
    
    # Simulate NeMo guardrails by enforcing strict prompting here
    response = await llm.ainvoke([
        SystemMessage(content="You are a strict debt collection AI adhering to RBI guidelines. Never threaten the customer. Keep it professional."),
        HumanMessage(content=prompt)
    ])
    
    audit_trail.append(f"Dunning message drafted: {response.content}")
    return {"audit_trail": audit_trail}

# Edge Logic
def route_after_diagnostic(state: RevenueRecoveryState):
    if state.get("interrupt_flag"):
        return "human_review"
    return "intervention_agent"

def human_review_node(state: RevenueRecoveryState):
    return {"audit_trail": ["Paused for Human-in-the-Loop review."]}

# Build the Graph
workflow = StateGraph(RevenueRecoveryState)

workflow.add_node("diagnostic_agent", diagnostic_agent)
workflow.add_node("intervention_agent", intervention_agent)
workflow.add_node("dunning_agent", dunning_agent)
workflow.add_node("human_review", human_review_node)

workflow.set_entry_point("diagnostic_agent")
workflow.add_conditional_edges(
    "diagnostic_agent",
    route_after_diagnostic,
    {
        "intervention_agent": "intervention_agent",
        "human_review": "human_review"
    }
)

workflow.add_edge("intervention_agent", "dunning_agent")
workflow.add_edge("dunning_agent", END)
workflow.add_edge("human_review", END) # In reality, human review resumes to intervention.

# Graph compilation requires Postgres checkpointer for state persistence
# This is handled dynamically when the graph is executed in tasks.py
