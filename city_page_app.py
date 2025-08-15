import streamlit as st
import wikipedia
import openai
import re
import requests
import nltk
import time
import io
from typing import List, Optional
from datetime import datetime
from bs4 import BeautifulSoup

# Download NLTK data if not already present
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

# Page configuration
st.set_page_config(
    page_title="City Page Creator - AI-Powered Content Generator",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "AI-powered city page generator for local business websites"
    }
)

# Custom CSS for modern styling
def load_custom_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container */
    .main > div {
        padding-top: 2rem;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .header-subtitle {
        font-size: 1.1rem;
        opacity: 0.9;
        font-weight: 400;
    }
    
    /* Card styling */
    .card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
        margin-bottom: 2rem;
    }
    
    .card-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(74, 144, 226, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(74, 144, 226, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background-color: #f8fafc;
        border: 2px solid #e2e8f0;
        border-radius: 10px;
        transition: border-color 0.3s ease;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #4A90E2;
        box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
    }
    
    /* Progress bar */
    .progress-container {
        background: #f1f5f9;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .progress-step {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .progress-icon {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: bold;
    }
    
    .progress-icon.completed {
        background-color: #10B981;
        color: white;
    }
    
    .progress-icon.current {
        background-color: #4A90E2;
        color: white;
    }
    
    .progress-icon.pending {
        background-color: #E5E7EB;
        color: #6B7280;
    }
    
    /* Success/Error alerts */
    .alert {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-weight: 500;
    }
    
    .alert-success {
        background-color: #D1FAE5;
        border: 1px solid #10B981;
        color: #065F46;
    }
    
    .alert-error {
        background-color: #FEE2E2;
        border: 1px solid #EF4444;
        color: #991B1B;
    }
    
    /* Content display */
    .content-container {
        background: #f8fafc;
        border-radius: 10px;
        padding: 2rem;
        border-left: 4px solid #4A90E2;
        margin: 2rem 0;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8fafc;
    }
    
    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        display: block;
    }
    
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .header-title {
            font-size: 2rem;
        }
        
        .card {
            padding: 1.5rem;
        }
        
        .stButton > button {
            width: 100%;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize OpenAI client (updated to modern API)
@st.cache_resource
def init_openai():
    try:
        return openai.OpenAI(api_key=st.secrets["openai"]["api_key"])
    except Exception as e:
        st.error(f"Failed to initialize OpenAI client: {e}")
        return None

# Cache city list for better performance
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cities() -> List[str]:
    """Fetch list of US cities with population > 25,000"""
    with st.spinner("🔄 Loading city data..."):
        try:
            url = "https://en.wikipedia.org/wiki/List_of_cities_in_the_United_States_by_population"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            cities = []

            for row in soup.select("table.wikitable > tbody > tr"):
                try:
                    population_cell = row.select_one("td:nth-child(4)")
                    if population_cell:
                        population_str = re.sub("[^0-9]", "", population_cell.text)
                        if population_str and int(population_str) > 25000:
                            city_cell = row.select_one("td:nth-child(2)")
                            if city_cell:
                                city = city_cell.text.strip()
                                if city and city not in cities:
                                    cities.append(city)
                except (ValueError, AttributeError):
                    continue

            return sorted(cities)
        except Exception as e:
            st.error(f"Error fetching city data: {e}")
            return ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]  # Fallback list

def generate_content_modern(client, text: str, city_name: str) -> str:
    """Generate engaging content using modern OpenAI API"""
    if not client:
        return "Error: OpenAI client not available"
    
    try:
        prompt = f"""
        Rewrite the following text about {city_name} in an engaging and unique way. 
        
        Requirements:
        - Use active voice and compelling language
        - Include proper H1, H2, and H3 headers in markdown format
        - Write as if you're an experienced SEO copywriter
        - Make it informative yet engaging for local business websites
        - Include relevant keywords naturally
        - Ensure the content is well-structured and readable
        
        Original text: {text}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # More cost-effective option
            messages=[
                {"role": "system", "content": "You are an expert SEO copywriter specializing in local business content."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2500,
            temperature=0.7,
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating content: {e}"

def chunk_text_smart(text: str, max_tokens: int = 1000, overlap: int = 50) -> List[str]:
    """Intelligently chunk text to respect sentence boundaries"""
    try:
        sentences = nltk.sent_tokenize(text)
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = len(sentence.split())
            
            if current_tokens + sentence_tokens > max_tokens and current_chunk:
                chunks.append(current_chunk.strip())
                # Keep overlap from previous chunk
                overlap_text = ' '.join(current_chunk.split()[-overlap:])
                current_chunk = overlap_text + " " + sentence
                current_tokens = len(overlap_text.split()) + sentence_tokens
            else:
                current_chunk += " " + sentence
                current_tokens += sentence_tokens
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    except Exception:
        # Fallback to simple word tokenization
        words = text.split()
        chunks = []
        for i in range(0, len(words), max_tokens - overlap):
            chunk = ' '.join(words[i:i + max_tokens])
            chunks.append(chunk)
        return chunks

def display_progress(steps: List[tuple], current_step: int):
    """Display progress indicator"""
    progress_html = "<div class='progress-container'>"
    
    for i, (step_name, description) in enumerate(steps):
        if i < current_step:
            icon_class = "completed"
            icon_text = "✓"
        elif i == current_step:
            icon_class = "current"
            icon_text = str(i + 1)
        else:
            icon_class = "pending"
            icon_text = str(i + 1)
        
        progress_html += f"""
        <div class='progress-step'>
            <div class='progress-icon {icon_class}'>{icon_text}</div>
            <div>
                <strong>{step_name}</strong><br>
                <small style='color: #6B7280;'>{description}</small>
            </div>
        </div>
        """
    
    progress_html += "</div>"
    st.markdown(progress_html, unsafe_allow_html=True)

def main():
    """Main application function"""
    load_custom_css()
    
    # Header
    st.markdown("""
    <div class='header-container'>
        <div class='header-title'>🏙️ City Page Creator</div>
        <div class='header-subtitle'>AI-Powered Content Generator for Local Business Websites</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Quick Stats")
        
        # Initialize session state
        if 'total_generated' not in st.session_state:
            st.session_state.total_generated = 0
        if 'last_generation_time' not in st.session_state:
            st.session_state.last_generation_time = None
        
        # Display stats
        st.markdown(f"""
        <div class='stat-card'>
            <span class='stat-number'>{st.session_state.total_generated}</span>
            <span class='stat-label'>Pages Generated</span>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.last_generation_time:
            st.info(f"🕐 Last generated: {st.session_state.last_generation_time}")
        
        st.markdown("---")
        st.markdown("### ℹ️ How it works")
        st.markdown("""
        1. **Select** a city from the dropdown
        2. **Generate** AI-powered content
        3. **Review** and download the result
        4. **Use** on your local business website
        """)
        
        st.markdown("---")
        st.markdown("### 🎯 Features")
        st.markdown("""
        - ✅ SEO-optimized content
        - ✅ Mobile-responsive design
        - ✅ Fast generation
        - ✅ Professional formatting
        """)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class='card'>
            <div class='card-header'>🎯 Select Your City</div>
        """, unsafe_allow_html=True)
        
        # City selection with search
        cities = get_cities()
        
        # Search functionality
        search_term = st.text_input("🔍 Search for a city:", placeholder="Type to search cities...")
        
        # Filter cities based on search
        if search_term:
            filtered_cities = [city for city in cities if search_term.lower() in city.lower()]
            if not filtered_cities:
                st.warning("No cities found matching your search. Showing all cities.")
                filtered_cities = cities
        else:
            filtered_cities = cities
        
        selected_city = st.selectbox(
            "Choose from available cities:",
            options=filtered_cities,
            index=0 if filtered_cities else 0,
            help=f"Showing {len(filtered_cities)} cities (population > 25,000)"
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='card'>
            <div class='card-header'>⚡ Quick Actions</div>
        """, unsafe_allow_html=True)
        
        generate_button = st.button(
            "🚀 Generate City Page",
            help="Click to generate AI-powered content for the selected city",
            use_container_width=True
        )
        
        if st.button("🔄 Refresh City List", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Generation process
    if generate_button and selected_city:
        st.markdown("""
        <div class='card'>
            <div class='card-header'>🔄 Generating Content</div>
        """, unsafe_allow_html=True)
        
        # Progress tracking
        steps = [
            ("Fetch Data", "Getting city information from Wikipedia"),
            ("Process Content", "Breaking content into manageable chunks"),
            ("AI Enhancement", "Generating engaging content with AI"),
            ("Finalize", "Preparing final formatted content")
        ]
        
        progress_container = st.empty()
        content_container = st.empty()
        
        try:
            # Step 1: Fetch Wikipedia data
            progress_container.empty()
            with progress_container.container():
                display_progress(steps, 0)
            
            with st.spinner("📡 Fetching city information..."):
                city_page = wikipedia.page(selected_city)
                city_summary = city_page.content
                city_url = city_page.url
            
            # Step 2: Process content
            progress_container.empty()
            with progress_container.container():
                display_progress(steps, 1)
            
            with st.spinner("✂️ Processing content..."):
                time.sleep(0.5)  # Brief pause for UX
                chunks = chunk_text_smart(city_summary)
            
            # Step 3: AI Enhancement
            progress_container.empty()
            with progress_container.container():
                display_progress(steps, 2)
            
            client = init_openai()
            if not client:
                st.error("❌ OpenAI client initialization failed. Please check your API key.")
                return
            
            city_page_chunks = []
            progress_bar = st.progress(0)
            
            for i, chunk in enumerate(chunks):
                with st.spinner(f"🤖 AI processing chunk {i+1} of {len(chunks)}..."):
                    enhanced_chunk = generate_content_modern(client, chunk, selected_city)
                    city_page_chunks.append(enhanced_chunk)
                    progress_bar.progress((i + 1) / len(chunks))
            
            # Step 4: Finalize
            progress_container.empty()
            with progress_container.container():
                display_progress(steps, 3)
            
            with st.spinner("📝 Finalizing content..."):
                time.sleep(0.5)
                city_page_content = '\n\n'.join(city_page_chunks)
            
            # Complete progress
            progress_container.empty()
            with progress_container.container():
                display_progress(steps, 4)
            
            # Update session state
            st.session_state.total_generated += 1
            st.session_state.last_generation_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Success message
            st.markdown("""
            <div class='alert alert-success'>
                ✅ <strong>Success!</strong> City page generated successfully!
            </div>
            """, unsafe_allow_html=True)
            
            # Display results
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### 📄 Generated Content for {selected_city}")
                st.markdown(f"**Source:** [{city_url}]({city_url})")
            
            with col2:
                # Download button
                content_bytes = city_page_content.encode('utf-8')
                st.download_button(
                    label="📥 Download Content",
                    data=content_bytes,
                    file_name=f"{selected_city.replace(' ', '_')}_page.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            # Content display in expandable sections
            with st.expander("📖 View Generated Content", expanded=True):
                st.markdown("""
                <div class='content-container'>
                """, unsafe_allow_html=True)
                
                st.markdown(city_page_content)
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Additional info
            st.info(f"📊 **Generation Stats:** {len(chunks)} content chunks processed | "
                   f"Approximately {len(city_page_content.split())} words generated")
        
        except wikipedia.exceptions.DisambiguationError as e:
            st.markdown("""
            <div class='alert alert-error'>
                ❌ <strong>Multiple pages found.</strong> Please be more specific with the city name.
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("Available options:"):
                for option in e.options[:10]:  # Show first 10 options
                    st.write(f"• {option}")
        
        except wikipedia.exceptions.PageError:
            st.markdown("""
            <div class='alert alert-error'>
                ❌ <strong>City not found.</strong> Please select a different city from the dropdown.
            </div>
            """, unsafe_allow_html=True)
        
        except Exception as e:
            st.markdown(f"""
            <div class='alert alert-error'>
                ❌ <strong>Error:</strong> {str(e)}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()