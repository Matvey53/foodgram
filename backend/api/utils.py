def encode_base36(number):
    alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'

    if number == 0:
        return '0'

    result = ''

    while number > 0:
        number, remainder = divmod(number, 36)
        result = alphabet[remainder] + result

    return result

def decode_base36(code):
    return int(code, 36)