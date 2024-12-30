// components/ImageGen.tsx
'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import axios, { AxiosError } from 'axios';
import { useCallback, useState } from 'react';
import Image from 'next/image';
import { TwitterShareButton, TwitterIcon } from 'next-share';
import toast from 'react-hot-toast';

const FormSchema = z.object({
  imageFile: z.instanceof(File, { message: 'Please upload an image.' }).optional(),
});

type FormData = z.infer<typeof FormSchema>;

const ERROR_MESSAGES = {
  FILE_TOO_LARGE: 'The image file is too large. Please upload a smaller file.',
  INVALID_FILE_TYPE: 'Invalid file type. Please upload a valid image file.',
  SERVER_ERROR: 'Server error occurred. Please try again later.',
  NETWORK_ERROR: 'Network error. Please check your connection and try again.',
  DEFAULT: 'An unexpected error occurred. Please try again.',
};

const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ message?: string }>;

    switch (axiosError.response?.status) {
      case 413:
        return ERROR_MESSAGES.FILE_TOO_LARGE;
      case 415:
        return ERROR_MESSAGES.INVALID_FILE_TYPE;
      case 500:
        return ERROR_MESSAGES.SERVER_ERROR;
    }

    if (axiosError.code === 'ECONNABORTED' || axiosError.code === 'ERR_NETWORK') {
      return ERROR_MESSAGES.NETWORK_ERROR;
    }

    return axiosError.response?.data?.message || ERROR_MESSAGES.DEFAULT;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return ERROR_MESSAGES.DEFAULT;
};

interface ImageGenProps {
  text: string | null;
  textGemma: string | null;
  onImageEncoded: (encodedImageUrl: string) => void;
}

const ImageGen: React.FC<ImageGenProps> = ({ text, textGemma, onImageEncoded }) => {
  const form = useForm<FormData>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      imageFile: undefined,
    },
  });

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<{ encodedImageUrl: string } | null>(null);

  const onSubmit = async (data: FormData) => {
    setIsLoading(true);
    try {
      if (!data.imageFile) {
        throw new Error('Please upload an image.');
      }

      const MAX_FILE_SIZE = 5 * 1024 * 1024;
      if (data.imageFile.size > MAX_FILE_SIZE) {
        throw new Error(ERROR_MESSAGES.FILE_TOO_LARGE);
      }

      const formData = new FormData();
      formData.append('file', data.imageFile);
      formData.append('text', text || textGemma || '');

      const res = await axios.post('/api/encode', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        responseType: 'blob',
        timeout: 30000,
      });

      const encodedImageUrl = URL.createObjectURL(new Blob([res.data], { type: 'image/png' }));
      setPreviewData({ encodedImageUrl });
      setUploadedImageUrl(null);
      onImageEncoded(encodedImageUrl);
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      console.error('Error encoding image:', { error, message: errorMessage });
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const onFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      toast.error(ERROR_MESSAGES.INVALID_FILE_TYPE);
      e.target.value = '';
      return;
    }

    const MAX_FILE_SIZE = 5 * 1024 * 1024;
    if (file.size > MAX_FILE_SIZE) {
      toast.error(ERROR_MESSAGES.FILE_TOO_LARGE);
      e.target.value = '';
      return;
    }

    form.setValue('imageFile', file);
    setUploadedImageUrl(URL.createObjectURL(file));
    setPreviewData(null);
  }, [form]);

  const handleCopyToClipboard = () => {
    if (previewData?.encodedImageUrl) {
      navigator.clipboard.writeText(previewData.encodedImageUrl);
      toast.success('Link copied to clipboard!');
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="max-w-4xl mx-auto space-y-9 w-full">
        <div>
          <FormLabel>Generated Text</FormLabel>
          <FormControl>
            <textarea
              value={text || textGemma || ''}
              readOnly
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            />
          </FormControl>
        </div>

        <FormField
          control={form.control}
          name="imageFile"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Upload Image</FormLabel>
              <FormControl>
                <Input type="file" accept="image/*" onChange={onFileChange} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {uploadedImageUrl && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-2">Uploaded Image</h3>
            <div className="relative w-full h-64 overflow-hidden rounded-md">
              <Image src={uploadedImageUrl} alt="Uploaded Image" layout="fill" objectFit="contain" className="rounded-md" />
            </div>
          </div>
        )}

        {previewData && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold mb-4">Preview</h2>
            <div className="relative w-full max-w-md mx-auto h-64 overflow-hidden rounded-md">
              <Image src={previewData.encodedImageUrl} alt="Encoded Image Preview" layout="fill" objectFit="contain" className="rounded-md" />
            </div>

            <div className="mt-6 flex justify-center space-x-4">
              <TwitterShareButton
                url={previewData.encodedImageUrl}
                title={`Check out this post: ${text || textGemma}`}
                hashtags={['encodedImage', 'mycreation']}
              >
                <Button variant="outline" size="sm">
                  <TwitterIcon size={16} className="mr-2" /> Share on Twitter
                </Button>
              </TwitterShareButton>

              <Button variant="outline" size="sm" onClick={handleCopyToClipboard}>
                Copy Link for Instagram
              </Button>
            </div>
          </div>
        )}

        <Button type="submit" className="w-full" disabled={isLoading || !uploadedImageUrl}>
          {isLoading ? 'Processing...' : 'Generate Preview and Continue'}
        </Button>
      </form>
    </Form>
  );
};

export default ImageGen;