"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { ArrowRight, Globe, CheckCircle, AlertCircle } from "lucide-react"

export default function APIGeneratorLanding() {
  const router = useRouter()
  const [inputText, setInputText] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [responseMessage, setResponseMessage] = useState<{
    type: 'success' | 'error' | 'warning';
    message: string;
  } | null>(null)
  const [particles, setParticles] = useState<Array<{
    left: string;
    top: string;
    animationDelay: string;
    animationDuration: string;
  }>>([])

  // Generate particles on client side only to avoid hydration mismatch
  useEffect(() => {
    const newParticles = [...Array(20)].map(() => ({
      left: `${Math.random() * 100}%`,
      top: `${Math.random() * 100}%`,
      animationDelay: `${Math.random() * 5}s`,
      animationDuration: `${3 + Math.random() * 4}s`,
    }))
    setParticles(newParticles)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputText.trim()) return

    setIsLoading(true)
    setResponseMessage(null)

    try {
      // First call: Start the navigation/endpoint creation
      const response = await fetch('http://localhost:5000/navigate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          website: inputText.trim()
        })
      });

      const data = await response.json();

      if (response.ok) {
        // Generate endpoint slug from input with special handling for Trader Joe's
        let endpointSlug;
        if (data.extracted_website === "traderjoes.com.special") {
          endpointSlug = "whatsnew";
        } else {
          endpointSlug = inputText.trim()
            .toLowerCase()
            .replace(/[^a-zA-Z0-9\s]/g, '')
            .replace(/\s+/g, '-')
            .replace(/^-+|-+$/g, '')
            .substring(0, 30) || 'generated-endpoint';
        }

        // Start documentation generation immediately
        const docResponse = await fetch('/api/generate-docs', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            request: inputText.trim(),
            endpoint: endpointSlug
          })
        });

        const docData = await docResponse.json();

        if (docResponse.ok) {
          // Show success message briefly
          let successMessage = `✅ ${data.message}. Documentation started...`;
          if (data.original_input && data.extracted_website && data.original_input !== data.extracted_website) {
            successMessage = `✅ I understood "${data.original_input}" as ${data.extracted_website}. ${data.message}. Documentation started...`;
          }
          
          setResponseMessage({
            type: 'success',
            message: successMessage
          });

          // Navigate immediately to docs page with session info
          setTimeout(() => {
            // Add slide-out animation class to current page
            document.body.classList.add('slide-out-left');
            
            setTimeout(() => {
              const searchParams = new URLSearchParams({
                request: inputText.trim(),
                endpoint: endpointSlug,
                sessionId: docData.sessionId
              });
              
              router.push(`/docs?${searchParams.toString()}`);
            }, 300); // Wait for animation to start before navigation
          }, 1500); // Reduced delay since docs generation has already started

        } else {
          setResponseMessage({
            type: 'warning',
            message: `✅ ${data.message}. ⚠️ Documentation generation may be delayed: ${docData.error}`
          });

          // Still navigate but without session ID
          setTimeout(() => {
            document.body.classList.add('slide-out-left');
            
            setTimeout(() => {
              const searchParams = new URLSearchParams({
                request: inputText.trim(),
                endpoint: endpointSlug
              });
              
              router.push(`/docs?${searchParams.toString()}`);
            }, 300);
          }, 2000);
        }

      } else {
        setResponseMessage({
          type: 'error',
          message: `❌ ${data.error || 'Failed to navigate to website'}${data.suggestion ? `\n\n💡 ${data.suggestion}` : ''}`
        });
      }

    } catch (error) {
      console.error('Error connecting to backend:', error);
      setResponseMessage({
        type: 'error',
        message: '❌ Failed to connect to backend. Make sure the Flask server is running on http://localhost:5000'
      });
    } finally {
      setIsLoading(false)
    }
  }

  const getQuickWebsite = (website: string) => {
    setInputText(website);
  }

  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative font-sans">
      {/* Holographic Background */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Animated holographic mesh */}
        <div className="absolute inset-0 opacity-30">
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
          <div className="w-full h-full bg-[linear-gradient(rgba(0,191,255,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(0,191,255,0.1)_1px,transparent_1px)] bg-[size:100px_100px] animate-pulse"></div>
        </div>

        {/* Large holographic shapes */}
        <div className="absolute -top-40 -left-40 w-96 h-96 border border-cyan-400/20 rotate-45 transform animate-spin-slow"></div>
        <div className="absolute -bottom-40 -right-40 w-80 h-80 border border-blue-400/20 rotate-12 transform animate-spin-reverse"></div>

        {/* Glowing orbs */}
        <div className="absolute top-1/4 left-1/3 w-72 h-72 bg-gradient-radial from-blue-400/20 via-cyan-400/10 to-transparent rounded-full blur-2xl animate-float"></div>
        <div
          className="absolute bottom-1/3 right-1/4 w-96 h-96 bg-gradient-radial from-purple-400/15 via-blue-400/10 to-transparent rounded-full blur-3xl animate-float"
          style={{ animationDelay: "2s" }}
        ></div>

        {/* Holographic lines */}
        <div className="absolute top-20 left-0 w-full h-px bg-gradient-to-r from-transparent via-cyan-400/50 to-transparent animate-pulse"></div>
        <div
          className="absolute bottom-20 left-0 w-full h-px bg-gradient-to-r from-transparent via-blue-400/50 to-transparent animate-pulse"
          style={{ animationDelay: "1.5s" }}
        ></div>
      </div>

      {/* Main Content */}
      <main className="relative z-10 px-6 py-20">
        <div className="max-w-5xl mx-auto text-center">
          {/* Hero Section */}
          <div className="mb-20">
            <div className="inline-flex items-center px-6 py-3 rounded-full bg-cyan-950/30 border border-cyan-400/30 mb-12 backdrop-blur-xl">
              <div className="w-2 h-2 bg-cyan-400 rounded-full mr-3 animate-pulse"></div>
              <span className="text-sm text-cyan-300 font-medium tracking-wide">COMPUTER USE AGENT</span>
            </div>

            <h1 className="text-7xl md:text-8xl font-bold mb-8 leading-tight tracking-tighter">
              <span className="block mb-4">Transform Any</span>
              <span className="block bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent animate-gradient">
              
              Website Into API
              </span>
            </h1>

            <p className="text-2xl text-gray-300 mb-16 max-w-3xl mx-auto leading-relaxed font-light">
              Powered by Claude Computer Use API to automatically open websites via Mac Spotlight.
              <span className="text-cyan-400"> Just type a website and watch the magic happen.</span>
            </p>
          </div>

          {/* Holographic Input Section */}
          <div className="relative max-w-4xl mx-auto mb-20">
            {/* Holographic glow effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-400/20 via-blue-400/20 to-purple-400/20 rounded-3xl blur-2xl animate-pulse"></div>

            <form onSubmit={handleSubmit} className="relative">
              <div className="relative group">
                {/* Holographic container */}
                <div className="relative bg-black/40 backdrop-blur-2xl border border-cyan-400/30 rounded-3xl p-2 transition-all duration-500 group-focus-within:border-cyan-400/60 group-focus-within:shadow-[0_0_50px_rgba(0,191,255,0.4)] group-focus-within:bg-black/60">
                  {/* Inner holographic border */}
                  <div className="absolute inset-1 rounded-3xl bg-gradient-to-r from-cyan-400/10 via-transparent to-blue-400/10 opacity-0 group-focus-within:opacity-100 transition-opacity duration-500"></div>

                  <div className="flex items-center relative z-10">
                    <div className="flex-1 relative">
                      <div className="absolute left-8 top-1/2 transform -translate-y-1/2 z-0 pointer-events-none">
                        <Globe className="w-6 h-6 text-cyan-400/70" />
                        <div className="absolute inset-0 w-6 h-6 bg-cyan-400/20 rounded-full blur-sm animate-pulse"></div>
                      </div>

                      <textarea
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        onFocus={(e) => e.target.select()}
                        placeholder="Enter a website or describe where you want to go..."
                        className="w-full bg-transparent text-white placeholder-gray-400 pl-20 pr-8 py-8 text-xl resize-none focus:outline-none min-h-[100px] max-h-[250px] font-light tracking-wide cursor-text relative z-20"
                        rows={3}
                        autoFocus
                      />
                    </div>

                    <Button
                      type="submit"
                      disabled={!inputText.trim() || isLoading}
                      className="mr-3 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-black border-0 px-10 py-8 text-xl font-semibold rounded-2xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed group shadow-[0_0_30px_rgba(0,191,255,0.3)] hover:shadow-[0_0_40px_rgba(0,191,255,0.5)]"
                    >
                      {isLoading ? (
                        <div className="flex items-center">
                          <div className="w-6 h-6 border-2 border-black/30 border-t-black rounded-full animate-spin mr-3"></div>
                          <span className="tracking-wide">NAVIGATING...</span>
                        </div>
                      ) : (
                        <div className="flex items-center">
                          <span className="tracking-wide">NAVIGATE</span>
                          <ArrowRight className="w-6 h-6 ml-3 group-hover:translate-x-1 transition-transform" />
                        </div>
                      )}
                    </Button>
                  </div>
                </div>

                {/* Scanning line effect */}
                <div className="absolute inset-0 rounded-3xl overflow-hidden opacity-0 group-focus-within:opacity-100 transition-opacity duration-500 pointer-events-none z-0">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-scan"></div>
                </div>
              </div>
            </form>

            {/* Response Message */}
            {responseMessage && (
              <div className={`mt-8 p-6 rounded-2xl backdrop-blur-xl border ${
                responseMessage.type === 'success' 
                  ? 'bg-green-950/30 border-green-400/30 text-green-300' 
                  : responseMessage.type === 'warning'
                  ? 'bg-yellow-950/30 border-yellow-400/30 text-yellow-300'
                  : 'bg-red-950/30 border-red-400/30 text-red-300'
              }`}>
                <div className="flex items-center">
                  {responseMessage.type === 'success' ? (
                    <CheckCircle className="w-5 h-5 mr-3" />
                  ) : (
                    <AlertCircle className="w-5 h-5 mr-3" />
                  )}
                  <span className="font-medium">{responseMessage.message}</span>
                </div>
              </div>
            )}

            {/* Holographic suggestions */}
            <div className="mt-12 flex flex-wrap justify-center gap-4">
              {[
                "Navigate to Google",
                "Go to GitHub", 
                "Take me to YouTube",
                "Open Reddit",
                "stackoverflow.com",
                "traderjoes.com"
              ].map((example, index) => (
                <button
                  key={index}
                  onClick={() => getQuickWebsite(example)}
                  className="group px-6 py-3 bg-black/30 hover:bg-cyan-950/40 border border-cyan-400/20 hover:border-cyan-400/40 rounded-2xl text-sm text-cyan-300 hover:text-cyan-200 transition-all duration-300 backdrop-blur-xl hover:shadow-[0_0_20px_rgba(0,191,255,0.2)]"
                >
                  <span className="relative">
                    {example}
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-400/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded"></div>
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* Holographic footer */}
      <footer className="relative z-10 border-t border-cyan-400/20 px-6 py-16 mt-20">
        <div className="max-w-7xl mx-auto text-center">
          <div className="text-cyan-400/60 font-light text-lg tracking-wider">
            COMPUTER USE AGENT • POWERED BY CLAUDE • BUILT FOR AUTOMATION
          </div>
        </div>
      </footer>
    </div>
  )
}
