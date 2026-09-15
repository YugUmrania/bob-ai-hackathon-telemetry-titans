import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import { useEffect } from 'react';
import L from 'leaflet';
import type { Asset } from '../../types';
import { RiskMarker } from './RiskMarker';

// Fix broken Leaflet default icon — use bundled assets to avoid external CDN requests
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
  iconUrl:       new URL('leaflet/dist/images/marker-icon.png',    import.meta.url).href,
  shadowUrl:     new URL('leaflet/dist/images/marker-shadow.png',  import.meta.url).href,
});

interface GridMapProps {
  assets: Asset[];
  selectedAssetId?: string | null;
  onAssetSelect?: (id: string) => void;
  center?: [number, number];
  zoom?: number;
  height?: string | number;
}

// Delhi NCR default center
const DEFAULT_CENTER: [number, number] = [28.6139, 77.2090];
const DEFAULT_ZOOM = 11;

function MapController({
  assets,
  selectedAssetId,
  center,
  zoom,
}: {
  assets: Asset[];
  selectedAssetId?: string | null;
  center?: [number, number];
  zoom?: number;
}) {
  const map = useMap();

  // Invalidate size after mount so Leaflet fills flexbox container properly
  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 200);
    return () => clearTimeout(timer);
  }, [map]);

  // Smoothly focus when a specific asset is selected
  useEffect(() => {
    if (!selectedAssetId) return;
    const selected = assets.find((a) => a.id === selectedAssetId);
    if (
      selected?.location &&
      typeof selected.location.lat === 'number' &&
      !isNaN(selected.location.lat) &&
      typeof selected.location.lng === 'number' &&
      !isNaN(selected.location.lng)
    ) {
      map.flyTo([selected.location.lat, selected.location.lng], 14, { duration: 0.8 });
    }
  }, [selectedAssetId, assets, map]);

  // Dynamically fit bounds when assets are loaded or filtered
  useEffect(() => {
    if (selectedAssetId) return; // let selection flyTo handle view if selected

    if (center && zoom) {
      map.setView(center, zoom);
      return;
    }

    const validCoords = assets
      .filter(
        (a) =>
          a.location &&
          typeof a.location.lat === 'number' &&
          !isNaN(a.location.lat) &&
          typeof a.location.lng === 'number' &&
          !isNaN(a.location.lng),
      )
      .map((a) => [a.location.lat, a.location.lng] as [number, number]);

    if (validCoords.length === 0) {
      map.setView(DEFAULT_CENTER, DEFAULT_ZOOM);
    } else if (validCoords.length === 1) {
      map.setView(validCoords[0], 13);
    } else {
      const bounds = L.latLngBounds(validCoords);
      map.fitBounds(bounds, { padding: [35, 35], maxZoom: 13 });
    }
  }, [assets, center, zoom, selectedAssetId, map]);

  return null;
}

export function GridMap({
  assets,
  selectedAssetId,
  onAssetSelect,
  center,
  zoom,
  height = '100%',
}: GridMapProps) {
  const initialCenter = center ?? DEFAULT_CENTER;
  const initialZoom = zoom ?? DEFAULT_ZOOM;

  return (
    <div
      style={{ height }}
      className="rounded-xl overflow-hidden border border-surface-border"
    >
      <MapContainer
        center={initialCenter}
        zoom={initialZoom}
        className="w-full h-full"
        zoomControl
      >
        <MapController
          assets={assets}
          selectedAssetId={selectedAssetId}
          center={center}
          zoom={zoom}
        />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {assets.map((asset) => (
          <RiskMarker
            key={asset.id}
            asset={asset}
            isSelected={asset.id === selectedAssetId}
            onClick={onAssetSelect}
          />
        ))}
      </MapContainer>
    </div>
  );
}

