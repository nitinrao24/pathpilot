// src/components/ControlPanel.jsx
// Left sidebar: building selectors, route comparison, time slider

import { useState } from 'react'
import styles from './ControlPanel.module.css'

const DAYS = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

const LABEL_COLOR = { low: '#22c55e', medium: '#eab308', high: '#ef4444' }

function CongestionBadge({ label }) {
  if (!label) return null
  return (
    <span style={{
      display: 'inline-block',
      padding: '1px 7px',
      borderRadius: 3,
      fontSize: 10,
      fontFamily: 'var(--mono)',
      fontWeight: 700,
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      color: LABEL_COLOR[label],
      border: `1px solid ${LABEL_COLOR[label]}`,
      background: `${LABEL_COLOR[label]}18`,
    }}>
      {label}
    </span>
  )
}

function RouteCard({ label, color, dashed, route }) {
  if (!route) return null
  return (
    <div className={styles.routeCard}>
      <div className={styles.routeCardHeader}>
        <span className={styles.routeLine} style={{
          background: dashed ? 'transparent' : color,
          border: dashed ? `2px dashed ${color}` : 'none',
        }} />
        <span className={styles.routeCardLabel} style={{ color }}>{label}</span>
        <span className={styles.routeCardDist}>{route.distance_m}m · ~{route.walk_min} min</span>
      </div>
      <div className={styles.routePath}>
        {route.names.map((name, i) => (
          <span key={i} className={styles.routeStep}>
            {i > 0 && <span className={styles.routeArrow}>→</span>}
            {name}
          </span>
        ))}
      </div>
    </div>
  )
}

export default function ControlPanel({
  buildings,
  source, setSource,
  target, setTarget,
  compareResult,
  routeLoading, routeError,
  onFetchRoute,
  selectedHour, setSelectedHour,
  isPlaying, setIsPlaying,
  dow, setDow,
  stats,
  heatmapLoading,
}) {
  const [activeTab, setActiveTab] = useState('route')  // 'route' | 'info'

  const canRoute = source && target && source !== target

  return (
    <div className={styles.panel}>
      {/* ── Header ── */}
      <div className={styles.header}>
        <div className={styles.logo}>
          <span className={styles.logoMark}>P</span>
          <div>
            <div className={styles.logoTitle}>PathPilot</div>
            <div className={styles.logoSub}>UC Berkeley Campus Nav</div>
          </div>
        </div>
        {stats && (
          <div className={styles.statPill}>
            <span className={styles.statDot} />
            {stats.total_queries.toLocaleString()} routes logged
          </div>
        )}
      </div>

      {/* ── Tabs ── */}
      <div className={styles.tabs}>
        <button className={`${styles.tab} ${activeTab==='route' ? styles.tabActive : ''}`} onClick={() => setActiveTab('route')}>Route</button>
        <button className={`${styles.tab} ${activeTab==='info'  ? styles.tabActive : ''}`} onClick={() => setActiveTab('info')}>About</button>
      </div>

      <div className={styles.body}>
        {activeTab === 'route' && (
          <>
            {/* ── Building selectors ── */}
            <div className={styles.section}>
              <label className={styles.label}>FROM</label>
              <select
                className={styles.select}
                value={source}
                onChange={e => setSource(e.target.value)}
              >
                <option value="">Select building...</option>
                {buildings.map(b => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>

              <div className={styles.swapRow}>
                <div className={styles.dividerLine} />
                <button
                  className={styles.swapBtn}
                  onClick={() => { setSource(target); setTarget(source) }}
                  title="Swap"
                >⇅</button>
                <div className={styles.dividerLine} />
              </div>

              <label className={styles.label}>TO</label>
              <select
                className={styles.select}
                value={target}
                onChange={e => setTarget(e.target.value)}
              >
                <option value="">Select building...</option>
                {buildings.map(b => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            </div>

            {/* ── Time controls ── */}
            <div className={styles.section}>
              <div className={styles.sectionRow}>
                <label className={styles.label}>TIME</label>
                <span className={styles.timeValue}>
                  {String(selectedHour).padStart(2,'0')}:00
                </span>
              </div>
              <div className={styles.sliderRow}>
                <button
                  className={styles.playBtn}
                  onClick={() => setIsPlaying(p => !p)}
                  title={isPlaying ? 'Pause' : 'Play timeline'}
                >
                  {isPlaying ? '⏸' : '▶'}
                </button>
                <input
                  type="range" min={7} max={23} step={1}
                  value={selectedHour}
                  onChange={e => { setIsPlaying(false); setSelectedHour(Number(e.target.value)) }}
                  className={styles.slider}
                />
              </div>
              <div className={styles.dayRow}>
                {DAYS.map((d, i) => (
                  <button
                    key={d}
                    className={`${styles.dayBtn} ${dow === i ? styles.dayActive : ''}`}
                    onClick={() => setDow(i)}
                  >{d}</button>
                ))}
              </div>
            </div>

            {/* ── Route button ── */}
            <button
              className={`${styles.routeBtn} ${!canRoute ? styles.routeBtnDisabled : ''}`}
              onClick={onFetchRoute}
              disabled={!canRoute || routeLoading}
            >
              {routeLoading
                ? <><span className={styles.spinner} /> Computing...</>
                : '⟶  Find Route'}
            </button>

            {routeError && (
              <div className={styles.errorMsg}>{routeError}</div>
            )}

            {/* ── Compare results ── */}
            {compareResult && !routeLoading && (
              <div className={styles.results} style={{ animation: 'slideIn 0.2s ease' }}>
                <div className={styles.sectionRow} style={{ marginBottom: 8 }}>
                  <span className={styles.label}>ROUTES</span>
                  <span className={styles.responseMs}>{compareResult.response_ms}ms</span>
                </div>

                {compareResult.fast.path.join() === compareResult.smart.path.join() ? (
                  <div className={styles.sameRouteNote}>
                    ✓ No congestion detected — fastest route is optimal
                  </div>
                ) : (
                  <div className={styles.savedNote}>
                    Smart route avoids congestion
                    {compareResult.saved_m < 0
                      ? ` (+${Math.abs(compareResult.saved_m)}m extra)`
                      : ` (saves ${compareResult.saved_m}m)`}
                  </div>
                )}

                <RouteCard
                  label="FASTEST"
                  color="#3b82f6"
                  dashed={true}
                  route={compareResult.fast}
                />
                <RouteCard
                  label="SMART"
                  color="#22c55e"
                  dashed={false}
                  route={compareResult.smart}
                />
              </div>
            )}
          </>
        )}

        {activeTab === 'info' && (
          <div className={styles.infoTab}>
            <div className={styles.infoBlock}>
              <div className={styles.infoTitle}>How it works</div>
              <p>PathPilot models UC Berkeley as a weighted directed graph (56 buildings, 1,786 edges) and runs Dijkstra's algorithm to find the shortest path between any two buildings.</p>
              <p>A Random Forest classifier (84% accuracy) predicts congestion 30 minutes ahead for each building based on time of day, day of week, and building type.</p>
              <p>High-congestion buildings get edge weight penalties, rerouting you around crowded areas automatically.</p>
            </div>
            <div className={styles.infoBlock}>
              <div className={styles.infoTitle}>Map legend</div>
              <div className={styles.legendRow}><span className={styles.legendDot} style={{background:'#22c55e'}} />Low congestion</div>
              <div className={styles.legendRow}><span className={styles.legendDot} style={{background:'#eab308'}} />Medium congestion</div>
              <div className={styles.legendRow}><span className={styles.legendDot} style={{background:'#ef4444'}} />High congestion</div>
              <div className={styles.legendRow}><span className={styles.legendLine} style={{borderColor:'#3b82f6'}} />Fastest route</div>
              <div className={styles.legendRow}><span className={styles.legendSolid} style={{background:'#22c55e'}} />Smart route</div>
            </div>
            {stats && (
              <div className={styles.infoBlock}>
                <div className={styles.infoTitle}>Live stats</div>
                <div className={styles.statRow}><span>Total routes</span><span className={styles.statVal}>{stats.total_queries}</span></div>
                <div className={styles.statRow}><span>Unique sources</span><span className={styles.statVal}>{stats.unique_sources}</span></div>
                <div className={styles.statRow}><span>Congestion used</span><span className={styles.statVal}>{stats.congestion_used_pct}%</span></div>
                {stats.most_common_src && <div className={styles.statRow}><span>Top source</span><span className={styles.statVal}>{stats.most_common_src}</span></div>}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Footer ── */}
      <div className={styles.footer}>
        <span className={styles.footerDot} style={{ background: heatmapLoading ? '#eab308' : '#22c55e' }} />
        <span>{heatmapLoading ? 'Loading heatmap...' : 'Live · PathPilot v1.0'}</span>
      </div>
    </div>
  )
}
