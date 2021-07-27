from pg_orm.errors import ValidationError


class Validator:
    def __call__(self):
        raise NotImplementedError


class ValueValidator(Validator):
    def __init__(
        self, min_value: int = None, max_value: int = None, message=None
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.error_message = message

        if not min_value and not max_value:
            raise TypeError("Need to pass in min_value or max_value to ValueValidator")

    def __call__(self, data: int):
        if not isinstance(data, int):
            raise ValueError("Data passed into ValueValidator needs to be int")

        data = int(data)

        if self.min_value is not None:
            if data < self.min_value:
                if self.error_message is not None:
                    raise ValidationError(self.error_message)
                else:
                    raise ValidationError

        if self.max_value is not None:
            if data > self.max_value:
                if self.error_message is not None:
                    raise ValidationError(self.error_message)
                else:
                    raise ValidationError


class LengthValidator(Validator):
    def __init__(
        self, min_length: int = None, max_length: int = None, message=None
    ):
        
        self.min_length=min_length
        self.max_length=max_length
        self.error_message=message

        if not min_length and not max_length:
            raise TypeError(
                "Need to pass in min_length or max_length to LengthValidator"
            )

    def __call__(self, data):
        data_length = len(data)

        if self.min_length is not None:
            if data_length < self.min_length:
                if self.error_message is not None:
                    raise ValidationError(self.error_message)
                else:
                    raise ValidationError

        if self.max_length is not None:
            if data_length > self.max_length:
                if self.error_message is not None:
                    raise ValidationError(self.error_message)
                else:
                    raise ValidationError
