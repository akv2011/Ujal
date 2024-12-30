import OpenAI from 'openai';
import dotenv from 'dotenv';

dotenv.config(); // Load environment variables from .env

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

async function testOpenAI() {
  try {
    const messages = [
      {
        role: 'system',
        content: 'You are a helpful assistant.',
      },
      {
        role: 'user',
        content: 'Hello, how are you?',
      },
    ];

    console.log('Sending request to OpenAI...');
    const response = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo', // Or your preferred model
      messages: messages,
      response_format: { type: 'json_object' },
    });

    console.log('Response from OpenAI:');
    console.log(JSON.stringify(response, null, 2));

    // Extract and log the generated text
    const generatedText = response.choices[0].message.content;
    console.log('Generated Text:', generatedText);

    // Add assertions here to validate the response
    if (typeof generatedText === 'string' && generatedText.length > 0) {
      console.log('Test Passed: Generated text is a non-empty string.');
    } else {
      console.error('Test Failed: Generated text is empty or not a string.');
    }
  } catch (error) {
    console.error('Error calling OpenAI API:', error);
  }
}

testOpenAI();