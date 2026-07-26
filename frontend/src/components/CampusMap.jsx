// src/components/CampusMap.jsx
// Leaflet map with D3 congestion heatmap + route polylines

import { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip, useMap } from 'react-leaflet'
import * as d3 from 'd3'
import 'leaflet/dist/leaflet.css'

const BERKELEY  = [37.8724, -122.2595]
const BOUNDS    = [[37.860, -122.272], [37.882, -122.245]]

// D3 color scale: green (low) → yellow (medium) → red (high)
const colorScale = d3.scaleSequential()
  .domain([0, 2])
  .interpolator(t => {
    if (t < 0.5) return d3.interpolate('#22c55e', '#eab308')(t * 2)
    return d3.interpolate('#eab308', '#ef4444')((t - 0.5) * 2)
  })

const LABEL_COLOR = { low: '#22c55e', medium: '#eab308', high: '#ef4444' }
const LABEL_BG    = { low: 'rgba(34,197,94,0.12)', medium: 'rgba(234,179,8,0.12)', high: 'rgba(239,68,68,0.12)' }

function FitBounds() {
  const map = useMap()
  useEffect(() => { map.fitBounds(BOUNDS) }, [map])
  return null
}

export default function CampusMap({ heatmapPoints, compareResult, selectedBuilding, onBuildingClick }) {

  return (
    <MapContainer
      center={BERKELEY}
      zoom={16}
      maxBounds={BOUNDS}
      maxBoundsViscosity={0.9}
      zoomControl={true}
      style={{ width: '100%', height: '100%' }}
    >
      <FitBounds />

      {/* Dark OSM tiles */}
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution="&copy; OpenStreetMap &copy; CARTO"
        maxZoom={19}
      />

      {/* ── Heatmap layer — one circle per building ── */}
      {heatmapPoints.map(b => {
        const color   = colorScale(b.level)
        const isSelected = selectedBuilding === b.building_id
        return (
          <CircleMarker
            key={b.building_id}
            center={[b.lat, b.lng]}
            radius={isSelected ? 14 : 9}
            pathOptions={{
              fillColor:   color,
              fillOpacity: isSelected ? 0.95 : 0.72,
              color:       isSelected ? '#fff' : color,
              weight:      isSelected ? 2 : 0.5,
              opacity:     1,
            }}
            eventHandlers={{ click: () => onBuildingClick(b.building_id) }}
          >
            <Tooltip
              permanent={false}
              direction="top"
              offset={[0, -6]}
              className="pp-tooltip"
            >
              <div style={{
                background: LABEL_BG[b.label],
                border: `1px solid ${LABEL_COLOR[b.label]}`,
                borderRadius: 4,
                padding: '4px 8px',
                fontFamily: "'DM Sans', sans-serif",
                fontSize: 12,
                color: '#f0f2f5',
              }}>
                <strong>{b.name}</strong>
                <span style={{ marginLeft: 8, color: LABEL_COLOR[b.label], fontWeight: 600, textTransform: 'uppercase', fontSize: 10 }}>
                  {b.label}
                </span>
              </div>
            </Tooltip>
          </CircleMarker>
        )
      })}

      {/* ── Route lines ── */}
      {compareResult && (
        <>
          {/* Fast route — blue dashed */}
          <Polyline
            positions={compareResult.fast.coordinates}
            pathOptions={{ color: '#3b82f6', weight: 3, opacity: 0.6, dashArray: '8 5' }}
          />
          {/* Smart route — solid green */}
          <Polyline
            positions={compareResult.smart.coordinates}
            pathOptions={{ color: '#22c55e', weight: 4, opacity: 0.9 }}
          />
        </>
      )}
    </MapContainer>
  )
}
