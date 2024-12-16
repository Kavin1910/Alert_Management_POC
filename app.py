import os
import time
import google.generativeai as genai
import psutil  # System monitoring
import streamlit as st
from dotenv import load_dotenv  # For environment variable management

# Load environment variables from the .env file
load_dotenv()  # This loads the API key stored in the .env file

# Configure Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create the model configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Initialize the model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Function to send the message with retry logic on rate limit exceeded
def send_request_with_throttling(prompt):
    try:
        # Start a new chat session
        chat_session = model.start_chat(
            history=[]
        )

        # Send the message to Gemini API
        response = chat_session.send_message(prompt)

        # Return the response text
        return response.text
    except Exception as e:
        # Check for rate limit exceeded error
        if "RATE_LIMIT_EXCEEDED" in str(e):
            print(f"Rate limit exceeded: {e}")
            print("Waiting for 1 minute before retrying...")
            time.sleep(60)  # Wait for 60 seconds before retrying
            return send_request_with_throttling(prompt)  # Retry the request
        else:
            raise e  # If not a rate limit error, raise the exception

# Function to get AI-generated solution from Gemini based on system metric
def get_ai_solution(metric_name, value):
    prompt = f"The {metric_name} usage is {value}%. Provide step-by-step recommendations on how to resolve high {metric_name} usage."
    
    # Send the prompt to the API and get the response with retry logic
    return send_request_with_throttling(prompt)

# Streamlit UI layout
st.title("POC- System Metrics Monitoring")

# Threshold for triggering alerts
THRESHOLD = 75  # You can change this threshold as needed

# Monitor CPU Usage
cpu_usage = psutil.cpu_percent(interval=1)
st.write(f"CPU Usage: {cpu_usage:.2f}%")
if cpu_usage > THRESHOLD:
    st.warning(f"CPU usage is high! ({cpu_usage:.2f}%)")
    solution = get_ai_solution("CPU", cpu_usage)
    st.write(f"### AI-generated Solution for CPU Usage:")
    st.write(solution)
else:
    st.success("CPU usage is within normal limits.")

st.write("---")

# Monitor Memory Usage
memory_usage = psutil.virtual_memory().percent
st.write(f"Memory Usage: {memory_usage:.2f}%")
if memory_usage > THRESHOLD:
    st.warning(f"Memory usage is high! ({memory_usage:.2f}%)")
    solution = get_ai_solution("Memory", memory_usage)
    st.write(f"### AI-generated Solution for Memory Usage:")
    st.write(solution)
else:
    st.success("Memory usage is within normal limits.")

st.write("---")

# Monitor Network Usage (bytes per second)
# Calculate the network usage based on bytes sent and received in 1 second
net_before = psutil.net_io_counters()
time.sleep(1)  # Wait for 1 second
net_after = psutil.net_io_counters()

# Calculate bytes per second (network speed)
network_usage = ((net_after.bytes_recv + net_after.bytes_sent) - (net_before.bytes_recv + net_before.bytes_sent)) / (1024 * 1024)  # in MB/s
st.write(f"Network Usage: {network_usage:.2f} MB/s")
if network_usage > THRESHOLD:
    st.warning(f"Network usage is high! ({network_usage:.2f} MB/s)")
    solution = get_ai_solution("Network", network_usage)
    st.write(f"### AI-generated Solution for Network Usage:")
    st.write(solution)
else:
    st.success("Network usage is within normal limits.")

st.write("---")

# Monitor Disk I/O Usage (MB read/write per second)
# Calculate disk I/O usage based on read and write operations in 1 second
disk_before = psutil.disk_io_counters()
time.sleep(1)  # Wait for 1 second
disk_after = psutil.disk_io_counters()

# Calculate MB/s read/write
disk_io_usage = ((disk_after.read_bytes + disk_after.write_bytes) - (disk_before.read_bytes + disk_before.write_bytes)) / (1024 * 1024)  # in MB/s
st.write(f"Disk I/O Usage: {disk_io_usage:.2f} MB/s")
if disk_io_usage > THRESHOLD:
    st.warning(f"Disk I/O usage is high! ({disk_io_usage:.2f} MB/s)")
    solution = get_ai_solution("Disk I/O", disk_io_usage)
    st.write(f"### AI-generated Solution for Disk I/O Usage:")
    st.write(solution)
else:
    st.success("Disk I/O usage is within normal limits.")

# --- Chatbot Section ---
st.write("---")
st.subheader("Ask the AI a question:")

# Input text box for user to ask a question
user_question = st.text_input("Type your question here:")

# Check if the user asked a question and get the response from the AI
if user_question:
    response = send_request_with_throttling(user_question)
    st.write(f"### AI's Answer:")
    st.write(response)

# --- Custom CSS for Fading In Effect (text box remains always visible) ---
st.markdown("""
    <style>
        /* Fade-in effect for the text box on page load */
        .stTextInput input {
            opacity: 0;
            animation: fadeIn 2s forwards;
        }

        /* Define the fade-in animation */
        @keyframes fadeIn {
            0% { opacity: 0; }
            100% { opacity: 1; }
        }

        /* Keep the text box always visible */
        .stTextInput input:focus {
            opacity: 1;  /* Remain visible when focused */
        }
    </style>
""", unsafe_allow_html=True)
