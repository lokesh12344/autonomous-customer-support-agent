"""
Streamlit Web UI for Autonomous Customer Support Agent
"""

import streamlit as st
import requests
from datetime import datetime
import json

# FastAPI backend URL
API_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="Customer Support Agent",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d%H%M%S")

# Sidebar
with st.sidebar:
    st.title("🤖 Support Agent")
    st.markdown("---")
    
    st.subheader("Quick Actions")
    
    # Test buttons
    if st.button("🧪 Test Database"):
        with st.spinner("Testing database..."):
            try:
                # Test fetch customer
                response = requests.post(
                    f"{API_URL}/chat/",
                    json={"message": "Fetch customer CUST001"}
                )
                st.success("Database connected!")
            except Exception as e:
                st.error(f"Database error: {e}")
    
    if st.button("🔍 Test Vector Search"):
        with st.spinner("Testing vector store..."):
            try:
                response = requests.post(
                    f"{API_URL}/chat/",
                    json={"message": "How do I get a refund?"}
                )
                st.success("Vector store connected!")
            except Exception as e:
                st.error(f"Vector store error: {e}")
    
    st.markdown("---")
    
    st.subheader("Sample Queries")
    
    sample_queries = [
        "What is customer CUST001's email?",
        "Show me orders for customer CUST002",
        "Check status of order ORD0001",
        "How do I get a refund?",
        "What payment methods do you accept?",
        "How long does shipping take?",
    ]
    
    for query in sample_queries:
        if st.button(query, key=query):
            st.session_state.messages.append({"role": "user", "content": query})
            st.rerun()
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    # API Status
    st.markdown("---")
    st.subheader("API Status")
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Error")
    except:
        st.error("❌ API Offline")

# Main content
st.title("🤖 Autonomous Customer Support Agent")
st.markdown("Ask me anything about orders, customers, refunds, or FAQs!")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your question here..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{API_URL}/chat/",
                    json={
                        "message": prompt,
                        "session_id": st.session_state.session_id
                    },
                    timeout=120
                )
                
                if response.status_code == 200:
                    assistant_response = response.json()["response"]
                else:
                    assistant_response = f"Error: {response.status_code} - {response.text}"
            
            except requests.exceptions.Timeout:
                assistant_response = "Request timed out. Please try again."
            except Exception as e:
                assistant_response = f"Error connecting to API: {str(e)}\n\nMake sure the FastAPI server is running on port 8000."
        
        message_placeholder.markdown(assistant_response)
    
    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Messages", len(st.session_state.messages))

with col2:
    st.metric("Session ID", st.session_state.session_id[-6:])

with col3:
    if st.session_state.messages:
        last_time = datetime.now().strftime("%H:%M:%S")
        st.metric("Last Activity", last_time)
