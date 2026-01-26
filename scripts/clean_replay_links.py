#!/usr/bin/env python3
"""
Script to clean and extract valid replay links from the JSON output.
"""

import json
import sys

def extract_replay_links(json_data):
    """
    Extract only valid replay URLs from the JSON data.
    """
    replay_links = []
    
    # If it's a string, parse it as JSON
    if isinstance(json_data, str):
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            print("Error: Invalid JSON data")
            return []
    else:
        data = json_data
    
    # Extract valid replay URLs
    for item in data:
        url = item.get('url', '')
        text = item.get('text', '')
        
        # Only include items with valid replay URLs
        if url and url != 'N/A' and 'replay' in url.lower():
            replay_links.append({
                'url': url,
                'text': text if text != 'Replay' else '',  # Skip generic "Replay" text
                'replay_id': url.split('id=')[-1] if 'id=' in url else ''
            })
    
    # Remove duplicates
    seen_urls = set()
    unique_links = []
    for link in replay_links:
        if link['url'] not in seen_urls:
            seen_urls.add(link['url'])
            unique_links.append(link)
    
    return unique_links

def save_links(replay_links, output_file='replay_links_clean.txt'):
    """Save replay links to a text file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        for link in replay_links:
            f.write(link['url'] + '\n')
    print(f"✅ Saved {len(replay_links)} replay links to {output_file}")

def save_csv(replay_links, output_file='replay_links_clean.csv'):
    """Save replay links to a CSV file."""
    import csv
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['url', 'replay_id', 'text'])
        writer.writeheader()
        writer.writerows(replay_links)
    print(f"✅ Saved {len(replay_links)} replay links to {output_file}")

if __name__ == '__main__':
    # The JSON data from the console
    json_data = """[
  {
    "text": "Welcome to Duelingbook!We've made some updates to the rules of the site. Click to view the Rules & Punishments.(9/24/25) You can now duel in Genesys Format and view its cardpool's points in Deck Constructor. For more information, visit https://www.yugioh-card.com/en/genesys/(11/6/23) Our 2023 Judge Exam is here! If you have at least 100 experience, you can test your ruling knowledge by taking this exam. You can take the exam at https://www.duelingbook.com/judge-exam(10/22/23) We've added Edison Format to the Duel Room! This is the format that was played at the 75th Shonen Jump Championship in Edison, New Jersey, on April 24th, 2010. You can learn more about Edison Format at https://www.duelingbook.com/edison-format(4/14/20) We've added ranked sections for Goat Format and Speed Duels! You can find more information about Goat Format here and more info about Speed Duels here.(4/1/20) We are following the new Master Rule update regarding Special Summoning monsters from the Extra Deck. We are also following new rules related to the activation legality of Trigger effects and various other mechanics.(11/6/19) Interested in becoming a judge on DB? Now's your chance! If you have attained at least 100 experience, you are ready to take our new Judge Exam(5/8/19) You can now play in Tag Duels! Here is a guide for how to set them up and play.(4/16/19) Replays now have the option to show both players' hands!Also, make sure you're familiar with the site's General Policies(3/19/19) You can now enter Solo Mode, which starts a game by yourself, with no opponent. Good for testing hands and combos!(1/30/19) Duelingbook has added a Speed Duel format! In Speed Duels, your deck contains 20-30 cards, and you can use a special skill throughout that game.(11/19/18) You can now create your own custom cards to use in duels! Check out our new Custom Cards feature.(10/29/18) You can now search for official tournament stores and regional qualifiers in your area! Try out our new Tournament Locator.(9/17/18) You can now change your card sleeves! You can unlock more sleeves by gaining more experience. Also, ratings have been reset for the new Forbidden/Limited list.(8/20/18) You can now take the Judge Exam. If you score well, we may contact you regarding a staff position.(11/06/17) You can now view replays of your games and watch them over and over again! To see them, scroll down in the main menu and click on Duel Records.(10/23/17) Check out Duelingbook's new forum! Click the Forum button above to get there.Tip: If your screen freezes, try resizing your browser window to fix the issue.",
    "url": "N/A"
  },
  {
    "text": "Goat & Edison replays",
    "url": "https://www.youtube.com/channel/UC7W85a2Slyy2CO4sKAVdeeA"
  },
  {
    "text": "Replay",
    "url": "N/A"
  },
  {
    "text": "Replay",
    "url": "https://www.duelingbook.com/replay?id=1313181-78115439"
  },
  {
    "text": "Replay",
    "url": "N/A"
  },
  {
    "text": "Replay",
    "url": "https://www.duelingbook.com/replay?id=1313181-78114879"
  },
  {
    "text": "Replay",
    "url": "N/A"
  },
  {
    "text": "Replay",
    "url": "https://www.duelingbook.com/replay?id=1313181-78114255"
  },
  {
    "text": "Replay",
    "url": "N/A"
  },
  {
    "text": "Replay",
    "url": "https://www.duelingbook.com/replay?id=1313181-78113613"
  },
  {
    "text": "Replay",
    "url": "N/A"
  },
  {
    "text": "Replay",
    "url": "https://www.duelingbook.com/replay?id=1313181-78113301"
  },
  {
    "text": "Replay",
    "url": "N/A"
  },
  {
    "text": "Replay",
    "url": "https://www.duelingbook.com/replay?id=1313181-78112773"
  },
  {
    "text": "Replay",
    "url": "N/A"
  },
  {
    "text": "Replay",
    "url": "https://www.duelingbook.com/replay?id=1313181-78112576"
  },
  {
    "text": "Replay",
    "url": "N/A"
  },
  {
    "text": "Replay",
    "url": "https://www.duelingbook.com/replay?id=1313181-78105300"
  },
  {
    "text": "Replay",
    "url": "N/A"
  },
  {
    "text": "Replay",
    "url": "https://www.duelingbook.com/replay?id=1313181-78105001"
  },
  {
    "text": "Replay",
    "url": "N/A"
  },
  {
    "text": "Replay",
    "url": "https://www.duelingbook.com/replay?id=1313181-78104774"
  },
  {
    "text": "Replay",
    "url": "N/A"
  },
  {
    "text": "Replay",
    "url": "https://www.duelingbook.com/replay?id=1313181-76237082"
  }
]"""
    
    print("Extracting replay links...\n")
    replay_links = extract_replay_links(json_data)
    
    print(f"Found {len(replay_links)} valid replay links:\n")
    for i, link in enumerate(replay_links, 1):
        print(f"{i}. {link['url']}")
    
    save_links(replay_links)
    save_csv(replay_links)
    
    print(f"\n✅ Done! You now have all {len(replay_links)} replay links saved to files.")

