import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const data = await request.json();
    console.log('Received data in /api/decompose:', data);

    if (data.resImage) {
      // **Replace this with your actual image decomposition/processing logic**
      console.log('Processing resImage:', data.resImage);
      const encodedImage = `processed_${data.resImage}`; // Placeholder
      return NextResponse.json({ encodedImage });
    } else if (data.resText) {
      // **Replace this with your actual text decomposition/processing logic**
      console.log('Processing resText:', data.resText);
      const decomposed = { text: data.resText, /* other decomposed data */ }; // Placeholder
      return NextResponse.json({ decomposed });
    } else {
      console.log('Invalid data received:', data);
      return new NextResponse('Invalid request data', { status: 400 });
    }
  } catch (error: any) {
    console.error('Error in /api/decompose:', error);
    return new NextResponse(`Internal Server Error: ${error.message}`, { status: 500 });
  }
}