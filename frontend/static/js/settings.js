document.addEventListener('DOMContentLoaded', function() {
    const categoriesList = document.getElementById('categories-list');

    async function fetchCategories() {
        try {
            const response = await fetch('/api/categories/');
            if (!response.ok) {
                throw new Error('Failed to fetch categories');
            }
            const categories = await response.json();
            renderCategories(categories);
        } catch (error) {
            console.error('Error fetching categories:', error);
            categoriesList.innerHTML = '<p class="text-red-500">Error loading categories.</p>';
        }
    }

    function renderCategories(categories) {
        categoriesList.innerHTML = '';
        if (categories.length === 0) {
            categoriesList.innerHTML = '<p>No categories found.</p>';
            return;
        }

        categories.forEach(category => {
            const categoryItem = document.createElement('div');
            categoryItem.className = 'category-item flex items-center justify-between p-2 border rounded-lg';
            
            const categoryName = document.createElement('span');
            categoryName.className = 'font-semibold';
            categoryName.textContent = category.name;
            
            const colorPickerContainer = document.createElement('div');
            colorPickerContainer.className = 'flex items-center space-x-2';

            const colorInput = document.createElement('input');
            colorInput.type = 'color';
            colorInput.value = category.color;
            colorInput.className = 'w-10 h-10 p-0 border-none';

            colorInput.addEventListener('change', (event) => {
                updateCategoryColor(category.id, event.target.value);
            });

            const colorValue = document.createElement('span');
            colorValue.textContent = category.color;

            colorPickerContainer.appendChild(colorInput);
            colorPickerContainer.appendChild(colorValue);

            categoryItem.appendChild(categoryName);
            categoryItem.appendChild(colorPickerContainer);
            categoriesList.appendChild(categoryItem);
        });
    }

    async function updateCategoryColor(categoryId, newColor) {
        try {
            const response = await fetch(`/api/categories/${categoryId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ color: newColor }),
            });

            if (!response.ok) {
                throw new Error('Failed to update color');
            }
            // Re-fetch to show updated state and confirm change
            fetchCategories(); 
        } catch (error) {
            console.error('Error updating category color:', error);
            alert('Failed to update color. Please try again.');
        }
    }

    fetchCategories();
}); 