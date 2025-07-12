import React, { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';

const MapControls: React.FC = () => {
  const map = useMap();

  useEffect(() => {
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
        
        container.innerHTML = '<button class="map-reset-button" title="Reset View">⟲</button>';
        container.onclick = function () {
          map.setView([34.0522, -118.2437], 10); // Reset to LA
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
  }, [map]);

  return null;
};

export default MapControls;