import re

def markdown_to_html(text: str) -> str:
    """
    Convert basic markdown to HTML for display in chat bubbles.
    """
    if not text:
        return text
    
    # Convert **bold** to <strong>bold</strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert *italic* to <em>italic</em>
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    # Convert bullet points and numbered lists to HTML lists
    lines = text.split('\n')
    html_lines = []
    in_ul = False
    in_ol = False
    
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        
        # Check for bullet points
        if stripped_line.startswith('• ') or stripped_line.startswith('- '):
            if in_ol:
                html_lines.append('</ol>')
                in_ol = False
            if not in_ul:
                html_lines.append('<ul>')
                in_ul = True
            content = stripped_line[2:]  # Remove bullet and space
            html_lines.append(f'<li>{content}</li>')
            
        # Check for numbered lists (1., 2., 3., etc.)
        elif re.match(r'^\d+\.\s', stripped_line):
            if in_ul:
                html_lines.append('</ul>')
                in_ul = False
            if not in_ol:
                html_lines.append('<ol>')
                in_ol = True
            # Extract content after the number and period
            content = re.sub(r'^\d+\.\s*', '', stripped_line)
            html_lines.append(f'<li>{content}</li>')
            
        else:
            # Only close lists if this is a non-empty line that's not part of a list
            if stripped_line and not (stripped_line.startswith('• ') or stripped_line.startswith('- ') or re.match(r'^\d+\.\s', stripped_line)):
                # Close any open lists
                if in_ul:
                    html_lines.append('</ul>')
                    in_ul = False
                if in_ol:
                    html_lines.append('</ol>')
                    in_ol = False
                    
                # Handle regular text
                html_lines.append(f'<p>{stripped_line}</p>')
            # If it's an empty line, don't close lists - they might continue
            
    
    # Close any remaining open lists
    if in_ul:
        html_lines.append('</ul>')
    if in_ol:
        html_lines.append('</ol>')
    
    # Join the HTML lines
    html_text = '\n'.join(html_lines)
    
    
    return html_text 