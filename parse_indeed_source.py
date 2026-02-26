import json
import re

def main():
    try:
        with open("indeed_v2_source.html", "r", encoding="utf-8") as f:
            content = f.read()
            
        output = []
        output.append(f"Content length: {len(content)}")
        
        matches = re.finditer(r'"datePosted"\s*:\s*"([^"]+)"', content)
        for match in matches:
            output.append(f"Found datePosted (regex): {match.group(1)}")
            
        matches = re.finditer(r'<meta[^>]*itemprop=["\']datePosted["\'][^>]*content=["\']([^"\']+)["\']', content)
        for match in matches:
            output.append(f"Found meta datePosted: {match.group(1)}")

        matches = re.finditer(r'"validThrough"\s*:\s*"([^"]+)"', content)
        for match in matches:
            output.append(f"Found validThrough (regex): {match.group(1)}")
            
        with open("dates_utf8.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(output))
            
    except Exception as e:
        with open("dates_utf8.txt", "w", encoding="utf-8") as f:
            f.write(f"Error: {e}")

if __name__ == "__main__":
    main()
