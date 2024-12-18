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
        const response = await fetch("/DemoData.json");
        const data = await response.json();

        if (data.success && Array.isArray(data.data)) {
          this.locations = data.data;

          // Add markers and circles for crowd, noise, and vehicles
          this.locations.forEach((location) => {
            const [lat, lon] = location.gps.split(",").map(Number);
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
      if (locationData.people >= 200) {
        circleColor = "darkred";
      } else if (locationData.people >= 150) {
        circleColor = "red";
      } else if (locationData.people >= 100) {
        circleColor = "darkgreen";
      } else if (locationData.people >= 50) {
        circleColor = "green";
      } else {
        circleColor = "lightgreen";
      }

      // Add a marker at the GPS location with the number of people
      const marker = L.marker([lat, lon]).addTo(this.crowdLayer);
      marker.bindTooltip(
        `<strong>People:</strong> ${locationData.people}`,
        {
          permanent: true,
          direction: "top",
          offset: [0, -10],
        }
      );

      // Add a circle around the marker
      L.circle([lat, lon], {
        color: circleColor,
        fillColor: circleColor,
        fillOpacity: 0.5,
        radius: radius,
      }).addTo(this.crowdLayer);
    },

    // Method to add noise marker and circle
    addNoiseMarkerAndCircle(lat, lon, noiseData) {
      const radius = 100;
      let circleColor;

      // Define the circle color based on the noise level
      if (noiseData.noise >= 100) {
        circleColor = "darkred"; // Very Loud
      } else if (noiseData.noise > 70 && noiseData.noise <= 100) {
        circleColor = "lightcoral"; // Loud
      } else if (noiseData.noise >= 50 && noiseData.noise <= 70) {
        circleColor = "darkgreen"; // Noisy
      } else {
        circleColor = "lightgreen"; // Moderate
      }

      // Add a marker for noise level data
      const marker = L.marker([lat, lon]).addTo(this.noiseLayer);
      marker.bindTooltip(
        `<strong>Noise Level:</strong> ${noiseData.noise} dB`,
        {
          permanent: true,
          direction: "top",
          offset: [0, -10],
        }
      );

      // Add a circle around the marker
      L.circle([lat, lon], {
        color: circleColor,
        fillColor: circleColor,
        fillOpacity: 0.5,
        radius: radius,
      }).addTo(this.noiseLayer);
    },

    // Method to add vehicle marker and circle
    addVehiclesMarkerAndCircle(lat, lon, vehicleData) {
      const radius = 100;
      let circleColor;

      // Define the circle color based on the number of vehicles
      if (vehicleData.vehicles >= 100) {
        circleColor = "darkred"; // High traffic
      } else if (vehicleData.vehicles >= 50 && vehicleData.vehicles <100) {
        circleColor = "red"; // Moderate traffic
      } else if (vehicleData.vehicles >= 0 && vehicleData.vehicles <50) {
        circleColor = "green"; // Low traffic
      }

      // Add a marker for vehicle data
      const marker = L.marker([lat, lon]).addTo(this.vehiclesLayer);
      marker.bindTooltip(
        `<strong>Vehicles:</strong> ${vehicleData.vehicles}`,
        {
          permanent: true,
          direction: "top",
          offset: [0, -10],
        }
      );

      // Add a circle around the marker
      L.circle([lat, lon], {
        color: circleColor,
        fillColor: circleColor,
        fillOpacity: 0.5,
        radius: radius,
      }).addTo(this.vehiclesLayer);
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
  height: 900px; /* Increased height */
  width: 100%;
  margin-top: 20px;
}

/* Style for the map */
#map {
  height: 100%; /* Ensure the map fills the container */
  width: 100%;
}
</style>
