import streamlit as st
import requests
import google.generativeai as genai
from together import Together
from dotenv import load_dotenv
import os

# ------------------ LOAD ENV ------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
OPENROUTER_KEYS = os.getenv("OPENROUTER_API_KEYS", "").split(",")

EXA_API_KEY = "12d72bbb-1a3a-41f8-9be3-04ae796352da"
EXA_SEARCH_URL = "https://api.exa.ai/search"

TAVILY_API_KEY = "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"
TAVILY_URL = "https://api.tavily.com/search"

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

    with st.expander("🔽 Scira Functionality", expanded=True):
        chain_mode = st.toggle("🔁 Enable Chain Mode")
        enable_web_search = st.toggle("🌐 Enable Web Search")
        include_reddit = st.toggle("📥 Include Reddit Posts")
        include_youtube = st.toggle("🎥 Include YouTube Links")

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

def web_search_exa(query):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {EXA_API_KEY}"
    }
    payload = {
        "query": query,
        "numResults": 3
    }
    try:
        res = requests.post(EXA_SEARCH_URL, headers=headers, json=payload)
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            if not results:
                return "⚠️ No results found from web search."

            context = ""
            for r in results:
                title = r.get("title", "Untitled")
                url = r.get("url", "")
                snippet = r.get("text", r.get("snippet", "No snippet available"))
                link = f"[🔹 **{title}**]({url})"
                context += f"{link}\n\n{snippet}\n\n"

            return f"### 🌐 Web Search Results\n\n{context.strip()}"
        else:
            return f"⚠️ Web search failed: {res.status_code} - {res.text}"
    except Exception as e:
        return f"⚠️ Web search error: {str(e)}"

def search_reddit_with_tavily(query):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TAVILY_API_KEY}"
    }
    payload = {
        "query": f"{query} site:reddit.com",
        "search_depth": "advanced",
        "include_answer": False,
        "max_results": 5
    }
    try:
        res = requests.post(TAVILY_URL, headers=headers, json=payload)
        if res.status_code == 200:
            results = res.json().get("results", [])
            links = [f"{r.get('url', '')}" for r in results if r.get("url")]
            formatted_links = "\n".join([f"- [{url}]({url})" for url in links])
            return f"### 📥 Reddit Links\n\n{formatted_links}"
        else:
            return f"⚠️ Reddit search failed: {res.status_code} - {res.text}"
    except Exception as e:
        return f"⚠️ Reddit search error: {str(e)}"

import re

def extract_youtube_id(url):
    # Extract YouTube video ID using regex
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

def search_youtube_with_tavily(query):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TAVILY_API_KEY}"
    }
    payload = {
        "query": f"{query} site:youtube.com",
        "search_depth": "advanced",
        "include_answer": False,
        "max_results": 3
    }
    try:
        res = requests.post(TAVILY_URL, headers=headers, json=payload)
        if res.status_code == 200:
            results = res.json().get("results", [])
            formatted_blocks = ""
            for r in results:
                url = r.get("url", "")
                if not url:
                    continue
                video_id = extract_youtube_id(url)
                if video_id:
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                    block = f"""
<img src="{thumbnail_url}" width="320"><br>
🔗 [Watch Video]({url})  
<br><br>
"""
                    formatted_blocks += block
            return f"### 🎥 YouTube Links with Thumbnails\n\n{formatted_blocks}"
        else:
            return f"⚠️ YouTube search failed: {res.status_code} - {res.text}"
    except Exception as e:
        return f"⚠️ YouTube search error: {str(e)}"


# ------------------ LLM CALL FUNCTION ------------------
def call_llm(prompt, full_label):
    model = extract_model_name(full_label)
    model_lower = model.lower()

    if "gemini" in model_lower:
        try:
            gemini_model = genai.GenerativeModel("models/gemini-1.5-flash")
            response = gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ Gemini Error: {str(e)}"

    elif any(k in model_lower for k in ["llama-vision", "deepseek-r1-distill"]):
        try:
            response = together_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Together Error: {str(e)}"

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

    elif "mistral-small" in model_lower or "mistral-medium" in model_lower or "mistral-large" in model_lower:
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
                return f"❌ MistralAI Error {res.status_code}: {res.text}"
        except Exception as e:
            return f"❌ MistralAI Exception: {str(e)}"

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
    enriched_prompt = prompt

    if enable_web_search:
        with st.spinner("🔎 Searching the web..."):
            search_results = web_search_exa(prompt)
            st.markdown(search_results, unsafe_allow_html=True)
            enriched_prompt += f"\n\n{search_results}"

    if include_reddit:
        with st.spinner("📥 Searching Reddit..."):
            reddit_results = search_reddit_with_tavily(prompt)
            st.markdown(reddit_results, unsafe_allow_html=True)
            enriched_prompt += f"\n\n{reddit_results}"

    if include_youtube:
        with st.spinner("🎥 Searching YouTube..."):
            youtube_results = search_youtube_with_tavily(prompt)
            st.markdown(youtube_results, unsafe_allow_html=True)
            enriched_prompt += f"\n\n{youtube_results}"

    if chain_mode and selected_models:
        current_input = enriched_prompt
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

    elif not chain_mode and 'selected_model' in locals():
        with st.spinner(f"🤖 Thinking using {selected_model}..."):
            response = call_llm(enriched_prompt, selected_model)

    if response:
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
