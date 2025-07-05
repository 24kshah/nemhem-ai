import streamlit as st
import requests
import random

# ------------------ CONFIG ------------------
API_KEYS = [
    "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"
]

MODEL_OPTIONS = [
    "mistralai/mistral-7b-instruct",
    "mistralai/mistral-small-3.2-24b-instruct:free",
    "openrouter/cypher-alpha:free",
    "moonshotai/kimi-dev-72b:free",
    "deepseek/deepseek-r1-0528-qwen3-8b:free",
    "deepseek/deepseek-r1-0528:free",
    "sarvamai/sarvam-m:free",
    "mistralai/devstral-small:free",
    "qwen/qwen3-30b-a3b:free",
    "qwen/qwen3-8b:free",
    "qwen/qwen3-14b:free",
    "qwen/qwen3-32b:free",
    "qwen/qwen3-235b-a22b:free",
    "tngtech/deepseek-r1t-chimera:free",
    "microsoft/mai-ds-r1:free",
    "thudm/glm-z1-32b:free",
    "meta-llama/llama-4-maverick:free",
    "deepseek/deepseek-v3-base:free",
    "deepseek/deepseek-chat-v3-0324:free",
    "featherless/qwerky-72b:free",
    "cognitivecomputations/dolphin3.0-r1-mistral-24b:free",
    "deepseek/deepseek-r1:free",
    "deepseek/deepseek-chat:free"
]

BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# ------------------ STREAMLIT PAGE SETUP ------------------
st.set_page_config("Unified AI Chat", layout="wide")
st.title("🧠 NemHem Unified AI Interface")

# ------------------ SESSION STATE ------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ------------------ SIDEBAR ------------------
with st.sidebar:
    st.header("⚙️ Options")
    chain_mode = st.toggle("🔁 Enable Chain Mode")
    if chain_mode:
        selected_models = st.multiselect("🤖 Select Models to Chain", MODEL_OPTIONS)
    else:
        selected_model = st.selectbox("🤖 Choose LLM", MODEL_OPTIONS)

    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []

# ------------------ DISPLAY CHAT HISTORY ------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------ Helper: Call LLM ------------------
def call_llm(prompt, model):
    for key in API_KEYS:
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            res = requests.post(BASE_URL, headers=headers, json=payload)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            elif res.status_code in (401, 403, 429):
                continue  # Try next key
            else:
                return f"❌ Error {res.status_code}: {res.text}"
        except Exception as e:
            continue  # Try next key

    return "❌ All API keys failed or were rate-limited."

# ------------------ CHAT INPUT ------------------
prompt = st.chat_input("Ask me anything...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = None

    if chain_mode and selected_models:
        current_input = prompt
        for idx, model in enumerate(selected_models):
            st.markdown(f"#### 🔗 Model {idx+1}: `{model}`")
            with st.spinner(f"🤖 Thinking using {model}..."):
                output = call_llm(current_input, model)
                st.code(output)
                current_input = output
        response = current_input
    else:
        with st.spinner(f"🤖 Thinking using {selected_model}..."):
            response = call_llm(prompt, selected_model)

    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
