fetch('/previous_searches_data/')
  .then(response => response.json())
  .then(data => {
        const topics = data.topics;
        const carouselInner = document.querySelector('.carousel-inner');
        const loadingSpinner = document.getElementById('loading-spinner');
        const carouselIndicators = document.querySelector('.carousel-indicators');
        let imagesLoaded = 0;
        const totalImages = topics.length;
        const chunkSize = 4;
        const numChunks = Math.ceil(topics.length / chunkSize);

        for (let i = 0; i < numChunks; i++) {
            const carouselItem = document.createElement('div');
            carouselItem.classList.add('carousel-item');
            if (i === 0) {
                carouselItem.classList.add('active');
            }

            const indicator = document.createElement('button');
            indicator.type = 'button';
            indicator.setAttribute('data-bs-target', '#search-results-carousel');
            indicator.setAttribute('data-bs-slide-to', i.toString());
            indicator.setAttribute('aria-label', `Slide ${i + 1}`);
            if (i === 0) {
                indicator.classList.add('active');
                indicator.setAttribute('aria-current', 'true');
            }
            carouselIndicators.appendChild(indicator);

            const row = document.createElement('div');
            row.classList.add('row', 'mt-4', 'row-cols-1', 'row-cols-md-2', 'row-cols-lg-4', 'g-4');

            const chunk = topics.slice(i * chunkSize, (i + 1) * chunkSize);

            chunk.forEach((topic) => {
                const col = document.createElement('div');
                col.classList.add('col');

                const card = document.createElement('div');
                card.classList.add('card', 'h-100');

                const img = document.createElement('img');
                img.src = "http://localhost:8080/" + topic.imageUrl;
                img.classList.add('card-img-top', 'img-fluid', 'img-container');
                img.alt = topic.title;
                img.onload = () => {
                    imagesLoaded++;
                    if (imagesLoaded === totalImages) {
                        if (loadingSpinner) {
                            loadingSpinner.style.display = 'none';
                        }
                    }
                };

                const cardBody = document.createElement('div');
                cardBody.classList.add('card-body');

                const cardTitle = document.createElement('h5');
                cardTitle.classList.add('card-title', 'text-black');
                cardTitle.textContent = topic.title;

                const cardText = document.createElement('p');
                cardText.classList.add('card-text', 'text-muted', 'text-content');
                cardText.textContent = topic.description;

                cardBody.appendChild(cardTitle);
                cardBody.appendChild(cardText);
                card.appendChild(img);
                card.appendChild(cardBody);
                col.appendChild(card);
                row.appendChild(col);
            });
            carouselItem.appendChild(row);
            carouselInner.appendChild(carouselItem);
        }
    })
    .catch(error => console.error('Error loading data:', error));
