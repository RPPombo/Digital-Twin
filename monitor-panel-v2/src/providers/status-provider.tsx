import { createContext, useContext, useState, type ReactNode } from "react"

interface StatusContextType {
  isRunning: boolean
  setIsRunning: (state: boolean) => void
}

const StatusContext = createContext<StatusContextType | undefined>(undefined)

export function StatusProvider({ children }: { children: ReactNode }) {
  const [isRunning, setIsRunning] = useState(true)

  return (
    <StatusContext.Provider value={{ isRunning, setIsRunning }}>
      {children}
    </StatusContext.Provider>
  )
}

export const useStatus = () => {
  const ctx = useContext(StatusContext)
  if (!ctx) throw new Error("useStatus must be used inside StatusProvider")
  return ctx
}
