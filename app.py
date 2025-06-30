# Simple Q&A App using Streamlit
# Students: Replace the documents below with your own!

# IMPORTS - These are the libraries we need
import streamlit as st          # Creates web interface components
import chromadb                # Stores and searches through documents  
from transformers import pipeline  # AI model for generating answers

def setup_documents():
    """
    This function creates our document database
    NOTE: This runs every time someone uses the app
    In a real app, you'd want to save this data permanently
    """
    client = chromadb.Client()
    try:
        collection = client.get_collection(name="docs")
    except Exception:
        collection = client.create_collection(name="docs")
    
    # STUDENT TASK: Replace these 5 documents with your own!
    # Pick ONE topic: movies, sports, cooking, travel, technology
    # Each document should be 150-200 words
    # IMPORTANT: The quality of your documents affects answer quality!
    
    my_documents = [
        """Europe’s Historic Landmarks and Heritage: Europe is a treasure of historical landmarks and cultural heritage. From ancient ruins to medieval castles, the continent showcases thousands of years of history. Many sites are protected on UNESCO’s World Heritage List for their “outstanding universal value”. In fact, Italy leads the world with 60 UNESCO World Heritage Sites, more than any other country. Each year new locations are added, highlighting Europe’s ongoing commitment to preserving its past. For example, in 2024 UNESCO recognized the ancient Via Appia in Italy and the 19th-century Schwerin Castle ensemble in Germany. Europe’s heritage isn’t limited to monuments; it also includes cultural landscapes like Scotland’s Flow Country peatlands, one of the world’s largest carbon-rich bogs now on the heritage list. These landmarks and landscapes attract millions of visitors, allowing travellers to step back in time and experience Europe’s rich tapestry of civilizations and traditions. Whether exploring the Acropolis in Athens or a newly inscribed site in Eastern Europe, travellers can witness firsthand how Europe’s history is carefully preserved and celebrated for future generations.""",
        """European Culinary Traditions and Cuisine: European cuisine is as diverse as its cultures, with each region offering unique culinary traditions passed down through generations. Food it’s a key part of cultural identity and social life. Several European food practices are recognized by UNESCO as intangible cultural heritage. For example, the Mediterranean diet (practiced in countries like Italy, Greece, Spain, and Croatia) is on UNESCO’s heritage list, encompassing traditional knowledge from harvesting crops to sharing meals. Italy’s Neapolitan pizza-making is considered an art; the skill of the pizzaiuolo (pizza maker) in Naples, has UNESCO recognition for its cultural significance. Belgium’s beer culture, with thousands of beer varieties and centuries-old brewing traditions is another UNESCO-listed practice. France is famed for its cheeses, and the gastronomic meal of the French is world-renowned, while Spain’s tapas culture and Scandinavia’s foraging-inspired New Nordic cuisine have gained global attention. These culinary traditions make Europe a place for food lovers. Travelers can sample, experiencing how food and culture blend in each locale. The continent’s commitment to its food heritage ensures that classic recipes and food rituals remain a vibrant part of modern life, even as new gastronomic trends emerge.""",
        """Travel Trends and Popular Destinations in Europe: Travel in Europe is booming with tourism. Europeans themselves are eager travellers: 73% of Europeans planned trips between late 2024 and early 2025, a jump of 6% compared to the previous year. Traditional destinations remain highly popular. Spain and France were each the top choice for 7% of surveyed European travellers (with Italy close behind at 6%). Major cities continue to draw crowds, and iconic attractions such as the Eiffel Tower or Colosseum are as beloved as ever. Many tourists are looking beyond the hotspots: over half of European travellers (51%) now express interest in visiting lesser-known spots within popular countries, aiming to avoid crowds. Younger generations are searching these “hidden gem” destinations off the usual tourist trail. This means a rise in visits to smaller towns, rural regions, and second-tier cities that offer rich culture. Another trend is the blending of work and travel with about 1 in 5 Europeans planning a trip that combines business and leisure. Travelers are also increasingly conscious of sustainability and authentic experiences, leading to more interest in local culture, food, and community interactions. All these trends indicate that travel patterns are diversifying.""",
        """Festivals and Cultural Events in Europe: European festivals often feature historic dress and community celebrations. Europe hosts many festivals and cultural events, everything from ancient traditions to modern arts. Here are a few of Europe’s most iconic festivals:Carnival of Venice: Venice is transformed by this masquerade festival. Visitors wear elegant masks and elaborate costumes. San Fermín: This festival, known for the Running of the Bulls, where brave (or reckless) participants sprint ahead of bulls through the streets. Oktoberfest: Late September to early October means Oktoberfest, the world’s largest beer festival. What began as a Bavarian royal wedding celebration has evolved into a two-week folk festival attracting millions of visitors from around the globe. Edinburgh Festival Fringe: The world’s largest arts festival, turning the entire city into a stage. Thousands of performers present shows ranging from stand-up comedy and theater to dance, music, and spoken word. La Tomatina: Is essentially the world’s biggest food fight. The celebration continues with music and dancing. Europe’s calendar is filled with events like Ireland’s St. Patrick’s Day parades, France’s Cannes Film Festival, Austria’s classical Salzburg Festival, and so many more. Just remember to plan, as popular events can mean crowded cities and booked-out accommodations.""",
        """Travel Tips and Sustainable Tourism in Europe: Traveling in Europe can be enriching and enjoyable. Here are some tips and trends for a smooth travel: Travel Off-Season to Avoid Crowds: Popular destinations in Europe are very crowded in peak summer months. Consider visiting in other seasons. Cities are encouraging off-peak travel. You’ll not only find fewer tourists but also cheaper prices and a warmer welcome from locals. Explore Lesser-Known Destinations: Include some “hidden gems” in your itinerary. Smaller towns and less-touristed regions also offer experiences and reduce overtourism in hotspots. Use Trains and Public Transportation: Europe’s transportation network is excellent and environmentally friendly. It has a well-developed rail system that’s scenic. High-speed trains connect major cities, and sleeper trains mean saving time and hotel costs. Respect Local Culture and Rules: Learn a bit of the basics of the local language as a courtesy. Follow dress codes at religious and cultural sites. Be aware of local regulations for preserving communities. Some places limit the number of visitors at popular attractions or have rules to protect historic centers. Choose Sustainable Services: Support businesses with green certifications or community initiatives. Stay in family-run guesthouses or eco-certified hotels that invest in the local area."""
    ]
    
    # Add documents to database with unique IDs
    # ChromaDB needs unique identifiers for each document
    collection.add(
        documents=my_documents,
        ids=["doc1", "doc2", "doc3", "doc4", "doc5"]
    )
    
    return collection

def get_answer(collection, question):
    """
    This function searches documents and generates answers while minimizing hallucination
    """
    
    # STEP 1: Search for relevant documents in the database
    # We get 3 documents instead of 2 for better context coverage
    results = collection.query(
        query_texts=[question],    # The user's question
        n_results=3               # Get 3 most similar documents
    )
    
    # STEP 2: Extract search results
    # docs = the actual document text content
    # distances = how similar each document is to the question (lower = more similar)
    docs = results["documents"][0]
    distances = results["distances"][0]
    
    # STEP 3: Check if documents are actually relevant to the question
    # If no documents found OR all documents are too different from question
    # Return early to avoid hallucination
    if not docs or min(distances) > 1.5:  # 1.5 is similarity threshold - adjust as needed
        return "I cannot answer this question with my knowledge."
    
    # STEP 4: Create structured context for the AI model
    # Format each document clearly with labels
    # This helps the AI understand document boundaries
    context = "\n\n".join([f"Document {i+1}: {doc}" for i, doc in enumerate(docs)])
    
    # STEP 5: Build improved prompt to reduce hallucination
    # Key changes from original:
    # - Separate context from instructions
    # - More explicit instructions about staying within context
    # - Clear format structure
    prompt = f"""Context information:
{context}

Question: {question}

Instructions: Answer ONLY using the information provided above. If the answer is not in the context, respond with "I don't know." Do not add information from outside the context.

Answer:"""
    
    # STEP 6: Generate answer with anti-hallucination parameters
    ai_model = pipeline("text2text-generation", model="google/flan-t5-small")
    response = ai_model(
        prompt, 
        max_length=150
    )
    
    # STEP 7: Extract and clean the generated answer
    answer = response[0]['generated_text'].strip()
    

    
    # STEP 8: Return the final answer
    return answer

# MAIN APP STARTS HERE - This is where we build the user interface

# Set page config first
st.set_page_config(
    page_title="Travel Buddy",
    page_icon="🎒",
    layout="centered"
)

# CUSTOM CSS - FORCING THE STYLES
st.markdown("""
<style>
    /* Force background image everywhere */
    .stApp, .stApp > header, .stApp > div, body {
        background: url("https://images.unsplash.com/photo-1467269204594-9661b134dd2b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80") center/cover no-repeat !important;
        background-attachment: fixed !important;
    }
    
    /* Target all possible container selectors */
    .main .block-container,
    .stMainBlockContainer,
    [data-testid="stMainBlockContainer"],
    .main > div,
    .block-container {
        background: #cbebe3 !important;
        padding: 2rem !important;
        border-radius: 20px !important;
        margin: 2rem auto !important;
        max-width: 900px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3) !important;
        border: 2px solid #ddd !important;
    }
    
    /* Force ALL text to be dark */
    .stApp *, 
    .stApp p, 
    .stApp div, 
    .stApp span, 
    .stApp h1, 
    .stApp h2, 
    .stApp h3,
    .stApp label {
        color: #333333 !important;
    }
    
    /* Title specific styling */
    .stApp h1 {
        color: #2c3e50 !important;
        text-align: center !important;
        font-weight: bold !important;
    }
    
    /* Input field styling */
    .stTextInput input {
        background: white !important;
        color: #333 !important;
        border: 2px solid #ddd !important;
    }
</style>
""", unsafe_allow_html=True)

# STREAMLIT BUILDING BLOCK 0: LOGO
# st.image() displays an image file
# width parameter controls the size of the logo
# Put your logo file (logo.png, logo.jpg, etc.) in the same folder as app.py
# Using columns to center the logo within the white container - more to the right
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
with col3:
    st.image("logo.png", width=150)

# STREAMLIT BUILDING BLOCK 1: PAGE TITLE
# st.title() creates a large heading at the top of your web page
# The emoji 🤖 makes it more visually appealing
# This appears as the biggest text on your page
st.title("🎒 Your best travel buddy")

# STREAMLIT BUILDING BLOCK 2: DESCRIPTIVE TEXT  
# st.write() displays regular text on the page
# Use this for instructions, descriptions, or any text content
# It automatically formats the text nicely
st.write("🌟 Welcome to your ultimate European adventure companion! ✈️🗺️ Ready to explore the magic of Europe? 🏰🍝 Ask me anything about your dream trip and I'll guide you to the most amazing experiences! 🎭🍷🚂 From hidden gems to famous landmarks, I've got all the insider tips! 🏛️🎪🥖")

# STREAMLIT BUILDING BLOCK 3: FUNCTION CALLS
# We call our function to set up the document database
# This happens every time someone uses the app
collection = setup_documents()

# STREAMLIT BUILDING BLOCK 4: TEXT INPUT BOX
# st.text_input() creates a box where users can type
# - First parameter: Label that appears above the box
# - The text users type gets stored in the 'question' variable
# - Users can click in this box and type their question
question = st.text_input("Write your thoughts:")

# CUSTOM CSS FOR BUTTON COLOR
st.markdown("""
<style>
div.stButton > button:first-child {
    background-color: #ffffff;
    color: #2c3e50;
    border: 2px solid #d1d5db;
    border-radius: 20px;
    padding: 0.5rem 1rem;
    font-size: 16px;
    font-weight: bold;
}
div.stButton > button:first-child:hover {
    background-color: #f8f9fa;
    color: #2c3e50;
    border-color: #a0a0a0;
}
</style>
""", unsafe_allow_html=True)

# STREAMLIT BUILDING BLOCK 5: BUTTON
# st.button() creates a clickable button
# - When clicked, all code inside the 'if' block runs
# - type="primary" makes the button blue and prominent
# - The button text appears on the button itself
if st.button("✈️", type="primary"):
    
    # STREAMLIT BUILDING BLOCK 6: CONDITIONAL LOGIC
    # Check if user actually typed something (not empty)
    if question:
        
        # STREAMLIT BUILDING BLOCK 7: SPINNER (LOADING ANIMATION)
        # st.spinner() shows a rotating animation while code runs
        # - Text inside quotes appears next to the spinner
        # - Everything inside the 'with' block runs while spinner shows
        # - Spinner disappears when the code finishes
        with st.spinner("Searching for the best travelling reccomendation for you..."):
            answer = get_answer(collection, question)
        
        # STREAMLIT BUILDING BLOCK 8: FORMATTED TEXT OUTPUT
        # st.write() can display different types of content
        # - **text** makes text bold (markdown formatting)
        # - First st.write() shows "Answer:" in bold
        # - Second st.write() shows the actual answer
        st.success("🎉 Found the perfect travel recommendation for you!")
        st.write("**🗺️ Here is the best answer to your question:**")
        st.write(answer)
    
    else:
        # STREAMLIT BUILDING BLOCK 9: SIMPLE MESSAGE
        # This runs if user didn't type a question
        # Reminds them to enter something before clicking
        st.warning("✏️ Please ask me something about your European adventure!")
        st.info("💡 Tip: Try asking about European destinations, local cuisine, festivals, or travel tips!")

# STREAMLIT BUILDING BLOCK 10: EXPANDABLE SECTION
# st.expander() creates a collapsible section
# - Users can click to show/hide the content inside
# - Great for help text, instructions, or extra information
# - Keeps the main interface clean
with st.expander("About me:"):
    st.write("""
    I have up-to-date insights on Europe’s travel and culture:
    - Historic landmarks and living heritage
    - Regional food traditions and culinary highlights
    - 2025 travel trends and top destinations
    - Key festivals and seasonal events
    - Practical tips for sustainable travel

    Ask me about your next trip:
    - Best places to visit in Europe
    - Hidden gems off the beaten path
    - Local dishes to try by region
    """)


# TO RUN: Save as app.py, then type: streamlit run app.py