import { exec } from 'child_process';
import cors from 'cors';
import dotenv from 'dotenv';
import voice from 'elevenlabs-node';
import express from 'express';
import { promises as fs } from 'fs';
import axios from 'axios';

dotenv.config();

const elevenLabsApiKey = process.env.ELEVEN_LABS_API_KEY;
const voiceID = 'cgSgspJ2msm6clMCkdW9'; // Replace with your desired voice ID
const HUGGINGFACE_API_TOKEN = process.env.HUGGINGFACE_API_TOKEN;
const MODEL = "mistralai/Mistral-7B-Instruct-v0.2"; // Example model

const app = express();
app.use(express.json());

// **Enable CORS for development (replace with specific origin in production)**
app.use(cors()); 

const port = 4000;

// Serve the 'audios' directory statically
app.use('/audios', express.static('audios'));

app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.get('/voices', async (req, res) => {
    try {
        const voices = await voice.getVoices(elevenLabsApiKey);
        res.send(voices);
    } catch (error) {
        console.error('Error fetching voices:', error);
        res.status(500).send({ error: 'Error fetching voices from ElevenLabs.' });
    }
});

const execCommand = (command) => {
    return new Promise((resolve, reject) => {
        exec(command, (error, stdout, stderr) => {
            if (error) {
                console.error('exec error:', error);
                reject(error);
            } else {
                resolve(stdout);
            }
        });
    });
};

const lipSyncMessage = async (messageIndex) => {
    const time = new Date().getTime();
    console.log(`Starting conversion for message ${messageIndex}`);
    try {
        await execCommand(
            `ffmpeg -y -i audios/message_${messageIndex}.mp3 audios/message_${messageIndex}.wav`
        );
        console.log(`Conversion done in ${new Date().getTime() - time}ms`);
        await execCommand(
          `/home/harisudhan/pondy_hack/Ujal/ai-avatar/Rhubarb-Lip-Sync-1.13.0-Linux/rhubarb -f json -o audios/message_${messageIndex}.json audios/message_${messageIndex}.wav -r phonetic`
        );
        console.log(`Lip sync done in ${new Date().getTime() - time}ms`);
    } catch (error) {
        console.error('Error during lip-sync:', error);
        throw error;
    }
};

app.post('/chat', async (req, res) => {
    console.log("--- /chat request received ---");
    console.log("Request body:", req.body);
    const userMessage = req.body.message;
    console.log("User message:", userMessage);

    if (!userMessage) {
        return res.status(400).send({ error: 'User message is required.' });
    }

    if (!elevenLabsApiKey) {
        return res.status(400).send({ error: 'ElevenLabs API key is missing.' });
    }

    if (!HUGGINGFACE_API_TOKEN) {
        return res.status(400).send({ error: 'Hugging Face API key is missing.' });
    }

    try {
        console.log("Sending request to Hugging Face Inference API...");
        const hfResponse = await axios.post(
            `https://api-inference.huggingface.co/models/${MODEL}`,
            {
                inputs: userMessage,
                parameters: {
                    max_new_tokens: 250,
                    temperature: 0.7,
                    return_full_text: false,
                },
            },
            {
                headers: {
                    Authorization: `Bearer ${HUGGINGFACE_API_TOKEN}`,
                },
            }
        );
        console.log("Response from Hugging Face:", JSON.stringify(hfResponse.data));

        const generatedText = hfResponse.data[0].generated_text;

        // Format the generated text into the expected structure
        const responseMessages = {
            messages: [{
                text: generatedText,
                facialExpression: 'smile', // Default or based on text analysis
                animation: 'Talking_1' // Default or based on text analysis
            }]
        };

        console.log('Formatted response:', responseMessages);

        for (let i = 0; i < responseMessages.messages.length; i++) {
            const message = responseMessages.messages[i];
            const fileName = `audios/message_${i}.mp3`;
            const textInput = message.text;

            console.log(`\n--- Processing message ${i} ---`);
            console.log('Sending request to ElevenLabs:', textInput);

            await voice.textToSpeech(elevenLabsApiKey, voiceID, fileName, textInput);
            console.log('Audio file generated:', fileName);

            await lipSyncMessage(i);
            console.log('Lip sync generated for:', fileName);

            message.audio = await audioFileToBase64(fileName);
            message.lipsync = await readJsonTranscript(`audios/message_${i}.json`);
        }

        console.log('Sending response to frontend:', responseMessages);
        res.send(responseMessages);

    } catch (error) {
        console.error('Error during conversation:', error);
        if (error.response) {
            console.error('Error Response Data:', error.response.data);
            console.error('Error Response Status:', error.response.status);
            console.error('Error Response Headers:', error.response.headers);
        } else if (error.request) {
            console.error('Error Request:', error.request);
        } else {
            console.error('Error Message:', error.message);
        }
        return res.status(500).send({ error: 'Error processing your request.' });
    }
});

// Utility function to read and parse JSON transcripts
const readJsonTranscript = async (file) => {
    try {
        const data = await fs.readFile(file, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        console.error('Error reading transcript:', error);
        throw error;
    }
};

// Utility function to convert audio files to base64
const audioFileToBase64 = async (file) => {
    try {
        const data = await fs.readFile(file);
        return data.toString('base64');
    } catch (error) {
        console.error('Error converting audio to base64:', error);
        throw error;
    }
};

// Start the server
app.listen(port, () => {
    console.log(`Virtual Girlfriend listening on port ${port}`);
});