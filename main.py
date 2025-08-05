import streamlit as st
from PIL import Image
from backend.backend_agent import run_agent
import asyncio

# Page configuration
st.set_page_config(
    page_title="Aircraft Maintenance Log Analyzer",
    page_icon="✈️"
)

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = []

# Header
st.title(":blue[_✈️Aircraft Maintenance Log Analyzer_]")

# Upload section
uploaded_file = st.file_uploader(
    "Upload Aircraft Maintenance Log Image",
    type=['png', 'jpg', 'jpeg'],
    label_visibility="hidden"
)


# Display uploaded image
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Aircraft Maintenance Log",use_container_width=True)

# Analysis button and results
if uploaded_file is not None :
    if st.button("Analyze" , use_container_width=True):
        st.session_state.analysis_results = []
        
        # Status indicator
        with st.spinner("Analyzing..."):
            img_byte_data = uploaded_file.getvalue()
            
            async def run_analysis():
                results = []
                async for frame in run_agent(img_byte_data):
                    # Parse the frame
                    parts = frame.split("] ", 1)
                    if len(parts) == 2:
                        timestamp = parts[0].replace("[", "")
                        message_parts = parts[1].split(": ", 1)
                        if len(message_parts) == 2:
                            agent_name = message_parts[0]
                            message_content = message_parts[1]
                            results.append({
                                'agent': agent_name,
                                'message': message_content,
                                'timestamp': timestamp
                            })
                return results
            
            try:
                # Run analysis
                results = asyncio.run(run_analysis())
                st.session_state.analysis_results = results
                st.success("Analysis Complete!")
                
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")

# Display results
if st.session_state.analysis_results:
    st.subheader("Analysis Results")
    
    for result in st.session_state.analysis_results:
        with st.expander(f"{result['agent']} - {result['timestamp']}"):
            st.write(result['message'])

elif not uploaded_file:
    st.info("Please upload an aircraft maintenance log image to begin analysis")