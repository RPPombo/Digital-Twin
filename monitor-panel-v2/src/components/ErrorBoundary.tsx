// ErrorBoundary.tsx
"use client";
import React from "react";

export class ErrorBoundary extends React.Component<
  { fallback?: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props:any){ super(props); this.state = { hasError:false }; }
  static getDerivedStateFromError(){ return { hasError:true }; }
  componentDidCatch(err:any, info:any){ console.warn("Canvas error:", err, info); }
  render(){
    if (this.state.hasError) return this.props.fallback ?? <div className="p-4">Falha ao carregar cena.</div>;
    return this.props.children as any;
  }
}
