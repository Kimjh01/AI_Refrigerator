document.querySelector('.fixed-button').addEventListener('click', function() {
    const popupList = document.getElementById('popup-list');
    popupList.classList.toggle('show');
  });
  
  document.querySelectorAll('.popup-list li').forEach(function(item) {
    item.addEventListener('click', function() {
      const link = this.getAttribute('data-link');
      window.location.href = link;
    });
  });