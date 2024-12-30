import React from 'react';
import { Button } from './ui/button';
import { ShareIcon } from 'lucide-react';
import Image from 'next/image';
import axios from 'axios';
import toast from 'react-hot-toast'; // Import toast

interface ShareProps {
  imageURL: string;
  resText: string;
  setShared: (shared: boolean) => void;
}

function Share({ imageURL, resText, setShared }: ShareProps) {
  const [encodedImage, setEncodedImage] = React.useState<string>('');
  const [isProcessing, setIsProcessing] = React.useState(false); // Add loading state

  const handleCommonFunction = async () => {
    setIsProcessing(true);
    try {
      console.log('Sending resImage to /api/decompose:', imageURL);
      const encodeImage = await axios.post('/api/decompose', {
        resImage: imageURL,
      });
      setEncodedImage(encodeImage.data.encodedImage);

      console.log('Sending resText to /api/decompose:', resText);
      const decomposeReq = await axios.post('/api/decompose', {
        resText: resText,
      });

      const data = {
        ...decomposeReq.data.decomposed,
        status: 'pending',
      };

      console.log('Sending data to /api/save:', data);
      const saveReq = await axios.post('/api/save', data);

      if (saveReq.status !== 200) {
        console.error('Failed to save to DB');
        toast.error('Failed to save post.');
      } else {
        toast.success('Post saved successfully!');
        setShared(true);
      }
    } catch (error: any) {
      console.error('Error in handleCommonFunction:', error);
      toast.error(`Error sharing: ${error.message}`); // Show user-friendly error
    } finally {
      setIsProcessing(false);
    }
  };

  const handleShareTelegram = () => {
    if (!encodedImage) {
      toast.error('Please wait for the preview to generate.');
      return;
    }
    const telegramShareUrl = `https://t.me/share/url?url=${encodeURIComponent(
      encodedImage
    )}`;
    window.open(telegramShareUrl, '_blank');
    handleCommonFunction();
  };

  const handleShareTwitter = () => {
    const twitterShareUrl = `https://twitter.com/intent/tweet?url=${encodeURIComponent(
      imageURL
    )}`;
    window.open(twitterShareUrl, '_blank');
    handleCommonFunction();
  };

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative w-[500px] h-[500px]">
        <Image
          src={imageURL}
          alt="Generated Image"
          layout="fill"
          objectFit="cover"
          className="rounded-md"
        />
      </div>

      <div className="flex items-center gap-4">
        <Button
          variant="default"
          className="flex items-center gap-2"
          onClick={handleShareTelegram}
          disabled={isProcessing} // Disable button while processing
        >
          <ShareIcon size={24} />
          Share on Telegram
        </Button>
        <Button
          variant="default"
          className="flex items-center gap-2 bg-black text-white"
          onClick={handleShareTwitter}
          disabled={isProcessing} // Disable button while processing
        >
          <ShareIcon size={24} />
          Share on Twitter
        </Button>
        <Button
          variant="default"
          className="flex items-center gap-2 bg-gradient-to-r from-[#405DE6] to-[#5851DB] text-white"
          disabled={isProcessing} // Disable button while processing
        >
          <ShareIcon size={24} />
          Share on Instagram 
        </Button>
        <Button
          variant="default"
          className="flex items-center gap-2"
          disabled={isProcessing} // Disable button while processing
        >
          <ShareIcon size={24} />
          Share on Slack
        </Button>
      </div>
    </div>
  );
}

export default Share;