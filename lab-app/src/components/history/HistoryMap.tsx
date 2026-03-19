'use client';

import { useEffect } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import type { EpochData } from '@/types/lab';
import 'leaflet/dist/leaflet.css';

interface HistoryMapProps {
  epoch: EpochData;
}

// Component to handle map view changes
function MapController({ epoch }: { epoch: EpochData }) {
  const map = useMap();

  useEffect(() => {
    // Fly to Kazakhstan center when epoch changes
    map.flyTo([48.0196, 66.9237], 5, { duration: 1 });
  }, [epoch.id, map]);

  return null;
}

export function HistoryMap({ epoch }: HistoryMapProps) {
  return (
    <div className="lab-map-container w-full h-full">
      <MapContainer
        center={[48.0196, 66.9237]}
        zoom={5}
        className="w-full h-full"
        zoomControl={false}
        attributionControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png"
          maxZoom={10}
          minZoom={3}
        />
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png"
          maxZoom={10}
          minZoom={3}
          pane="tooltipPane"
        />
        <MapController epoch={epoch} />

        {/* Territory GeoJSON layers will be added in Phase 3 */}
        {/* <TerritoryLayer epoch={epoch} /> */}
        {/* <MapMarkers epoch={epoch} /> */}
      </MapContainer>

      {/* Epoch color indicator */}
      <div
        className="absolute top-20 right-3 z-[1000] w-3 h-3 rounded-full border-2 border-white shadow"
        style={{ backgroundColor: epoch.color }}
      />
    </div>
  );
}
