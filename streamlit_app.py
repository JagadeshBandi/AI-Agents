import streamlit as st
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agent import AIAgent, MultiModalAgent, ToolUsingAgent
from src.training import TrainingManager

# Page configuration
st.set_page_config(
    page_title="AI Agents",
    page_icon="Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: flex-start;
        gap: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 2rem;
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 2rem;
    }
    .message-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: white;
    }
    .user-avatar {
        background-color: #2196f3;
    }
    .assistant-avatar {
        background-color: #4caf50;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'agent' not in st.session_state:
    st.session_state.agent = None

def initialize_agent(provider, model):
    """Initialize the AI agent"""
    try:
        st.session_state.agent = AIAgent(provider_type=provider)
        return True
    except Exception as e:
        st.error(f"Error initializing agent: {e}")
        return False

def display_message(role, content):
    """Display a chat message"""
    with st.container():
        if role == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <div class="message-avatar user-avatar">U</div>
                <div class="message-content">{content}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <div class="message-avatar assistant-avatar">AI</div>
                <div class="message-content">{content}</div>
            </div>
            """, unsafe_allow_html=True)

def main():
    st.title("AI Agents")
    st.markdown("Build and interact with your own AI assistant")
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        
        # Provider selection
        provider = st.selectbox(
            "LLM Provider",
            ["openai", "anthropic", "huggingface"],
            help="Choose the AI provider"
        )
        
        # Model selection
        models = {
            "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"],
            "anthropic": ["claude-3-sonnet-20240229", "claude-3-opus-20240229"],
            "huggingface": ["microsoft/DialoGPT-medium", "microsoft/DialoGPT-large"]
        }
        
        model = st.selectbox(
            "Model",
            models[provider],
            help="Choose the specific model"
        )
        
        # Parameters
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Controls randomness in responses"
        )
        
        max_tokens = st.number_input(
            "Max Tokens",
            min_value=100,
            max_value=4000,
            value=1000,
            step=100,
            help="Maximum response length"
        )
        
        # Initialize button
        if st.button("Initialize Agent", type="primary"):
            if initialize_agent(provider, model):
                st.session_state.conversation_id = None
                st.session_state.messages = []
                st.success("Agent initialized successfully!")
                st.rerun()
    
    # Main chat interface
    if st.session_state.agent is None:
        st.info("Please configure and initialize the agent in the sidebar.")
        return
    
    # Chat history
    st.header("Chat")
    
    # Display messages
    for message in st.session_state.messages:
        display_message(message["role"], message["content"])
    
    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Type your message...",
            height=100,
            placeholder="Enter your message here..."
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            send_button = st.form_submit_button("Send", type="primary")
        with col2:
            clear_button = st.form_submit_button("Clear Chat")
    
    # Handle clear button
    if clear_button:
        st.session_state.messages = []
        st.session_state.conversation_id = None
        st.rerun()
    
    # Handle send button
    if send_button and user_input.strip():
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Start new conversation if needed
        if st.session_state.conversation_id is None:
            import asyncio
            st.session_state.conversation_id = asyncio.run(
                st.session_state.agent.start_conversation()
            )
        
        # Generate response
        with st.spinner("AI is thinking..."):
            try:
                import asyncio
                response = asyncio.run(
                    st.session_state.agent.chat(
                        st.session_state.conversation_id,
                        user_input,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                )
                
                # Add assistant response
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response["response"]
                })
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Error generating response: {e}")
    
    # Training section
    st.markdown("---")
    st.header("Training")
    
    with st.expander("Fine-tune your own model"):
        st.write("Train a custom model on your own data")
        
        # Training options
        training_option = st.selectbox(
            "Training Data",
            ["Sample Data", "Custom Dataset", "Hugging Face Dataset"]
        )
        
        if training_option == "Sample Data":
            st.write("Use sample conversation data for testing")
            if st.button("Run Sample Training"):
                with st.spinner("Training..."):
                    try:
                        from src.training import quick_fine_tune_example
                        quick_fine_tune_example()
                        st.success("Training completed!")
                    except Exception as e:
                        st.error(f"Training error: {e}")
        
        elif training_option == "Custom Dataset":
            uploaded_file = st.file_uploader(
                "Upload your training data (JSON)",
                type="json"
            )
            if uploaded_file and st.button("Train with Custom Data"):
                st.info("Custom training not implemented in this demo")
        
        elif training_option == "Hugging Face Dataset":
            dataset_name = st.text_input(
                "Dataset Name",
                value="databricks/databricks-dolly-15k"
            )
            if st.button("Train with HF Dataset"):
                st.info("HF dataset training not implemented in this demo")
    
    # Information section
    with st.expander("About AI Agents"):
        st.markdown("""
        ### Features
        - **Multiple LLM Providers**: OpenAI, Anthropic, Hugging Face
        - **Conversation Management**: Persistent chat history
        - **Customizable Parameters**: Temperature, max tokens, etc.
        - **Training Capabilities**: Fine-tune models on your data
        - **Web Interface**: Clean and responsive UI
        
        ### Getting Started
        1. Configure your API keys in the `.env` file
        2. Choose your preferred LLM provider
        3. Initialize the agent
        4. Start chatting!
        
        ### Training Your Model
        - Prepare your conversation data in JSON format
        - Use the training section to fine-tune a model
        - Export and use your custom model
        """)

if __name__ == "__main__":
    main()
