document.addEventListener('DOMContentLoaded', () => {
    if (!document.getElementById('weekly-view')) return;

    let currentDate = new Date();
    currentDate.setHours(0, 0, 0, 0);

    const weeklyView = document.getElementById('weekly-view');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const todayBtn = document.getElementById('today-btn');
    const eventCount = document.getElementById('event-count');

    function isSameDay(d1, d2) {
        return d1.getFullYear() === d2.getFullYear() &&
               d1.getMonth() === d2.getMonth() &&
               d1.getDate() === d2.getDate();
    }
    
    function formatEventTime(event) {
        const start = new Date(event.start_time);
        const format = { hour: 'numeric', minute: 'numeric', hour12: true };
        return `${start.toLocaleTimeString([], format)}`;
    }

    const renderWeeklyGrid = (events) => {
        const grid = weeklyView.querySelector('.weekly-grid');
        grid.innerHTML = ''; // Clear previous content

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const startOfWeek = new Date(currentDate);
        startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());

        // Create Header
        const headerRow = document.createElement('div');
        headerRow.className = 'week-header-row';
        for (let i = 0; i < 7; i++) {
            const day = new Date(startOfWeek);
            day.setDate(startOfWeek.getDate() + i);
            const headerCell = document.createElement('div');
            headerCell.className = 'week-header-cell';
            if (isSameDay(day, today)) {
                headerCell.classList.add('today');
            }
            headerCell.textContent = day.toLocaleDateString('en-US', { weekday: 'short', month: 'numeric', day: 'numeric' });
            headerRow.appendChild(headerCell);
        }
        grid.appendChild(headerRow);

        // Create Body
        const bodyContainer = document.createElement('div');
        bodyContainer.className = 'week-body-container';
        
        const hourLabelsCol = document.createElement('div');
        hourLabelsCol.className = 'week-hour-labels';
        for (let hour = 7; hour <= 23; hour++) {
            const label = document.createElement('div');
            label.className = 'week-hour-label';
            label.textContent = `${hour % 12 === 0 ? 12 : hour % 12} ${hour < 12 ? 'AM' : 'PM'}`;
            hourLabelsCol.appendChild(label);
        }
        bodyContainer.appendChild(hourLabelsCol);

        const weekGrid = document.createElement('div');
        weekGrid.className = 'week-grid-body';

        for (let i = 0; i < 7; i++) {
            const day = new Date(startOfWeek);
            day.setDate(startOfWeek.getDate() + i);
            const dayColumn = document.createElement('div');
            dayColumn.className = 'week-day-column';

            for (let hour = 7; hour <= 23; hour++) {
                const hourCell = document.createElement('div');
                hourCell.className = 'week-cell';
                if (isSameDay(day, today)) {
                    hourCell.classList.add('today');
                }

                const hourEvents = events.filter(event => {
                    const eventDate = new Date(event.start_time);
                    return isSameDay(eventDate, day) && eventDate.getHours() === hour;
                });

                hourEvents.forEach(event => {
                    const eventDiv = document.createElement('div');
                    eventDiv.className = 'event';
                    eventDiv.setAttribute('onclick', `openEditEventModal(${JSON.stringify(event)})`);
                    eventDiv.textContent = event.title;

                    if (event.category && event.category.color) {
                        eventDiv.style.backgroundColor = event.category.color;
                        const r = parseInt(event.category.color.slice(1, 3), 16);
                        const g = parseInt(event.category.color.slice(3, 5), 16);
                        const b = parseInt(event.category.color.slice(5, 7), 16);
                        eventDiv.style.color = ((r * 299 + g * 587 + b * 114) / 1000) > 128 ? '#000' : '#FFF';
                    }
                    hourCell.appendChild(eventDiv);
                });
                dayColumn.appendChild(hourCell);
            }
            weekGrid.appendChild(dayColumn);
        }
        bodyContainer.appendChild(weekGrid);
        grid.appendChild(bodyContainer);
    };

    window.updateDateLabel = () => {
        const dateLabel = document.getElementById('current-date');
        const startOfWeek = new Date(currentDate);
        startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
        const endOfWeek = new Date(startOfWeek);
        endOfWeek.setDate(startOfWeek.getDate() + 6);

        dateLabel.textContent = `${startOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${endOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
    };

    window.fetchAndRenderEvents = async () => {
        try {
            const response = await fetch('/api/events/');
            const allEvents = await response.json();
            
            const startOfWeek = new Date(currentDate);
            startOfWeek.setHours(0,0,0,0);
            startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
            
            const endOfWeek = new Date(startOfWeek);
            endOfWeek.setDate(startOfWeek.getDate() + 7);

            const weekEvents = allEvents.filter(event => {
                const eventDate = new Date(event.start_time);
                return eventDate >= startOfWeek && eventDate < endOfWeek;
            });
            
            renderWeeklyGrid(weekEvents);
            window.updateDateLabel();
            eventCount.textContent = `${weekEvents.length} event${weekEvents.length !== 1 ? 's' : ''}`;

        } catch (error) {
            console.error("Failed to fetch events for weekly view:", error);
        }
    };
    
    prevBtn.addEventListener('click', () => {
        currentDate.setDate(currentDate.getDate() - 7);
        window.fetchAndRenderEvents();
    });

    nextBtn.addEventListener('click', () => {
        currentDate.setDate(currentDate.getDate() + 7);
        window.fetchAndRenderEvents();
    });

    todayBtn.addEventListener('click', () => {
        currentDate = new Date();
        currentDate.setHours(0, 0, 0, 0);
        window.fetchAndRenderEvents();
    });

    // Initial render
    window.fetchAndRenderEvents();
}); 