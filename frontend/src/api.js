// src/api.js — centralised API client for PathPilot backend

import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: BASE, timeout: 15000 })

export const fetchBuildings = () =>
  api.get('/buildings').then(r => r.data)

export const fetchRoute = (source, target, hour, dow, avoidCongestion = true) =>
  api.get('/route', {
    params: { source, target, hour, dow, avoid_congestion: avoidCongestion }
  }).then(r => r.data)

export const fetchCompare = (source, target, hour, dow) =>
  api.get('/route/compare', {
    params: { source, target, hour, dow }
  }).then(r => r.data)

export const fetchHeatmapFull = (dow) =>
  api.get('/heatmap/full', { params: { dow } }).then(r => r.data)

export const fetchStats = () =>
  api.get('/heatmap/stats').then(r => r.data)
