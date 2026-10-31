import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import {
  Layers,
  MapPin,
  Eye,
  EyeOff,
  Activity,
  Info,
  Compass,
  Wind,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { StationDetail } from '../types';
import { AQIBadge } from '../components/AQIBadge';
import { DisclaimerBanner } from '../components/DisclaimerBanner';

export const LiveMapPage: React.FC = () => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const stationsLayerRef = useRef<L.LayerGroup | null>(null);
  const gridLayerRef = useRef<L.GeoJSON | null>(null);

  const [stations, setStations] = useState<StationDetail[]>([]);
  const [selectedStation, setSelectedStation] = useState<StationDetail | null>(null);
  const [showStations, setShowStations] = useState<boolean>(true);
  const [showGrid, setShowGrid] = useState<boolean>(true);
  const [activePollutant, setActivePollutant] = useState<'pm25' | 'pm10'>('pm25');
  const [loading, setLoading] = useState<boolean>(true);

  // Initialize Leaflet Map with CartoDB Positron Light Tiles
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [28.62, 77.21],
      zoom: 11,
      zoomControl: true,
      minZoom: 9,
      maxZoom: 16,
    });

    // CartoDB Positron (Light, Calm, Editorial)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(map);

    stationsLayerRef.current = L.layerGroup().addTo(map);
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Fetch stations and grid GeoJSON
  useEffect(() => {
    const loadMapData = async () => {
      try {
        setLoading(true);
        const stRes = await apiClient.getStations();
        setStations(stRes.stations);
        if (stRes.stations.length > 0) {
          setSelectedStation(stRes.stations[0]);
        }

        // Fetch Grid GeoJSON
        try {
          const gridGeoJson = await apiClient.getGridGeoJSON();
          if (mapInstanceRef.current && gridGeoJson) {
            if (gridLayerRef.current) {
              gridLayerRef.current.remove();
            }

            gridLayerRef.current = L.geoJSON(gridGeoJson, {
              style: (feature) => {
                const val = feature?.properties?.[activePollutant] || 90;
                let fillColor = '#527D75';
                if (val > 250) fillColor = '#7A2338';
                else if (val > 120) fillColor = '#B83E3E';
                else if (val > 90) fillColor = '#C26738';
                else if (val > 60) fillColor = '#C48A2C';
                else fillColor = '#3D8B7A';

                return {
                  fillColor,
                  fillOpacity: 0.22,
                  weight: 1,
                  color: '#D8D8D0',
                  dashArray: '2',
                };
              },
              onEachFeature: (feature, layer) => {
                const props = feature.properties;
                layer.bindPopup(`
                  <div style="font-family: inherit; font-size: 12px; line-height: 1.4;">
                    <div style="font-weight: 600; color: #202A30; margin-bottom: 4px;">Cell ${props.cell_id}</div>
                    <div style="color: #5A626A;">PM2.5: <b style="color: #202A30;">${props.pm25} µg/m³</b></div>
                    <div style="color: #5A626A;">PM10: <b style="color: #202A30;">${props.pm10} µg/m³</b></div>
                    <div style="color: #8C959D; font-size: 11px; margin-top: 4px;">Type: ${props.is_monitored ? 'Physical Station Anchor' : 'Spatial Model Estimate'}</div>
                  </div>
                `);
              },
            }).addTo(mapInstanceRef.current);
          }
        } catch (e) {
          console.warn('Grid GeoJSON not loaded:', e);
        }
      } catch (err) {
        console.error('Error loading stations:', err);
      } finally {
        setLoading(false);
      }
    };

    loadMapData();
  }, [activePollutant]);

  // Update station markers on layer
  useEffect(() => {
    if (!stationsLayerRef.current) return;
    stationsLayerRef.current.clearLayers();

    if (!showStations) return;

    stations.forEach((st) => {
      const val = activePollutant === 'pm25' ? st.current_pm25 || 92 : st.current_pm10 || 162;
      let markerBorder = '#527D75';
      let markerBg = '#EAF4F1';
      let markerText = '#285D52';

      if (st.aqi > 400) {
        markerBorder = '#7A2338';
        markerBg = '#F9EAEF';
        markerText = '#631427';
      } else if (st.aqi > 300) {
        markerBorder = '#B83E3E';
        markerBg = '#FCEEEE';
        markerText = '#8A2424';
      } else if (st.aqi > 200) {
        markerBorder = '#C26738';
        markerBg = '#FDF1EB';
        markerText = '#8C431F';
      } else if (st.aqi > 100) {
        markerBorder = '#C48A2C';
        markerBg = '#FDF6E9';
        markerText = '#865914';
      }

      const customIcon = L.divIcon({
        className: 'custom-station-pin',
        html: `
          <div style="
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: #FFFFFF;
            border: 2px solid ${markerBorder};
            box-shadow: 0 2px 8px rgba(0,0,0,0.12);
            color: #202A30;
            font-size: 11px;
            font-family: monospace;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.15s ease;
          ">
            ${Math.round(val)}
          </div>
        `,
        iconSize: [30, 30],
        iconAnchor: [15, 15],
      });

      const marker = L.marker([st.latitude, st.longitude], { icon: customIcon });

      marker.on('click', () => {
        setSelectedStation(st);
      });

      marker.bindPopup(`
        <div style="font-family: inherit; font-size: 12px; padding: 2px;">
          <div style="font-weight: 600; color: #202A30; font-size: 13px; margin-bottom: 2px;">${st.name}</div>
          <div style="color: #8C959D; font-size: 11px; margin-bottom: 6px;">${st.neighborhood_id} · ${st.classification}</div>
          <div style="display: flex; gap: 12px; margin-bottom: 6px;">
            <div><span style="color: #5A626A;">PM2.5:</span> <strong style="color: #202A30;">${st.current_pm25 || '—'} µg/m³</strong></div>
            <div><span style="color: #5A626A;">PM10:</span> <strong style="color: #202A30;">${st.current_pm10 || '—'} µg/m³</strong></div>
          </div>
          <div><span style="color: #5A626A;">AQI:</span> <strong style="color: #202A30;">${st.aqi} (${st.aqi_category})</strong></div>
        </div>
      `);

      stationsLayerRef.current?.addLayer(marker);
    });
  }, [stations, showStations, activePollutant]);

  // Toggle grid visibility
  useEffect(() => {
    if (gridLayerRef.current && mapInstanceRef.current) {
      if (showGrid) {
        mapInstanceRef.current.addLayer(gridLayerRef.current);
      } else {
        mapInstanceRef.current.removeLayer(gridLayerRef.current);
      }
    }
  }, [showGrid]);

  return (
    <div className="space-y-4">
      <DisclaimerBanner type="observation" />

      {/* Map Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-[#E5E5DF] bg-white p-3.5 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 rounded-lg border border-[#E5E5DF] bg-[#FAFAF7] p-1 text-xs">
            <button
              onClick={() => setActivePollutant('pm25')}
              className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                activePollutant === 'pm25'
                  ? 'bg-white text-charcoal font-semibold shadow-[0_1px_2px_rgba(0,0,0,0.04)] border border-[#E5E5DF]'
                  : 'text-charcoal-muted hover:text-charcoal'
              }`}
            >
              PM2.5 (Fine)
            </button>
            <button
              onClick={() => setActivePollutant('pm10')}
              className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                activePollutant === 'pm10'
                  ? 'bg-white text-charcoal font-semibold shadow-[0_1px_2px_rgba(0,0,0,0.04)] border border-[#E5E5DF]'
                  : 'text-charcoal-muted hover:text-charcoal'
              }`}
            >
              PM10 (Coarse)
            </button>
          </div>

          <div className="h-4 w-px bg-[#E5E5DF]" />

          {/* Layer toggles */}
          <button
            onClick={() => setShowStations(!showStations)}
            className={`flex items-center gap-1.5 rounded-lg border px-3 py-1 text-xs font-medium transition-colors ${
              showStations
                ? 'border-[#CDE5DF] bg-[#EAF4F1] text-[#285D52]'
                : 'border-[#E5E5DF] bg-white text-[#8C959D]'
            }`}
          >
            {showStations ? <Eye className="h-3.5 w-3.5" /> : <EyeOff className="h-3.5 w-3.5" />}
            <span>Stations (15)</span>
          </button>

          <button
            onClick={() => setShowGrid(!showGrid)}
            className={`flex items-center gap-1.5 rounded-lg border px-3 py-1 text-xs font-medium transition-colors ${
              showGrid
                ? 'border-[#D5E3EC] bg-[#EEF4F8] text-[#50728F]'
                : 'border-[#E5E5DF] bg-white text-[#8C959D]'
            }`}
          >
            {showGrid ? <Eye className="h-3.5 w-3.5" /> : <EyeOff className="h-3.5 w-3.5" />}
            <span>Spatial Mesh (121 cells)</span>
          </button>
        </div>

        <div className="flex items-center gap-4 text-xs text-charcoal-muted">
          <span className="flex items-center gap-1.5">
            <Compass className="h-3.5 w-3.5 text-brand-green" />
            Northwest Wind 2.5 m/s
          </span>
          <span className="flex items-center gap-1.5">
            <Layers className="h-3.5 w-3.5 text-brand-blue" />
            0.05° Resolution (~5.5 km)
          </span>
        </div>
      </div>

      {/* Main Map View & Details Panel */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">
        {/* Map Canvas */}
        <div className="relative h-[600px] overflow-hidden rounded-xl border border-[#E5E5DF] bg-white shadow-[0_1px_3px_rgba(0,0,0,0.02)] lg:col-span-3">
          <div ref={mapContainerRef} className="h-full w-full" />

          {/* Map Legend Overlay */}
          <div className="absolute bottom-4 left-4 z-[1000] rounded-lg border border-[#E5E5DF] bg-white/95 p-3.5 shadow-md backdrop-blur text-xs">
            <div className="text-[11px] font-semibold text-charcoal-muted uppercase tracking-wider mb-2">
              Pollution Severity Scale
            </div>
            <div className="space-y-1.5 text-xs text-charcoal">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-[#3D8B7A]" />
                <span>Good / Satisfactory (0 – 100)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-[#C48A2C]" />
                <span>Moderate (101 – 200)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-[#C26738]" />
                <span>Poor (201 – 300)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-[#B83E3E]" />
                <span>Very Poor / Severe (&gt; 300)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Station Detail Sidebar */}
        <div className="rounded-xl border border-[#E5E5DF] bg-white p-5 space-y-4 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
          <div className="border-b border-[#F2F2EC] pb-3">
            <span className="text-[11px] font-semibold text-charcoal-muted uppercase tracking-wider">
              Selected Monitoring Station
            </span>
            {selectedStation ? (
              <div className="mt-1.5">
                <div className="font-semibold text-sm text-charcoal">{selectedStation.name}</div>
                <div className="font-mono text-xs text-brand-green">{selectedStation.neighborhood_id}</div>
              </div>
            ) : (
              <div className="mt-1.5 text-xs text-charcoal-muted">Click any station pin on the map</div>
            )}
          </div>

          {selectedStation && (
            <div className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-lg border border-[#E5E5DF] bg-[#FAFAF7] p-3">
                  <span className="text-[10px] text-charcoal-muted block uppercase">PM2.5</span>
                  <span className="text-xl font-mono font-semibold text-brand-green">
                    {selectedStation.current_pm25 || selectedStation.pm2_5 || 92}
                  </span>
                  <span className="text-[10px] text-charcoal-muted ml-1">µg/m³</span>
                </div>
                <div className="rounded-lg border border-[#E5E5DF] bg-[#FAFAF7] p-3">
                  <span className="text-[10px] text-charcoal-muted block uppercase">PM10</span>
                  <span className="text-xl font-mono font-semibold text-brand-blue">
                    {selectedStation.current_pm10 || selectedStation.pm10 || 162}
                  </span>
                  <span className="text-[10px] text-charcoal-muted ml-1">µg/m³</span>
                </div>
              </div>

              <div className="rounded-lg border border-[#E5E5DF] bg-[#FAFAF7] p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-charcoal-muted">Air Quality</span>
                  <AQIBadge aqi={selectedStation.aqi} category={selectedStation.aqi_category} size="sm" />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-charcoal-muted">Zoning</span>
                  <span className="font-medium text-charcoal">{selectedStation.classification}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-charcoal-muted">Traffic Factor</span>
                  <span className="font-mono text-charcoal">{selectedStation.road_density_factor.toFixed(2)}x</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-charcoal-muted">Coordinates</span>
                  <span className="font-mono text-charcoal text-[11px]">
                    {selectedStation.latitude.toFixed(4)}°, {selectedStation.longitude.toFixed(4)}°
                  </span>
                </div>
              </div>

              <div className="rounded-lg border border-[#E5E5DF] bg-[#FAF8F5] p-3 text-[11px] text-charcoal-muted space-y-1">
                <div className="font-medium text-charcoal flex items-center gap-1.5">
                  <Info className="h-3.5 w-3.5 text-brand-green" />
                  Station Role
                </div>
                <p className="leading-relaxed">
                  Serves as a physical ground-truth anchor in the spatial graph network, constraining
                  interpolations and GNN predictions across surrounding unmonitored sectors.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
