'use client';

import { CircleMarker, Popup, GeoJSON } from 'react-leaflet';

interface MapMarkersProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any;
  currentEpochId: number;
  locale: string;
}

const MARKER_STYLES: Record<string, { radius: number; color: string; fillColor: string; emoji: string }> = {
  city:           { radius: 6, color: '#2C3E50', fillColor: '#3498DB', emoji: '\uD83C\uDFDB\uFE0F' },
  capital:        { radius: 8, color: '#8E44AD', fillColor: '#9B59B6', emoji: '\u2B50' },
  battle:         { radius: 7, color: '#C0392B', fillColor: '#E74C3C', emoji: '\u2694\uFE0F' },
  archaeological: { radius: 7, color: '#D35400', fillColor: '#E67E22', emoji: '\uD83C\uDFFA' },
  silk_road:      { radius: 5, color: '#B7950B', fillColor: '#F1C40F', emoji: '\uD83D\uDC2B' },
  geographic:     { radius: 6, color: '#16A085', fillColor: '#1ABC9C', emoji: '\uD83C\uDF0A' },
  modern:         { radius: 6, color: '#2980B9', fillColor: '#3498DB', emoji: '\uD83D\uDE80' },
};

export function MapMarkers({ data, currentEpochId, locale }: MapMarkersProps) {
  const isKk = locale === 'kz';

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const pointFeatures = data.features.filter((f: any) =>
    f.geometry.type === 'Point' &&
    f.properties?.epoch_ids?.includes(currentEpochId)
  );

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const lineFeatures = data.features.filter((f: any) =>
    f.geometry.type === 'LineString' &&
    f.properties?.epoch_ids?.includes(currentEpochId)
  );

  return (
    <>
      {/* Silk Road route line */}
      {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
      {lineFeatures.map((feature: any) => (
        <GeoJSON
          key={`line-${feature.properties?.id}-${currentEpochId}`}
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          data={{ type: 'FeatureCollection', features: [feature] } as any}
          style={{
            color: feature.properties?.strokeColor || '#D4AC0D',
            weight: feature.properties?.strokeWidth || 3,
            dashArray: feature.properties?.strokeDasharray || '10,5',
            opacity: 0.7,
          }}
        />
      ))}

      {/* Point markers */}
      {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
      {pointFeatures.map((feature: any) => {
        const coords = feature.geometry.coordinates;
        const props = feature.properties;
        const style = MARKER_STYLES[props.type] || MARKER_STYLES.city;
        const name = isKk && props.name_kk ? props.name_kk : props.name;
        const description = isKk && props.description_kk ? props.description_kk : props.description;

        return (
          <CircleMarker
            key={`marker-${props.id}`}
            center={[coords[1], coords[0]]}
            radius={style.radius}
            pathOptions={{
              color: style.color,
              fillColor: style.fillColor,
              fillOpacity: 0.9,
              weight: 2,
            }}
          >
            <Popup>
              <div className="min-w-[180px] max-w-[240px]">
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-base">{style.emoji}</span>
                  <strong className="text-sm leading-tight">{name}</strong>
                </div>
                {props.year && (
                  <p className="text-xs text-gray-500 mb-1">{props.year} {isKk ? 'ж.' : 'г.'}</p>
                )}
                <p className="text-xs leading-relaxed text-gray-700">{description}</p>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </>
  );
}
