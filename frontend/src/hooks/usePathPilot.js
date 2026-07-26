// src/hooks/usePathPilot.js
// Central state management — fetches buildings, heatmap, and routes.

import { useState, useEffect, useCallback } from 'react'
import { fetchBuildings, fetchCompare, fetchHeatmapFull, fetchStats } from '../api'

const now = new Date()
const DEFAULT_HOUR = now.getHours() + now.getMinutes() / 60
const DEFAULT_DOW  = now.getDay() === 0 ? 6 : now.getDay() - 1  // JS Sun=0→ we want Mon=0

export function usePathPilot() {
  // ── buildings ──────────────────────────────────────────────
  const [buildings, setBuildings] = useState([])

  // ── route selection ────────────────────────────────────────
  const [source, setSource] = useState('')
  const [target, setTarget] = useState('')

  // ── compare result ─────────────────────────────────────────
  const [compareResult, setCompareResult] = useState(null)
  const [routeLoading,  setRouteLoading]  = useState(false)
  const [routeError,    setRouteError]    = useState(null)

  // ── heatmap ────────────────────────────────────────────────
  const [heatmapData,    setHeatmapData]    = useState(null)  // full 24h grid
  const [heatmapLoading, setHeatmapLoading] = useState(true)
  const [selectedHour,   setSelectedHour]   = useState(Math.round(DEFAULT_HOUR))
  const [isPlaying,      setIsPlaying]      = useState(false)
  const [dow,            setDow]            = useState(DEFAULT_DOW)

  // ── stats ──────────────────────────────────────────────────
  const [stats, setStats] = useState(null)

  // ── load buildings once ────────────────────────────────────
  useEffect(() => {
    fetchBuildings().then(setBuildings).catch(console.error)
  }, [])

  // ── load heatmap when dow changes ──────────────────────────
  useEffect(() => {
    setHeatmapLoading(true)
    fetchHeatmapFull(dow)
      .then(setHeatmapData)
      .catch(console.error)
      .finally(() => setHeatmapLoading(false))
  }, [dow])

  // ── load stats ─────────────────────────────────────────────
  useEffect(() => {
    fetchStats().then(setStats).catch(console.error)
  }, [compareResult])   // refresh after each route query

  // ── animate time slider ────────────────────────────────────
  useEffect(() => {
    if (!isPlaying) return
    const id = setInterval(() => {
      setSelectedHour(h => {
        const next = h + 1
        if (next > 23) { setIsPlaying(false); return 7 }
        return next
      })
    }, 600)
    return () => clearInterval(id)
  }, [isPlaying])

  // ── fetch compare route ────────────────────────────────────
  const fetchRoute = useCallback(async () => {
    if (!source || !target || source === target) return
    setRouteLoading(true)
    setRouteError(null)
    try {
      const result = await fetchCompare(source, target, selectedHour, dow)
      setCompareResult(result)
    } catch (err) {
      setRouteError(err.response?.data?.detail || 'Failed to fetch route')
    } finally {
      setRouteLoading(false)
    }
  }, [source, target, selectedHour, dow])

  // ── current hour snapshot from heatmap grid ────────────────
  const currentHeatmap = useCallback(() => {
    if (!heatmapData) return []
    return Object.entries(heatmapData).map(([id, data]) => {
      const slot = data.hours.find(h => h.hour === selectedHour)
              || data.hours.reduce((a, b) =>
                  Math.abs(a.hour - selectedHour) < Math.abs(b.hour - selectedHour) ? a : b)
      return {
        building_id: id,
        name:  data.name,
        lat:   data.lat,
        lng:   data.lng,
        label: slot.label,
        level: slot.level,
      }
    })
  }, [heatmapData, selectedHour])

  return {
    buildings,
    source, setSource,
    target, setTarget,
    compareResult,
    routeLoading, routeError,
    fetchRoute,
    heatmapLoading,
    selectedHour, setSelectedHour,
    isPlaying, setIsPlaying,
    dow, setDow,
    currentHeatmap,
    stats,
  }
}
