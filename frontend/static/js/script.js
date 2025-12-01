const words = ["inspiration.", "passion.", "motivation."];
let i = 0;

setInterval(() => {
  i = (i + 1) % words.length;
  document.getElementById("word").textContent = words[i];
}, 1500);

