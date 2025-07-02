# 🎯 WHAT THIS APP DOES:
# This is a smart app that lets you upload documents (PDF, Word, text files)
# and then ask questions about them! The AI reads your documents and gives you answers.
# It's like having a super smart assistant that remembers everything in your documents!

# 📚 Import all the tools we need to make our app work
import streamlit as st           # Makes beautiful web apps (like the one you're using!)
import chromadb                  # Stores documents in a smart way so we can search them fast
from transformers import pipeline # The AI brain that answers questions
from pathlib import Path         # Helps us work with file paths (like addresses for files)
import tempfile                  # Creates temporary files that disappear when we're done
import sys                       # Lets us talk to the computer system
from datetime import datetime    # Tells us what time and date it is
import time                      # Helps us add pauses and delays

# 🔧 Fix a technical problem with databases on some computers
# (This is like making sure all the puzzle pieces fit together properly)
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass  # If it doesn't work, that's okay - keep going!

# 📄 Import tools for converting documents (turning PDFs into text we can read)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.backend.docling_parse_v2_backend import DoclingParseV2DocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions, AcceleratorDevice

# 🧠 Import tools for making text smart and searchable
from langchain.text_splitter import RecursiveCharacterTextSplitter  # Cuts text into smart pieces
from sentence_transformers import SentenceTransformer              # Understands what text means

def convert_to_markdown(file_path: str) -> str:
    """
    🔄 THE MAGIC DOCUMENT CONVERTER! 
    
    What this function does (in simple words):
    - Takes any document file (PDF, Word doc, or text file)
    - Reads what's inside it
    - Converts it to simple text that our AI can understand
    - It's like translating different languages into one language everyone understands!
    
    Think of it like this: 📄➡️🔄➡️📝
    (Document file) → (Magic converter) → (Simple text)
    
    What it expects:
    - file_path: The location of your file (like an address)
    
    What it gives back:
    - A string of text containing everything from your document
    """
    try:
        # 🕵️ First, let's figure out what kind of file this is
        path = Path(file_path)  # Turn the file path into something we can work with
        ext = path.suffix.lower()  # Get the file extension (.pdf, .docx, etc.) and make it lowercase

        # 📕 If it's a PDF file, use special PDF tools
        if ext == ".pdf":
            try:
                # 🔧 Set up the PDF converter with special settings
                # (Like preparing the right tools before starting a job)
                pdf_opts = PdfPipelineOptions(do_ocr=False)  # Don't try to read pictures as text
                pdf_opts.accelerator_options = AcceleratorOptions(
                    num_threads=4,              # Use 4 workers to process faster
                    device=AcceleratorDevice.CPU # Use the computer's CPU
                )
                
                # 🏭 Create the document converter factory
                converter = DocumentConverter(
                    format_options={
                        InputFormat.PDF: PdfFormatOption(
                            pipeline_options=pdf_opts,
                            backend=DoclingParseV2DocumentBackend  # The engine that does the work
                        )
                    }
                )
                
                # 🎯 Convert the PDF and extract the text
                doc = converter.convert(file_path).document
                result = doc.export_to_markdown(image_mode="placeholder")  # Turn it into readable text
                
                # 🎉 Return the text, or a helpful message if nothing was found
                return result if result else f"# {path.name}\n\nDocument conversion completed but no content extracted."
                
            except Exception as e:
                # 😢 If something goes wrong, tell us what happened
                return f"Error converting PDF {path.name}: {str(e)}"

        # 📘 If it's a Word document (.doc or .docx), use the Word converter
        elif ext in [".doc", ".docx"]:
            try:
                # 🔧 Create a simple converter for Word documents
                converter = DocumentConverter()
                doc = converter.convert(file_path).document  # Convert the document
                result = doc.export_to_markdown(image_mode="placeholder")  # Turn it into text
                
                # 🎉 Return the text, or a helpful message if nothing was found
                return result if result else f"# {path.name}\n\nDocument conversion completed but no content extracted."
                
            except Exception as e:
                # 😢 If something goes wrong, tell us what happened
                return f"Error converting document {path.name}: {str(e)}"

        # 📄 If it's a simple text file, just read it directly
        elif ext == ".txt":
            try:
                # 📖 Try to read the file using UTF-8 encoding (the most common way)
                content = path.read_text(encoding="utf-8")
                return content if content else f"# {path.name}\n\nEmpty text file."
                
            except UnicodeDecodeError:
                # 🔄 If that doesn't work, try a different encoding
                try:
                    content = path.read_text(encoding="latin-1", errors="replace")
                    return content if content else f"# {path.name}\n\nEmpty text file."
                except Exception as e:
                    return f"Error reading text file {path.name}: {str(e)}"
                    
            except Exception as e:
                # 😢 If we still can't read it, explain what went wrong
                return f"Error reading text file {path.name}: {str(e)}"

        # ❌ If it's a file type we don't understand, say so
        else:
            return f"# {path.name}\n\nUnsupported file format: {ext}"
            
    except Exception as e:
        # 😱 If something really unexpected happens, catch it here
        return f"# {Path(file_path).name}\n\nUnexpected error processing file: {str(e)}"


def check_app_health():
    """
    🏥 THE APP DOCTOR!
    
    What this function does (in simple words):
    - Checks if all parts of our app are working properly
    - It's like a doctor checking if you're healthy!
    - If something is broken, it makes a list of problems
    
    Think of it like this: 🔍🏥✅
    (Look around) → (Check health) → (Report status)
    
    What it gives back:
    - A list of problems (empty list = everything is perfect!)
    """
    issues = []  # 📝 Start with an empty list to collect any problems we find
    
    # 🔍 Check if documents were processed but the database is missing
    # (Like checking if someone said they put cookies in the jar, but the jar is empty)
    if st.session_state.get('uploaded_files_processed') and not st.session_state.get('collection'):
        issues.append("Documents processed but no database collection found")
    
    # 🗄️ Check if our document database (CromaDB) is working properly
    try:
        if st.session_state.get('collection'):
            count = st.session_state.collection.count()  # Count how many documents are stored
            # If we processed documents but the database is empty, that's a problem!
            if count == 0 and st.session_state.get('uploaded_files_processed'):
                issues.append("Database collection is empty despite processed documents")
    except Exception as e:
        # 😢 If we can't even check the database, that's definitely a problem
        issues.append(f"Database connection issue: {str(e)}")
    
    # 🤖 Check if our AI brain is working
    try:
        # Only test the AI if we haven't loaded it yet (don't want to waste time)
        if 'qa_pipeline' not in st.session_state:
            # 🧪 Do a quick test - try to create an AI pipeline
            test_pipeline = pipeline("text2text-generation", model="google/flan-t5-small", max_length=50)
            # Clean up the test pipeline
            del test_pipeline
    except Exception as e:
        # 😢 If the AI brain isn't working, add it to our problem list
        issues.append(f"AI model loading issue: {str(e)}")
    
    return issues  # 📋 Give back the list of problems (hopefully empty!)


def show_loading_animation(text="Processing..."):
    """
    ⏳ THE WAITING HELPER!
    
    What this function does (in simple words):
    - Shows a spinning wheel while the computer is working hard
    - It's like showing "Please wait..." so people don't get worried
    - Adds a tiny pause to make sure users see the message
    
    Think of it like this: ⏳💭✨
    (Show spinner) → (Let user know we're working) → (Make it look nice)
    
    What it expects:
    - text: The message to show (like "Processing your documents...")
    """
    with st.spinner(text):  # 🌀 Show the spinning animation with our message
        time.sleep(0.3)  # 😴 Take a tiny nap (0.3 seconds) so users can see the message



def reset_collection(client, collection_name: str):
    """
    🗑️➡️📦 THE FRESH START MAKER!
    
    What this function does (in simple words):
    - Deletes the old document storage box
    - Creates a brand new, empty storage box
    
    Think of it like this: 🗑️🧹📦
    (Delete old box) → (Clean everything) → (Make new empty box)
    
    What it expects:
    - client: The database manager
    - collection_name: The name of our storage box
    
    What it gives back:
    - A new empty collection ready for documents
    """
    try:
        # 🗑️ Try to delete the old collection
        client.delete_collection(name=collection_name)
        print(f"Deleted collection '{collection_name}'")  # Tell the console what we did
    except Exception as e:
        # 🤷 If there's nothing to delete, that's okay!
        print(f"Collection '{collection_name}' doesn't exist or already deleted")
    
    # 📦 Create a brand new, empty collection
    new_collection = client.create_collection(name=collection_name)
    print(f"Created new empty collection '{collection_name}'")  # Tell the console we made it
    return new_collection  # 🎁 Give back the new empty box


def add_text_to_chromadb(text: str, filename: str, collection_name: str = "documents"):
    """
    📚➡️🧠 THE SMART STORAGE HELPER!
    
    What this function does (in simple words):
    - Takes a long document and cuts it into smaller, smart pieces
    - Stores each piece in our smart database so we can find them later
    
    Think of it like this: 📄✂️📦🏷️
    (Big document) → (Cut into pieces) → (Store in smart boxes) → (Label everything)
    
    What it expects:
    - text: The content of your document (all the words)
    - filename: What the document is called
    - collection_name: Which storage box to put it in
    
    What it gives back:
    - The collection where everything is stored
    """
    # Split text into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,       
        chunk_overlap=100,     
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_text(text)
    
    # Initialize components (reuse if possible)
    if not hasattr(add_text_to_chromadb, 'client'):
        add_text_to_chromadb.client = chromadb.Client()  # The database manager
        add_text_to_chromadb.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # The brain that understands text
        add_text_to_chromadb.collections = {}  # A dictionary to remember our storage boxes
    
    # Get or create collection
    if collection_name not in add_text_to_chromadb.collections:
        try:
            # 🔍 Try to find an existing storage box with this name
            collection = add_text_to_chromadb.client.get_collection(name=collection_name)
        except:
            # 📦 If we can't find it, create a new one
            collection = add_text_to_chromadb.client.create_collection(name=collection_name)
        # 💾 Remember this storage box for next time
        add_text_to_chromadb.collections[collection_name] = collection
    
    collection = add_text_to_chromadb.collections[collection_name]  # Get our storage box
    
    # Process chunks
    for i, chunk in enumerate(chunks):
        # 🧠 Let the AI brain understand it means
        embedding = add_text_to_chromadb.embedding_model.encode(chunk).tolist()
        
        # 🏷️ Create a label with information about this
        metadata = {
            "filename": filename,      # Which document this came from
            "chunk_index": i,         # Which piece number this is (0, 1, 2, etc.)
            "chunk_size": len(chunk)  # How big this piece is
        }
        
        # 📦 Store in our smart storage box
        collection.add(
            embeddings=[embedding],    # The AI's understanding of what this means
            documents=[chunk],         # The actual text
            metadatas=[metadata],      # The label with information
            ids=[f"{filename}_chunk_{i}"]  # A unique name for this piece
        )
    
    # 🎉 Tell everyone we're done and how many pieces we stored
    print(f"Added {len(chunks)} chunks from {filename}")
    return collection


def get_answer(collection, question):
    """
    This function searches documents and generates answers while minimizing hallucination
    """
    # STEP 1: Search for relevant documents in the database
    results = collection.query(
        query_texts=[question],    # The user's question
        n_results=3               # Get 3 most similar documents
    )
    
    # STEP 2: Extract search results
    docs = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0] if results["metadatas"] else []
    
    # STEP 3: Check if documents are actually relevant to the question
    if not docs or min(distances) > 1.5:  # 1.5 is similarity threshold
        return "I cannot answer this question based on the uploaded documents."
    
    # STEP 4: Create structured context for the AI model
    if metadatas:
        context = "\n\n".join([
            f"Document {i+1} (from {metadatas[i].get('filename', 'unknown')}): {doc}"
            for i, doc in enumerate(docs)
        ])
    else:
        context = "\n\n".join([f"Document {i+1}: {doc}" for i, doc in enumerate(docs)])
    
    # STEP 5: Build improved prompt to reduce hallucination
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
    return answer


# ENHANCED FEATURES FROM STEP2

# FEATURE 1: Enhanced answer function with source tracking
def get_answer_with_source(collection, question):
    """
    🤖🔍📖 THE SUPER SMART QUESTION ANSWERER!
    
    What this function does (in simple words):
    - Someone asks a question about their documents
    - We search through all the document pieces to find the best answers
    - The AI reads and writes a smart answer
    - We also tell you which document the answer came from!
    """
    # 🔍 STEP 1: Search through all our document pieces to find the best matches
    results = collection.query(
        query_texts=[question],  # What are we looking for?
        n_results=3             # Give us the 3 best matches
    )
    
    # 📦 STEP 2: Unpack what we found
    docs = results["documents"][0]      # The actual text we found
    distances = results["distances"][0]  # How well matches (smaller = better)
    ids = results["ids"][0]             # The names of the pieces we found
    metadatas = results["metadatas"][0] if results["metadatas"] else []  # Info about each piece
    
    # 🤔 STEP 3: Check if we found anything good enough to use
    # (If the closest match is still far away, we probably don't have the answer)
    if not docs or min(distances) > 1.5:  # 1.5 is our "good enough" threshold
        return "I cannot answer this question based on the uploaded documents.", "No source"
    
    # Create structured context for the AI model
    if metadatas:
        # Include which document each piece came from (like footnotes in a book)
        context = "\n\n".join([
            f"Document {i+1} (from {metadatas[i].get('filename', 'unknown')}): {doc}"
            for i, doc in enumerate(docs)
        ])
    else:
        # If we don't have filename info, just number the pieces
        context = "\n\n".join([f"Document {i+1}: {doc}" for i, doc in enumerate(docs)])
    
    # 🎯 STEP 5: Create a really good question for the AI that reduces hallucination
    # (We're very specific about what we want the AI to do)
    prompt = f"""Context information:
{context}

Question: {question}

Instructions: Answer ONLY using the information provided above. If the answer is not in the context, respond with "I don't know." Do not add information from outside the context.

Answer:"""
    
    # 🤖 STEP 6: Ask the AI brain to answer our question
    ai_model = pipeline("text2text-generation", model="google/flan-t5-small")
    response = ai_model(prompt, max_length=150)  # Don't make the answer too long
    
    # ✨ STEP 7: Clean up the AI's answer
    answer = response[0]['generated_text'].strip()
    
    # 📚 STEP 8: Figure out which document the answer came from
    if metadatas and len(metadatas) > 0:
        best_source = metadatas[0].get('filename', 'Unknown source')
    else:
        # Fallback: try to extract from ID
        try:
            best_source = ids[0].split('_chunk_')[0] if ids else "Unknown source"
        except:
            best_source = "Unknown source"
    
    # 🎁 STEP 9: Give back both the answer and where it came from
    return answer, best_source

# FEATURE 2: Search history functions
def add_to_search_history(question, answer, source):
    """
    📝💾 THE MEMORY KEEPER!
    
    What this function does (in simple words):
    - Remembers every question someone asks and the answer they got
    - Shows the most recent questions first
    - Only keeps the last 10 questions so it doesn't get too cluttered
    """
    # 📚 Make sure we have a memory book (create it if it doesn't exist)
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    
    # Add new search to beginning of list
    st.session_state.search_history.insert(0, {
        'question': question,
        'answer': answer,
        'source': source,
        'timestamp': str(datetime.now().strftime("%H:%M:%S"))
    })
    
    # 🧹 Keep only the last 10 searches
    if len(st.session_state.search_history) > 10:
        st.session_state.search_history = st.session_state.search_history[:10]

def show_search_history():
    """Display search history"""
    st.subheader("🕒 Recent Searches")
    
    if 'search_history' not in st.session_state or not st.session_state.search_history:
        st.info("No searches yet.")
        return
    
    for i, search in enumerate(st.session_state.search_history):
        with st.expander(f"Q: {search['question'][:50]}... ({search['timestamp']})"):
            st.write("**Question:**", search['question'])
            st.write("**Answer:**", search['answer'])
            st.write("**Source:**", search['source'])

# FEATURE 3: Modern card-based document manager
def show_document_manager():
    """Display modern card-based document manager interface"""
    st.markdown("### 📋 Manage your documents")
    st.markdown("*Organize, preview, and download your processed documents*")
    
    if not st.session_state.uploaded_files_processed:
        # Beautiful empty state
        st.markdown("""
        <div style="
            text-align: center;
            padding: 60px 20px;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(147, 51, 234, 0.05));
            border-radius: 20px;
            border: 2px dashed rgba(99, 102, 241, 0.3);
            margin: 20px 0;
        ">
            <div style="font-size: 3rem; margin-bottom: 20px;">📄</div>
            <h3 style="color: #6366f1; margin: 10px 0;">No documents yet</h3>
            <p style="color: #64748b; margin: 10px 0;">
                Upload documents in the Upload tab to start managing your knowledge base
            </p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Create responsive grid layout for document cards
    num_docs = len(st.session_state.uploaded_files_processed)
    
    # Determine number of columns based on screen size
    if num_docs == 1:
        cols = st.columns(1)
    elif num_docs == 2:
        cols = st.columns(2)
    else:
        cols = st.columns(3)  # 3 columns for 3+ documents
    
    # Display documents as cards
    for i, filename in enumerate(st.session_state.uploaded_files_processed):
        col_index = i % len(cols)
        
        with cols[col_index]:
            # Get file info
            file_ext = Path(filename).suffix.lower()
            file_name_display = Path(filename).stem
            
            # Calculate stats
            word_count = 0
            file_size_kb = 0
            if hasattr(st.session_state, 'document_contents') and filename in st.session_state.document_contents:
                content = st.session_state.document_contents[filename]
                word_count = len(content.split())
                file_size_kb = len(content.encode('utf-8')) / 1024
            
            # Choose icon based on file type
            if file_ext == '.pdf':
                file_icon = "📕"
                file_color = "#ef4444"
            elif file_ext in ['.doc', '.docx']:
                file_icon = "📘"
                file_color = "#3b82f6"
            elif file_ext == '.txt':
                file_icon = "📄"
                file_color = "#10b981"
            else:
                file_icon = "📄"
                file_color = "#6b7280"
            
            # Create beautiful document card
            card_html = f"""
            <div style="
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px);
                border-radius: 16px;
                padding: 20px;
                margin: 10px 0;
                border: 1px solid rgba(255, 255, 255, 0.4);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            ">
                <div style="text-align: center; margin-bottom: 15px;">
                    <div style="font-size: 2.5rem; margin-bottom: 8px;">{file_icon}</div>
                    <h4 style="color: #2c3e50; margin: 0; font-size: 16px; font-weight: 600;">
                        {file_name_display}
                    </h4>
                    <p style="color: #64748b; margin: 5px 0 0 0; font-size: 12px;">
                        {file_ext.upper()} • {word_count:,} words
                    </p>
                </div>
                
                <div style="
                    background: rgba(248, 250, 252, 0.8);
                    border-radius: 8px;
                    padding: 10px;
                    margin: 15px 0;
                    text-align: center;
                ">
                    <div style="color: #64748b; font-size: 11px; margin-bottom: 5px;">PROCESSED</div>
                    <div style="color: #10b981; font-size: 12px; font-weight: 600;">
                        {datetime.now().strftime("%b %d, %Y")}
                    </div>
                </div>
            </div>
            """
            
            st.markdown(card_html, unsafe_allow_html=True)
            
            # Action buttons in a nice layout
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                # Preview button
                if st.button("👁️", key=f"preview_{i}", help="Preview document", use_container_width=True):
                    st.session_state[f'show_preview_{i}'] = not st.session_state.get(f'show_preview_{i}', False)
            
            with col_b:
                # Download button
                if hasattr(st.session_state, 'document_contents') and filename in st.session_state.document_contents:
                    content = st.session_state.document_contents[filename]
                    base_name = Path(filename).stem
                    download_filename = f"{base_name}_converted.md"
                    st.download_button(
                        label="💾",
                        data=content,
                        file_name=download_filename,
                        mime="text/markdown",
                        key=f"download_{i}",
                        help="Download as markdown",
                        use_container_width=True
                    )
            
            with col_c:
                # Delete button
                if st.button("🗑️", key=f"delete_{i}", help="Delete document", use_container_width=True):
                    # Remove from processed files list
                    st.session_state.uploaded_files_processed.pop(i)
                    # Remove from document contents
                    if hasattr(st.session_state, 'document_contents') and filename in st.session_state.document_contents:
                        del st.session_state.document_contents[filename]
                    # Clear preview state
                    if f'show_preview_{i}' in st.session_state:
                        del st.session_state[f'show_preview_{i}']
                    st.success(f"✅ Removed {filename}")
                    st.rerun()
            
            # Show preview if requested
            if st.session_state.get(f'show_preview_{i}', False):
                with st.expander(f"📖 Preview: {file_name_display}", expanded=True):
                    if hasattr(st.session_state, 'document_contents') and filename in st.session_state.document_contents:
                        content = st.session_state.document_contents[filename]
                        preview_text = content[:800] + "..." if len(content) > 800 else content
                        
                        # Styled preview container
                        st.markdown(f"""
                        <div style="
                            background: rgba(248, 250, 252, 0.8);
                            border-radius: 8px;
                            padding: 15px;
                            font-family: 'Monaco', 'Menlo', monospace;
                            font-size: 12px;
                            line-height: 1.5;
                            color: #374151;
                            white-space: pre-wrap;
                            max-height: 300px;
                            overflow-y: auto;
                        ">
{preview_text}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("Preview not available - document content not stored in session.")
            
            # Add some spacing between cards
            st.markdown("<br>", unsafe_allow_html=True)

# FEATURE 4: Document statistics
def show_document_stats():
    """Show statistics about uploaded documents"""
    st.subheader("📊 Document Statistics")
    
    if not st.session_state.uploaded_files_processed:
        st.info("No documents to analyze.")
        return
    
    # Calculate basic stats
    total_docs = len(st.session_state.uploaded_files_processed)
    
    # Calculate word count if available
    total_words = 0
    if hasattr(st.session_state, 'document_contents'):
        total_words = sum(
            len(st.session_state.document_contents.get(filename, "").split()) 
            for filename in st.session_state.uploaded_files_processed
        )
    
    avg_words = total_words // total_docs if total_docs > 0 and total_words > 0 else 0
    
    # Display in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Documents", total_docs)
    
    with col2:
        if total_words > 0:
            st.metric("Total Words", f"{total_words:,}")
        else:
            st.metric("Total Words", "N/A")
    
    with col3:
        if avg_words > 0:
            st.metric("Average Words/Doc", f"{avg_words:,}")
        else:
            st.metric("Average Words/Doc", "N/A")
    
    # Show breakdown by file type
    file_types = {}
    for filename in st.session_state.uploaded_files_processed:
        ext = Path(filename).suffix.lower()
        if not ext:
            ext = "no extension"
        file_types[ext] = file_types.get(ext, 0) + 1
    
    st.write("**File Types:**")
    for ext, count in file_types.items():
        st.write(f"• {ext}: {count} files")

# FEATURE 5: Create tabbed interface
def create_tabbed_interface():
    """Create a tabbed interface for better organization"""
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📁 Upload", "❓ Ask Questions", "📋 Manage", "📊 Stats", "🔧 System Status"])
    
    with tab1:
        st.markdown("### 📁 Upload & Convert Documents")
        st.markdown("*Transform your documents into searchable knowledge with AI-powered conversion*")
        
        uploaded_files = st.file_uploader(
            "",
            type=["pdf", "doc", "docx", "txt"],
            accept_multiple_files=True,
            help=None
        )
        
        # Show file preview if files are selected
        if uploaded_files:
            st.markdown("#### 📋 Selected Files")
            for file in uploaded_files:
                file_size = len(file.getvalue()) / (1024 * 1024)  # Size in MB
                size_color = "#22c55e" if file_size <= 10 else "#ef4444"
                st.markdown(f"""
                <div style="
                    background: rgba(255, 255, 255, 0.9);
                    border-radius: 8px;
                    padding: 12px;
                    margin: 8px 0;
                    border-left: 4px solid {size_color};
                ">
                    📄 <strong>{file.name}</strong> • 
                    <span style="color: {size_color};">{file_size:.1f} MB</span>
                </div>
                """, unsafe_allow_html=True)
        
        # Enhanced process button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            process_clicked = st.button(
                "⚙️ Process Documents", 
                type="primary",
                help="Convert and add documents to your knowledge base",
                use_container_width=True
            )
        
        # Processing with enhanced feedback
        if process_clicked:
            if uploaded_files:
                # Validate files before processing
                valid_files = []
                errors = []
                
                for file in uploaded_files:
                    file_size = len(file.getvalue()) / (1024 * 1024)
                    if file_size > 10:
                        errors.append(f"❌ {file.name}: File too large ({file_size:.1f}MB > 10MB)")
                    else:
                        valid_files.append(file)
                
                if errors:
                    for error in errors:
                        st.error(error)
                
                if valid_files:
                    # Enhanced processing with better UX
                    with st.container():
                        st.markdown("#### 🔄 Processing Documents...")
                        
                        # Create/reset ChromaDB collection
                        client = chromadb.Client()
                        collection = reset_collection(client, "uploaded_documents")
                        
                        # Progress tracking with enhanced UI
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        processed_files = []
                        document_contents = {}
                        total_files = len(valid_files)
                        processing_errors = []
                        
                        for idx, file in enumerate(valid_files):
                            try:
                                # Update status with professional messaging
                                status_text.text(f"🔄 Converting {file.name} to searchable format... ({idx + 1}/{total_files})")
                                
                                # Create temporary file
                                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.name).suffix) as temp_file:
                                    temp_file.write(file.getvalue())
                                    temp_file_path = temp_file.name
                                
                                # Convert to markdown
                                text = convert_to_markdown(temp_file_path)
                                
                                # Validate conversion
                                if not text or len(text.strip()) < 10:
                                    text = f"# {file.name}\n\nDocument appears to be empty or corrupted."
                                    processing_errors.append(f"⚠️ {file.name}: Content appears empty or corrupted")
                                
                                # Store content for preview and stats
                                document_contents[file.name] = text
                                
                                # Add to ChromaDB with error handling
                                status_text.text(f"📚 Adding {file.name} to knowledge base...")
                                collection = add_text_to_chromadb(text, file.name, collection_name="uploaded_documents")
                                processed_files.append(file.name)
                                
                                # Clean up temp file
                                Path(temp_file_path).unlink(missing_ok=True)
                                
                            except Exception as e:
                                processing_errors.append(f"❌ {file.name}: {str(e)}")
                                # Still clean up temp file if it exists
                                try:
                                    Path(temp_file_path).unlink(missing_ok=True)
                                except:
                                    pass
                                continue
                            
                            # Update progress with smooth animation
                            progress_bar.progress((idx + 1) / total_files)
                        
                        # Clear status text
                        status_text.text("✅ Processing complete!")
                        
                        # Update session state
                        st.session_state.collection = collection
                        st.session_state.uploaded_files_processed = processed_files
                        st.session_state.document_contents = document_contents
                        
                        # Enhanced success message with stats
                        if processed_files:
                            total_words = sum(len(document_contents[filename].split()) for filename in processed_files)
                            
                            st.success(f"✅ Successfully processed {len(processed_files)} documents!")
                            
                            # Show processing errors if any
                            if processing_errors:
                                with st.expander("⚠️ Processing warnings", expanded=False):
                                    for error in processing_errors:
                                        st.warning(error)
                            
                            # Success metrics in a beautiful layout
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("📄 Documents", len(processed_files))
                            with col2:
                                st.metric("📝 Total Words", f"{total_words:,}")
                            with col3:
                                st.metric("🧠 Knowledge Base", "Ready")
                            
                            # List processed files
                            with st.expander("📋 View processed files", expanded=False):
                                for filename in processed_files:
                                    word_count = len(document_contents[filename].split())
                                    st.markdown(f"• **{filename}** - {word_count:,} words")
                        else:
                            st.error("❌ No documents were successfully processed.")
            else:
                st.warning("⚠️ Please upload files first!")
    
    with tab2:
        st.markdown("### ❓ Ask Questions")
        st.markdown("*Get intelligent answers from your uploaded documents with AI-powered search*")
        
        if st.session_state.collection is not None:
            # Professional question interface with examples
            with st.expander("💡 Example questions you can ask", expanded=False):
                st.markdown("""
                **📖 Content Analysis:**
                • "What are the main topics covered in these documents?"
                • "Summarize the key findings from the research papers"
                
                **🔍 Specific Information:**
                • "What does the document say about [specific topic]?"
                • "Find statistics or data about [subject]"
                
                **📊 Comparative Analysis:**
                • "Compare information between different documents"
                • "What are the similarities and differences in approach?"
                """)
            
            # Enhanced question input
            question = st.text_input(
                "What would you like to know about your documents?",
                placeholder="e.g., What are the main findings in the research papers?",
                help="💬 Ask any question about your uploaded documents in natural language"
            )
            
            # Professional button layout with enhanced UX
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                search_clicked = st.button(
                    "🔍 Search & Answer", 
                    type="primary",
                    help="Search through your documents and generate an AI-powered answer",
                    use_container_width=True
                )
                
                # Add helpful hint
                st.markdown("""
                <div style="text-align: center; margin-top: 8px;">
                    <small style="color: #64748b; font-size: 12px;">
                        🧠 AI will analyze your documents to provide accurate answers
                    </small>
                </div>
                """, unsafe_allow_html=True)
            
            if search_clicked and question.strip():
                with st.container():
                    # Professional loading state
                    with st.spinner("🧠 Analyzing your documents..."):
                        try:
                            # Use enhanced answer function with source tracking
                            answer, source = get_answer_with_source(st.session_state.collection, question)
                            
                            # Professional answer display
                            st.markdown("---")
                            st.markdown("### 💡 AI-Generated Answer")
                            
                            # Answer in a styled container
                            st.markdown(f"""
                            <div style="
                                background: rgba(34, 197, 94, 0.05);
                                border-left: 4px solid #22c55e;
                                padding: 20px;
                                border-radius: 8px;
                                margin: 15px 0;
                            ">
                                <p style="color: #2c3e50; font-size: 16px; line-height: 1.6; margin: 0;">
                                    {answer}
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Source attribution with styling
                            st.markdown(f"""
                            <div style="
                                background: rgba(59, 130, 246, 0.05);
                                border: 1px solid rgba(59, 130, 246, 0.2);
                                padding: 12px;
                                border-radius: 8px;
                                margin: 10px 0;
                            ">
                                📖 <strong>Primary Source:</strong> <em>{source}</em>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Add to search history
                            add_to_search_history(question, answer, source)
                            
                        except Exception as e:
                            st.error(f"❌ Error generating answer: {str(e)}")
            elif search_clicked:
                st.warning("⚠️ Please enter a question to search.")
        else:
            # Professional empty state
            st.markdown("""
            <div style="
                text-align: center;
                padding: 40px;
                background: rgba(59, 130, 246, 0.05);
                border-radius: 12px;
                border: 2px dashed #3b82f6;
                margin: 20px 0;
            ">
                <h3 style="color: #3b82f6; margin: 10px 0;">📚 No Documents Yet</h3>
                <p style="color: #64748b; margin: 10px 0;">
                    Upload and process documents in the Upload tab to start asking questions!
                </p>
                <p style="color: #64748b; font-size: 14px; margin: 0;">
                    💡 Once processed, you can ask questions about your document content
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Enhanced search history display
        if st.session_state.get('search_history'):
            st.markdown("---")
            show_search_history()
    
    with tab3:
        show_document_manager()
    
    with tab4:
        show_document_stats()
    
    with tab5:
        st.markdown("### 🔧 System Status & Health Check")
        st.markdown("*Monitor system components and troubleshoot any issues*")
        
        # Run health check
        health_issues = check_app_health()
        
        if not health_issues:
            st.success("✅ All system components are functioning correctly!")
            
            # Show system information
            st.markdown("#### 📊 System Information")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("ChromaDB", "✅ Active", "Running")
            with col2:
                st.metric("AI Models", "✅ Loaded", "Ready")
            with col3:
                st.metric("Docling", "✅ Available", "Processing")
                
        else:
            st.error("⚠️ Some system components need attention:")
            for issue in health_issues:
                st.markdown(f"❌ **{issue}**")
            
            st.markdown("#### 🔧 Troubleshooting Tips")
            st.info("""
            **Common Solutions:**
            - Restart the application
            - Check internet connection for model downloads
            - Ensure all dependencies are installed: `pip install -r requirements.txt`
            - Clear browser cache and refresh the page
            - Check if sufficient memory is available
            """)
        
        # Additional system diagnostics
        st.markdown("#### 🔍 Detailed Diagnostics")
        with st.expander("View Detailed System Check", expanded=False):
            try:
                import platform
                import psutil
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**System Info:**")
                    st.write(f"• Platform: {platform.system()} {platform.release()}")
                    st.write(f"• Python: {platform.python_version()}")
                    st.write(f"• Streamlit: {st.__version__}")
                
                with col2:
                    st.markdown("**Resource Usage:**")
                    memory = psutil.virtual_memory()
                    st.write(f"• Memory Usage: {memory.percent}%")
                    st.write(f"• Available Memory: {memory.available // (1024**3)} GB")
                    st.write(f"• CPU Usage: {psutil.cpu_percent()}%")
                    
            except ImportError:
                st.write("Install `psutil` for detailed system diagnostics: `pip install psutil`")
            except Exception as e:
                st.write(f"System diagnostics unavailable: {e}")

# HEALTH CHECK SYSTEM
def check_system_health():
    """Check system health and display issues if any"""
    health_issues = []
    
    # Check ChromaDB
    try:
        client = chromadb.Client()
        client.heartbeat()
    except Exception as e:
        health_issues.append(f"ChromaDB: {str(e)}")
    
    # Check Transformers
    try:
        from transformers import pipeline
        # Quick test to see if model loading works
        pipeline("text2text-generation", model="google/flan-t5-small")
    except Exception as e:
        health_issues.append(f"Transformers/AI Model: {str(e)}")
    
    # Check Docling
    try:
        from docling.document_converter import DocumentConverter
    except Exception as e:
        health_issues.append(f"Docling Document Converter: {str(e)}")
    
    # Check SentenceTransformers
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        health_issues.append(f"SentenceTransformers: {str(e)}")
    
    return health_issues

# MAIN APPLICATION
def main():
    """
    🏠 THE MAIN HOUSE OF OUR APP!
    
    What this function does (in simple words):
    - The front view of our app
    - Sets up how everything looks (colors, fonts, layout)
    - Creates all the different pages (tabs) people can visit
    - Starts up all the important parts of our app
    
    Think of it like this: 🏠🎨📱
    (Build the house) → (Decorate it nicely) → (Open the doors for visitors)
    
    This is where everything begins when someone visits our app!
    """
    # 🎯 Set up the basic settings for our web app
    st.set_page_config(
        page_title="Smart Document Q&A",  # What shows in the browser tab
        page_icon="📚",                   # The little icon in the browser tab
        layout="centered"                 # Put everything in the center (looks nice!)
    )
    
    # 🎨 CUSTOM CSS - Make our app look absolutely beautiful!
    st.markdown("""
    <style>
        /* 🌈 Beautiful background */
        .stApp, .stApp > header, .stApp > div, body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            background-attachment: fixed !important;
        }
        
        /* Main container with glass morphism effect */
        .main .block-container,
        .stMainBlockContainer,
        [data-testid="stMainBlockContainer"],
        .main > div,
        .block-container {
            background: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(10px) !important;
            padding: 2rem !important;
            border-radius: 20px !important;
            margin: 2rem auto !important;
            max-width: 900px !important;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2) !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
        }
        
        /* Professional Typography */
        .stApp *, 
        .stApp p, 
        .stApp div, 
        .stApp span, 
        .stApp h1, 
        .stApp h2, 
        .stApp h3,
        .stApp label {
            color: #2c3e50 !important;
            font-family: 'Segoe UI', 'Roboto', sans-serif !important;
        }
        
        /* Professional Input Styling */
        .stTextInput input {
            background: white !important;
            color: #2c3e50 !important;
            border: 2px solid #e5e7eb !important;
            border-radius: 10px !important;
            padding: 12px !important;
            font-size: 16px !important;
            transition: all 0.3s ease !important;
        }
        
        .stTextInput input:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        }
        
        /* Enhanced Button Styling - Primary buttons with maximum specificity */
        div.stButton > button:first-child,
        div.stButton > button[kind="primary"],
        div.stButton > button[data-testid="baseButton-primary"],
        .stButton > button,
        button[kind="primary"] {
            background: linear-gradient(45deg, #3b82f6, #1d4ed8) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 12px 24px !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
        }
        
        /* Force white text on ALL button content */
        div.stButton > button:first-child *,
        div.stButton > button[kind="primary"] *,
        div.stButton > button[data-testid="baseButton-primary"] *,
        .stButton > button *,
        button[kind="primary"] *,
        div.stButton > button span,
        div.stButton > button p {
            color: white !important;
        }
        
        div.stButton > button:first-child:hover,
        div.stButton > button[kind="primary"]:hover,
        div.stButton > button[data-testid="baseButton-primary"]:hover,
        .stButton > button:hover,
        button[kind="primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4) !important;
            color: white !important;
        }
        
        /* Ensure hover state text remains white */
        div.stButton > button:hover *,
        button[kind="primary"]:hover * {
            color: white !important;
        }
        
        /* Professional Tab Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px !important;
            background: rgba(248, 250, 252, 0.8) !important;
            padding: 8px !important;
            border-radius: 12px !important;
            margin-bottom: 20px !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.7) !important;
            border-radius: 8px !important;
            color: #64748b !important;
            font-weight: 600 !important;
            padding: 12px 20px !important;
            border: 1px solid rgba(203, 213, 225, 0.5) !important;
            transition: all 0.3s ease !important;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(45deg, #3b82f6, #1d4ed8) !important;
            color: white !important;
            border-color: transparent !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
        }
        
        /* Force white text on ALL content within active tab */
        .stTabs [aria-selected="true"] *,
        .stTabs [aria-selected="true"] span,
        .stTabs [aria-selected="true"] p,
        .stTabs [aria-selected="true"] div {
            color: white !important;
        }
        
        /* Professional Cards for Content */
        .stExpander {
            background: rgba(255, 255, 255, 0.9) !important;
            border-radius: 12px !important;
            border: 1px solid rgba(203, 213, 225, 0.3) !important;
            margin: 10px 0 !important;
        }
        
        /* Enhanced Metrics */
        [data-testid="metric-container"] {
            background: rgba(255, 255, 255, 0.9) !important;
            border-radius: 12px !important;
            padding: 16px !important;
            border: 1px solid rgba(203, 213, 225, 0.3) !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05) !important;
        }
        
        /* Success/Error Messages Enhancement */
        .stSuccess {
            background: rgba(34, 197, 94, 0.1) !important;
            border-left: 4px solid #22c55e !important;
            border-radius: 8px !important;
        }
        
        .stError {
            background: rgba(239, 68, 68, 0.1) !important;
            border-left: 4px solid #ef4444 !important;
            border-radius: 8px !important;
        }
        
        .stInfo {
            background: rgba(59, 130, 246, 0.1) !important;
            border-left: 4px solid #3b82f6 !important;
            border-radius: 8px !important;
        }
        
        /* Download Button Special Styling */
        .stDownloadButton > button {
            background: linear-gradient(45deg, #10b981, #059669) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 8px 16px !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            transition: all 0.3s ease !important;
        }
        
        .stDownloadButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
        }
        
        /* Loading Spinner Enhancement */
        .stSpinner {
            border-color: #3b82f6 !important;
        }
        
        /* Professional Footer */
        .footer-style {
            text-align: center;
            padding: 30px 20px;
            color: #64748b;
            font-size: 14px;
            border-top: 2px solid rgba(203, 213, 225, 0.2);
            margin-top: 40px;
            background: rgba(248, 250, 252, 0.5);
            border-radius: 12px;
        }
        
        /* Enhanced spacing for better visual hierarchy */
        .stTabs [data-baseweb="tab-panel"] {
            padding-top: 20px !important;
        }
        
        /* Improved section headers */
        .stApp h3 {
            border-bottom: 2px solid rgba(59, 130, 246, 0.2) !important;
            padding-bottom: 8px !important;
            margin-bottom: 20px !important;
        }
        
        /* Enhanced file uploader styling */
        .stFileUploader {
            border: 2px dashed rgba(59, 130, 246, 0.3) !important;
            border-radius: 12px !important;
            padding: 20px !important;
            background: rgba(59, 130, 246, 0.02) !important;
        }
    </style>
    
    <script>
    // Aggressively ensure button text is white - fallback JavaScript solution
    function ensureButtonStyling() {
        // Find ALL buttons and make them properly styled
        const allButtons = document.querySelectorAll('button');
        allButtons.forEach(button => {
            // Check if it's a primary button or contains "Process Documents"
            const isPrimary = button.getAttribute('kind') === 'primary' || 
                            button.hasAttribute('data-testid') && button.getAttribute('data-testid').includes('baseButton-primary') ||
                            button.textContent.includes('Process Documents') ||
                            button.textContent.includes('Search & Answer');
            
            if (isPrimary) {
                button.style.setProperty('color', 'white', 'important');
                button.style.setProperty('background', 'linear-gradient(45deg, #3b82f6, #1d4ed8)', 'important');
                
                // Force ALL child elements to have white text
                const allChildElements = button.querySelectorAll('*');
                allChildElements.forEach(child => {
                    child.style.setProperty('color', 'white', 'important');
                });
                
                // Also target text nodes directly
                const walker = document.createTreeWalker(
                    button,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                
                let textNode;
                while (textNode = walker.nextNode()) {
                    if (textNode.parentElement) {
                        textNode.parentElement.style.setProperty('color', 'white', 'important');
                    }
                }
            }
        });
        
        // Extra safety - target by common Streamlit button selectors
        const streamlitButtons = document.querySelectorAll('div.stButton > button, .stButton button');
        streamlitButtons.forEach(button => {
            if (button.textContent.includes('Process Documents') || button.textContent.includes('Search & Answer')) {
                button.style.setProperty('color', 'white', 'important');
                button.style.setProperty('background', 'linear-gradient(45deg, #3b82f6, #1d4ed8)', 'important');
                
                const allChildren = button.querySelectorAll('*');
                allChildren.forEach(child => {
                    child.style.setProperty('color', 'white', 'important');
                });
            }
        });
        
        // Force white text on active tabs
        const activeTabs = document.querySelectorAll('.stTabs [aria-selected="true"]');
        activeTabs.forEach(tab => {
            tab.style.setProperty('color', 'white', 'important');
            
            // Force all child elements to have white text
            const allTabChildren = tab.querySelectorAll('*');
            allTabChildren.forEach(child => {
                child.style.setProperty('color', 'white', 'important');
            });
        });
    }
    
    // Run immediately
    ensureButtonStyling();
    
    // Use MutationObserver to catch dynamically added buttons
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                ensureButtonStyling();
            }
        });
    });
    observer.observe(document.body, { childList: true, subtree: true });
    
    // Run periodically to catch any missed elements
    setInterval(ensureButtonStyling, 500);
    </script>
    """, unsafe_allow_html=True)

    # Professional Header with Logo
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col3:
        try:
            st.image("logo.png", width=120)
        except:
            # Professional fallback logo with styled container
            st.markdown("""
            <div style="
                text-align: center; 
                font-size: 3rem; 
                background: linear-gradient(45deg, #3b82f6, #1d4ed8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin: 10px 0;
            ">
                📚
            </div>
            """, unsafe_allow_html=True)

    # Professional Title and Subtitle
    st.markdown("""
    <div style="text-align: center; margin: 30px 0; padding: 20px 0;">
        <h1 style="
        ">📚 Smart Document Knowledge Base</h1>

                        
        🌟 Transform your documents into an intelligent Q&A system with AI-powered insights ✨
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state
    if "collection" not in st.session_state:
        st.session_state.collection = None  # Where we store our smart document
    if "uploaded_files_processed" not in st.session_state:
        st.session_state.uploaded_files_processed = []  # List of files we've successfully processed
    if "document_contents" not in st.session_state:
        st.session_state.document_contents = {}  # The actual text from each document
    if "search_history" not in st.session_state:
        st.session_state.search_history = []  # Memory of all questions and answers

    # 📱 Create the main app with all its tabs and features
    create_tabbed_interface()

    # Professional Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer-style">
        <div style="display: flex; justify-content: center; align-items: center; gap: 15px; margin: 10px 0;">
            <span style="background: rgba(59, 130, 246, 0.1); padding: 4px 12px; border-radius: 20px; font-size: 12px;">
                🤖 AI-Powered
            </span>
            <span style="background: rgba(16, 185, 129, 0.1); padding: 4px 12px; border-radius: 20px; font-size: 12px;">
                🔒 Privacy-First
            </span>
            <span style="background: rgba(147, 51, 234, 0.1); padding: 4px 12px; border-radius: 20px; font-size: 12px;">
                ⚡ Real-time
            </span>
        </div>
        <p style="margin: 10px 0; font-size: 12px; color: #94a3b8;">
            Built with ❤️ using Streamlit • Document Intelligence Platform
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced Help section with professional styling
    with st.expander("ℹ️ How to use this app", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **📁 Upload Tab:**
            - Select PDF, DOC, DOCX, or TXT files
            - Maximum 200MB per file
            - Click 'Process Documents' to convert and store them
            
            **❓ Ask Questions Tab:**
            - Type questions about your uploaded documents
            - View AI-generated answers with source attribution
            - See your complete search history
            """)
        
        with col2:
            st.markdown("""
            **📋 Manage Tab:**
            - Preview document content
            - Download converted markdown files
            - Delete unwanted documents
            - Manage your document collection
            
            **📊 Stats Tab:**
            - View comprehensive document statistics
            - Monitor file type breakdown
            - Track collection size and metrics
            """)
        
        st.markdown("---")
        st.markdown("""
        **💡 Pro Tips for Best Results:**
        - Upload related documents for better context and cross-referencing
        - Ask specific, focused questions rather than very broad queries
        - Use the search history to build on previous questions and answers
        - Download important converted files as markdown backups
        - Try different phrasings if you don't get the answer you're looking for
        """)
        
        # Technical information in an expandable section
        with st.expander("🔧 Technical Details", expanded=False):
            st.markdown("""
            **🏗️ Architecture:**
            - **Document Processing:** Docling for PDF/Word conversion with OCR support
            - **Text Chunking:** RecursiveCharacterTextSplitter for optimal search performance
            - **Vector Database:** ChromaDB for semantic similarity search
            - **AI Model:** Google Flan-T5 for answer generation with anti-hallucination
            - **Embeddings:** SentenceTransformers for document understanding
            
            **🌐 Deployment:**
            - **Cloud Ready:** Compatible with Streamlit Cloud, no file system dependencies
            - **Cross-Platform:** Works on Windows, Mac, and Linux
            - **Privacy First:** In-memory processing, no permanent file storage
            - **Real-time:** Instant document processing and question answering
            """)


# 🚀 THE LAUNCH PAD!
# This is where our app starts its journey!
# When someone runs this file, this part says "Hey, start the main function!"
# It's like pressing the "ON" button for our entire app.
# Think of it like this: 🎬🚀✨
# (Someone runs the app) → (This launches everything) → (Main function starts)

if __name__ == "__main__":
    main()  # 🎯 Start the main app!