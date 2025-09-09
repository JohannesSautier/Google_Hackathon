import { GoogleGenerativeAI } from '@google/generative-ai';
import { NextRequest, NextResponse } from 'next/server';

// Initialize Gemini AI
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');

export async function POST(request: NextRequest) {
  try {
    const { message, context } = await request.json();

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    // Get the generative model
    const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });

    // Create a context-aware prompt for migration assistance
    const systemPrompt = `You are an AI assistant specialized in helping people with immigration and migration processes. You provide accurate, helpful, and up-to-date information about visa requirements, document preparation, timeline planning, and general migration guidance.

Context about the user's migration journey: ${context ? JSON.stringify(context) : 'No specific context provided'}

Please provide helpful, accurate, and actionable advice. If you're unsure about specific legal requirements or recent policy changes, recommend consulting official government sources or immigration professionals.

User's question: ${message}`;

    // Generate content
    const result = await model.generateContent(systemPrompt);
    const response = await result.response;
    const text = response.text();

    return NextResponse.json({ 
      message: text,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Error in chat API:', error);
    return NextResponse.json(
      { error: 'Failed to process chat message' }, 
      { status: 500 }
    );
  }
}
