// Create the js directory and sync.js file if missing
// Handles the Sync Now button and calls the backend sync API

document.addEventListener('DOMContentLoaded', async () => {
    // Auto-sync from iCloud on every page load
    const syncStatus = document.getElementById('sync-status');
    if (syncStatus) syncStatus.textContent = 'Syncing from iCloud...';
    try {
        const response = await fetch('/api/calendar/sync', { method: 'POST' });
        const result = await response.json();
        if (response.ok) {
            if (syncStatus) syncStatus.textContent = result.message || 'Sync successful!';
        } else {
            throw new Error(result.detail || 'Sync failed');
        }
    } catch (error) {
        console.error('Auto-sync failed:', error);
        if (syncStatus) syncStatus.textContent = `Error: ${error.message}`;
    }
    // After sync, refresh events if available
    if (window.fetchAndRenderEvents) {
        window.fetchAndRenderEvents();
    }

    const syncNowBtn = document.getElementById('sync-now-btn');
    const syncUpBtn = document.getElementById('sync-up-btn');
    const lastSync = document.getElementById('last-sync');

    if (syncNowBtn) {
        syncNowBtn.addEventListener('click', async () => {
            syncStatus.textContent = 'Syncing from iCloud...';
            try {
                const response = await fetch('/api/calendar/sync', { method: 'POST' });
                const result = await response.json();

                if (response.ok) {
                    syncStatus.textContent = result.message || 'Sync successful!';
                    if (window.fetchAndRenderEvents) {
                        window.fetchAndRenderEvents(); // Refresh view
                    }
                } else {
                    throw new Error(result.detail || 'Sync failed');
                }
            } catch (error) {
                console.error('Sync failed:', error);
                syncStatus.textContent = `Error: ${error.message}`;
            }
        });
    }

    if (syncUpBtn) {
        syncUpBtn.addEventListener('click', async () => {
            syncStatus.textContent = 'Pushing to iCloud...';
            try {
                const response = await fetch('/api/calendar/sync-up', { method: 'POST' });
                const result = await response.json();

                if (response.ok) {
                    console.log('Upward sync success:', result);
                    syncStatus.textContent = result.message || 'Upward sync successful!';
                    // Optionally show count or list in console
                } else {
                    console.error('Upward sync error response:', result);
                    throw new Error(result.detail || result.message || 'Upward sync failed');
                }
            } catch (error) {
                console.error('Upward sync failed:', error);
                syncStatus.textContent = `Error: ${error.message}`;
            }
        });
    }
}); 