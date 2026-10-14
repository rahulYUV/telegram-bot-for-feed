import requests
from config import RAPIDAPI_KEY, RAPIDAPI_HOST

def fetch_latest_posts(username: str):
    """
    Fetches latest reels using POST /get_ig_user_reels.php
    """
    url = f"https://{RAPIDAPI_HOST}/get_ig_user_reels.php"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    data = {
        "username_or_url": username,
        "amount": "5"
    }

    try:
        res = requests.post(url, headers=headers, data=data, timeout=25)
        if res.status_code != 200:
            print(f"API Error ({res.status_code}): {res.text[:120]}")
            return []

        resp_json = res.json()
        
        # Parse items based on API return format
        items = (
            resp_json.get("data", {}).get("items", [])
            or resp_json.get("items", [])
            or resp_json.get("data", [])
            or []
        )

        posts = []
        for entry in items[:5]:
            node = entry.get("node", entry)
            post_id = node.get("id") or node.get("code") or node.get("pk")
            code = node.get("code") or node.get("shortcode")
            
            # Caption parsing
            caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
            if caption_edges:
                caption_text = caption_edges[0].get("node", {}).get("text", "")
            elif isinstance(node.get("caption"), dict):
                caption_text = node.get("caption", {}).get("text", "")
            else:
                caption_text = str(node.get("caption") or "")

            # Video/Reel media URL extraction
            is_video = node.get("is_video", True) or node.get("media_type") == 2
            media_url = None
            if node.get("video_versions"):
                media_url = node["video_versions"][0].get("url")
            elif node.get("video_url"):
                media_url = node.get("video_url")
            elif node.get("image_versions2", {}).get("candidates"):
                media_url = node["image_versions2"]["candidates"][0].get("url")
            else:
                media_url = node.get("display_url")

            posts.append({
                "id": str(post_id),
                "url": f"https://www.instagram.com/reel/{code}/" if code else f"https://www.instagram.com/{username}/",
                "media_url": media_url,
                "is_video": is_video,
                "caption": caption_text[:280] + ("..." if len(caption_text) > 280 else "")
            })
        return posts
    except Exception as e:
        print(f"Error fetching @{username}: {e}")
        return []

def fetch_post_by_url(target_url: str):
    """
    Fetches a specific reel/post details via URL
    """
    url = f"https://{RAPIDAPI_HOST}/get_ig_post_details.php"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    data = {
        "username_or_url": target_url,
        "url_or_shortcode": target_url
    }

    try:
        res = requests.post(url, headers=headers, data=data, timeout=25)
        if res.status_code != 200:
            return None

        resp_json = res.json()
        item = resp_json.get("data", resp_json)
        if isinstance(item, dict) and "items" in item and len(item["items"]) > 0:
            item = item["items"][0]

        node = item.get("node", item)
        is_video = node.get("is_video", True) or node.get("media_type") == 2 or "video_versions" in node

        media_url = None
        if node.get("video_versions"):
            media_url = node["video_versions"][0].get("url")
        elif node.get("video_url"):
            media_url = node.get("video_url")
        elif node.get("image_versions2", {}).get("candidates"):
            media_url = node["image_versions2"]["candidates"][0].get("url")
        else:
            media_url = node.get("display_url")

        caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
        if caption_edges:
            caption_text = caption_edges[0].get("node", {}).get("text", "")
        elif isinstance(node.get("caption"), dict):
            caption_text = node.get("caption", {}).get("text", "")
        else:
            caption_text = str(node.get("caption") or "")

        return {
            "media_url": media_url,
            "is_video": is_video,
            "caption": caption_text[:280] + ("..." if len(caption_text) > 280 else "")
        }
    except Exception as e:
        print(f"Error fetching reel link: {e}")
        return None