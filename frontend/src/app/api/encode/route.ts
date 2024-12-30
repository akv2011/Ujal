// app/api/encode/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { createCanvas, loadImage } from 'canvas';
import sharp from 'sharp';

export const config = {
  api: {
    bodyParser: false,
  },
};

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;
    const text = formData.get('text') as string;

    if (!file || !text) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // Convert File to Buffer
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);

    // Get image dimensions using sharp
    const metadata = await sharp(buffer).metadata();
    const width = metadata.width || 800;
    const height = metadata.height || 600;

    // Create canvas with image dimensions
    const canvas = createCanvas(width, height);
    const ctx = canvas.getContext('2d');

    // Load and draw the image
    const image = await loadImage(buffer);
    ctx.drawImage(image, 0, 0, width, height);

    // Configure text style
    ctx.font = '20px Arial';
    ctx.fillStyle = 'white';
    ctx.strokeStyle = 'black';
    ctx.lineWidth = 2;

    // Position text at bottom-right with padding
    const padding = 20;
    const metrics = ctx.measureText(text);
    const x = width - metrics.width - padding;
    const y = height - padding;

    // Draw text with stroke for visibility
    ctx.strokeText(text, x, y);
    ctx.fillText(text, x, y);

    // Convert canvas to buffer
    const outputBuffer = canvas.toBuffer('image/png');

    // Return the processed image
    return new NextResponse(outputBuffer, {
      headers: {
        'Content-Type': 'image/png',
        'Content-Disposition': 'inline; filename="encoded-image.png"'
      },
    });

  } catch (error) {
    console.error('Error processing image:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Error processing image' },
      { status: 500 }
    );
  }
}