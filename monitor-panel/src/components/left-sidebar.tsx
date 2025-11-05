"use client"

import { Card, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Thermometer, Ruler, Gauge, Eye, Hand } from "lucide-react"
import { useSensor } from "@/providers/sensor-provider"
import type { ReactNode } from "react"

const getTemperatureColor = (temp: number) => {
  if (temp < 20) return "text-blue-400"
  if (temp < 30) return "text-green-400"
  if (temp < 40) return "text-yellow-400"
  if (temp < 50) return "text-orange-400"
  return "text-red-400"
}

export default function LeftSidebar() {
  const { sensorData } = useSensor()

  return (
    <aside
      className="
        col-span-3 flex flex-col gap-4 h-full
        max-lg:col-span-12 max-lg:flex-row max-lg:flex-wrap max-lg:justify-center
      "
    >

      <SensorCard
        icon={<Thermometer className="h-4 w-4" />}
        title="TEMPERATURE SENSOR"
        subtitle="Thermocouple Type K"
        value={`${sensorData.temperature.toFixed(1)}°C`}
        valueColor={getTemperatureColor(sensorData.temperature)}
      >
        <div className="w-full h-2 bg-secondary/40 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 via-yellow-500 to-red-500 transition-all duration-500 ease-in-out"
            style={{
              width: `${Math.min(100, (sensorData.temperature / 100) * 100)}%`,
            }}
          />
        </div>
      </SensorCard>

      <SensorCard
        icon={<Ruler className="h-4 w-4" />}
        title="DISTANCE SENSOR"
        subtitle="cm — HC-SR04 Ultrasonic"
        value={`${sensorData.distance.toFixed(1)}`}
        valueColor={getTemperatureColor(sensorData.distance)}
      >
        <div className="w-full h-2 bg-secondary/40 rounded-full overflow-hidden mt-2">
          <div
            className="h-full bg-chart-2 transition-all duration-500 ease-in-out"
            style={{
              width: `${Math.min(100, (sensorData.distance / 400) * 100)}%`,
            }}
          />
        </div>
      </SensorCard>

      <SensorCard
        icon={<CardContent className="p-0 space-y-2" />}
        title="PRESSURE SENSOR"
        subtitle="kPa — XGZP701DBR1R"
        value={sensorData.pressure.toFixed(2)}
        valueColor={getTemperatureColor(sensorData.pressure)}
      >
        <div className="relative h-24 sm:h-28 flex items-center justify-center mt-2">
          <svg viewBox="0 0 100 60" className="w-full max-w-[220px]">
            <path
              d="M 10 50 A 40 40 0 0 1 90 50"
              fill="none"
              stroke="rgba(59,130,246,0.25)"
              strokeWidth="8"
              strokeLinecap="round"
            />
            <path
              d="M 10 50 A 40 40 0 0 1 90 50"
              fill="none"
              stroke="#3b82f6"
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={`${(sensorData.pressure / 200) * 126} 126`}
              className="transition-all duration-500 ease-in-out"
            />
            <circle cx="50" cy="50" r="3" fill="#3b82f6" />
          </svg>
        </div>
      </SensorCard>

      <SensorCard
        icon={<CardContent className="p-0 space-y-2" />}
        title="IR SENSORS"
        subtitle="Bread Detection"
        value={sensorData.ir_bread ? "DETECTED" : "CLEAR"}

        valueColor={getTemperatureColor(sensorData.ir_bread)}
      >
        <div className="relative h-24 sm:h-28 flex items-center justify-center mt-2">
          <svg viewBox="0 0 100 60" className="w-full max-w-[220px]">
            <path
              d="M 10 50 A 40 40 0 0 1 90 50"
              fill="none"
              stroke="rgba(59,130,246,0.25)"
              strokeWidth="8"
              strokeLinecap="round"
            />
            <path
              d="M 10 50 A 40 40 0 0 1 90 50"
              fill="none"
              stroke="#3b82f6"
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={`${(sensorData.pressure / 200) * 126} 126`}
              className="transition-all duration-500 ease-in-out"
            />
            <circle cx="50" cy="50" r="3" fill="#3b82f6" />
          </svg>
        </div>
      </SensorCard>

      {/* 👁️ IR */}
      <Card className="bg-card/80 backdrop-blur-sm border-primary/30 p-4 flex flex-col justify-between flex-1 min-w-[250px] max-w-[350px]">
        <CardTitle className="flex items-center gap-2 text-primary text-sm mb-2">
          <Eye className="h-4 w-4" />
          IR SENSORS
        </CardTitle>

        <CardContent className="p-0 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Bread Detection</span>
            <Badge
              variant={sensorData.ir_bread ? "default" : "secondary"}
              className="text-[10px] sm:text-xs px-2"
            >
              {sensorData.ir_bread ? "DETECTED" : "CLEAR"}
            </Badge>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Hand className="h-3 w-3" />
              Hand Safety
            </span>
            <Badge
              variant={sensorData.ir_hand ? "destructive" : "default"}
              className="text-[10px] sm:text-xs px-2"
            >
              {sensorData.ir_hand ? "BLOCKED" : "SAFE"}
            </Badge>
          </div>

          <p className="text-[11px] sm:text-xs text-muted-foreground mt-3">
            TCRT-5000 Sensors
          </p>
        </CardContent>
      </Card>
    </aside>
  )
}



// 
// 
// 

interface SensorCardProps {
  icon?: ReactNode
  title: string
  subtitle?: string
  value?: string | number
  valueColor?: string
  children?: ReactNode // ex: gauge, barra, badges
}

export function SensorCard({
  icon,
  title,
  subtitle,
  value,
  valueColor,
  children,
}: SensorCardProps) {
  return (
    <Card className="bg-card/80 backdrop-blur-sm border-primary/30 p-4 flex flex-col justify-between w-full h-full">
      {/* 🔹 Header */}
      <CardTitle className="flex items-center gap-2 text-primary text-sm sm:text-xs mb-2">
        {icon}
        <span className="truncate font-semibold">{title}</span>
      </CardTitle>

      {/* 🔹 Conteúdo */}
      <CardContent className="p-0 flex flex-col justify-between flex-1 space-y-2">
        {value !== undefined && (
          <div
            className={`font-bold text-3xl md:text-4xl leading-tight ${valueColor ?? "text-foreground"
              }`}
          >
            {value}
          </div>
        )}

        {subtitle && (
          <p className="text-[11px] sm:text-xs text-muted-foreground">{subtitle}</p>
        )}

        {/* children: pode ser gauge, barras ou badges */}
        {children && <div className="mt-2">{children}</div>}
      </CardContent>
    </Card>
  )
}