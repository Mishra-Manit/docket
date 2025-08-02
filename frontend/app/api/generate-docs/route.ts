import { NextRequest } from 'next/server'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const userRequest = searchParams.get('request')
  const endpoint = searchParams.get('endpoint')

  console.log('🔗 Frontend API route called with:', { userRequest, endpoint })

  if (!userRequest) {
    return new Response('Missing request parameter', { status: 400 })
  }

  // Create a readable stream for Server-Sent Events
  const stream = new ReadableStream({
    start(controller) {
      const encoder = new TextEncoder()

      // Helper to safely enqueue without throwing if the controller has been closed
      const safeEnqueue = (data: string) => {
        try {
          controller.enqueue(encoder.encode(data))
        } catch (_) {
          /* controller might already be closed – ignore */
        }
      }

      // AbortController so we can cancel the backend fetch when we hit the timeout
      const abortCtrl = new AbortController()

      // Connect to the backend EventSource
      const backendUrl = `http://localhost:5000/generate-docs?${new URLSearchParams({
        request: userRequest,
        endpoint: endpoint || 'generated-endpoint'
      })}`

      console.log('🔗 Connecting to backend stream:', backendUrl)

      // Send initial connection status
      safeEnqueue(`data: ${JSON.stringify({
        type: 'connecting',
        message: 'Connecting to backend...'
      })}\n\n`)

      // Use fetch to handle the backend EventSource stream with timeout
      const timeoutId = setTimeout(() => {
        console.error('❌ Backend connection timeout after 60 seconds')
        safeEnqueue(`data: ${JSON.stringify({
          type: 'error',
          error: 'Backend connection timeout. Make sure Flask server is running on http://localhost:5000'
        })}\n\n`)
        abortCtrl.abort() // Cancel the fetch; the catch handler will close the stream
      }, 60000) // 60-second timeout

      fetch(backendUrl, {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache'
        },
        signal: abortCtrl.signal
      })
        .then(async (response) => {
          clearTimeout(timeoutId)
          
          console.log('✅ Backend response received:', {
            status: response.status,
            statusText: response.statusText
          })

          if (!response.ok) {
            throw new Error(`Backend responded with ${response.status}: ${response.statusText}`)
          }

          const reader = response.body?.getReader()
          if (!reader) {
            throw new Error('Unable to read response stream')
          }

          const decoder = new TextDecoder()
          let buffer = ''
          
          try {
            while (true) {
              const { done, value } = await reader.read()
              
              if (done) {
                console.log('✅ Stream completed')
                // Process any remaining buffer content
                if (buffer.trim()) {
                  safeEnqueue(buffer)
                }
                break
              }

              // Decode the chunk and add to buffer
              const chunk = decoder.decode(value, { stream: true })
              buffer += chunk

              // Process complete SSE events in buffer
              let eventStart = 0
              let eventEnd = buffer.indexOf('\n\n')
              
              while (eventEnd !== -1) {
                const eventData = buffer.slice(eventStart, eventEnd + 2)
                // Forward the complete event
                safeEnqueue(eventData)
                
                // Move to next event
                eventStart = eventEnd + 2
                eventEnd = buffer.indexOf('\n\n', eventStart)
              }
              
              // Keep remaining incomplete event in buffer
              buffer = buffer.slice(eventStart)
            }
          } catch (error) {
            console.error('❌ Stream error:', error)
            const errorMessage = error instanceof Error ? error.message : 'Unknown stream error'
            safeEnqueue(`data: ${JSON.stringify({
              type: 'error',
              error: errorMessage
            })}\n\n`)
          } finally {
            reader.releaseLock()
            controller.close()
          }
        })
        .catch(error => {
          clearTimeout(timeoutId)
          console.error('❌ Backend connection error:', error)
          
          let errorMessage = 'Unknown connection error'
          if (error instanceof Error) {
            errorMessage = error.message
            if (error.message.includes('fetch')) {
              errorMessage = 'Cannot connect to Flask backend. Please ensure the server is running on http://localhost:5000'
            }
          }
          
          safeEnqueue(`data: ${JSON.stringify({
            type: 'error',
            error: errorMessage,
            troubleshooting: {
              'Check Flask server': 'Make sure Flask is running: cd backend && python app.py server',
              'Check port': 'Verify Flask is on port 5000',
              'Check CORS': 'Flask should allow CORS from frontend'
            }
          })}\n\n`)
          controller.close()
        })
    }
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  })
}

// POST endpoint to trigger documentation generation (called from landing page)
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { request: userRequest, endpoint } = body

    console.log('📋 POST /api/generate-docs called with:', { userRequest, endpoint })

    if (!userRequest) {
      return Response.json({ error: 'Missing request parameter' }, { status: 400 })
    }

    // Test backend connectivity first
    try {
      const healthResponse = await fetch('http://localhost:5000/health', {
        method: 'GET',
        timeout: 5000
      } as any)
      
      if (!healthResponse.ok) {
        throw new Error(`Backend health check failed: ${healthResponse.status}`)
      }
      
      console.log('✅ Backend health check passed')
    } catch (healthError) {
      console.error('❌ Backend health check failed:', healthError)
      return Response.json({ 
        error: 'Cannot connect to Flask backend',
        details: 'Make sure Flask server is running on http://localhost:5000',
        healthCheck: false
      }, { status: 503 })
    }

    // Generate a unique session ID for this documentation generation
    const sessionId = `doc-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

    console.log('🚀 Starting documentation generation with session:', sessionId)

    // Return immediately with session info - the actual generation will be streamed via GET
    return Response.json({ 
      success: true, 
      sessionId,
      message: 'Documentation generation initiated',
      streamUrl: `/api/generate-docs?${new URLSearchParams({
        request: userRequest,
        endpoint: endpoint || 'generated-endpoint',
        sessionId
      })}`,
      backendStatus: 'connected'
    })

  } catch (error) {
    console.error('❌ POST /api/generate-docs error:', error)
    return Response.json({ 
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
} 