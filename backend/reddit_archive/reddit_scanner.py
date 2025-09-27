import os
import praw

# --- CONFIGURATION ---
CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET")
USER_AGENT = os.environ.get("REDDIT_USER_AGENT")

def search_posts_by_title(subreddit_name: str, keyword: str, limit: int):
    """
    Uses Reddit's own search to find posts with a keyword in the title.
    """
    if not all([CLIENT_ID, CLIENT_SECRET, USER_AGENT]):
        print("❌ Error: Missing Reddit API credentials.")
        return

    print(f"🔍 Using Reddit search in 'r/{subreddit_name}' for titles with '{keyword}'...")

    try:
        reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent=USER_AGENT,
        )

        subreddit = reddit.subreddit(subreddit_name)
        
        # This uses the search query format `title:"your keyword"`
        search_query = f'title:"{keyword}"'
        
        found_posts = []
        # The search function is much more direct than scanning .hot()
        for submission in subreddit.search(search_query, limit=limit):
            found_posts.append({
                "title": submission.title,
                "url": f"https://www.reddit.com{submission.permalink}"
            })

        if not found_posts:
            print(f"\n✅ No posts found matching the query '{search_query}'.")
        else:
            print(f"\n✅ Found {len(found_posts)} matching posts:")
            print("-" * 30)
            for post in found_posts:
                print(f"Title: {post['title']}")
                print(f"URL: {post['url']}\n")

    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    sub_name = input("Enter the subreddit name (e.g., 'futurology'): ")
    search_keyword = input("Enter the keyword to search for in the title: ")
    search_limit = int(input("What is the maximum number of results you want? (e.g., 25): "))
    
    if sub_name and search_keyword and search_limit > 0:
        search_posts_by_title(sub_name, search_keyword, search_limit)