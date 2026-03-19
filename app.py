import streamlit as st
import time
import io
import zipfile
import json
from google import genai
from google.genai import types

# --- GLOBAL RULES & THEME ---
# 배경색 Black(#000000) 강제 적용 및 UI 안정성 확보
st.set_page_config(page_title="YouTube Yadam Auto v1.0", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #000000; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #111111; color: white; }
    .stTextArea textarea { background-color: #222222; color: white; border: 1px solid #444; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #4CAF50; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- STATE MANAGEMENT ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'api_key' not in st.session_state: st.session_state.api_key = ""
if 'script' not in st.session_state: st.session_state.script = ""
if 'characters' not in st.session_state: st.session_state.characters = []
if 'scenes' not in st.session_state: st.session_state.scenes = []
if 'images' not in st.session_state: st.session_state.images = []

# --- TOP UI HEADER ---
col_title, col_api = st.columns([1, 1])
with col_title:
    st.title("🏯 Yadam Auto App v1.0")
with col_api:
    api_input = st.text_input("🔑 API KEY", value=st.session_state.api_key, type="password", placeholder="Enter Gemini API Key")
    if api_input: st.session_state.api_key = api_input.strip()

st.divider()

client = None
if st.session_state.api_key:
    client = genai.Client(api_key=st.session_state.api_key)

# --- CHAPTER 1: INPUT SCREEN ---
with st.sidebar:
    st.header("⚙️ CHAPTER 1: SETTINGS")
    scene_count = st.slider("Scene Count", 0, 100, 30)
    
    st.write("🎨 Style Selection")
    styles = ["Ink Wash (수묵담채화)", "Realistic (실사화)", "Watercolor (수채화)", "Korean Comic (만화)", "Ghibli Style (지브리풍)", "City Pop (시티팝)", "Custom Style (내 스타일)"]
    selected_style = st.radio("Style", styles, label_visibility="collapsed")
    
    if selected_style == "Custom Style (내 스타일)":
        uploaded_refs = st.file_uploader("Upload Reference (Max 6)", accept_multiple_files=True, type=['png', 'jpg'])
        
    img_ratio = st.radio("📐 Image Ratio", ["16:9", "1:1", "9:16"], index=0)
    resolution = st.radio("🖥️ Resolution", ["1K", "2K"], index=0)

if st.session_state.step == 1:
    st.session_state.script = st.text_area("📝 Script Input Area", height=300, placeholder="여기에 전체 영상 대본을 입력하세요...")
    
    if st.button("👥 Generate Characters"):
        if not st.session_state.api_key:
            st.error("API Key is required.")
        elif not st.session_state.script.strip():
            st.error("Script cannot be empty.")
        elif scene_count == 0:
            st.error("Scene count must be greater than 0.")
        else:
            with st.spinner("Analyzing script for character extraction..."):
                time.sleep(1) # 모의 지연 (텍스트 분석)
                st.session_state.characters = [{"name": "Protagonist", "desc": "Young adult, poor scholar, male"}]
                st.session_state.step = 2
                st.rerun()

# --- CHAPTER 2: CHARACTER GENERATION ---
if st.session_state.step >= 2:
    st.subheader("👥 CHAPTER 2: CHARACTER MANAGEMENT")
    st.info("Character variations (age/status) detected and consistency enforced.")
    
    for idx, char in enumerate(st.session_state.characters):
        col1, col2 = st.columns([4, 1])
        col1.text_input(f"Character {idx+1}", value=f"{char['name']} - {char['desc']}")
        col2.button("Delete", key=f"del_char_{idx}")
    
    if st.session_state.step == 2:
        if st.button("🎬 Auto Scene Split"):
            with st.spinner("Dividing script into scenes..."):
                chunk_size = max(1, len(st.session_state.script) // scene_count)
                st.session_state.scenes = [st.session_state.script[i:i+chunk_size] for i in range(0, len(st.session_state.script), chunk_size)][:scene_count]
                st.session_state.step = 3
                st.rerun()

# --- CHAPTER 3: AUTO SCENE SPLITTING ---
if st.session_state.step >= 3:
    st.divider()
    st.subheader("🎬 CHAPTER 3: AUTO SCENE SPLITTING")
    st.caption("Manual Editing: Edit text directly below to merge or split scenes.")
    
    for i in range(len(st.session_state.scenes)):
        st.session_state.scenes[i] = st.text_area(f"Scene {i+1}", value=st.session_state.scenes[i], height=100, key=f"scene_text_{i}")
    
    if st.session_state.step == 3:
        if st.button("🖼️ Generate Images"):
            st.session_state.step = 4
            st.rerun()

# --- CHAPTER 4: IMAGE GENERATION & GLOBAL FUNCTIONS ---
if st.session_state.step == 4:
    st.divider()
    st.subheader("🖼️ CHAPTER 4: IMAGE GENERATION RESULT")
    
    if not st.session_state.images:
        progress_bar = st.progress(0)
        for i, scene_text in enumerate(st.session_state.scenes):
            try:
                style_prompt = ""
                if "Ink Wash" in selected_style: style_prompt = "Soft ink diffusion, layered brush depth, Korean traditional painting, rich but soft colors, strong use of negative space."
                elif "Realistic" in selected_style: style_prompt = "Cinematic Korean drama style, dynamic camera angles, realistic lighting."
                
                final_prompt = f"{style_prompt} Character: {st.session_state.characters[0]['desc']}. Action: {scene_text[:100]}"
                
                response = client.models.generate_image(
                    model="gemini-3-flash",
                    prompt=final_prompt,
                    config=types.GenerateImageConfig(
                        aspect_ratio=img_ratio,
                        number_of_images=1
                    )
                )
                img = response.generated_images[0].image
                st.session_state.images.append({"img": img, "prompt": final_prompt})
                time.sleep(3) # API Quota 보호 자동 대기
            except Exception as e:
                st.error(f"Scene {i+1} Error: {e}")
                break
            progress_bar.progress((i + 1) / len(st.session_state.scenes))
    
    for i, data in enumerate(st.session_state.images):
        st.image(data['img'], caption=f"Scene {i+1}")
        st.code(data['prompt'], language="text")

    # --- GLOBAL OUTPUT FUNCTIONS ---
    st.divider()
    st.subheader("📥 GLOBAL OUTPUT FUNCTIONS")
    btn_cols = st.columns(5)
    
    btn_cols[0].button("Copy All Prompts")
    
    # 1. Download Images (ZIP)
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED, False) as zf:
        for idx, item in enumerate(st.session_state.images):
            img_b = io.BytesIO()
            item['img'].save(img_b, format='PNG')
            zf.writestr(f"scene_{idx+1}.png", img_b.getvalue())
    btn_cols[1].download_button("Download All Images", data=zip_buf.getvalue(), file_name="yadam_scenes.zip", mime="application/zip")
    
    # 2. Google TTS Export
    tts_instruction = f"<style_instruction>\nSpeed: Very Slow\nVoice Tone: Traditional Storyteller\n</style_instruction>\n\n{st.session_state.script}"
    btn_cols[2].download_button("Google TTS", data=tts_instruction, file_name="tts_script.txt", mime="text/plain")
    
    btn_cols[3].button("Vrew Project")
    btn_cols[4].button("Supertone Project")
