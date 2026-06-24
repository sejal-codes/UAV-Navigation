import { MapContainer, TileLayer, Polyline, Circle, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'

const uavIcon = new L.DivIcon({
  className: 'uav-marker',
  html: `<div style="
    width: 16px; height: 16px;
    background: #3da9fc;
    border: 2px solid #e7eeec;
    border-radius: 50%;
    box-shadow: 0 0 12px 4px rgba(61,169,252,0.7);
  "></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
})

export default function MissionMap({ waypoints, dangerZone, telemetry }) {
  const center = waypoints.length
    ? [waypoints[Math.floor(waypoints.length / 2)].lat, waypoints[Math.floor(waypoints.length / 2)].lon]
    : [12.63, 77.1]

  const routeLatLngs = waypoints.map((wp) => [wp.lat, wp.lon])

  return (
    <MapContainer
      center={center}
      zoom={9}
      style={{ height: '100%', width: '100%', borderRadius: '8px' }}
      zoomControl={true}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; OpenStreetMap contributors &copy; CARTO'
      />

      {routeLatLngs.length > 1 && (
        <Polyline
          positions={routeLatLngs}
          pathOptions={{ color: dangerZone ? '#f5b942' : '#3ddc84', weight: 3, opacity: 0.9 }}
        />
      )}

      {waypoints.map((wp, i) => (
        <Circle
          key={i}
          center={[wp.lat, wp.lon]}
          radius={400}
          pathOptions={{ color: '#6e8389', fillColor: '#6e8389', fillOpacity: 0.6, weight: 0 }}
        />
      ))}

      {dangerZone && (
        <Circle
          center={[dangerZone.lat, dangerZone.lon]}
          radius={dangerZone.radius_km * 1000}
          pathOptions={{ color: '#ff4d4d', fillColor: '#ff4d4d', fillOpacity: 0.18, weight: 2 }}
        >
          <Popup>Active danger zone &middot; radius {dangerZone.radius_km} km</Popup>
        </Circle>
      )}

      {telemetry && (
        <Marker position={[telemetry.lat, telemetry.lon]} icon={uavIcon}>
          <Popup>
            UAV &middot; {telemetry.speed_kmh} km/h &middot; {telemetry.altitude_m} m alt
          </Popup>
        </Marker>
      )}
    </MapContainer>
  )
}
