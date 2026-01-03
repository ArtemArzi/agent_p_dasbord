"""User Management Page."""
from nicegui import ui, app
from auth import require_auth
from components.layout import page_layout
from data import get_all_users, create_user, delete_user, get_tenants

@ui.page("/users")
@require_auth()
async def users_page():
    # Security check: only super_admin
    if app.storage.user.get("role") != "super_admin":
        ui.navigate.to("/overview")
        return

    async def create_new_user():
        if not email.value or not password.value or not first_name.value:
            ui.notify("Заполните обязательные поля (Email, Пароль, Имя)", type="warning")
            return
            
        data = {
            "email": email.value,
            "password": password.value, # Will be hashed in data.py
            "first_name": first_name.value,
            "last_name": last_name.value,
            "role": role.value,
            "active": True
        }
        
        # Add tenant_id if selected
        if tenant.value:
             data["tenant_id"] = tenant.value
        elif role.value != "super_admin":
             ui.notify("Для этой роли необходимо выбрать Салон", type="warning")
             return
        
        success, msg = create_user(data)
        if success:
            ui.notify("Пользователь создан успешно!", type="positive")
            dialog.close()
            # Clear form
            email.value = ""
            password.value = ""
            first_name.value = ""
            last_name.value = ""
            await refresh_table()
        else:
            ui.notify(f"Ошибка создания: {msg}", type="negative")

    async def delete_handler(e):
        user_id = e.args
        if delete_user(user_id):
            ui.notify("Пользователь удален", type="positive")
            await refresh_table()
        else:
            ui.notify("Ошибка при удалении", type="negative")

    async def refresh_table():
        rows = get_all_users()
        # Enrich tenant names if possible, but simplest is showing ID or just basic info
        table.rows = rows
        table.update()

    # Layout
    with page_layout("Управление сотрудниками"):
        # Header + Add Button
        with ui.row().classes("w-full justify-between items-center mb-6"):
            with ui.column().classes("gap-0"):
                ui.label("Сотрудники и Доступы").style("font-family: 'Outfit', sans-serif").classes("text-3xl font-light text-white")
                ui.label("Управление пользователями системы").classes("text-gray-400 text-sm")
            
            ui.button("Добавить сотрудника", icon="add", on_click=lambda: dialog.open()) \
                .classes("bg-amber-400 text-gray-900 rounded-xl px-4")

        # Users Table
        columns = [
            {'name': 'first_name', 'label': 'Имя', 'field': 'first_name', 'sortable': True, 'align': 'left'},
            {'name': 'last_name', 'label': 'Фамилия', 'field': 'last_name', 'sortable': True, 'align': 'left'},
            {'name': 'email', 'label': 'Email', 'field': 'email', 'sortable': True, 'align': 'left'},
            {'name': 'role', 'label': 'Роль', 'field': 'role', 'sortable': True, 'align': 'left'},
            {'name': 'tenant_id', 'label': 'Tenant ID', 'field': 'tenant_id', 'sortable': True, 'align': 'left', 'classes': 'text-xs text-gray-500'},
            {'name': 'actions', 'label': '', 'field': 'actions', 'align': 'center'},
        ]
        
        table = ui.table(columns=columns, rows=[], pagination=10).classes("w-full glass-card")
        
        # Add delete button slot
        table.add_slot('body-cell-actions', r'''
            <q-td :props="props">
                <q-btn icon="delete_outline" color="negative" flat round dense 
                    @click="$parent.$emit('delete', props.row.id)">
                    <q-tooltip>Удалить пользователя</q-tooltip>
                </q-btn>
            </q-td>
        ''')
        table.on('delete', delete_handler)
        
        await refresh_table()

        # Create User Dialog
        with ui.dialog() as dialog, ui.card().classes("w-full max-w-lg bg-gray-900 border border-gray-700 p-6 rounded-2xl"):
            ui.label("Новый сотрудник").style("font-family: 'Outfit', sans-serif").classes("text-2xl mb-6 text-white text-center w-full")
            
            with ui.column().classes("w-full gap-4"):
                email = ui.input("Email *").classes("w-full").props("outlined dark")
                password = ui.input("Пароль *", password=True).classes("w-full").props("outlined dark")
                
                with ui.row().classes("w-full gap-4"):
                    first_name = ui.input("Имя *").classes("w-full flex-1").props("outlined dark")
                    last_name = ui.input("Фамилия").classes("w-full flex-1").props("outlined dark")
                
                role = ui.select(
                    ["super_admin", "admin", "staff"], 
                    value="staff", label="Роль *"
                ).classes("w-full").props("outlined dark options-dense")
                
                ui.separator().classes("bg-gray-700 my-2")
                
                # Fetch tenants for select
                tenants_list = get_tenants()
                tenant_options = {t['id']: t['name'] for t in tenants_list}
                tenant = ui.select(tenant_options, label="Салон (Tenant)", clearable=True).classes("w-full").props("outlined dark options-dense")
                
                with ui.row().classes("w-full justify-end gap-4 mt-6"):
                    ui.button("Отмена", on_click=dialog.close).props("flat color=grey")
                    ui.button("Создать сотрудника", on_click=create_new_user).classes("bg-amber-400 text-gray-900 rounded-lg px-6")
