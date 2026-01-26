#!/usr/bin/env python3
"""
Extract and clean replay URLs from the JSON output you got from the browser console.
You can paste the JSON directly into this script or save it to a file.
"""

import json
import sys
import csv

def extract_replay_links(data):
    """Extract valid replay URLs from the data."""
    replay_links = []
    
    for item in data:
        url = item.get('url', '')
        # Only include valid replay URLs (not "N/A" and contains "replay")
        if url and url != 'N/A' and 'replay' in url.lower() and 'duelingbook.com' in url:
            replay_id = url.split('id=')[-1] if 'id=' in url else ''
            replay_links.append({
                'url': url,
                'replay_id': replay_id
            })
    
    # Remove duplicates
    seen = set()
    unique = []
    for link in replay_links:
        if link['url'] not in seen:
            seen.add(link['url'])
            unique.append(link)
    
    return unique

def main():
    # Check if JSON data was provided as command line argument
    if len(sys.argv) > 1:
        # Read from file
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        # Read from stdin (you can paste JSON here)
        print("Paste your JSON data (press Ctrl+D or Cmd+D when done, or type 'END' on a new line):")
        lines = []
        for line in sys.stdin:
            if line.strip() == 'END':
                break
            lines.append(line)
        json_str = ''.join(lines)
        data = json.loads(json_str)
    
    print("\nExtracting replay links...\n")
    replay_links = extract_replay_links(data)
    
    print(f"Found {len(replay_links)} valid replay links:\n")
    for i, link in enumerate(replay_links, 1):
        print(f"{i}. {link['url']}")
    
    # Save to text file (one URL per line)
    with open('replay_links.txt', 'w', encoding='utf-8') as f:
        for link in replay_links:
            f.write(link['url'] + '\n')
    print(f"\n✅ Saved to replay_links.txt")
    
    # Save to CSV
    with open('replay_links.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['url', 'replay_id'])
        writer.writeheader()
        writer.writerows(replay_links)
    print(f"✅ Saved to replay_links.csv")
    
    return replay_links

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    except json.JSONDecodeError as e:
        print(f"\n❌ Error: Invalid JSON data\n{e}")
        print("\nMake sure you copied the complete JSON from the console.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

