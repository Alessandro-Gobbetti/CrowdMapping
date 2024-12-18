<template>
  <div>
    <h1>Crowd Mapping</h1>

    <!-- Toggle to switch between maps -->
    <div>
      <label for="map-type">Select Map Type:</label>
      <select v-model="mapType" id="map-type">
        <option value="crowd">Crowd Map</option>
        <option value="noise">Noise Level Map</option>
        <option value="vehicles">Vehicles Map</option>
      </select>
    </div>

    <!-- Container for the map -->
    <div id="map-container" style="height: 500px; width: 100%; margin-top: 20px;">
      <div id="map" style="height: 100%; width: 100%;"></div>
    </div>
  </div>
</template>

<script>
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { viewDepthKey } from "vue-router";

export default {
  name: "MapPage",
  data() {
    return {
      map: null, // Initialize the map once
      mapType: "crowd", // Default to the crowd map
      crowdLayer: null, // Layer for crowd markers and circles
      noiseLayer: null, // Layer for noise markers and circles
      vehiclesLayer: null, // Layer for vehicle markers and circles
      locations: [], // Array to store multiple locations
    };
  },
  async mounted() {
    this.initMap();
    await this.fetchData();
  },
  methods: {
    initMap() {
      // Initialize the main map (shared for all types)
      this.map = L.map("map").setView([46.0168, 8.9575], 15);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 16,
      }).addTo(this.map);

      // Initialize empty layers for crowd, noise, and vehicles
      this.crowdLayer = L.layerGroup().addTo(this.map);
      this.noiseLayer = L.layerGroup().addTo(this.map);
      this.vehiclesLayer = L.layerGroup().addTo(this.map);
    },

    async fetchData() {
      try {
        // Fetch data from the server
        const date_range = ['2021-10-01 10:10:19', '2025-10-31 10:10:19'];
        const url = `${import.meta.env.VITE_BACKEND_URL}/get?date_range=${date_range.join(',')}`;
        const response = await fetch(url, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });
        const data = await response.json();

        if (Array.isArray(data.data)) {
          this.locations = data.data;
          console.log(this.locations)

          // Add markers and circles for crowd, noise, and vehicles
          this.locations.forEach((location) => {
            const [lat, lon] = [location.gps_lat, location.gps_lon];
            this.addCrowdMarkerAndCircle(lat, lon, location);
            this.addNoiseMarkerAndCircle(lat, lon, location);
            this.addVehiclesMarkerAndCircle(lat, lon, location);
          });

          // Initially load the crowd layer and hide the other layers
          this.updateMapView();
        } else {
          console.error("Invalid data format in DemoData.json");
        }
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    },

    // Method to add crowd marker and circle
    addCrowdMarkerAndCircle(lat, lon, locationData) {
      const radius = 100;
      let circleColor;

      // Define the circle color based on the number of people
      let maxPeople = 200;
      const hue = Math.max(0, Math.min(maxPeople - locationData.people, maxPeople));
      circleColor = `hsl(${hue}, 100%, 50%)`;


      // Add a marker at the GPS location with the number of people
      L.marker([lat, lon]).addTo(this.crowdLayer);

      // Add a circle around the marker
      const circle = L.circle([lat, lon], {
        color: circleColor,
        fillColor: circleColor,
        fillOpacity: 0.5,
        radius: radius,
      }).addTo(this.crowdLayer);

      circle.bindTooltip(
        `<strong>People:</strong> ${locationData.people} <br>
        <strong>Usual:</strong> ${Math.round(locationData.stats_people)} <br>
        <strong>Crowd:</strong> ${Math.round(locationData.people / locationData.stats_people * 100)}%`,
        {
          direction: "top",
          offset: [0, -10],
          className: "fade-tooltip",
        }
      );
    },

    // Method to add noise marker and circle
    addNoiseMarkerAndCircle(lat, lon, noiseData) {
      const radius = 100;
      let circleColor;

      // Define the circle color based on the noise level
      let maxNoise = 100;
      const hue = Math.max(0, Math.min(maxNoise - noiseData.noise, maxNoise));
      circleColor = `hsl(${hue}, 100%, 50%)`;

      // Add a marker for noise level data
      L.marker([lat, lon]).addTo(this.noiseLayer);

      // Add a circle around the marker
      const circle = L.circle([lat, lon], {
        color: circleColor,
        fillColor: circleColor,
        fillOpacity: 0.5,
        radius: radius,
      }).addTo(this.noiseLayer);

      circle.bindTooltip(
        `<strong>Noise Level:</strong> ${noiseData.noise} dB <br>
        <strong>Usual:</strong> ${Math.round(noiseData.stats_noise)} dB <br>
        <strong>Noisy:</strong> ${Math.round(noiseData.noise - noiseData.stats_noise)} dB`,
        {
          direction: "top",
          offset: [0, -10],
          className: "fade-tooltip",
        }
      );
    },

    // Method to add vehicle marker and circle
    addVehiclesMarkerAndCircle(lat, lon, vehicleData) {
      const radius = 100;
      let circleColor;

      // Define the circle color based on the number of vehicles
      // Calculate the hue based on the number of vehicles (0 vehicles = green, 100+ vehicles = red)
      let maxVehicles = 150;
      const hue = Math.max(0, Math.min(maxVehicles - (vehicleData.vehicles * 1.2), maxVehicles));
      circleColor = `hsl(${hue}, 100%, 50%)`;

      // Add a marker for vehicle data
      L.marker([lat, lon]).addTo(this.vehiclesLayer);

      // Add a circle around the marker
      const circle = L.circle([lat, lon], {
        color: circleColor,
        fillColor: circleColor,
        fillOpacity: 0.5,
        radius: radius,
      }).addTo(this.vehiclesLayer);

      circle.bindTooltip(
        `<strong>Vehicles:</strong> ${vehicleData.vehicles} <br>
        <strong>Usual:</strong> ${Math.round(vehicleData.stats_vehicles)} <br>
        <strong>Traffic:</strong> ${Math.round(vehicleData.vehicles / vehicleData.stats_vehicles * 100)}%`,
        {
          direction: "top",
          offset: [0, -10],
          className: ".fade-tooltip",
        }
      );
    },

    // Update the map view based on selected map type (crowd, noise, or vehicles)
    updateMapView() {
      if (this.mapType === "crowd") {
        this.crowdLayer.addTo(this.map);
        this.noiseLayer.removeFrom(this.map);
        this.vehiclesLayer.removeFrom(this.map);
      } else if (this.mapType === "noise") {
        this.noiseLayer.addTo(this.map);
        this.crowdLayer.removeFrom(this.map);
        this.vehiclesLayer.removeFrom(this.map);
      } else if (this.mapType === "vehicles") {
        this.vehiclesLayer.addTo(this.map);
        this.crowdLayer.removeFrom(this.map);
        this.noiseLayer.removeFrom(this.map);
      }
    },
  },

  watch: {
    // Watch for map type change and update the map accordingly
    mapType(newType) {
      this.updateMapView();
    },
  },
};
</script>

<style scoped>
/* Ensure map height is set correctly */
#map-container {
  height: 900px;
  /* Increased height */
  width: 100%;
  margin-top: 20px;
}

/* Style for the map */
#map {
  height: 100%;
  /* Ensure the map fills the container */
  width: 100%;
}
</style>
