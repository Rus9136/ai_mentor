'use client';

import { GeoJSON } from 'react-leaflet';

interface TerritoryLayerProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any;
  currentEpochId: number;
}

export function TerritoryLayer({ data, currentEpochId }: TerritoryLayerProps) {
  const filteredFeatures = data.features.filter(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (f: any) => f.properties?.epoch_id === currentEpochId
  );

  if (filteredFeatures.length === 0) return null;

  const filteredData = {
    type: 'FeatureCollection' as const,
    features: filteredFeatures,
  };

  return (
    <GeoJSON
      key={`territory-${currentEpochId}`}
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      data={filteredData as any}
      style={(feature) => ({
        color: feature?.properties?.color || '#888',
        fillColor: feature?.properties?.color || '#888',
        fillOpacity: feature?.properties?.fillOpacity || 0.3,
        weight: 2,
        opacity: 0.8,
      })}
    />
  );
}
