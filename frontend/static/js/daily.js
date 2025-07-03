document.addEventListener('DOMContentLoaded', () => {
    if (!document.getElementById('daily-view')) return;

    let currentDate = new Date();
    currentDate.setHours(0, 0, 0, 0);

    const dailyView = document.getElementById('daily-view');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const todayBtn = document.getElementById('today-btn');
    const eventCount = document.getElementById('event-count');
    
    function isSameDay(d1, d2) {
        return d1.getFullYear() === d2.getFullYear() &&
               d1.getMonth() === d2.getMonth() &&
               d1.getDate() === d2.getDate();
    }
    
    function formatHour(hour) {
        const ampm = hour < 12 ? 'AM' : 'PM';
        const displayHour = hour % 12 === 0 ? 12 : hour % 12;
        return `${displayHour}:00 ${ampm}`;
    }
    
    function formatEventTime(event) {
        const start = new Date(event.start_time);
        const end = new Date(event.end_time);
        const format = { hour: 'numeric', minute: 'numeric', hour12: true };
        return `${start.toLocaleTimeString([], format)} - ${end.toLocaleTimeString([], format)}`;
    }

    const renderDailyGrid = (events) => {
        const grid = dailyView.querySelector('.daily-grid');
        grid.innerHTML = '';

        for (let hour = 7; hour <= 23; hour++) {
            const row = document.createElement('div');
            row.className = 'hour-row';
            const label = document.createElement('div');
            label.className = 'hour-label';
            label.textContent = formatHour(hour);
            row.appendChild(label);

            const slot = document.createElement('div');
            slot.className = 'hour-slot';
            
            const eventsWrapper = document.createElement('div');
            eventsWrapper.className = 'events-wrapper';
            
            const hourEvents = events.filter(e => new Date(e.start_time).getHours() === hour);

            // If multiple events overlap this hour, lay them out horizontally
            const totalEvents = hourEvents.length;
            if (totalEvents > 1) {
                eventsWrapper.style.display = 'flex';
                eventsWrapper.style.flexDirection = 'row';
                eventsWrapper.style.gap = '4px';
            }

            hourEvents.forEach((event, idx) => {
                const eventDiv = document.createElement('div');
                eventDiv.className = 'event';
                eventDiv.setAttribute('onclick', `openEditEventModal(${JSON.stringify(event)})`);
                
                if (totalEvents > 1) {
                    const segment = 100 / Math.min(totalEvents, 4);
                    eventDiv.style.flex = `0 0 calc(${segment}% - 4px)`;
                    eventDiv.style.width = 'auto';
                    eventDiv.classList.add('compact');
                    eventDiv.textContent = `${event.title} (${formatEventTime(event)})`;
                } else {
                    eventDiv.innerHTML = `
                        <div class="event-title">${event.title}</div>
                        <div class="event-time">${formatEventTime(event)}</div>
                    `;
                }
                
                if (event.category && event.category.color) {
                    eventDiv.style.backgroundColor = event.category.color;
                    // basic contrast check
                    const r = parseInt(event.category.color.slice(1, 3), 16);
                    const g = parseInt(event.category.color.slice(3, 5), 16);
                    const b = parseInt(event.category.color.slice(5, 7), 16);
                    eventDiv.style.color = ((r * 299 + g * 587 + b * 114) / 1000) > 128 ? '#000' : '#FFF';
                }
                
                eventsWrapper.appendChild(eventDiv);
            });
            
            slot.appendChild(eventsWrapper);
            row.appendChild(slot);
            grid.appendChild(row);
        }
    };

    window.updateDateLabel = () => {
        const dateLabel = document.getElementById('current-date');
        dateLabel.textContent = currentDate.toLocaleDateString('en-US', {
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
        });
    };

    window.fetchAndRenderEvents = async () => {
        try {
            const response = await fetch('/api/events/');
            const allEvents = await response.json();
            const dayEvents = allEvents.filter(event => isSameDay(new Date(event.start_time), currentDate));
            
            renderDailyGrid(dayEvents);
            window.updateDateLabel();
            eventCount.textContent = `${dayEvents.length} event${dayEvents.length !== 1 ? 's' : ''}`;

        } catch (error) {
            console.error("Failed to fetch events for daily view:", error);
        }
    };

    prevBtn.addEventListener('click', () => {
        currentDate.setDate(currentDate.getDate() - 1);
        window.fetchAndRenderEvents();
    });

    nextBtn.addEventListener('click', () => {
        currentDate.setDate(currentDate.getDate() + 1);
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