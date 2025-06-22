"use client"

import React, { useState, useEffect, useCallback, Suspense, useRef } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Copy, Check, Globe, FileText, Zap, Loader2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

function DocsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [documentation, setDocumentation] = useState<string>('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string>('')
  const [copiedToClipboard, setCopiedToClipboard] = useState(false)
  const [particles, setParticles] = useState<Array<{
    left: string;
    top: string;
    animationDelay: string;
    animationDuration: string;
  }>>([])
  
  // Refs for throttling updates
  const streamingContentRef = useRef<string>('')
  const updateTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  // Get parameters from URL
  const request = searchParams.get('request')
  const endpoint = searchParams.get('endpoint')

  // Generate particles for background
  useEffect(() => {
    const newParticles = [...Array(15)].map(() => ({
      left: `${Math.random() * 100}%`,
      top: `${Math.random() * 100}%`,
      animationDelay: `${Math.random() * 5}s`,
      animationDuration: `${3 + Math.random() * 4}s`,
    }))
    setParticles(newParticles)
  }, [])

  // Throttled update function to reduce re-renders
  const throttledUpdate = useCallback((content: string) => {
    streamingContentRef.current = content
    
    // Clear existing timeout
    if (updateTimeoutRef.current) {
      clearTimeout(updateTimeoutRef.current)
    }
    
    // Throttle updates to every 100ms for smoother streaming
    updateTimeoutRef.current = setTimeout(() => {
      setDocumentation(streamingContentRef.current)
    }, 100)
  }, [])

  const generateDocumentation = useCallback(async () => {
    try {
      setIsStreaming(true)
      setError('')
      setDocumentation('')
      streamingContentRef.current = ''

      // Close any existing connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }

      // Connect to our Next.js API route for streaming
      const apiUrl = `/api/generate-docs?${new URLSearchParams({
        request: request || '',
        endpoint: endpoint || 'generated-endpoint'
      })}`;

      console.log('🔗 Connecting to frontend API stream:', apiUrl)

      const eventSource = new EventSource(apiUrl);
      eventSourceRef.current = eventSource

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 EventSource message received:', data.type)
          
          if (data.type === 'connecting') {
            console.log('🔗 Connecting to backend...');
          } else if (data.type === 'start') {
            console.log('📋 Starting documentation generation...');
          } else if (data.type === 'chunk') {
            // Use throttled update for smoother streaming
            throttledUpdate(data.partial_content);
          } else if (data.type === 'complete') {
            console.log('✅ Documentation generation complete');
            // Final update with complete content
            setDocumentation(data.documentation);
            setIsStreaming(false);
            eventSource.close();
            eventSourceRef.current = null;
          } else if (data.type === 'error') {
            console.error('❌ Documentation generation error:', data.error);
            
            let errorMessage = data.error || 'Failed to generate documentation';
            if (data.troubleshooting) {
              errorMessage += '\n\nTroubleshooting steps:\n';
              Object.entries(data.troubleshooting).forEach(([key, value]) => {
                errorMessage += `• ${key}: ${value}\n`;
              });
            }
            
            setError(errorMessage);
            setIsStreaming(false);
            eventSource.close();
            eventSourceRef.current = null;
          }
        } catch (err) {
          console.error('Error parsing SSE data:', err, 'Raw event:', event.data);
          setError('Failed to parse server response. Check console for details.');
          setIsStreaming(false);
          eventSource.close();
          eventSourceRef.current = null;
        }
      };

      eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        console.error('EventSource readyState:', eventSource.readyState);
        eventSource.close();
        eventSourceRef.current = null;
        
        setError('Connection to documentation stream failed. Please check that:\n• Flask backend is running on http://localhost:5000\n• The /generate-docs endpoint is available\n• No firewall is blocking the connection');
        setIsStreaming(false);
      };

      eventSource.onopen = () => {
        console.log('✅ EventSource connection opened');
      };

    } catch (err) {
      console.error('Error setting up stream:', err);
      setError('Failed to set up documentation stream. Please try again.')
      setIsStreaming(false)
    }
  }, [request, endpoint, throttledUpdate])

  // Generate documentation on component mount
  useEffect(() => {
    // Add slide-in animation when component mounts
    document.body.classList.remove('slide-out-left');
    document.body.classList.add('slide-in-right');
    
    if (request) {
      generateDocumentation()
    } else {
      setError('No request parameters found. Please navigate from the main page.')
      setIsStreaming(false)
    }
    
    // Cleanup animation class and connections on unmount
    return () => {
      document.body.classList.remove('slide-in-right');
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }
    }
  }, [request, endpoint, generateDocumentation])

  const copyToClipboard = () => {
    navigator.clipboard.writeText(documentation)
    setCopiedToClipboard(true)
    setTimeout(() => setCopiedToClipboard(false), 2000)
  }

  const goBack = () => {
    // Clean up connections before navigating
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    router.push('/')
  }

  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative font-sans">
      {/* Holographic Background */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Animated holographic mesh */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-blue-600/20 via-transparent to-purple-600/20 animate-pulse"></div>
          <div
            className="absolute top-0 right-0 w-full h-full bg-gradient-to-bl from-cyan-500/15 via-transparent to-blue-500/15 animate-pulse"
            style={{ animationDelay: "1s" }}
          ></div>
        </div>

        {/* Floating holographic particles */}
        <div className="absolute inset-0">
          {particles.map((particle, i) => (
            <div
              key={i}
              className="absolute w-1 h-1 bg-blue-400/40 rounded-full animate-float"
              style={{
                left: particle.left,
                top: particle.top,
                animationDelay: particle.animationDelay,
                animationDuration: particle.animationDuration,
              }}
            ></div>
          ))}
        </div>

        {/* Holographic grid */}
        <div className="absolute inset-0">
          <div className="w-full h-full bg-[linear-gradient(rgba(0,191,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(0,191,255,0.05)_1px,transparent_1px)] bg-[size:100px_100px] animate-pulse"></div>
        </div>

        {/* Large holographic shapes */}
        <div className="absolute -top-40 -left-40 w-96 h-96 border border-cyan-400/10 rotate-45 transform animate-spin-slow"></div>
        <div className="absolute -bottom-40 -right-40 w-80 h-80 border border-blue-400/10 rotate-12 transform animate-spin-reverse"></div>
      </div>

      {/* Main Content */}
      <main className="relative z-10 px-6 py-12">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-12">
            <Button
              onClick={goBack}
              className="mb-8 bg-black/40 hover:bg-cyan-950/40 border border-cyan-400/30 hover:border-cyan-400/50 text-cyan-300 hover:text-cyan-200 px-6 py-3 rounded-xl transition-all duration-300 backdrop-blur-xl"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Generator
            </Button>

            <div className="inline-flex items-center px-6 py-3 rounded-full bg-cyan-950/30 border border-cyan-400/30 mb-8 backdrop-blur-xl">
              <FileText className="w-4 h-4 text-cyan-400 mr-3" />
              <span className="text-sm text-cyan-300 font-medium tracking-wide">API DOCUMENTATION</span>
            </div>

            <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight tracking-tighter">
              <span className="block mb-2">Your</span>
              <span className="block bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent animate-gradient">
                Custom API
              </span>
            </h1>

            {request && (
              <p className="text-xl text-gray-300 mb-8 max-w-3xl leading-relaxed font-light">
                Generated for: <span className="text-cyan-400 font-medium">&ldquo;{request}&rdquo;</span>
              </p>
            )}

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-4 mb-8">
              <Button
                onClick={copyToClipboard}
                disabled={!documentation || isStreaming}
                className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-black border-0 px-6 py-3 text-sm font-semibold rounded-xl transition-all duration-300 disabled:opacity-50 shadow-[0_0_20px_rgba(0,191,255,0.3)] hover:shadow-[0_0_30px_rgba(0,191,255,0.5)]"
              >
                {copiedToClipboard ? (
                  <>
                    <Check className="w-4 h-4 mr-2" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4 mr-2" />
                    Copy Documentation
                  </>
                )}
              </Button>

              <Button
                onClick={generateDocumentation}
                disabled={isStreaming}
                className="bg-black/40 hover:bg-purple-950/40 border border-purple-400/30 hover:border-purple-400/50 text-purple-300 hover:text-purple-200 px-6 py-3 rounded-xl transition-all duration-300 backdrop-blur-xl"
              >
                <Zap className="w-4 h-4 mr-2" />
                Regenerate
              </Button>
            </div>
          </div>

          {/* Documentation Content */}
          <div className="relative">
            {/* Holographic glow effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-400/10 via-blue-400/10 to-purple-400/10 rounded-3xl blur-2xl animate-pulse"></div>

            <div className="relative bg-black/60 backdrop-blur-2xl border border-cyan-400/30 rounded-3xl p-8 md:p-12">
              
              {/* Subtle corner streaming indicator */}
              {isStreaming && (
                <div className="absolute top-6 right-6 flex items-center space-x-2 bg-black/70 backdrop-blur-md rounded-full px-4 py-2 border border-cyan-400/20">
                  <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
                  <span className="text-xs text-cyan-300 font-medium">Streaming...</span>
                  <div className="flex space-x-1">
                    <div className="w-1 h-1 bg-cyan-400 rounded-full animate-pulse"></div>
                    <div className="w-1 h-1 bg-cyan-400 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                    <div className="w-1 h-1 bg-cyan-400 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                  </div>
                </div>
              )}

              {/* Content display logic */}
              {!documentation && !isStreaming && !error ? (
                <div className="flex flex-col items-center justify-center py-20">
                  <div className="w-12 h-12 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin mb-6"></div>
                  <div className="text-xl text-cyan-300 mb-2">Initializing Documentation...</div>
                  <div className="text-gray-400 text-center max-w-md">
                    Preparing to generate comprehensive API documentation
                  </div>
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center py-20">
                  <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mb-6">
                    <Globe className="w-8 h-8 text-red-400" />
                  </div>
                  <div className="text-xl text-red-400 mb-2">Documentation Generation Failed</div>
                  <div className="text-gray-400 text-center max-w-md mb-6 whitespace-pre-line">{error}</div>
                  <Button
                    onClick={generateDocumentation}
                    className="bg-red-500/20 hover:bg-red-500/30 border border-red-400/30 hover:border-red-400/50 text-red-300 hover:text-red-200 px-6 py-3 rounded-xl transition-all duration-300"
                  >
                    Try Again
                  </Button>
                </div>
              ) : (
                <div className="docs-content prose prose-invert max-w-none">
                  <ReactMarkdown>
                    {documentation}
                  </ReactMarkdown>
                  
                  {/* Show hint when documentation is empty but streaming */}
                  {!documentation && isStreaming && (
                    <div className="flex items-center justify-center py-8">
                      <div className="text-center">
                        <div className="text-cyan-300 mb-2">📝 Documentation generating...</div>
                        <div className="text-gray-400 text-sm">Content will appear as it streams in</div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="mt-16 text-center">
            <div className="text-cyan-400/60 font-light text-lg tracking-wider">
              DOCUMENTATION GENERATED BY CLAUDE • READY TO USE
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

function DocsPageFallback() {
  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin mb-6 mx-auto"></div>
        <div className="text-xl text-cyan-300">Loading documentation page...</div>
      </div>
    </div>
  )
}

export default function DocsPage() {
  return (
    <Suspense fallback={<DocsPageFallback />}>
      <DocsContent />
    </Suspense>
  )
} 