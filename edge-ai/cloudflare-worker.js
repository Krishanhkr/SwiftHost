/**
 * Cloudflare Worker for real-time image moderation using AI
 * Processes images at the edge before they reach the origin server
 */
export default {
  async fetch(request, env) {
    // Only process POST requests to /upload endpoint
    if (request.method === 'POST' && request.url.includes('/upload')) {
      try {
        // Parse the multipart form data
        const formData = await request.formData();
        const file = formData.get('file');
        
        // Check if file exists and is an image
        if (!file || !file.type.startsWith('image/')) {
          return new Response('File must be an image', { status: 400 });
        }
        
        // Convert file to array buffer for AI processing
        const image = await file.arrayBuffer();
        
        // Process image with Cloudflare's AI model for NSFW content detection
        const result = await env.AI.run(
          '@cf/google/vit-base-patch16-224-in21k',
          { image }
        );
        
        // Check NSFW score threshold
        if (result.nsfw_score > 0.85) {
          return new Response(
            JSON.stringify({
              success: false,
              message: 'Content violation detected',
              details: 'The image contains inappropriate content that violates our terms of service.'
            }),
            { 
              status: 451, 
              headers: { 'Content-Type': 'application/json' }
            }
          );
        }
        
        // Check if image contains text that might violate policies
        const textResult = await env.AI.run(
          '@cf/microsoft/ocr-optical-character-recognition',
          { image }
        );
        
        // List of potentially problematic terms to check in image text
        const problematicTerms = ['hack', 'password', 'credit card', 'ssn', 'social security'];
        const detectedText = textResult.text.toLowerCase();
        
        // Check for problematic terms in the detected text
        const containsProblematicTerms = problematicTerms.some(term => 
          detectedText.includes(term.toLowerCase())
        );
        
        if (containsProblematicTerms) {
          return new Response(
            JSON.stringify({
              success: false,
              message: 'Content violation detected',
              details: 'The image contains sensitive information that violates our terms of service.'
            }),
            { 
              status: 451, 
              headers: { 'Content-Type': 'application/json' }
            }
          );
        }
        
        // Add metadata to the form indicating the image passed moderation
        formData.append('moderation_passed', 'true');
        formData.append('moderation_timestamp', new Date().toISOString());
        
        // Create a new request to forward to the origin server
        const newRequest = new Request(request.url, {
          method: request.method,
          headers: request.headers,
          body: formData
        });
        
        // Pass the request to the origin server
        return fetch(newRequest);
      } catch (error) {
        console.error('Edge AI processing error:', error);
        
        return new Response(
          JSON.stringify({
            success: false,
            message: 'Error processing image',
            details: 'An error occurred while processing your image'
          }),
          { 
            status: 500, 
            headers: { 'Content-Type': 'application/json' }
          }
        );
      }
    }
    
    // Additional endpoint for AI-based text moderation
    if (request.method === 'POST' && request.url.includes('/moderate-text')) {
      try {
        const { text } = await request.json();
        
        if (!text) {
          return new Response('Text content is required', { status: 400 });
        }
        
        // Process text with Cloudflare's AI model for content moderation
        const result = await env.AI.run(
          '@cf/huggingface/microsoft/phi-2',
          { 
            prompt: `Analyze the following text and determine if it contains harmful, offensive, or inappropriate content. 
                    Respond with a JSON object with a 'is_inappropriate' boolean and a 'reason' string.
                    Text to analyze: "${text}"` 
          }
        );
        
        // Parse the AI response
        const analysis = JSON.parse(result.response);
        
        if (analysis.is_inappropriate) {
          return new Response(
            JSON.stringify({
              success: false,
              message: 'Content violation detected',
              details: analysis.reason
            }),
            { 
              status: 451, 
              headers: { 'Content-Type': 'application/json' }
            }
          );
        }
        
        // Content is appropriate, forward to origin
        return fetch(request);
      } catch (error) {
        console.error('Edge AI text processing error:', error);
        
        return new Response(
          JSON.stringify({
            success: false,
            message: 'Error processing text',
            details: 'An error occurred while moderating your text content'
          }),
          { 
            status: 500, 
            headers: { 'Content-Type': 'application/json' }
          }
        );
      }
    }
    
    // For all other requests, pass through to origin
    return fetch(request);
  }
}; 