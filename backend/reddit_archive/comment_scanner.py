import os
import praw

# --- CONFIGURATION ---
# Your API credentials, loaded from environment variables
CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET")
USER_AGENT = os.environ.get("REDDIT_USER_AGENT")

def get_comments_from_post(post_url: str):
    """
    Fetches all comments from a single Reddit post URL.
    """
    if not all([CLIENT_ID, CLIENT_SECRET, USER_AGENT]):
        print("❌ Error: Missing Reddit API credentials.")
        return None

    print(f"🔥 Fetching all comments from: {post_url}")

    try:
        # 1. Authenticate with Reddit
        reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent=USER_AGENT,
        )

        # 2. Get the submission object from the URL
        submission = reddit.submission(url=post_url)

        # 3. Expand all "load more comments" links
        # This is a crucial step to get all comments, not just the top-level ones.
        # It can take a moment for posts with many comments.
        print("   - Expanding all comments (this might take a second)...")
        submission.comments.replace_more(limit=0)

        # 4. Extract the text (body) from every comment
        all_comments = []
        for comment in submission.comments.list():
            # The actual text of the comment is in the 'body' attribute
            all_comments.append(comment.body)
            
        print(f"   - ✅ Found {len(all_comments)} comments.")
        return all_comments

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return None

if __name__ == "__main__":
    url_input = input("Enter the full URL of the Reddit post: ")
    
    if url_input:
        comments = get_comments_from_post(url_input)
        
        if comments:
            print("\n--- All Comments ---")
            # We'll just print the first 10 for this example
            for i, text in enumerate(comments[:10]):
                print(f"COMMENT #{i+1}:\n{text}\n---")
            
            if len(comments) > 10:
                print(f"... and {len(comments) - 10} more comments not shown.")
            
            # You can also save all comments to a file
            # with open("comments.txt", "w", encoding="utf-8") as f:
            #     f.write("\n\n---\n\n".join(comments))
            # print("\nAll comments also saved to comments.txt")