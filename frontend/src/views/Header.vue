<template>
    <header class="header">
      <div class="logo">Crowd Mapping</div>
      <nav>
        <ul>
          <li><a href="#">Home</a></li>
          <li><a href="#">About</a></li>
          <li><a href="#">Contact</a></li>
        </ul>
      </nav>
    </header>
  </template>
  
  <script>
  export default {
    name: "Header",
  };
  </script>
  
  <style scoped>
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: #1b252b;
    padding: 10px 20px;
    color: white;
  }
  
  .logo {
    font-size: 1.5em;
    font-weight: bold;
  }
  
  nav ul {
    list-style: none;
    display: flex;
    gap: 15px;
  }
  
  nav a {
    text-decoration: none;
    color: white;
    font-size: 1em;
  }
  
  nav a:hover {
    text-decoration: underline;
  }
  </style>
  