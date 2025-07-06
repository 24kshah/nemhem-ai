import streamlit as st
import requests
import google.generativeai as genai
from together import Together

# ------------------ LOAD SECRETS ------------------
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
MISTRAL_API_KEY = st.secrets["MISTRAL_API_KEY"]
OPENROUTER_KEYS = st.secrets["OPENROUTER_API_KEYS"].split(",")

genai.configure(api_key=GEMINI_API_KEY)
together_client = Together(api_key=TOGETHER_API_KEY)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# ------------------ MODEL OPTIONS ------------------
MODEL_OPTIONS = [
    "🔹 Gemini: gemini/gemini-1.5-flash",
    "🟦 Together: meta-llama/Llama-Vision-Free",
    "🟦 Together: deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
    "🟧 Groq: llama3-8b-8192",
    "🟧 Groq: llama3-70b-8192",
    "🟧 Groq: mixtral-8x7b-32768",
    "🟧 Groq: gemma-7b-it",
    "🟥 MistralAI: mistral-small-latest",
    "🟩 OpenRouter: mistralai/mistral-7b-instruct",
    "🟩 OpenRouter: moonshotai/kimi-dev-72b:free",
    "🟩 OpenRouter: deepseek/deepseek-r1-0528-qwen3-8b:free"
]

# ------------------ STREAMLIT UI ------------------
st.set_page_config("Unified AI Chat", layout="wide")
st.title("🧠 NemHem Unified AI Interface")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("⚙️ Options")
    chain_mode = st.toggle("🔁 Enable Chain Mode")
    if chain_mode:
        selected_models = st.multiselect("🤖 Select Models to Chain", MODEL_OPTIONS)
    else:
        selected_model = st.selectbox("🤖 Choose LLM", MODEL_OPTIONS)

    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------ UTILITIES ------------------
def extract_model_name(full_label):
    return full_label.split(":", 1)[-1].strip()

# ------------------ LLM CALL FUNCTION ------------------
def call_llm(prompt, full_label):
    model = extract_model_name(full_label)
    model_lower = model.lower()

    # Gemini
    if "gemini" in model_lower:
        try:
            gemini_model = genai.GenerativeModel("models/gemini-1.5-flash")
            response = gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ Gemini Error: {str(e)}"

    # Together
    elif any(k in model_lower for k in ["llama-vision", "deepseek-r1-distill"]):
        try:
            response = together_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Together Error: {str(e)}"

    # Groq
    elif any(k in model_lower for k in ["llama3", "mixtral", "gemma"]):
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}]
            }
            res = requests.post(url, headers=headers, json=payload)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            else:
                return f"❌ Groq Error {res.status_code}: {res.text}"
        except Exception as e:
            return f"❌ Groq Exception: {str(e)}"

    # Mistral
    elif "mistral-small" in model_lower:
        try:
            url = "https://api.mistral.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {MISTRAL_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}]
            }
            res = requests.post(url, headers=headers, json=payload)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            else:
                return f"❌ Mistral Error {res.status_code}: {res.text}"
        except Exception as e:
            return f"❌ Mistral Exception: {str(e)}"

    # OpenRouter
    else:
        for key in OPENROUTER_KEYS:
            headers = {
                "Authorization": f"Bearer {key.strip()}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}]
            }
            try:
                res = requests.post(OPENROUTER_BASE_URL, headers=headers, json=payload)
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"]
                elif res.status_code in (401, 403, 429):
                    continue
                else:
                    return f"❌ OpenRouter Error {res.status_code}: {res.text}"
            except Exception:
                continue
        return "❌ All OpenRouter API keys failed or were rate-limited."

# ------------------ CHAT INPUT ------------------
prompt = st.chat_input("Ask me anything...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = None

    if chain_mode and selected_models:
        current_input = prompt
        for idx, model_label in enumerate(selected_models):
            st.markdown(f"#### 🔗 Model {idx+1}: `{model_label}`")
            with st.spinner(f"🤖 Thinking using {model_label}..."):
                output = call_llm(current_input, model_label)
                if output.startswith("❌"):
                    st.error(output)
                    break
                st.code(output)
                current_input = output
        response = current_input
    else:
        with st.spinner(f"🤖 Thinking using {selected_model}..."):
            response = call_llm(prompt, selected_model)

    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
