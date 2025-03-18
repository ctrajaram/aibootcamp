import streamlit as st
from app.content_enhancer import ContentEnhancer
import re
import difflib
import html

def render_content_enhancer_ui(content, on_update=None, blog_id=None):
    """
    Render the content enhancer UI.
    
    Parameters:
    -----------
    content : str
        The content to enhance
    on_update : callable, optional
        Callback function to call when content is updated
    blog_id : str, optional
        ID of the blog post being edited, if applicable
    
    Returns:
    --------
    str
        The updated content if any enhancements were applied, otherwise the original content
    """
    if not content or not isinstance(content, str):
        st.warning("No content to enhance. Generate content first.")
        return content
    
    # Initialize content enhancer
    enhancer = ContentEnhancer()
    
    # Track if content was updated
    content_updated = False
    updated_content = content
    
    # Store original content for comparison
    original_content = content
    
    st.markdown("---")
    st.markdown("## Content Enhancement")
    
    st.markdown(
        "<div style='background-color: #f0f7ff; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #4361EE;'>"
        "<h4 style='margin-top: 0; color: #1E40AF;'>Enhance Your Content</h4>"
        "<p style='margin-bottom: 0;'>"
        "Choose an enhancement option below to improve your entire content."
        "</p>"
        "</div>",
        unsafe_allow_html=True
    )
    
    # Create columns for the enhancement buttons
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        detail_clicked = st.button("Add Detail", key="detail_whole", use_container_width=True)
    
    with col2:
        example_clicked = st.button("Add Examples", key="example_whole", use_container_width=True)
    
    with col3:
        technical_clicked = st.button("Technical", key="technical_whole", use_container_width=True)
    
    with col4:
        simplify_clicked = st.button("Simplify", key="simplify_whole", use_container_width=True)
    
    with col5:
        counter_clicked = st.button("Counterpoint", key="counter_whole", use_container_width=True)
    
    # Handle button clicks
    if detail_clicked:
        with st.spinner("Enhancing content with more details..."):
            try:
                enhanced = enhancer.enhance_content(content, "detail")
                st.success("Content enhanced with additional details!")
                updated_content = enhanced
                content_updated = True
                # Show comparison
                show_content_comparison(original_content, enhanced)
            except Exception as e:
                st.error(f"Error enhancing content: {str(e)}")
    
    elif example_clicked:
        with st.spinner("Adding examples to content..."):
            try:
                enhanced = enhancer.enhance_content(content, "example")
                st.success("Examples added to content!")
                updated_content = enhanced
                content_updated = True
                # Show comparison
                show_content_comparison(original_content, enhanced)
            except Exception as e:
                st.error(f"Error adding examples: {str(e)}")
    
    elif technical_clicked:
        with st.spinner("Adding technical details..."):
            try:
                enhanced = enhancer.enhance_content(content, "technical")
                st.success("Technical details added!")
                updated_content = enhanced
                content_updated = True
                # Show comparison
                show_content_comparison(original_content, enhanced)
            except Exception as e:
                st.error(f"Error adding technical details: {str(e)}")
    
    elif simplify_clicked:
        with st.spinner("Simplifying content..."):
            try:
                enhanced = enhancer.enhance_content(content, "simplified")
                st.success("Content simplified!")
                updated_content = enhanced
                content_updated = True
                # Show comparison
                show_content_comparison(original_content, enhanced)
            except Exception as e:
                st.error(f"Error simplifying content: {str(e)}")
    
    elif counter_clicked:
        with st.spinner("Adding counterpoints..."):
            try:
                enhanced = enhancer.enhance_content(content, "counterpoint")
                st.success("Counterpoints added!")
                updated_content = enhanced
                content_updated = True
                # Show comparison
                show_content_comparison(original_content, enhanced)
            except Exception as e:
                st.error(f"Error adding counterpoints: {str(e)}")
    
    # Show save button if content was updated and we have a blog_id
    if content_updated and blog_id:
        if st.button("Save Changes to Blog", key="save_blog_changes"):
            from frontend.streamlit_app import update_blog
            if update_blog(blog_id, updated_content):
                st.success("Blog post updated successfully!")
            else:
                st.error("Failed to update blog post.")
    
    # Call the update callback if content was updated
    if content_updated and on_update:
        on_update(updated_content)
    
    return updated_content if content_updated else content

def show_content_comparison(original, enhanced):
    """
    Show a comparison between original and enhanced content.
    
    Parameters:
    -----------
    original : str
        The original content
    enhanced : str
        The enhanced content
    """
    # Check if content is identical
    if original == enhanced:
        st.info("✨ It looks like your content is already well-crafted! The AI didn't suggest any changes. You might want to try a different enhancement option or modify your content first.")
        return
    
    with st.expander("View Changes (Click to expand)", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Original Content")
            st.markdown(original)
        
        with col2:
            st.markdown("### Enhanced Content")
            st.markdown(enhanced)
        
        st.markdown("### Detailed Changes")
        
        # Create HTML for the diff view
        diff = difflib.ndiff(original.splitlines(), enhanced.splitlines())
        
        diff_html = "<pre style='white-space: pre-wrap;'>"
        for line in diff:
            if line.startswith('+ '):
                diff_html += f"<span style='background-color: #e6ffe6; color: #006600;'>{html.escape(line)}</span><br>"
            elif line.startswith('- '):
                diff_html += f"<span style='background-color: #ffe6e6; color: #cc0000;'>{html.escape(line)}</span><br>"
            elif line.startswith('? '):
                # Skip the "?" lines as they're just indicators
                continue
            else:
                diff_html += f"{html.escape(line)}<br>"
        diff_html += "</pre>"
        
        # Display the diff view
        st.markdown(diff_html, unsafe_allow_html=True)
