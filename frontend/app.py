import streamlit as st
import sys
import os
import zipfile
import io
from pathlib import Path
import logging
from contextlib import redirect_stdout
import streamlit.components.v1 as components

# Suppress verbose logging
logging.getLogger("langchain").setLevel(logging.CRITICAL)
logging.getLogger("langchain_aws").setLevel(logging.CRITICAL)
logging.getLogger("botocore").setLevel(logging.CRITICAL)

# Add workspace root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.report import weekly_report
from backend.report import create_report
from backend.process import weekly_report_core

st.set_page_config(page_title="Patent Report Generator", layout="wide")
st.title("📄 Patent Report Generator")

# Initialize session state
if "processing_complete" not in st.session_state:
    st.session_state.processing_complete = False

# File uploader
uploaded_file = st.file_uploader(
    "Upload an HTML file",
    type=["htm", "html"],
    help="Select the HTML file to process"
)

if uploaded_file is not None:
    # Display file info
    st.info(f"📁 File loaded: {uploaded_file.name}")
    
    # Process button
    if st.button("🔄 Process Report", type="primary"):
        st.session_state.processing_complete = False  # Reset on new processing
        
        try:
            # Save uploaded file temporarily
            temp_file_path = f"/tmp/{uploaded_file.name}"
            os.makedirs("/tmp", exist_ok=True)
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Create progress placeholder
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            # Processing step 1: Parse HTML
            with progress_placeholder.container():
                st.progress(10, text="📖 Parsing HTML file...")
            
            soup = weekly_report.HTMLParser(temp_file_path).split_file_as_individual_author_sections()
            st.session_state.soup = soup
            
            with status_placeholder.container():
                st.success("✓ HTML parsed successfully")
            
            # Processing step 2: Optimize parsing
            with progress_placeholder.container():
                st.progress(50, text="⚙️ Processing content (this may take a while)...")
            
            result = weekly_report_core.html_parser_optimized(
                soup, 
                max_workers=4, 
                max_retries=8
            )
            st.session_state.result = result
            
            with status_placeholder.container():
                st.success("✓ Content processed successfully")
            
            # Processing step 3: Generate report
            with progress_placeholder.container():
                st.progress(90, text="📊 Generating report...")
            
            # Suppress verbose output from create_report
            with redirect_stdout(io.StringIO()):
                result_tuple = create_report.main(result)
            
            if result_tuple is None:
                st.error("❌ Failed to generate report. Please check the console for details.")
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                st.stop()
                
            file_paths, dir_path = result_tuple

            # Persist paths to session state
            st.session_state.file_paths = file_paths
            st.session_state.dir_path = dir_path
            st.session_state.temp_file_path = temp_file_path
            
            with progress_placeholder.container():
                st.progress(100, text="✅ Report generated!")
            
            with status_placeholder.container():
                st.success("✓ Report generation complete")
            
            # Create ZIP file
            st.info("📦 Creating download package...")
            
            # Create a new folder in temp to organize all files
            import shutil
            import tempfile as tmp_module
            
            package_dir = os.path.join(tmp_module.gettempdir(), "patent_report")
            if os.path.exists(package_dir):
                shutil.rmtree(package_dir)
            os.makedirs(package_dir)
            st.session_state.package_dir = package_dir
            
            # Copy original uploaded HTML file to package
            shutil.copy2(temp_file_path, os.path.join(package_dir, uploaded_file.name))
            
            # Copy generated reports folder to package
            if dir_path and os.path.isdir(dir_path):
                package_reports_dir = os.path.join(package_dir, os.path.basename(dir_path))
                shutil.copytree(dir_path, package_reports_dir)
            
            # Create ZIP from the package folder
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(package_dir):
                    for file in files:
                        file_full_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_full_path, package_dir)
                        zip_file.write(file_full_path, arcname)
            
            zip_buffer.seek(0)
            st.session_state.zip_buffer = zip_buffer.getvalue()  # Store as bytes
            
            # Mark processing as complete
            st.session_state.processing_complete = True
        
        except Exception as e:
            import traceback
            st.error(f"❌ Error processing file: {str(e)}")
            st.error("Traceback:")
            st.code(traceback.format_exc())
            # Cleanup on error
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    # Show results if processing is complete
    if st.session_state.processing_complete:
        # Download button
        st.download_button(
            label="⬇️ Download Report (ZIP)",
            data=st.session_state.zip_buffer,
            file_name="patent_report.zip",
            mime="application/zip",
            type="primary"
        )

        # Preview / Compare UI
        try:
            file_paths = st.session_state.get("file_paths", [])
            temp_file_path = st.session_state.get("temp_file_path", "")

            if file_paths and isinstance(file_paths, list):
                st.markdown("---")
                st.header("🔎 Preview & Compare")
                author_options = [os.path.basename(p) for p in file_paths]
                
                # Initialize selected_author if not present
                if "selected_author" not in st.session_state:
                    st.session_state.selected_author = author_options[0]
                
                selected_author = st.selectbox(
                    "Select processed report (author)", 
                    author_options, 
                    index=author_options.index(st.session_state.selected_author) if st.session_state.selected_author in author_options else 0,
                    key="author_dropdown"
                )
                
                # Update session state when dropdown changes
                st.session_state.selected_author = selected_author
                
                show_original = st.checkbox("Show original HTML", value=True, key="show_original")

                # Find selected author path
                selected_path = None
                for p in file_paths:
                    if os.path.basename(p) == selected_author:
                        selected_path = p
                        break

                # Read contents
                author_html = ""
                original_html = ""
                if selected_path and os.path.isfile(selected_path):
                    with open(selected_path, "r", encoding="utf-8", errors="replace") as f:
                        author_html = f.read()
                if os.path.isfile(temp_file_path):
                    with open(temp_file_path, "r", encoding="utf-8", errors="replace") as f:
                        original_html = f.read()

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Processed Report")
                    if author_html:
                        components.html(author_html, height=600, scrolling=True)
                    else:
                        st.info("Processed report preview not available.")
                with col2:
                    st.subheader("Original File")
                    if show_original:
                        if original_html:
                            components.html(original_html, height=600, scrolling=True)
                        else:
                            st.info("Original HTML preview not available.")
        except Exception as e:
            st.warning(f"Preview not available: {e}")

        st.success("✅ All done! Click the button above to download your report.")

        # Cleanup button
        if st.button("🧹 Cleanup temporary files"):
            try:
                import shutil
                if os.path.exists(st.session_state.get("temp_file_path", "")):
                    os.remove(st.session_state.get("temp_file_path"))
                if os.path.exists(st.session_state.get("package_dir", "")):
                    shutil.rmtree(st.session_state.get("package_dir"))
                # Clear session state
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.success("Temporary files removed and session cleared.")
                st.rerun()
            except Exception as e:
                st.error(f"Cleanup failed: {e}")

else:
    st.info("👆 Please upload an HTML file to get started")
    st.markdown("""
    ### How it works:
    1. **Upload** your HTML file using the uploader above
    2. **Click** the "Process Report" button
    3. **Wait** for processing to complete (progress bar shows status)
    4. **Download** your report as ZIP file
    
    ### Features:
    - 📄 Supports .htm and .html files
    - ⚙️ Intelligent content processing
    - 📦 Results packaged as ZIP for easy download
    - 🔄 Retry mechanism for robust processing
    """)