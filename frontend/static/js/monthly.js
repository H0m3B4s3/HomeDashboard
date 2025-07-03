document.addEventListener('DOMContentLoaded', () => {
    if (!document.getElementById('monthly-view')) return;

    let currentDate = new Date();
    currentDate.setHours(0, 0, 0, 0);

    const monthlyView = document.getElementById('monthly-view');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const todayBtn = document.getElementById('today-btn');
    const eventCount = document.getElementById('event-count');

    function isSameDay(d1, d2) {
        return d1.getFullYear() === d2.getFullYear() &&
               d1.getMonth() === d2.getMonth() &&
               d1.getDate() === d2.getDate();
    }

    const renderMonthlyGrid = (events) => {
        const grid = monthlyView.querySelector('.monthly-grid');
        grid.innerHTML = '';

        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();
        const firstDayOfMonth = new Date(year, month, 1);
        const lastDayOfMonth = new Date(year, month + 1, 0);
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // Header
        ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].forEach(day => {
            const headerCell = document.createElement('div');
            headerCell.className = 'month-header-cell';
            headerCell.textContent = day;
            grid.appendChild(headerCell);
        });

        // Days from previous month
        const prevMonthLastDay = new Date(year, month, 0);
        for (let i = firstDayOfMonth.getDay(); i > 0; i--) {
            const day = new Date(prevMonthLastDay);
            day.setDate(prevMonthLastDay.getDate() - i + 1);
            const cell = document.createElement('div');
            cell.className = 'month-cell other-month';
            cell.innerHTML = `<div class="month-day-number">${day.getDate()}</div>`;
            grid.appendChild(cell);
        }

        // Days of current month
        for (let i = 1; i <= lastDayOfMonth.getDate(); i++) {
            const day = new Date(year, month, i);
            const cell = document.createElement('div');
            cell.className = 'month-cell';
            if (isSameDay(day, today)) {
                cell.classList.add('today');
            }
            cell.innerHTML = `<div class="month-day-number">${i}</div>`;
            
            const dayEvents = events.filter(event => isSameDay(new Date(event.start_time), day));
            const eventsContainer = document.createElement('div');
            eventsContainer.className = 'events-container';
            dayEvents.forEach(event => {
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
                eventsContainer.appendChild(eventDiv);
            });
            cell.appendChild(eventsContainer);
            grid.appendChild(cell);
        }

        // Days from next month
        const lastDayOfWeek = lastDayOfMonth.getDay();
        for (let i = 1; i < 7 - lastDayOfWeek; i++) {
             const day = new Date(year, month + 1, i);
            const cell = document.createElement('div');
            cell.className = 'month-cell other-month';
            cell.innerHTML = `<div class="month-day-number">${day.getDate()}</div>`;
            grid.appendChild(cell);
        }
    };

    window.updateDateLabel = () => {
        const dateLabel = document.getElementById('current-date');
        dateLabel.textContent = currentDate.toLocaleDateString('en-US', {
            month: 'long', year: 'numeric'
        });
    };

    window.fetchAndRenderEvents = async () => {
        try {
            const response = await fetch('/api/events/');
            const allEvents = await response.json();
            
            const year = currentDate.getFullYear();
            const month = currentDate.getMonth();

            const monthEvents = allEvents.filter(event => {
                const eventDate = new Date(event.start_time);
                return eventDate.getFullYear() === year && eventDate.getMonth() === month;
            });
            
            renderMonthlyGrid(monthEvents);
            window.updateDateLabel();
            eventCount.textContent = `${monthEvents.length} event${monthEvents.length !== 1 ? 's' : ''}`;

        } catch (error) {
            console.error("Failed to fetch events for monthly view:", error);
        }
    };
    
    prevBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        window.fetchAndRenderEvents();
    });

    nextBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
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