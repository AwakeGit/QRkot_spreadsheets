from datetime import datetime

from aiogoogle import Aiogoogle

from app.core.config import settings

FORMAT = "%Y/%m/%d %H:%M:%S"
SPREADSHEETS_API_VERSION = "v4"
DRIVE_API_VERSION = "v3"


async def spreadsheets_create(wrapper_services: Aiogoogle) -> str:
    """Создание таблицы."""
    service = await wrapper_services.discover(
        "sheets",
        SPREADSHEETS_API_VERSION)
    spreadsheet_body = {
        "properties": {"title": "Инвестирование", "locale": "ru_RU"},
        "sheets": [
            {
                "properties": {
                    "sheetType": "GRID",
                    "sheetId": 0,
                    "title": "Отчет",
                    "gridProperties": {"rowCount": 20, "columnCount": 4},
                }
            }
        ],
    }
    response = await wrapper_services.as_service_account(
        service.spreadsheets.create(json=spreadsheet_body)
    )
    spreadsheet_id = response["spreadsheetId"]
    return spreadsheet_id


async def set_user_permissions(
        spreadsheet_id: str, wrapper_services: Aiogoogle
) -> None:
    """Добавление пользователю разрешений на редактирование таблицы."""
    permissions_body = {
        "type": "user",
        "role": "writer",
        "emailAddress": settings.email,
    }
    service = await wrapper_services.discover("drive", DRIVE_API_VERSION)
    await wrapper_services.as_service_account(
        service.permissions.create(
            fileId=spreadsheet_id, json=permissions_body, fields="id"
        )
    )


async def spreadsheets_update_value(
        spreadsheet_id: str,
        project_list: list,
        wrapper_services: Aiogoogle
) -> None:
    """Заполнение таблицы данными."""
    now_date_time = datetime.now().strftime(FORMAT)
    service = await wrapper_services.discover(
        "sheets",
        SPREADSHEETS_API_VERSION)
    table_values = [
        ["Отчет", now_date_time],
        ["Топ проектов"],
        ["Название проекта", "Время сбора", "Описание", "Сумма"],
    ]
    for project in project_list:
        new_row = [
            str(project[0]),
            str(project[2]),
            str(project[3]),
            str(project[4]),
        ]
        table_values.append(new_row)

    update_body = {"majorDimension": "ROWS", "values": table_values}

    await wrapper_services.as_service_account(
        service.spreadsheets.values.update(
            spreadsheetId=spreadsheet_id,
            range="A1:D100",
            valueInputOption="USER_ENTERED",
            json=update_body,
        )
    )
