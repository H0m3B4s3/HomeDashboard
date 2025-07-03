document.addEventListener('DOMContentLoaded', function () {
    // --- STATE ---
    let categories = [];
    let allEvents = []; // Cache for all events

    // --- DOM ELEMENTS ---
    const newEventBtn = document.getElementById('new-event-btn');
    const newEventModal = document.getElementById('new-event-modal');
    const newEventForm = document.getElementById('new-event-form');
    const newEventModalClose = document.getElementById('new-event-modal-close');
    const newEventCancelBtn = document.getElementById('new-event-cancel');
    const newEventCategorySelect = document.getElementById('event-category');

    const editEventModal = document.getElementById('event-modal');
    const editEventForm = document.getElementById('edit-event-form');
    const editEventModalClose = document.getElementById('modal-close');
    const deleteEventBtn = document.getElementById('delete-event-btn');
    const editEventCategorySelect = document.getElementById('edit-event-category');

    // --- API & UTILITY FUNCTIONS ---

    const fetchCategories = async () => {
        if (categories.length > 0) return; // Don't refetch if already loaded
        try {
            const response = await fetch('/api/categories/');
            if (!response.ok) throw new Error('Failed to fetch categories');
            categories = await response.json();
        } catch (error) {
            console.error('Error fetching categories:', error);
            categories = []; // Reset on error
        }
    };

    const populateCategoryDropdown = async (selectElement) => {
        await fetchCategories();
        selectElement.innerHTML = ''; // Clear existing options
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.id;
            option.textContent = category.name;
            selectElement.appendChild(option);
        });
    };

    const toLocalISOString = (date) => {
        const dt = new Date(date);
        dt.setMinutes(dt.getMinutes() - dt.getTimezoneOffset());
        return dt.toISOString().slice(0, 16);
    };

    // --- MODAL MANAGEMENT ---

    const openNewEventModal = () => {
        newEventForm.reset();
        const now = new Date();
        document.getElementById('start-time').value = toLocalISOString(now);
        now.setHours(now.getHours() + 1);
        document.getElementById('end-time').value = toLocalISOString(now);
        populateCategoryDropdown(newEventCategorySelect);
        newEventModal.style.display = 'block';
    };

    const closeNewEventModal = () => newEventModal.style.display = 'none';
    const closeEditEventModal = () => editEventModal.style.display = 'none';

    const openEditEventModal = async (event) => {
        editEventForm.reset();
        await populateCategoryDropdown(editEventCategorySelect);

        document.getElementById('edit-event-id').value = event.id;
        document.getElementById('edit-event-title').value = event.title;
        if (event.category && event.category.id) {
            editEventCategorySelect.value = event.category.id;
        }
        document.getElementById('edit-start-time').value = toLocalISOString(event.start_time);
        document.getElementById('edit-end-time').value = toLocalISOString(event.end_time);
        document.getElementById('edit-event-location').value = event.location || '';
        document.getElementById('edit-event-description').value = event.description || '';

        editEventModal.style.display = 'block';
    };

    // --- FORM SUBMISSION HANDLERS ---

    const handleNewEventSubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const eventData = Object.fromEntries(formData.entries());
        eventData.category_id = parseInt(eventData.category_id, 10);

        try {
            const response = await fetch('/api/events/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(eventData),
            });
            if (response.ok) {
                closeNewEventModal();
                window.fetchAndRenderEvents(); // Use global function
            } else {
                const error = await response.json();
                alert(`Error: ${error.detail || 'Could not create event.'}`);
            }
        } catch (error) {
            console.error('Failed to submit event:', error);
            alert('An unexpected error occurred.');
        }
    };

    const handleEditEventSubmit = async (e) => {
        e.preventDefault();
        const eventId = document.getElementById('edit-event-id').value;
        const formData = new FormData(editEventForm);
        const data = Object.fromEntries(formData.entries());
        data.category_id = parseInt(data.category_id, 10);

        try {
            const response = await fetch(`/api/events/${eventId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            if (response.ok) {
                closeEditEventModal();
                window.fetchAndRenderEvents(); // Use global function
            } else {
                const error = await response.json();
                alert(`Error: ${error.detail || 'Could not update event.'}`);
            }
        } catch (error) {
            console.error('Error updating event:', error);
            alert('An unexpected error occurred.');
        }
    };

    const handleDeleteEvent = async () => {
        const eventId = document.getElementById('edit-event-id').value;
        if (!confirm('Are you sure you want to delete this event?')) return;

        try {
            const response = await fetch(`/api/events/${eventId}`, { method: 'DELETE' });
            if (response.ok) {
                closeEditEventModal();
                window.fetchAndRenderEvents(); // Use global function
            } else {
                const error = await response.json();
                alert(`Error: ${error.detail || 'Could not delete event.'}`);
            }
        } catch (error) {
            console.error('Error deleting event:', error);
            alert('An unexpected error occurred.');
        }
    };

    // --- EVENT LISTENERS ---
    if (newEventBtn) newEventBtn.addEventListener('click', openNewEventModal);
    if (newEventModalClose) newEventModalClose.addEventListener('click', closeNewEventModal);
    if (newEventCancelBtn) newEventCancelBtn.addEventListener('click', closeNewEventModal);
    if (newEventForm) newEventForm.addEventListener('submit', handleNewEventSubmit);

    if (editEventModalClose) editEventModalClose.addEventListener('click', closeEditEventModal);
    if (editEventForm) editEventForm.addEventListener('submit', handleEditEventSubmit);
    if (deleteEventBtn) deleteEventBtn.addEventListener('click', handleDeleteEvent);

    window.addEventListener('click', (event) => {
        if (event.target === newEventModal) closeNewEventModal();
        if (event.target === editEventModal) closeEditEventModal();
    });
    
    // --- GLOBAL FUNCTIONS for views to use ---
    
    // Placeholder functions that will be defined by view-specific scripts
    window.fetchAndRenderEvents = () => console.warn("fetchAndRenderEvents is not defined for this view.");
    window.updateDateLabel = () => console.warn("updateDateLabel is not defined for this view.");
    
    // openEditEventModal is attached to the window so that event handlers in HTML can call it.
    window.openEditEventModal = openEditEventModal;
});
