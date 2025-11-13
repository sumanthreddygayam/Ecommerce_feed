document.addEventListener('DOMContentLoaded', () => {
    const itemFeed = document.getElementById('item-feed');
    const searchBar = document.getElementById('search-bar');
    let allData = {};

    // Function to log an action to the backend
    async function logAction(action, detail) {
        try {
            await fetch('/api/log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: action,
                    detail: detail,
                    clientTimestamp: new Date().toISOString()
                }),
            });
            console.log(`Logged: ${action} - ${JSON.stringify(detail)}`);
        } catch (error) {
            console.error('Failed to log action:', error);
        }
    }

    // Function to render items on the page
    function renderItems(data) {
        itemFeed.innerHTML = '';

        for (const category in data) {
            const items = data[category];
            const categoryBlock = document.createElement('div');
            categoryBlock.className = 'category-block';

            const title = document.createElement('h2');
            title.className = 'category-title';
            title.textContent = category;
            categoryBlock.appendChild(title);
            
            const itemsGrid = document.createElement('div');
            itemsGrid.className = 'items-grid';

            items.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'item';
                // --- THIS HTML IS UPDATED ---
                itemDiv.innerHTML = `
                    <p><strong>Order #:</strong> ${item.order_number}</p>
                    <p><strong>Product:</strong> ${item.product}</p>
                    <p><strong>Brand:</strong> ${item.brand}</p>
                    <div class="item-actions">
                        <button class="cancel">Cancel</button>
                        <button class="reorder">Reorder</button>
                        <button class="seen">Seen</button>
                    </div>
                `;
                
                // --- THIS DATA OBJECT IS UPDATED FOR LOGGING ---
                const itemDetail = {
                    category: category,
                    order_number: item.order_number,
                    product: item.product,
                    brand: item.brand
                };

                itemDiv.querySelector('.cancel').addEventListener('click', () => logAction('Cancel', itemDetail));
                itemDiv.querySelector('.reorder').addEventListener('click', () => logAction('Reorder', itemDetail));
                itemDiv.querySelector('.seen').addEventListener('click', () => logAction('Seen', itemDetail));

                itemsGrid.appendChild(itemDiv);
            });
            
            categoryBlock.appendChild(itemsGrid);
            itemFeed.appendChild(categoryBlock);
        }
    }

    // Search bar functionality remains the same
    searchBar.addEventListener('keyup', (e) => {
        const searchQuery = e.target.value.toLowerCase();
        const filteredData = {};
        for (const category in allData) {
            if (category.toLowerCase().includes(searchQuery)) {
                filteredData[category] = allData[category];
            }
        }
        renderItems(filteredData);
    });

    // Initial fetch of items from the backend
    async function fetchItems() {
        try {
            const response = await fetch('/api/items'); 
            allData = await response.json();
            renderItems(allData);
        } catch (error) {
            console.error('Failed to fetch items:', error);
            itemFeed.innerHTML = '<p>Error loading item data.</p>';
        }
    }

    fetchItems();
});