import base64

def sourceAndArgNamer(source, stringUserArgs):
    return '{source}_{encodedArgs}'.format(
        source = source,
        encodedArgs = base64.b64encode(''.join(list(stringUserArgs.values())).encode()).decode().replace('=', '')
    )