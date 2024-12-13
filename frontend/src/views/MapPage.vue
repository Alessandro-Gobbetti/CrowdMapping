<template>
  <div class="w-100 align-center text-center body">
    <div class="h-100 w-100 align-center text-center d-flex flex-column mt-16">
      <h1 class="cap">Crowd Mapping</h1>
      <p class="w-50 text mb-2 mt-2">
        Some text
      </p>
    </div>
  </div>
</template>

<script>
import { defineComponent } from "vue";

export default defineComponent({
  name: "map",
  components: {},

  data: () => ({
  }),

  created() {
    // called when the component is created
    // has access to `this` component instance.
  },

  beforeRouteLeave(to, from, next) {
    // called when the route that renders this component is about to
    // be navigated away from.
    // has access to `this` component instance.
    // show alert
    this.$dialog
      .confirm("Do you want to proceed?")
      .then(function () {
        next();
      })
      .catch(function () {
        next(false);
      });
  },

  methods: {

  },
});
</script>

<style scoped>
.cover {
  height: 20vh;
  object-fit: cover;
}

.text {
  text-align: justify;
  text-justify: inter-word;
  font-size: 1.2rem;
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-gap: 1rem;
}

.answer-button {
  text-transform: none;
  font-size: 3rem;
}

h1 {
  font-size: 4rem;
}

h2.cap {
  font-size: 2rem;
}

.pt-20 {
  padding-top: 20vh;
}

.cap {
  font-variant: small-caps;
  text-transform: capitalize;
}
</style>
