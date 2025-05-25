import streamlit as st
import os
from dotenv import load_dotenv
from main import download_youtube_transcript, get_video_info, analyze_with_gpt, save_to_notion
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_teddynote import logging

# 페이지 설정
st.set_page_config(
    page_title="YouTube 분석기",
    page_icon="🎬",
    layout="wide"
)

# 환경 변수 로드
load_dotenv()

# 프로젝트 이름
logging.langsmith("jmango-yp")

# API 키 가져오기
def get_api_keys():
    return {
        'openai': os.getenv('OPENAI_API_KEY'),
        'notion': st.session_state.notion_api_key if 'notion_api_key' in st.session_state else '',
        'notion_db': st.session_state.notion_db_id if 'notion_db_id' in st.session_state else ''
    }

# 세션 상태 초기화
if 'results' not in st.session_state:
    st.session_state.results = None
if 'video_url' not in st.session_state:
    st.session_state.video_url = ""
if 'notion_api_key' not in st.session_state:
    st.session_state.notion_api_key = ""
if 'notion_db_id' not in st.session_state:
    st.session_state.notion_db_id = ""

# 사이드바 API 설정
with st.sidebar:
    st.title("⚙️ 설정")
    
    # Notion API 설정
    st.subheader("📝 Notion 설정")
    notion_api_key = st.text_input("Notion API Key", type="password", value=st.session_state.notion_api_key)
    notion_db_id = st.text_input("Notion Database ID", value=st.session_state.notion_db_id)
    
    # API 키 저장
    if notion_api_key != st.session_state.notion_api_key:
        st.session_state.notion_api_key = notion_api_key
    if notion_db_id != st.session_state.notion_db_id:
        st.session_state.notion_db_id = notion_db_id
    
    # Notion 설정 가이드
    with st.expander("📖 Notion 설정 가이드"):
        st.markdown("""
        ### Notion API 설정 방법
        
        1. **Notion API 키 생성하기**
           - [Notion Developers](https://www.notion.so/my-integrations) 페이지 방문
           - "새 API 통합" 클릭
           - API 통합 이름 추가
           - 관련 워크스페이스 선택 후 저장
           - 생성된 "프라이빗 API 통합 시크릿" 복사
        
        2. **Notion 데이터베이스 생성하기**
           - Notion에서 새 페이지 생성
           - "/database" 입력하여 새 데이터베이스 생성
           - ❗데이터베이스에 다음 속성 추가:
             - 제목 (Title)
             - 채널명 (Text)
             - URL (URL)
             - 분석일시 (Date)
             - 주요 인사이트 (Text)
        
        3. **데이터베이스 ID 찾기**
           - 데이터베이스 페이지 URL에서 ID 복사
           - URL 형식: `https://www.notion.so/workspace/[database-id]?v=...`
           - `[database-id]` 부분이 필요한 ID입니다
           - ❗본인의 워크스페이스명/ 다음부터 물음표(?) 전까지 복사
        
        4. **통합 연결하기**
           - 데이터베이스 페이지 우측 상단 "..." 클릭
           - "Add connections" 선택
           - 생성한 통합 선택
        """)
    
    st.markdown("---")
    
    # API 키 상태 확인
    api_keys = get_api_keys()
    if not api_keys['openai']:
        st.warning("⚠️ OpenAI API 키가 설정되지 않았습니다.")
    if not api_keys['notion'] or not api_keys['notion_db']:
        st.warning("⚠️ Notion API 키 또는 데이터베이스 ID가 설정되지 않았습니다.")

# 메인 타이틀
st.title("🎬 YouTube 보는 시간도 아깝다")
st.markdown("관심 있는 유튜브 URL만 입력하면, 알아서 요약하고 노션에 정리까지")

# URL 입력
video_url = st.text_input("YouTube URL을 입력하세요", 
                         placeholder="https://www.youtube.com/watch?v=...",
                         value=st.session_state.video_url)

# 버튼을 나란히 배치
col1, col2 = st.columns(2)
with col1:
    analyze_button = st.button("분석 시작", type="primary", use_container_width=True)
with col2:
    reset_button = st.button("초기화", use_container_width=True)

# 초기화 버튼 처리
if reset_button:
    st.session_state.results = None
    st.session_state.video_url = ""
    st.rerun()

# 분석 시작 버튼 처리
if analyze_button:
    if not video_url:
        st.error("YouTube URL을 입력해주세요.")
    else:
        st.session_state.video_url = video_url
        try:
            # 자막 다운로드 및 분석
            video_id = YouTube(video_url).video_id
            transcript = None
            used_language = None

            # 자막 다운로드 시도 (언어 우선순위: 한국어 → 한국어 자동생성 → 영어)
            try:
                # 먼저 사용 가능한 자막 목록 확인
                available_transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
                st.info("📋 사용 가능한 자막 언어:")
                for transcript in available_transcripts:
                    st.write(f"  - {transcript.language}: {transcript.language_code}")
                
                # 한국어 자막 시도 (수동 생성)
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
                    used_language = 'ko'
                    st.success("✅ 한국어 스크립트 생성 성공")
                except:
                    # 한국어 자동 생성 자막 시도
                    try:
                        # 자동 생성된 한국어 자막 찾기
                        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                        auto_generated = transcript_list.find_transcript(['ko'])
                        if auto_generated:
                            transcript = auto_generated.fetch()
                            used_language = 'ko'
                            st.success("✅ 한국어 자동 생성 스크립트 생성 성공")
                        else:
                            raise Exception("자동 생성된 한국어 자막을 찾을 수 없습니다.")
                    except:
                        # 영어 자막 시도
                        try:
                            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                            used_language = 'en'
                            st.success("✅ 영어 스크립트 생성 성공")
                        except Exception as e:
                            st.error(f"❌ 자막 다운로드 실패: {str(e)}")
                            transcript = None
                            used_language = None
            except Exception as e:
                st.error(f"❌ 자막 목록 조회 실패: {str(e)}")
                transcript = None
                used_language = None
            
            if transcript:
                # Get video info
                title, channel = get_video_info(video_url)
                
                # Convert transcript to text
                transcript_text = "\n".join([f"{item['text']}" for item in transcript])
                
                # Generate summary using GPT
                api_keys = get_api_keys()
                if api_keys['openai']:
                    with st.spinner('🤖 AI가 영상을 분석하고 있습니다...'):
                        analysis_text = analyze_with_gpt(transcript_text, title, channel, video_url, api_keys['openai'])
                        
                        if analysis_text:
                            # Save analysis to Notion if API key is provided
                            if api_keys['notion'] and api_keys['notion_db']:
                                with st.spinner('📝 Notion에 저장 중...'):
                                    notion_url = save_to_notion(
                                        analysis_text, 
                                        title, 
                                        channel, 
                                        video_url, 
                                        api_keys['notion_db'], 
                                        api_keys['notion']
                                    )
                                    if notion_url:
                                        st.success("✅ Notion에 저장되었습니다. 결과에서 링크를 확인하세요.")
                                    else:
                                        st.error("❌ Notion 저장에 실패했습니다.")
                        else:
                            st.error("❌ AI 분석에 실패했습니다.")
                
                # 결과를 세션 상태에 저장
                st.session_state.results = {
                    'transcript': transcript,
                    'transcript_text': transcript_text,
                    'analysis_text': analysis_text if 'analysis_text' in locals() else None,
                    'notion_url': notion_url if 'notion_url' in locals() else None,
                    'language': used_language,
                    'title': title,
                    'channel': channel
                }
            
        except Exception as e:
            st.error(f"❌ 오류가 발생했습니다: {str(e)}")
            if hasattr(e, 'response'):
                st.error(f"API 응답: {e.response}")

# 결과 표시 (세션 상태에서 가져옴)
if st.session_state.results:
    results = st.session_state.results
    st.success("✅ 분석이 완료되었습니다!")
    
    # 결과 컨테이너 생성
    results_container = st.container()
    
    with results_container:
        # 다운로드 버튼과 Notion 링크를 나란히 배치
        col1, col2 = st.columns(2)
        
        with col1:
            # 전체 스크립트 파일 다운로드
            if results['transcript_text']:
                st.download_button(
                    "📥 전체 스크립트 다운로드",
                    results['transcript_text'],
                    file_name=f"full_transcript_{results['language']}.txt",
                    mime="text/plain",
                    key="full_transcript_download"
                )
            
            # 요약 스크립트 파일 다운로드
            if results['analysis_text']:
                st.download_button(
                    "📊 요약 스크립트 다운로드",
                    results['analysis_text'],
                    file_name=f"summary_{results['language']}.txt",
                    mime="text/plain",
                    key="summary_download"
                )
        
        with col2:
            # Notion 링크
            if results['notion_url']:
                st.markdown("### 📝 Notion")
                st.markdown(f"[Notion에서 보기]({results['notion_url']})")
    

# 푸터
st.markdown("---")
st.markdown("Made by jmhanmu@gmail.com❤️ ")
