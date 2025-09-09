// src/app/api/parse-query/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { GoogleGenAI } from '@google/genai';

const genAI = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || '' });

export async function POST(req: NextRequest) {
  try {
    const { query } = await req.json();

    if (!query) {
      return NextResponse.json({ error: 'Query is required' }, { status: 400 });
    }

    const prompt = `
    Parse the following user query to extract migration context.
    The user is describing their immigration plan.
    Return a JSON object (just the object, without any additional text or punctuations) with the following keys: 
    - "originCountry": two-letter ISO 3166-1 alpha-2 country code
    - "destinationCountry": two-letter ISO 3166-1 alpha-2 country code
    - "purpose": one of: "work", "study", "family", "business"
    - "timeline": one of: "ASAP", "1-3 months", "3-6 months", "6-12 months"

    If a value is not found, it should be an empty string.

    Query: "${query}"
    `;

    const result = await genAI.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: [{ role: 'user', parts: [{ text: prompt }] }],
    });

    console.log('Raw Result:', result.text);

    let parsedResult;

    try {
        parsedResult = JSON.parse(result.text!);
    } catch (e) {
        const match = result.text!.match(/```(?:json)?\s*([\s\S]*?)```/i);
        if (match && match[1]) {
            try {
                parsedResult = JSON.parse(match[1]);
            } catch {
                parsedResult = JSON.parse(match[1]);
            }
        } else {
            parsedResult = {};
        }
    }

    console.log('Parsed Result:', parsedResult);

    return NextResponse.json(parsedResult);
  } catch (error) {
    console.error('Error parsing query with Gemini:', error);
    return NextResponse.json({ error: 'Failed to parse query' }, { status: 500 });
  }
}
