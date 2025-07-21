import React, { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';

interface ClaimsMapControlsProps {
  onResetView?: () => void;
  defaultCenter?: [number, number];
  defaultZoom?: number;
}

const ClaimsMapControls: React.FC<ClaimsMapControlsProps> = ({
  onResetView,
  defaultCenter = [34.0522, -118.2437], // Default to Los Angeles
  defaultZoom = 10,
}) => {
  const map = useMap();

  useEffect(() => {
    // Remove default zoom control (we'll add our own)
    map.zoomControl.remove();

    // Add zoom control to top right
    const zoomControl = L.control.zoom({
      position: 'topright',
    });
    
    map.addControl(zoomControl);

    // Add scale control to bottom left
    const scaleControl = L.control.scale({
      position: 'bottomleft',
      maxWidth: 200,
      metric: false,
      imperial: true,
    });
    
    map.addControl(scaleControl);

    // Add custom control for resetting view
    const ResetControl = L.Control.extend({
      options: {
        position: 'topright',
      },

      onAdd: function () {
        const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom');
        
        container.innerHTML = '<button class="claims-map-reset-button" title="Reset View">⟲</button>';
        container.onclick = function () {
          if (onResetView) {
            onResetView();
          } else {
            map.setView(defaultCenter, defaultZoom);
          }
        };

        return container;
      },
    });

    const resetControl = new ResetControl();
    map.addControl(resetControl);

    // Cleanup
    return () => {
      map.removeControl(zoomControl);
      map.removeControl(scaleControl);
      map.removeControl(resetControl);
    };
  }, [map, onResetView, defaultCenter, defaultZoom]);

  return null;
};

export default ClaimsMapControls;