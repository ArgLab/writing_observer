/*
  This is an API for calling LLMs.
*/

import { NextResponse, NextRequest } from 'next/server';
import * as openai from '../../lib/azureInterface';
import * as stub from '../../lib/stubInterface';

const listChatCompletions = openai.listChatCompletions;

const default_messages =     [
  { role: "system", content: "I am your writing coach. How can I help you?" },
  { role: "user", content: "Hi, how are you?"},
];

async function processPrompt(prompt) {
  return await listChatCompletions(
    [
      { role: "system", content: "I am your writing coach. How can I help you?" },
      { role: "user", content: prompt },
    ],
    {}
  );
}

export async function GET(request) {
  console.log('GET request called');
  const prompt = request.nextUrl.searchParams.get('prompt') || "How are you?";
  const jsonResponse = await processPrompt(prompt);
  return NextResponse.json({'response': jsonResponse});
}

// Handles POST requests
export async function POST(request) {
  console.log('POST request called');
  const req = await request.json();

  const prompt = req?.prompt || "How are you?";
  const jsonResponse = await processPrompt(prompt);
  return NextResponse.json({'response': jsonResponse});
}

/*export async function GET(request) {
  const messages = request.nextUrl.searchParams.get('messages');
  const temperature = request.nextUrl.searchParams.get('temperature');
  console.log(messages, temperature);
  const jsonResponse = await listChatCompletions(messages, {temperature});
  return NextResponse.json(jsonResponse);
}

// Handles POST requests
export async function POST(request) {
  const req = await request.json();
  const messages = req?.messages || default_messages;
  const temperature = req?.temperature || default_temperature;
  console.log(messages, temperature);

  const jsonResponse = await listChatCompletions(
    messages,
    {temperature}
  );
  return NextResponse.json(jsonResponse);
}
*/
