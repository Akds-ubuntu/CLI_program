import re
from typing import TypedDict


class FieldResult(TypedDict):
    status: bool
    message: str

class ValidationResult(TypedDict):
    status: bool
    sender: FieldResult
    recipient: FieldResult
    message: FieldResult

class SmsValidator:
    @staticmethod
    def validate_phone_number(phone_number:str)->FieldResult:
        # if isinstance(phone_number, str):
        #     return {'status': False, 'message': "Номер должен быть строкой"}
        result = re.match(r'^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$',
                          phone_number)
        if not result:
            return {'status': False, 'message': "Номер не соответствует формату"}
        return {'status': True, 'message': "Номер корректен"}
    @staticmethod
    def validate_message(message:str)->FieldResult:
        if isinstance(message, str) and len(message)>1:
            return {'status': True, 'message': "Cообщение корректно"}
        return {'status': False, 'message': 'Ошибка: сообщение должно быть непустой строкой'}
    @classmethod
    def validator(cls,sender:str,recipient:str,message:str)-> ValidationResult :
        sender=cls.validate_phone_number(sender)
        recipient=cls.validate_phone_number(recipient)
        message=cls.validate_message(message)
        if sender['status'] is False or recipient['status'] is False or message['status'] is False:
            return {
                'status': False,
                'sender': sender,
                'recipient': recipient,
                'message': message
            }
        else:
            return {
                'status': True,
                'sender': sender,
                'recipient': recipient,
                'message': message
            }