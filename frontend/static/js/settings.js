document.addEventListener('DOMContentLoaded', function() {
    const categoriesList = document.getElementById('categories-list');
    const addCategoryForm = document.getElementById('add-category-form');
    const newCategoryName = document.getElementById('new-category-name');
    const newCategoryColor = document.getElementById('new-category-color');
    const availableColors = document.getElementById('available-colors');

    // Load everything on page load
    fetchCategories();
    fetchAvailableColors();

    // Add category form handler
    addCategoryForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const name = newCategoryName.value.trim();
        const color = newCategoryColor.value;

        if (!name) {
            alert('Please enter a category name');
            return;
        }

        try {
            const response = await fetch('/api/categories/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, color }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create category');
            }

            // Clear form and refresh
            newCategoryName.value = '';
            newCategoryColor.value = '#BC13FE';
            fetchCategories();
            showNotification('Category created successfully!', 'success');
        } catch (error) {
            console.error('Error creating category:', error);
            showNotification(error.message, 'error');
        }
    });

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

    async function fetchAvailableColors() {
        try {
            const response = await fetch('/api/categories/colors');
            if (!response.ok) {
                throw new Error('Failed to fetch colors');
            }
            const data = await response.json();
            renderAvailableColors(data.colors);
        } catch (error) {
            console.error('Error fetching colors:', error);
        }
    }

    function renderCategories(categories) {
        categoriesList.innerHTML = '';
        if (categories.length === 0) {
            categoriesList.innerHTML = '<p class="text-gray-400">No categories found.</p>';
            return;
        }

        categories.forEach(category => {
            const categoryItem = document.createElement('div');
            categoryItem.className = 'category-item flex items-center justify-between p-3 bg-gray-700 rounded-lg border border-gray-600';
            
            // Category info
            const categoryInfo = document.createElement('div');
            categoryInfo.className = 'flex items-center space-x-3';
            
            const colorPreview = document.createElement('div');
            colorPreview.className = 'w-6 h-6 rounded border border-gray-500';
            colorPreview.style.backgroundColor = category.color;
            
            const categoryName = document.createElement('span');
            categoryName.className = 'font-semibold text-white';
            categoryName.textContent = category.name;
            
            const colorValue = document.createElement('span');
            colorValue.className = 'text-gray-400 text-sm';
            colorValue.textContent = category.color;
            
            categoryInfo.appendChild(colorPreview);
            categoryInfo.appendChild(categoryName);
            categoryInfo.appendChild(colorValue);

            // Actions
            const actions = document.createElement('div');
            actions.className = 'flex items-center space-x-2';

            // Edit button
            const editBtn = document.createElement('button');
            editBtn.className = 'px-3 py-1 bg-neon-blue text-black text-sm font-semibold rounded hover:bg-blue-400 transition-colors';
            editBtn.textContent = 'Edit';
            editBtn.onclick = () => editCategory(category);

            // Delete button
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'px-3 py-1 bg-neon-red text-black text-sm font-semibold rounded hover:bg-red-400 transition-colors';
            deleteBtn.textContent = 'Delete';
            deleteBtn.onclick = () => deleteCategory(category);

            actions.appendChild(editBtn);
            actions.appendChild(deleteBtn);

            categoryItem.appendChild(categoryInfo);
            categoryItem.appendChild(actions);
            categoriesList.appendChild(categoryItem);
        });
    }

    function renderAvailableColors(colors) {
        availableColors.innerHTML = '';
        colors.forEach(color => {
            const colorItem = document.createElement('div');
            colorItem.className = 'w-8 h-8 rounded border border-gray-500 cursor-pointer hover:scale-110 transition-transform';
            colorItem.style.backgroundColor = color;
            colorItem.title = color;
            colorItem.onclick = () => {
                newCategoryColor.value = color;
            };
            availableColors.appendChild(colorItem);
        });
    }

    async function editCategory(category) {
        const newName = prompt('Enter new name for category:', category.name);
        if (!newName || newName.trim() === '') return;

        const newColor = prompt('Enter new color (hex format):', category.color);
        if (!newColor) return;

        try {
            const response = await fetch(`/api/categories/${category.id}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    name: newName.trim(), 
                    color: newColor 
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to update category');
            }

            fetchCategories();
            showNotification('Category updated successfully!', 'success');
        } catch (error) {
            console.error('Error updating category:', error);
            showNotification(error.message, 'error');
        }
    }

    async function deleteCategory(category) {
        const confirmed = confirm(`Are you sure you want to delete the category "${category.name}"?`);
        if (!confirmed) return;

        try {
            const response = await fetch(`/api/categories/${category.id}/`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete category');
            }

            fetchCategories();
            showNotification('Category deleted successfully!', 'success');
        } catch (error) {
            console.error('Error deleting category:', error);
            showNotification(error.message, 'error');
        }
    }

    function showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 px-4 py-2 rounded-lg text-white font-semibold z-50 transition-all duration-300 ${
            type === 'success' ? 'bg-neon-green text-black' : 'bg-neon-red text-black'
        }`;
        notification.textContent = message;

        // Add to page
        document.body.appendChild(notification);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}); 