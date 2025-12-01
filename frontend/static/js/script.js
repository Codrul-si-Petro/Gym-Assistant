const text = document.querySelector('.text');
text.innerHTML = text.textContent.replace(/\S/g, "<span class='letter'>$&</span>");

anime.timeline()
  .add({
    targets: '.letter',
    opacity: [0, 1],
    translateY: [20, 0],
    easing: "easeOutExpo",
    duration: 500,
    delay: anime.stagger(50)
  });