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
    
    for line in lines:
        line = line.strip()
        
        # Check for bullet points
        if line.startswith('• ') or line.startswith('- '):
            if in_ol:
                html_lines.append('</ol>')
                in_ol = False
            if not in_ul:
                html_lines.append('<ul>')
                in_ul = True
            content = line[2:]  # Remove bullet and space
            html_lines.append(f'<li>{content}</li>')
            
        # Check for numbered lists (1., 2., 3., etc.)
        elif re.match(r'^\d+\.\s', line):
            if in_ul:
                html_lines.append('</ul>')
                in_ul = False
            if not in_ol:
                html_lines.append('<ol>')
                in_ol = True
            # Extract content after the number and period
            content = re.sub(r'^\d+\.\s*', '', line)
            html_lines.append(f'<li>{content}</li>')
            
        else:
            # Close any open lists
            if in_ul:
                html_lines.append('</ul>')
                in_ul = False
            if in_ol:
                html_lines.append('</ol>')
                in_ol = False
                
            # Handle regular text
            if line:
                html_lines.append(f'<p>{line}</p>')
            
    
    # Close any remaining open lists
    if in_ul:
        html_lines.append('</ul>')
    if in_ol:
        html_lines.append('</ol>')
    
    return '\n'.join(html_lines) 