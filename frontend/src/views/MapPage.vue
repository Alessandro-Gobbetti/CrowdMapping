<template>
  <div>
    <Header />
    <!-- Updated Intro Section -->
    <section class="content">
      <div class="intro">
        <h1>Explore the Pulse of Your City</h1>
        <p>Real-time maps displaying crowd density, noise levels, and traffic flow. Plan your journeys smarter.</p>
      </div>
    </section>

    <!-- Toggle to switch between maps -->
    <div class="map-toggle">
      <label for="map-type">Select Map Type:</label>
      <select v-model="mapType" id="map-type">
        <option value="crowd">Crowd Map</option>
        <option value="noise">Noise Level Map</option>
        <option value="vehicles">Vehicles Map</option>
      </select>
    </div>

    <!-- Map container in a styled box -->
    <div class="map-box">
      <h2>{{ mapType === "crowd" ? "Crowd Map" : mapType === "noise" ? "Noise Map" : "Vehicles Map" }}</h2>
      <div id="map-container">
        <div id="map"></div>
      </div>
    </div>

    <!-- Section for graph -->
    <div class="graph-box">
      <h2>People Data Over Time</h2>
      
      <!-- Date Picker -->
      <input type="date" v-model="selectedDate" @change="filterDataByDate" />
      
      <canvas id="peopleGraph"></canvas>
    </div>
  </div>
</template>

<script>
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import Header from "./Header.vue"; // Relative path as both are in the same folder
import Chart from 'chart.js/auto';

export default {
  components: {
    Header,
  },

  name: "MapPage",
  data() {
    return {
      map: null,
      mapType: "crowd",
      crowdLayer: null,
      noiseLayer: null,
      vehiclesLayer: null,
      locations: [],
      selectedDate: "", // To store selected date
    };
  },
  async mounted() {
    this.initMap();
    await this.fetchData();
    this.displayGraph();  // Initially display the graph
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

    filterDataByDate() {
  const filteredLocations = this.locations.filter(location => {
    return location.date.startsWith(this.selectedDate); // Filter data by the selected date
  });

  // Destroy the existing chart if it exists
  if (this.peopleChart) {
    this.peopleChart.destroy();
  }

  // Create a new chart with the filtered data
  this.peopleChart = new Chart(document.getElementById("peopleGraph"), {
    type: "line",
    data: {
      labels: filteredLocations.map(location => location.date),
      datasets: [
        {
          label: "People",
          data: filteredLocations.map(location => location.people),
          borderColor: "red",
          fill: false,
          tension: 0.1,
        },
        {
          label: "Noise",
          data: filteredLocations.map(location => location.noise),
          borderColor: "blue",
          fill: false,
          tension: 0.1,
        },
        {
          label: "Vehicles",
          data: filteredLocations.map(location => location.vehicles),
          borderColor: "green",
          fill: false,
          tension: 0.1,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: "People, Noise, and Vehicles Data Over Time",
        },
        tooltip: {
          mode: "index",
          intersect: false,
        },
      },
      scales: {
        x: {
          title: {
            display: true,
            text: "Time",
          },
        },
        y: {
          title: {
            display: true,
            text: "Count/Level",
          },
        },
      },
    },
  });
},

    // Method to display the graph
    displayGraph(filteredData = this.locations) {
      // Wait for the fetchData function to populate this.locations
      this.$nextTick(() => {
        const labels = filteredData.map(location => location.date);
        const peopleData = filteredData.map(location => location.people);
        const noiseData = filteredData.map(location => location.noise);
        const vehiclesData = filteredData.map(location => location.vehicles);

        // Create the chart
        new Chart(document.getElementById("peopleGraph"), {
          type: "line",
          data: {
            labels: labels,
            datasets: [
              {
                label: "People",
                data: peopleData,
                borderColor: "red",
                fill: false,
                tension: 0.1,
              },
              {
                label: "Noise",
                data: noiseData,
                borderColor: "blue",
                fill: false,
                tension: 0.1,
              },
              {
                label: "Vehicles",
                data: vehiclesData,
                borderColor: "green",
                fill: false,
                tension: 0.1,
              },
            ],
          },
          options: {
            responsive: true,
            plugins: {
              title: {
                display: true,
                text: "People, Noise, and Vehicles Data Over Time",
              },
              tooltip: {
                mode: "index",
                intersect: false,
              },
            },
            scales: {
              x: {
                title: {
                  display: true,
                  text: "Time",
                },
              },
              y: {
                title: {
                  display: true,
                  text: "Count/Level",
                },
              },
            },
          },
        });
      });
    },

    // Add methods for adding markers and circles as in your original code...
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
        {direction: "top",
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
    mapType(newType) {
      this.updateMapView();
    },
  },
};
</script>


<style scoped>
/* Set a darker background for the entire page */
body {
  background-color: #033649; /* Darker shade similar to the intro box */
  color: #fff; /* White text for readability */
  margin: 0;
  font-family: Arial, sans-serif;
}

/* Intro section with a gradient background */
.intro {
  background: linear-gradient(to bottom right, #036564, #033649);
  padding: 20px;
  border-radius: 15px;
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
}

/* Content section styling */
.content {
  text-align: center;
  margin: 50px auto;
  color: #fff;
}

/* Map toggle section */
.map-toggle {
  text-align: center;
  margin: 20px 0;
}

/* Style for the dropdown */
#map-type {
  background-color: #036564; /* Darker background for dropdown */
  color: white; /* White text */
  font-size: 1rem;
  padding: 10px 20px;
  border-radius: 8px;
  border: 2px solid #028582; /* Light border for focus */
  cursor: pointer;
  appearance: none;
  transition: all 1.0s ease;
  width: 200px;
  margin: 0 auto;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Hover effect for dropdown */
#map-type:hover {
  background-color: #028582; /* Slightly lighter on hover */
  border-color: #026a6a;
}

/* Focus effect for dropdown */
#map-type:focus {
  outline: none;
  box-shadow: 0 0 10px rgba(0, 168, 255, 0.7);
  border-color: #00a8ff;
}

/* Map box with white background and shadows and hover transition effect */
.map-box {
  margin: 20px auto;
  padding: 15px;
  background: linear-gradient(to bottom right, #036564, #033649);
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  max-width: 90%;
  transition: all 0.5s ease;
}

.map-box:hover {
  background: linear-gradient(to bottom right, #048f84, #045164);
  transform: scale(1.05);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
}


/* Map box title */
.map-box h2 {
  text-align: center;
  font-size: 1.5rem;
  color: #333;
  margin-bottom: 15px;
}

/* Map container styles */
#map-container {
  height: 600px;
  width: 100%;
  border-radius: 10px;
  overflow: hidden;
}

#map {
  height: 100%;
  width: 100%;
}

/* Graph box style to match the map box */
.graph-box {
  margin: 20px auto;
  padding: 15px;
  background: linear-gradient(to bottom right, #036564, #033649);
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  max-width: 90%;
  transition: all 0.5s ease;
}

.graph-box:hover {
  background: linear-gradient(to bottom right, #048f84, #045164);
  transform: scale(1.05);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
}

/* Graph header styling */
.graph-box h2 {
  text-align: center;
  font-size: 1.5rem;
  color: #fff; /* White color for the header */
  margin-bottom: 15px;
}

/* Chart container */
canvas {
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  background-color: #fff; /* White background for the chart */
}

</style>
