import argparse
import base64
import json
import logging
import socket

import toml
from typing import Dict

from validators import SmsValidator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='sms_client.log',
)
logger = logging.getLogger(__name__)

def parse_url(url: str) -> dict:
    """Функция для парсинга URL"""
    result = {
        'protocol': '',
        'host': '',
        'port': 0,
        'path': ''
    }

    # Удаляем протокол если есть
    if '://' in url:
        protocol, rest = url.split('://', 1)
        result['protocol'] = protocol
    else:
        rest = url

    parts = rest.split('/', 1)
    host_port = parts[0]
    result['path'] = '/' + parts[1] if len(parts) > 1 else '/'

    # Разбираем хост и порт
    if ':' in host_port:
        host, port = host_port.split(':', 1)
        result['host'] = host
        try:
            result['port'] = int(port)
        except ValueError:
            logger.error('Invalid port number',exc_info=True)
    else:
        result['host'] = host_port
        result['port'] = 443 if result['protocol'] == 'https' else 80

    return result
class HttpRequest:
    def __init__(self, method: str, path: str, headers: Dict[str,str], body=None):
        self.method = method
        self.path = path
        self.headers = headers
        self.body = body
    def to_bytes(self) -> bytes:
        p_url=parse_url(self.path)
        if self.body:
            body= json.dumps(self.body, ensure_ascii=False)
        else:
            body=''
        headers = self.headers.copy()
        headers['Host'] = p_url['host']
        headers['Content-Length'] = str(len(body.encode('utf-8')))
        headers['Connection'] = 'close'
        first_line=f"{self.method} {p_url['path']} HTTP/1.1\r\n"
        headers="\r\n".join([f"{k}: {v}" for k, v in headers.items()])
        return f"{first_line}{headers}\r\n\r\n{body}".encode('utf-8')
    @classmethod
    def from_bytes(cls, bin_data: bytes)-> 'HttpRequest':
        data=bin_data.decode('utf-8')
        lines = data.split("\r\n")
        method, path, _ = lines[0].split(" ")
        headers = {}
        body = None
        empty_line_idx = lines.index("") if "" in lines else len(lines)
        # Парсим заголовки
        for line in lines[1:empty_line_idx]:
            if ": " in line:
                key, value = line.split(": ", 1)
                headers[key] = value

        # Парсим тело
        if empty_line_idx + 1 < len(lines):
            body_str = "\r\n".join(lines[empty_line_idx + 1:])
            if body_str:
                body = json.loads(body_str)

        return cls(method, path, headers, body)

class HttpResponse:
    def __init__(self,status_line:int,headers:Dict[str,str],body):
        self.status_line = status_line
        self.headers = headers
        self.body = body
    def to_bytes(self) -> bytes:
        body_str = json.dumps(self.body, ensure_ascii=False) if self.body else ""
        headers_str = "\r\n".join([f"{k}: {v}" for k, v in self.headers.items()])
        return f"HTTP/1.1 {self.status_line}\r\n{headers_str}\r\n\r\n{body_str}".encode('utf-8')

    @classmethod
    def from_bytes(cls, binary_data: bytes) -> 'HttpResponse':
        try:
            data = binary_data.decode('utf-8')
            lines = data.split("\r\n")

            if not lines:
                return cls(500, {}, {"error": "Empty response"})

            status_line = lines[0].split(" ")
            if len(status_line) < 2:
                return cls(500, {}, {"error": "Invalid status line"})

            status_code = int(status_line[1])
            headers = {}
            body = None

            empty_line_idx = lines.index("") if "" in lines else len(lines)

            # Парсим заголовки
            for line in lines[1:empty_line_idx]:
                if ": " in line:
                    key, value = line.split(": ", 1)
                    headers[key] = value

            # Парсим тело
            if empty_line_idx + 1 < len(lines):
                body_str = "\r\n".join(lines[empty_line_idx + 1:])
                if body_str:
                    try:
                        body = json.loads(body_str)
                    except json.JSONDecodeError:
                        body = {"raw_response": body_str}

            return cls(status_code, headers, body)

        except Exception as e:
            return cls(500, {}, {"error": f"Response parsing error: {str(e)}"})
def load_config(config_path: str) -> Dict:
    with open(config_path, 'r', encoding='utf-8') as f:
        return toml.load(f)
def send_request(http_request: HttpRequest, host: str, port: int = 4010) -> HttpResponse:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(10)
            sock.connect((host, port))

            # Логируем отправляемый запрос
            request_data = http_request.to_bytes()
            # print(request_data.decode('utf-8'))
            logger.debug(
                "Sending request to %s:%d\n%s",
                host,
                port,
                request_data.decode('utf-8')
            )

            sock.sendall(request_data)

            # Получаем ответ
            response_data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk

            logger.debug("Received response:\n%s", response_data.decode('utf-8'))
            return HttpResponse.from_bytes(response_data)

    except socket.timeout:
        return HttpResponse(500, {}, {"error": "Connection timeout"})
    except ConnectionRefusedError:
        return HttpResponse(500, {}, {"error": "Connection refused"})
    except Exception as e:
        return HttpResponse(500, {}, {"error": f"Connection error: {str(e)}"})
def main():
    """Основная функция CLI"""
    parser = argparse.ArgumentParser(description="SMS отправщик")
    parser.add_argument("--config", required=True, help="Путь к файлу конфигурации")
    parser.add_argument("--sender", required=True, help="Номер отправителя")
    parser.add_argument("--recipient", required=True, help="Номер получателя")
    parser.add_argument("--message", required=True, help="Текст сообщения")
    args = parser.parse_args()
    validate_res=SmsValidator().validator(sender=args.sender, recipient=args.recipient, message=args.message)
    if validate_res['status'] is False:
        logger.error("Ошибки валидации ввода:")
        args.sender = None
        args.recipient = None
        args.message = None
        for field_name, field_result in validate_res.items():
            if field_name == 'status':
                continue
            if not field_result['status']:
                logger.error("- %s: %s", field_name, field_result['message'])

    # Загружаем конфиг
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error("Config loading error: %s", str(e))
        print(f"Ошибка загрузки конфигурации: {str(e)}")
        return

    # Логируем параметры
    logger.info(
        "Starting with params: sender=%s, recipient=%s, message=%s",
        args.sender, args.recipient, args.message
    )

    # Формируем базовую авторизацию
    try:
        auth = base64.b64encode(
            f"{config['username']}:{config['password']}".encode('utf-8')
        ).decode('utf-8')
    except Exception as e:
        logger.error("Auth error: %s", str(e), exc_info=True)
        auth = None

    # Формируем запрос
    request = HttpRequest(
        method="POST",
        path=f"{config['server']}/send_sms",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body={
            "sender": args.sender,
            "recipient": args.recipient,
            "message": args.message
        }
    )
    logger.debug("Request headers: %s", request.headers)

    # Отправляем запрос
    parsed_url = parse_url(config["server"])
    response = send_request(
        request,
        parsed_url['host'],
        parsed_url['port']
    )

    # Выводим результат
    print(f"Код ответа: {response.status_line}")
    print(f"Тело ответа: {response.body}")
    # Логируем результат
    if response.status_line in (500,400,401):
        logger.error(
            "Response: status=%s, body=%s",
            response.status_line, response.body
        )
    else:
        logger.info(
            "Response: status=%s, body=%s",
            response.status_line, response.body)


if __name__ == "__main__":
    main()