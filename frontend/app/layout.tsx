import React from 'react'
import './globals.css'

export const metadata = {
  title: 'AI Crypto Trading Assistant | Premium Analysis',
  description: 'Professional-grade crypto analysis and signal verification with AI-powered insights.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-space text-white/90 font-sans antialiased min-h-screen relative">
        {/* Global Background Elements */}
        <div className="space-bg">
          <div className="starfield" />
          <div className="grid-mesh" />
          <div className="orb orb-purple" />
          <div className="orb orb-gold" />
        </div>
        
        <div className="relative z-10 min-h-screen flex flex-col">
          {children}
        </div>
      </body>
    </html>
  )
}
