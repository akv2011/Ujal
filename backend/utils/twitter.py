import os
import logging
from pathlib import Path
import requests
import tweepy
from dotenv import load_dotenv
from fastapi import HTTPException

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TwitterClient:
    def __init__(self):
        """Initialize Twitter API credentials and clients."""
        self.consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
        self.consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
        self.access_key = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        
        if not all([self.consumer_key, self.consumer_secret, 
                   self.access_key, self.access_secret, self.bearer_token]):
            raise ValueError("Missing Twitter API credentials in environment variables")
        
        self.auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        self.auth.set_access_token(self.access_key, self.access_secret)
        
        self.api_v1 = tweepy.API(self.auth)
        self.api_v2 = tweepy.Client(
            bearer_token=self.bearer_token,
            access_token=self.access_key,
            access_token_secret=self.access_secret,
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
        )

    def send_message(self, image_url: str, caption: str) -> dict:
        """
        Send a tweet with an image and caption.
        
        Args:
            image_url: URL of the image to tweet
            caption: Text caption for the tweet
            
        Returns:
            dict: Response containing tweet status
            
        Raises:
            HTTPException: If image download or tweet posting fails
        """
        temp_image_path = Path("temp_image.png")
        
        try:
            # Download image
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            
            # Save temporary image
            temp_image_path.write_bytes(image_response.content)
            
            # Upload media using v1.1 API
            media = self.api_v1.media_upload(str(temp_image_path))
            
            # Create tweet using v2 API
            post_result = self.api_v2.create_tweet(
                text=caption,
                media_ids=[media.media_id]
            )
            
            logger.info(f"Successfully posted tweet with image: {caption[:30]}...")
            return {
                "message": "Tweet posted successfully",
                "data": post_result
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download image: {e}")
            raise HTTPException(status_code=400, detail="Failed to download image")
            
        except tweepy.TweepyException as e:
            logger.error(f"Twitter API error: {e}")
            raise HTTPException(status_code=500, detail=f"Twitter API error: {str(e)}")
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
        finally:
            # Cleanup
            if temp_image_path.exists():
                temp_image_path.unlink()

def send_message_to_twitter(image_url: str, caption: str) -> dict:
    """Wrapper function to maintain backward compatibility."""
    client = TwitterClient()
    return client.send_message(image_url, caption)