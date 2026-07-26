// src/App.jsx
import { useState } from 'react'
import CampusMap    from './components/CampusMap'
import ControlPanel from './components/ControlPanel'
import { usePathPilot } from './hooks/usePathPilot'
import './index.css'

export default function App() {
  const [selectedBuilding, setSelectedBuilding] = useState(null)

  const {
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
  } = usePathPilot()

  const heatmapPoints = currentHeatmap()

  return (
    <div style={{ display: 'flex', width: '100%', height: '100%' }}>
      <ControlPanel
        buildings={buildings}
        source={source}         setSource={setSource}
        target={target}         setTarget={setTarget}
        compareResult={compareResult}
        routeLoading={routeLoading}
        routeError={routeError}
        onFetchRoute={fetchRoute}
        selectedHour={selectedHour} setSelectedHour={setSelectedHour}
        isPlaying={isPlaying}   setIsPlaying={setIsPlaying}
        dow={dow}               setDow={setDow}
        stats={stats}
        heatmapLoading={heatmapLoading}
      />
      <div style={{ flex: 1, position: 'relative' }}>
        <CampusMap
          heatmapPoints={heatmapPoints}
          compareResult={compareResult}
          selectedBuilding={selectedBuilding}
          onBuildingClick={id => setSelectedBuilding(prev => prev === id ? null : id)}
        />
      </div>
    </div>
  )
}
