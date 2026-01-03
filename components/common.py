"""Common UI components and utilities."""

from nicegui import ui, app

RU_LOCALE = {
    'days': 'Воскресенье_Понедельник_Вторник_Среда_Четверг_Пятница_Суббота'.split('_'),
    'daysShort': 'Вс_Пн_Вт_Ср_Чт_Пт_Сб'.split('_'),
    'months': 'Январь_Февраль_Март_Апрель_Май_Июнь_Июль_Август_Сентябрь_Октябрь_Ноябрь_Декабрь'.split('_'),
    'monthsShort': 'Янв_Фев_Мар_Апр_Май_Июн_Июл_Авг_Сен_Окт_Ноя_Дек'.split('_'),
    'firstDayOfWeek': 1,
    'format24h': True,
    'pluralDay': 'дней'
}

def setup_dark_mode():
    """Setup robust dark mode synchronization between Quasar and Tailwind."""
    dark = ui.dark_mode()
    dark.bind_value(app.storage.user, 'dark_mode')
    
    # Robust sync script
    ui.add_head_html('''
        <script>
        (function() {
            function syncDark() {
                const isDark = document.body.classList.contains('body--dark');
                if (isDark) {
                    document.documentElement.classList.add('dark');
                } else {
                    document.documentElement.classList.remove('dark');
                }
            }
            
            // 1. Observer for dynamic changes
            const observer = new MutationObserver(syncDark);
            observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });
            
            // 2. Initial check
            document.addEventListener('DOMContentLoaded', syncDark);
            
            // 3. Periodic safeguard (for slow hydration)
            setInterval(syncDark, 1000);
        })();
        </script>
    ''')
    
    return dark
