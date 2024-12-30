// lib/twitter.ts
import tweepy from 'tweepy';
import axios from 'axios';
import fs from 'fs';
import path from 'path';
import { promises as fsPromises } from 'fs';

export class TwitterClient {
  private api_v1: any;
  private api_v2: any;

  constructor() {
    const consumer_key = process.env.TWITTER_CONSUMER_KEY;
    const consumer_secret = process.env.TWITTER_CONSUMER_SECRET;
    const access_key = process.env.TWITTER_ACCESS_TOKEN;
    const access_secret = process.env.TWITTER_ACCESS_TOKEN_SECRET;
    const bearer_token = process.env.TWITTER_BEARER_TOKEN;

    if (!consumer_key || !consumer_secret || !access_key || !access_secret || !bearer_token) {
      throw new Error('Missing Twitter API credentials');
    }

    const auth = new tweepy.OAuthHandler(consumer_key, consumer_secret);
    auth.set_access_token(access_key, access_secret);

    this.api_v1 = new tweepy.API(auth);
    this.api_v2 = new tweepy.Client({
      bearer_token,
      access_token: access_key,
      access_token_secret: access_secret,
      consumer_key,
      consumer_secret,
    });
  }

  async send_message(imageUrl: string, caption: string) {
    const tempDir = path.join(process.cwd(), 'tmp');
    const tempImagePath = path.join(tempDir, `temp_${Date.now()}.png`);

    try {
      // Create temp directory if it doesn't exist
      await fsPromises.mkdir(tempDir, { recursive: true });

      // Download image
      const response = await axios.get(imageUrl, { responseType: 'arraybuffer' });
      await fsPromises.writeFile(tempImagePath, response.data);

      // Upload media
      const media = await this.api_v1.media_upload(tempImagePath);

      // Create tweet
      const result = await this.api_v2.create_tweet({
        text: caption,
        media_ids: [media.media_id],
      });

      return {
        success: true,
        message: 'Tweet posted successfully',
        data: result,
      };

    } catch (error) {
      console.error('Twitter error:', error);
      throw error;
    } finally {
      // Cleanup
      try {
        if (fs.existsSync(tempImagePath)) {
          await fsPromises.unlink(tempImagePath);
        }
      } catch (error) {
        console.error('Error cleaning up temp file:', error);
      }
    }
  }
}