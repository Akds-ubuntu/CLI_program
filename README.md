# SMS Клиент (CLI программа)

Это консольный клиент для тестового сервиса отправки SMS сообщений.

## Требования

Перед использованием необходимо установить:

- Python 3.7 или новее
- Mock-сервер Prism (инструкция ниже)

## Установка

1. Установите зависимости Python:
```bash
pip install -r requirements.txt
```

2. Настройте mock-сервер Prism:

### Скачайте Prism
Загрузите версию для вашей ОС:
- [Windows](https://github.com/stoplightio/prism/releases)
- [Linux](https://github.com/stoplightio/prism/releases)
- [macOS](https://github.com/stoplightio/prism/releases)

### Настройка Prism
1. Поместите скачанный файл Prism в корневую папку проекта (рядом с `sms-platform.yaml`)
2. Дайте права на выполнение (Linux/macOS):
```bash
chmod +x Prism_CLI_*
```

## Использование

### 1. Запуск mock-сервера
Выполните в корне проекта:
```bash
./Prism_CLI_[ВашаОС] mock sms-platform.yaml
```
(Замените `[ВашаОС]` на вашу платформу: `MacOS`, `Linux` или `Windows.exe`)

### 2. Отправка SMS
Когда сервер запущен, отправляйте сообщения командой:
```bash
python CLI/sms_client.py \
  --config CLI/config.toml \
  --sender "НОМЕР_ОТПРАВИТЕЛЯ" \
  --recipient "НОМЕР_ПОЛУЧАТЕЛЯ" \
  --message "ТЕКСТ_СООБЩЕНИЯ"
```

## Пример
```bash
python CLI/sms_client.py \
  --config CLI/config.toml \
  --sender "+79991234567" \
  --recipient "+79998765432" \
  --message "Тестовое сообщение"
```

## Конфигурация
Настройки сервиса можно изменить в файле `CLI/config.toml`.

## Важно
- Mock-сервер должен быть запущен во время работы клиента
- Номера телефонов указывайте в международном формате (для России +7XXXXXXXXXX)
