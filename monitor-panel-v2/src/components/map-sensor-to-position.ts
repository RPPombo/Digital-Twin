/* 🧮 Mapeia o valor do sensor (20–60) → posição (-0.03 ↔ 0.03) */
export function mapSensorToPosition(distance: number): number {
  const clamped = Math.max(20, Math.min(60, distance))
  return 0.03 - ((clamped - 20) / 40) * 0.06
}
